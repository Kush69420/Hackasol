"""Replay classification and distill grounded triage verdicts for both training splits."""
from argparse import ArgumentParser
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from hashlib import sha256
import json
from math import ceil
from traceback import extract_tb

import yaml

from auditor.exclusions import iter_target_files
from auditor.llm import _mask_object
from auditor.llm.prompts import PROMPT_VERSION
from auditor.rag import _index
from auditor.rules.context import SEMGREP_DIR
from auditor.semgrep import prewarm_semgrep
from training.capture import DATA, EVAL, ROOT, capture, read_jsonl, write_jsonl
from training.dataset import MODEL, label, pinned_root
from training.leakage import REPORT_TARGETS, report_path

ROLE = 'triage'
EXCLUDED = {'edx-platform': 'Auditor crash: strict UTF-8 read at auditor/rules/rights_config.py:67'}
EXCLUSIONS_FILE = DATA / 'triage-exclusions.json'


def capture_triage(path, *, classification_teacher=True, blocked_hashes=frozenset()):
    rows = capture(path, classification_teacher=MODEL if classification_teacher else None,
                   blocked_classification_hashes=blocked_hashes)
    return [row for row in rows if row['role'] == ROLE]


def source_manifest():
    return yaml.safe_load((ROOT / 'training/sources.yaml').read_text(encoding='utf-8'))


def corpus_paths():
    return sorted(p for p in (ROOT / 'corpus').glob('*/*') if p.is_dir() and p.name in {'positive', 'negative'})


def input_path(root):
    relative = root.relative_to(ROOT)
    return DATA / 'triage-inputs' / relative.parent / (relative.name + '.jsonl')


def capture_repository(path, blocked):
    try:
        return capture_triage(path, blocked_hashes=blocked), None
    except Exception as exc:
        # Keep other sources usable without printing request material from errors.
        frames = extract_tb(exc.__traceback__)
        auditor_frames = [frame for frame in frames if frame.filename.startswith(f'{ROOT}/auditor/')]
        frame = (auditor_frames or frames)[-1]
        location = frame.filename.removeprefix(f'{ROOT}/')
        return [], f'Auditor crash: {type(exc).__name__} at {location}:{frame.lineno}'


def capture_inputs():
    exclusions = dict(EXCLUDED)
    paths = [pinned_root(name, source) for name, source in source_manifest().items() if name not in exclusions]
    fixtures = corpus_paths()
    targets = [ROOT / 'targets' / name for name in sorted(REPORT_TARGETS)]
    blocked = frozenset(row['snippet_sha256'] for row in read_jsonl(EVAL / 'classification.jsonl'))
    prime = [(path, [f.relative_to(path) for f in iter_target_files(path, 'corpus')[0]]) for path in fixtures]
    prewarm_semgrep(prime, [SEMGREP_DIR])
    with ProcessPoolExecutor(max_workers=4) as pool:
        ours = {pool.submit(capture_repository, path, blocked): path for path in paths}
        bundled = {pool.submit(capture_triage, path, blocked_hashes=blocked): path for path in fixtures}
        held_out = [pool.submit(capture_triage, path) for path in targets]
        cache_only = [pool.submit(capture_triage, path, classification_teacher=False) for path in targets]
        for job in as_completed([*ours, *bundled]):
            if job in ours:
                path = ours[job]
                rows, error = job.result()
                if error:
                    exclusions[path.name] = error
                    print(f'{path.name}: excluded ({error})', flush=True)
                    continue
                print(f'{path.name}: {len(rows)} triage inputs', flush=True)
            else:
                path, rows = bundled[job], job.result()
            write_jsonl(input_path(path), rows)
        # Only offline capture is run on the Report Targets, to exclude their inputs by hash.
        write_jsonl(DATA / 'eval/triage-inputs.jsonl', (row for job in held_out for row in job.result()))
        write_jsonl(DATA / 'eval/triage-cache-only-inputs.jsonl', (row for job in cache_only for row in job.result()))
    EXCLUSIONS_FILE.write_text(json.dumps(exclusions, indent=2) + '\n', encoding='utf-8')
    print(f'Captured {len(paths) - (len(exclusions) - len(EXCLUDED))} pinned repositories and '
          f'{len(fixtures)} Labelled Corpus fixtures.', flush=True)


def make_dataset():
    class_stats = json.loads((DATA / 'classification-stats.json').read_text(encoding='utf-8'))
    exclusions = json.loads(EXCLUSIONS_FILE.read_text(encoding='utf-8'))
    validation = class_stats['validation_repository']
    eval_rows = [row for path in (EVAL / 'classification.jsonl', DATA / 'eval/triage-inputs.jsonl',
                                  DATA / 'eval/triage-cache-only-inputs.jsonl') for row in read_jsonl(path)]
    eval_hashes = {row['snippet_sha256'] for row in eval_rows}
    eval_sources = {row['source'] for row in eval_rows}
    fixture_index = _index()[-1]
    inputs = DATA / 'triage-inputs'
    stats = defaultdict(Counter)
    candidates = []
    training_root = ROOT / 'targets/training'
    validation_hashes = {row['snippet_sha256'] for row in read_jsonl(input_path(training_root / validation))}
    roots = [*(training_root / name for name in source_manifest() if name not in exclusions), *corpus_paths()]
    for path in sorted(map(input_path, roots)):
        provenance = path.relative_to(inputs).parts
        fixture = provenance[0] == 'corpus'
        name = '/'.join(provenance[:2]) if fixture else path.stem
        split = 'val' if name == validation else 'train'
        allocated = stats[name]
        for row in read_jsonl(path):
            allocated['captured'] += 1
            if report_path(row['source']) or row['source'] in eval_sources or row['snippet_sha256'] in eval_hashes:
                allocated['held_out_overlap'] += 1
                continue
            if split == 'train' and row['snippet_sha256'] in validation_hashes:
                allocated['validation_overlap'] += 1
                continue
            gold = None
            if fixture:
                rule = provenance[1]
                if rule not in row['rules_fired']:
                    allocated['other_rule'] += 1
                    continue
                context = json.loads(row['user'])['context']
                # Assembly may merge neighboring Rules and select a different
                # Issue Type as the one actually presented to triage.
                if context['issue_type'] != rule[:6]:
                    allocated['other_issue'] += 1
                    continue
                fixture_label = path.stem
                gold = 'true-positive' if fixture_label == 'positive' else 'false-positive'
                indexed = fixture_index.get(context['issue_type'])
                if indexed and (code := indexed[1].get((rule, fixture_label))) is not None:
                    if any(example['code'] == _mask_object(code) for example in context['examples']):
                        allocated['self_retrieved'] += 1
            candidates.append((row, name, split, gold))

    values = label((row for row, _, _, _ in candidates), role=ROLE)
    written = defaultdict(list)
    disagreements = []
    for (row, name, split, gold), value in zip(candidates, values):
        allocated = stats[name]
        if value is None:
            allocated['invalid'] += 1
            continue
        if gold and gold != value['verdict']:
            # A reason for the opposite or uncertain verdict cannot be used as-is.
            disagreements.append(dict(row, deterministic_verdict=gold, teacher_value=value))
            allocated['teacher_disagreed'] += 1
            continue
        origin = 'deterministic' if gold else 'teacher'
        verdict = gold or value['verdict']
        messages = [{'role': 'system', 'content': row['system']}, {'role': 'user', 'content': row['user']},
                    {'role': 'assistant', 'content': json.dumps(value, ensure_ascii=False)}]
        written[split].append(({'role': ROLE, 'source': row['source'], 'messages': messages}, verdict, origin))
        allocated[origin] += 1
        allocated[verdict] += 1
    write_jsonl(DATA / 'triage-disagreements.jsonl', disagreements)
    summary = {'prompt_version': PROMPT_VERSION[ROLE], 'excluded_sources': exclusions, 'sources': stats, 'splits': {}}
    for split in ('train', 'val'):
        rows = written[split]
        path = DATA / split / 'triage.jsonl'
        write_jsonl(path, (row for row, _, _ in rows))
        lengths = sorted(ceil(sum(len(m['content']) for m in row['messages']) / 3.5) for row, _, _ in rows)
        summary['splits'][split] = {
            'rows': len(rows), 'counts': Counter(verdict for _, verdict, _ in rows),
            'label_origin': Counter(origin for _, _, origin in rows),
            'tokens_approx': [lengths[ceil(len(lengths) * p) - 1] for p in (.50, .95, 1)] if lengths else [],
            'sha256': sha256(path.read_bytes()).hexdigest(),
        }
    (DATA / 'triage-stats.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary['splits'], indent=2), flush=True)


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('capture', 'label', 'all'), default='all', nargs='?')
    phase = parser.parse_args().phase
    if phase in ('capture', 'all'):
        capture_inputs()
    if phase in ('label', 'all'):
        make_dataset()


if __name__ == '__main__':
    main()
