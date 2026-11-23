"""Offline retrieval over registry excerpts and the Labelled Corpus."""
from collections import Counter, defaultdict
from functools import lru_cache
from itertools import zip_longest
from math import log1p
from pathlib import Path
import re

from auditor.exclusions import iter_target_files
from auditor.masking import mask_for_egress
from auditor.registry import load_registry
from auditor.remediation import load_catalogue

_CORPUS = Path(__file__).resolve().parents[2] / 'corpus'
_LABELS = ('positive', 'negative')
_MAX_EXAMPLE_LINES = 60


def _tokens(text):
    # Split snake_case and camelCase, so code and prose use the same vocabulary.
    return re.findall(r'[^\W_]+', re.sub(r'(?<=[a-z0-9])(?=[A-Z])', ' ', text).casefold())


class _BM25:
    def __init__(self, documents):
        counts = {id_: Counter(_tokens(text)) for id_, text in documents.items()}
        lengths = {id_: sum(terms.values()) for id_, terms in counts.items()}
        average = sum(lengths.values()) / max(1, len(counts)) or 1
        postings = defaultdict(list)
        for id_, terms in counts.items():
            normalizer = 1.5 * (0.25 + 0.75 * lengths[id_] / average)
            for term, frequency in terms.items():
                postings[term].append((id_, frequency * 2.5 / (frequency + normalizer)))
        self.ids = tuple(sorted(counts))
        self.postings = {
            term: (log1p((len(counts) - len(rows) + 0.5) / (len(rows) + 0.5)), rows)
            for term, rows in postings.items()
        }

    def rank(self, query):
        scores = dict.fromkeys(self.ids, 0.0)
        # Sort unique terms so ties cannot depend on hash seed or summation order.
        for term in sorted(set(_tokens(query))):
            if term not in self.postings:
                continue
            idf, rows = self.postings[term]
            for id_, weight in rows:
                scores[id_] += idf * weight
        return sorted(self.ids, key=lambda id_: (-scores[id_], id_))


@lru_cache(maxsize=1)
def _index():
    registry = load_registry()
    catalogue = load_catalogue()
    provisions = _BM25({p.id: f'{p.citation}\n{p.title}\n{p.excerpt}' for p in registry.values()})

    examples = defaultdict(dict)
    for rule in sorted(_CORPUS.iterdir()):
        issue = rule.name[:6]
        if not rule.is_dir() or issue not in catalogue or rule.name[6:7] != '-':
            continue
        for label in _LABELS:
            root = rule / label
            # Accuracy evaluates each Rule/label tree as one fixture, including nested files.
            files, _ = iter_target_files(root, 'corpus')
            code = '\n'.join(path.read_text(encoding='utf-8', errors='replace') for path in files)
            if code.strip():
                examples[issue][(rule.name, label)] = code
    fixtures = {
        issue: (_BM25(documents), {
            id_: '\n'.join(code.splitlines()[:_MAX_EXAMPLE_LINES])
            for id_, code in documents.items()
        })
        for issue, documents in examples.items()
    }
    return registry, catalogue, provisions, fixtures


def retrieve_provisions(issue_types, query, k=8):
    """Seed catalogue Provisions and their parents, then use BM25 to reach k if needed."""
    registry, catalogue, bm25, _ = _index()
    if isinstance(issue_types, str):
        issue_types = (issue_types,)
    issues = [catalogue[id_] for id_ in issue_types]
    ids = dict.fromkeys(pid for issue in issues for pid in (issue.primary, *issue.related))
    for pid in tuple(ids):
        while parent := registry[pid].parent:
            ids.setdefault(parent)
            pid = parent

    if len(ids) < k:
        text = '\n'.join([mask_for_egress(query), *(issue.title for issue in issues)])
        for pid in bm25.rank(text):
            ids.setdefault(pid)
            if len(ids) == k:
                break

    return [dict(id=p.id, citation=p.citation, title=p.title, text=p.excerpt)
            for p in (registry[pid] for pid in ids)]


def retrieve_examples(issue_type, query, n=2):
    """Return up to n nearest fixtures, alternating positive and negative labels."""
    *_, fixtures = _index()
    if issue_type not in fixtures or n <= 0:
        return []
    bm25, code = fixtures[issue_type]
    ranked = bm25.rank(mask_for_egress(query))
    by_label = {label: [id_ for id_ in ranked if id_[1] == label] for label in _LABELS}
    balanced = [id_ for pair in zip_longest(*(by_label[label] for label in _LABELS))
                for id_ in pair if id_ is not None]
    return [dict(issue_type=issue_type, label=id_[1], code=code[id_]) for id_ in balanced[:n]]
