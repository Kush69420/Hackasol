import json

import pytest

from auditor import rag
from auditor.rag import retrieve_examples, retrieve_provisions
from auditor.registry import load_registry
from auditor.remediation import load_catalogue


@pytest.mark.parametrize('issue', load_catalogue().values(), ids=lambda issue: issue.id)
def test_catalogue_provisions_are_seeded_at_eight(issue):
    registry = load_registry()
    query = 'Process and store Personal Data only for the specified Purpose.'
    result = retrieve_provisions([issue.id], query)
    assert result == retrieve_provisions([issue.id], query)
    ids = [row['id'] for row in result]
    assert len(ids) == len(set(ids)) == 8
    assert ids[:1 + len(issue.related)] == [issue.primary, *issue.related]
    for pid in (issue.primary, *issue.related):
        parent = registry[pid].parent
        while parent:
            assert parent in ids
            parent = registry[parent].parent
    for row in result:
        provision = registry[row['id']]
        assert row == dict(id=provision.id, citation=provision.citation,
                           title=provision.title, text=provision.excerpt)


def test_tiny_budget_preserves_all_structured_seeds():
    result = retrieve_provisions(['SEC-07', 'CON-01'], '', k=1)
    ids = [row['id'] for row in result]
    assert ids[:3] == ['DPDP-Rule-6(1)(b)', 'CWE-639', 'OWASP-API1-2023']
    assert {'DPDP-Act-6(1)', 'DPDP-Rule-6', 'DPDP-Rule-6(1)'} <= set(ids)


def test_examples_rank_nested_fixtures_and_keep_both_labels():
    query = 'morgan :method :url log statement'
    result = retrieve_examples('SEC-01', query)
    assert result == retrieve_examples('SEC-01', query)
    assert [row['label'] for row in result] == ['positive', 'negative']
    assert all(row['issue_type'] == 'SEC-01' and 0 < len(row['code'].splitlines()) <= 60 for row in result)
    assert 'morgan' in result[0]['code']
    assert retrieve_examples('unknown', query) == []


_QUERIES = (
    'Process and store Personal Data only for the specified Purpose.',
    'morgan :method :url log statement',
    'ContactEmail john.doe@example.com in userProfile update',
)


def _bm25_state(bm25):
    return {
        'ids': list(bm25.ids),
        'postings': [[term, idf, sorted(rows)] for term, (idf, rows) in sorted(bm25.postings.items())],
    }


def _index_bytes():
    rag._index.cache_clear()
    _, catalogue, provisions, fixtures = rag._index()
    state = {
        'provisions': _bm25_state(provisions),
        'fixtures': {
            issue: {'bm25': _bm25_state(bm25), 'code': sorted(code.items())}
            for issue, (bm25, code) in sorted(fixtures.items())
        },
        'retrieval': {
            query: {
                issue: {
                    'provisions': [row['id'] for row in retrieve_provisions([issue], query)],
                    'examples': [[row['label'], row['code']] for row in retrieve_examples(issue, query)],
                }
                for issue in sorted(catalogue)
            }
            for query in _QUERIES
        },
    }
    return json.dumps(state, sort_keys=True, separators=(',', ':')).encode()


def test_index_build_is_byte_reproducible(monkeypatch):
    registry = load_registry()
    catalogue = load_catalogue()
    first = _index_bytes()
    monkeypatch.setattr(rag, 'load_registry', lambda: dict(reversed(registry.items())))
    monkeypatch.setattr(rag, 'load_catalogue', lambda: dict(reversed(catalogue.items())))
    assert list(rag.load_registry()) == list(reversed(registry))
    try:
        second = _index_bytes()
    finally:
        rag._index.cache_clear()
    assert first == second
    assert json.loads(first)['provisions']['ids'] == sorted(p.id for p in registry.values())
