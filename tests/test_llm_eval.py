import argparse
import json

import httpx
import pytest

from auditor.llm import evaluate

DEFAULT = 'omp:anthropic/claude-opus-5-5'
OPUS = ('omp', 'anthropic/claude-opus-5-5')
QWEN = ('ollama', 'qwen3.8:27b')
ROUTED = ['--role-model', 'triage=ollama:qwen3.8:27b', '--default', DEFAULT]
NOT_ASSESSED = {'status': 'not assessed'}


def _answer(value):
    return {'status': 'assessed', 'value': value}


def _parser():
    parser = argparse.ArgumentParser()
    evaluate.add_arguments(parser)
    return parser


def test_macro_f1_and_accuracy_match_hand_counts():
    pairs = [('A', 'A'), ('A', 'A'), ('A', 'B'), ('B', 'B'), ('B', 'A'), ('C', None)]
    # Per-class F1: A = 4/6, B = 2/4, C = 0, so macro-F1 = 7/18.
    assert evaluate.macro_f1(pairs) == pytest.approx(7 / 18)
    assert evaluate.accuracy(pairs) == 0.5
    assert evaluate.macro_f1([]) is None
    assert evaluate.accuracy([]) is None


def test_percentile_is_nearest_rank():
    values = list(range(1, 101))
    assert evaluate._percentile(values, 0.025) == 3
    assert evaluate._percentile(values, 0.975) == 98
    assert evaluate._percentile([5], 0.975) == 5


def test_bootstrap_is_reproducible_and_brackets_the_estimate():
    accuracy_only = {'accuracy': evaluate.accuracy}
    assert evaluate.bootstrap([], accuracy_only, 10, 0) == {'accuracy': None}
    both = {'accuracy': evaluate.accuracy, 'macro_f1': evaluate.macro_f1}
    assert evaluate.bootstrap([('A', 'A')] * 10, both, 20, 0) == {'accuracy': [1.0, 1.0], 'macro_f1': [1.0, 1.0]}
    assert evaluate.bootstrap([('A', 'B')] * 10, accuracy_only, 20, 0) == {'accuracy': [0.0, 0.0]}
    pairs = [('A', 'A')] * 15 + [('A', 'B')] * 5
    first = evaluate.bootstrap(pairs, accuracy_only, 200, 0)
    assert evaluate.bootstrap(pairs, accuracy_only, 200, 0) == first
    low, high = first['accuracy']
    assert low < 0.75 < high


def test_score_role_counts_invalid_and_out_of_taxonomy_answers_as_misses():
    rows = [
        ('Contact', _answer({'data_category': 'Contact', 'reason': 'r'})),
        ('Financial', _answer({'data_category': 'Health', 'reason': 'r'})),
        (None, _answer({'data_category': 'Profile', 'reason': 'r'})),
        ('Health', NOT_ASSESSED),
    ]
    result = evaluate.score_role('classification', rows, 20, 0)
    assert (result['items'], result['valid_json_and_citations'], result['scored']) == (4, 3, 3)
    assert result['validity'] == pytest.approx(0.75)
    assert result['accuracy'] == pytest.approx(1 / 3)
    assert result['macro_f1'] == pytest.approx(1 / 3)
    assert (result['out_of_taxonomy_items'], result['out_of_taxonomy_assigned_a_category']) == (1, 1)
    assert 'by_gold' not in result and 'uncertain' not in result


def test_score_role_triage_reports_by_gold_and_uncertain():
    rows = [
        ('true-positive', _answer({'verdict': 'true-positive', 'reason': 'r', 'citations': []})),
        ('true-positive', _answer({'verdict': 'uncertain', 'reason': 'r', 'citations': []})),
        ('false-positive', _answer({'verdict': 'false-positive', 'reason': 'r', 'citations': []})),
        ('false-positive', NOT_ASSESSED),
    ]
    result = evaluate.score_role('triage', rows, 20, 0)
    assert (result['valid_json_and_citations'], result['scored'], result['accuracy']) == (3, 4, 0.5)
    assert result['uncertain'] == 1
    assert result['by_gold'] == {'false-positive': {'items': 2, 'correct': 1},
                                 'true-positive': {'items': 2, 'correct': 1}}
    assert 'macro_f1' not in result


def test_eval_ollama_requests_json_at_zero_temperature_with_the_think_flag():
    seen = []

    def handler(request):
        seen.append((request.url.path, json.loads(request.content)))
        return httpx.Response(200, json={'message': {'content': '{"fix": "x"}'}})

    def provider(think):
        ollama = evaluate._EvalOllama('qwen3.8:27b', 30, think)
        ollama.client = httpx.Client(transport=httpx.MockTransport(handler))
        return ollama

    assert provider(False).complete('system', 'user') == '{"fix": "x"}'
    assert provider(None).complete('system', 'user') == '{"fix": "x"}'
    (path, first), (_, second) = seen
    assert path == '/api/chat'
    assert first['model'] == 'qwen3.8:27b' and first['stream'] is False and first['format'] == 'json'
    assert first['options'] == {'temperature': 0} and first['think'] is False
    assert 'think' not in second


def test_table_shows_intervals_and_n_a_where_a_metric_does_not_apply():
    roles = {
        'classification': {'provider': 'omp', 'model': 'm', 'accuracy': 0.5, 'accuracy_ci95': [0.25, 0.75],
                           'macro_f1': None, 'macro_f1_ci95': None, 'scored': 2,
                           'valid_json_and_citations': 2, 'items': 2},
        'triage': {'provider': 'ollama', 'model': 'q:1', 'accuracy': None, 'accuracy_ci95': None,
                   'scored': 0, 'valid_json_and_citations': 0, 'items': 0, 'uncertain': 0},
    }
    assert evaluate.table(roles).splitlines() == [
        '| Role | Model | Accuracy, 95% CI | Macro-F1, 95% CI | Scored | Valid | Uncertain |',
        '|---|---|---:|---:|---:|---:|---:|',
        '| classification | `omp:m` | 50.0% (25.0-75.0) | n/a | 2 | 2/2 | n/a |',
        '| triage | `ollama:q:1` | n/a | n/a | 0 | 0/0 | 0 |',
    ]


def test_role_assignments_route_each_gold_role_and_fall_back_to_default():
    assert evaluate.role_assignments(None, DEFAULT) == {'classification': OPUS, 'triage': OPUS}
    assert evaluate.role_assignments(['triage=ollama:qwen3.8:27b'], DEFAULT) == {'classification': OPUS, 'triage': QWEN}


def test_role_assignments_reject_unscored_roles_and_bad_specs():
    with pytest.raises(ValueError, match='no held-out gold set for consent, fix'):
        evaluate.role_assignments(['consent=omp:anthropic/claude-opus-5-5', 'fix=omp:anthropic/claude-opus-5-5'], DEFAULT)
    with pytest.raises(ValueError):
        evaluate.role_assignments(['triage=nope:x'], DEFAULT)
    with pytest.raises(ValueError):
        evaluate.role_assignments(None, 'nope:x')
    with pytest.raises(ValueError):
        evaluate.role_assignments(['triage=ollama:a', 'triage=omp:b'], DEFAULT)


def test_defaults_replay_the_auditor_verdict_cache():
    args = _parser().parse_args([])
    assert args.default == DEFAULT
    assert args.cache_root == evaluate.ROOT / '.dpdp-cache'
    assert args.out == evaluate.EVAL / 'results.json'
    assert (args.bootstrap, args.seed, args.workers) == (1000, 0, 4)


def test_bootstrap_must_be_positive_and_the_old_model_flag_is_gone():
    with pytest.raises(SystemExit):
        _parser().parse_args(['--bootstrap', '0'])
    with pytest.raises(SystemExit):
        _parser().parse_args(['--model', 'opus=omp:anthropic/claude-opus-5-5'])


ANSWERS = {
    'evidence A': {'data_category': 'Contact', 'reason': 'r'},
    'evidence B': {'data_category': 'Profile', 'reason': 'r'},
    'evidence T1': {'verdict': 'true-positive', 'reason': 'r', 'citations': ['P1']},
    # Cites a provision that is not in context.provisions, so the answer is invalid.
    'evidence T2': {'verdict': 'true-positive', 'reason': 'r', 'citations': ['NOPE']},
}
ITEMS = [
    ('classification', 'evidence A', {'name': 'a'}, 'Contact'),
    ('classification', 'evidence B', {'name': 'b'}, None),
    ('triage', 'evidence T1', {'provisions': [{'id': 'P1'}]}, 'true-positive'),
    ('triage', 'evidence T2', {'provisions': [{'id': 'P1'}]}, 'false-positive'),
]


class FakeProvider:
    def __init__(self, name, model, calls, available):
        self.name = name
        self.model = model
        self.calls = calls
        self._available = available

    def available(self):
        return self._available

    def complete(self, system, user):
        evidence = json.loads(user)['evidence']
        self.calls.append((self.name, self.model, evidence))
        return json.dumps(ANSWERS[evidence])


def _run(monkeypatch, tmp_path, calls, extra, available=(True, None)):
    monkeypatch.setattr(evaluate, 'load_items', lambda: ITEMS)
    monkeypatch.setattr(evaluate, 'make_provider',
                        lambda name, model, timeout, think: FakeProvider(name, model, calls, available))
    out = tmp_path / 'out.json'
    args = _parser().parse_args([*extra, '--cache-root', str(tmp_path / 'cache'), '--out', str(out),
                                 '--bootstrap', '50'])
    return evaluate.run(args), out


def test_run_scores_each_role_on_its_routed_model(tmp_path, monkeypatch, capsys):
    calls = []
    code, out = _run(monkeypatch, tmp_path, calls, ROUTED)
    assert code == 0
    result = json.loads(out.read_text(encoding='utf-8'))
    assert result['bootstrap'] == {'replicates': 50, 'seed': 0, 'confidence': 0.95}
    cls, tri = result['roles']['classification'], result['roles']['triage']
    assert (cls['provider'], cls['model'], cls['mode']) == ('omp', 'anthropic/claude-opus-5-5', 'live')
    assert (tri['provider'], tri['model']) == ('ollama', 'qwen3.8:27b')
    assert cls['items'] == 2 and cls['valid_json_and_citations'] == 2
    assert cls['scored'] == 1 and cls['accuracy'] == 1.0 and cls['accuracy_ci95'] == [1.0, 1.0]
    assert cls['macro_f1'] == 1.0 and cls['macro_f1_ci95'] == [1.0, 1.0]
    assert (cls['out_of_taxonomy_items'], cls['out_of_taxonomy_assigned_a_category']) == (1, 1)
    assert tri['items'] == 2 and tri['valid_json_and_citations'] == 1
    assert tri['scored'] == 2 and tri['accuracy'] == 0.5 and len(tri['accuracy_ci95']) == 2
    assert tri['uncertain'] == 0
    assert tri['by_gold'] == {'false-positive': {'items': 1, 'correct': 0},
                              'true-positive': {'items': 1, 'correct': 1}}
    assert 'macro_f1' not in tri
    assert {(name, model) for name, model, evidence in calls if evidence in ('evidence A', 'evidence B')} == {OPUS}
    assert {(name, model) for name, model, evidence in calls if evidence.startswith('evidence T')} == {QWEN}
    assert '| triage | `ollama:qwen3.8:27b` |' in capsys.readouterr().out


def test_rerun_replays_cached_verdicts_and_asks_only_for_the_invalid_item(tmp_path, monkeypatch):
    _run(monkeypatch, tmp_path, [], ROUTED)
    calls = []
    code, out = _run(monkeypatch, tmp_path, calls, ROUTED)
    assert code == 0
    result = json.loads(out.read_text(encoding='utf-8'))
    assert result['roles']['classification']['cache_hits'] == 2
    assert result['roles']['triage']['cache_hits'] == 1
    assert {evidence for _, _, evidence in calls} == {'evidence T2'}


def test_unavailable_provider_is_never_asked(tmp_path, monkeypatch, capsys):
    calls = []
    code, out = _run(monkeypatch, tmp_path, calls, ROUTED, available=(False, 'omp is not installed'))
    assert code == 0 and calls == []
    result = json.loads(out.read_text(encoding='utf-8'))
    assert result['roles']['classification']['mode'] == 'cache-only'
    assert result['roles']['classification']['valid_json_and_citations'] == 0
    assert result['roles']['triage']['valid_json_and_citations'] == 0
    assert ('classification on omp:anthropic/claude-opus-5-5 is cache-only (omp is not installed)'
            in capsys.readouterr().err)


def test_run_rejects_a_role_without_a_gold_set(tmp_path, capsys):
    args = _parser().parse_args(['--role-model', 'consent=omp:anthropic/claude-opus-5-5',
                                 '--out', str(tmp_path / 'out.json')])
    assert evaluate.run(args) == 1
    assert 'no held-out gold set for consent' in capsys.readouterr().err
    assert not (tmp_path / 'out.json').exists()
