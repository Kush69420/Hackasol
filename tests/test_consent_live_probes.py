import copy
import json

from auditor.consent.criteria import assess_consent, attach_live_probes
from test_consent_assessment_criteria import NoLLM, empty_graph


def _report(findings=()):
    graph = empty_graph()
    graph['controls'] = [{'id': 'c', 'name': 'consent_email', 'default_selected': False, 'evidence': []}]
    assessment = assess_consent(graph, list(findings), NoLLM())
    return {'target': {'name': 'trackmyrupee', 'commit': '47990e4f19d7debea70c5d56bab77e3c3f051546'},
            'findings': list(findings), 'consent_assessment': assessment}


def _outcome(assertion, result, criterion='enforced server-side', **extra):
    return {'assertion': assertion, 'finding_id': None, 'result': result, 'method': 'POST',
            'route': '/accounts/signup/', 'reason': f'{assertion} reason', 'request': 'req [masked]',
            'response': 'resp [masked]', 'criterion': criterion, **extra}


def _row(report, name):
    return next(row for row in report['consent_assessment']['criteria'] if row['criterion'] == name)


def test_probe_outcomes_attach_to_their_criterion_only():
    report = _report()
    attached = attach_live_probes(report, [
        _outcome('consent-declined:consent_email', 'Refuted', purpose='Email Address'),
        _outcome('analytics-withdrawn', 'Confirmed', purpose='Analytics'),
        _outcome('comparable-ease', 'inconclusive', criterion='withdrawable with comparable ease'),
        _outcome('transport', 'Confirmed', criterion=None),
    ], observed_at='2026-11-23T00:00:00+00:00')
    assert attached == 3
    enforced = _row(report, 'enforced server-side')['live_probes']
    assert [(p['assertion'], p['status']) for p in enforced] == [
        ('consent-declined:consent_email', 'Not Confirmed'), ('analytics-withdrawn', 'Confirmed')]
    assert enforced[0]['meaning'] == 'enforcement observed' and enforced[1]['meaning'] == 'violation observed'
    ease = _row(report, 'withdrawable with comparable ease')['live_probes']
    assert [(p['assertion'], p['status']) for p in ease] == [('comparable-ease', 'Inconclusive')]
    assert 'no effect' in ease[0]['meaning']
    others = [row for row in report['consent_assessment']['criteria']
              if row['criterion'] not in ('enforced server-side', 'withdrawable with comparable ease')]
    assert others and all('live_probes' not in row for row in others)
    run = report['consent_assessment']['live_probe_run']
    assert run == {'target': 'trackmyrupee', 'commit': '47990e4f19d7debea70c5d56bab77e3c3f051546',
                   'observed_at': '2026-11-23T00:00:00+00:00'}


def test_probes_never_rewrite_static_verdicts_or_create_findings():
    report = _report()
    before = copy.deepcopy(report)
    attach_live_probes(report, [_outcome('analytics-declined', 'Confirmed')])
    for row, old in zip(report['consent_assessment']['criteria'], before['consent_assessment']['criteria']):
        assert {k: v for k, v in row.items() if k != 'live_probes'} == old
    assert report['findings'] == before['findings'] == []
    assert report['consent_assessment']['graph'] == before['consent_assessment']['graph']


def test_absence_of_probe_results_changes_nothing():
    report = _report()
    before = json.dumps(report, sort_keys=True)
    assert attach_live_probes(report, []) == 0
    assert json.dumps(report, sort_keys=True) == before
    assert attach_live_probes(report, [_outcome('transport', 'Confirmed', criterion=None)]) == 0
    assert json.dumps(report, sort_keys=True) == before
    assert attach_live_probes({'target': {}, 'consent_assessment': None}, [_outcome('x', 'Confirmed')]) == 0


def test_rerun_replaces_previous_probe_evidence():
    report = _report()
    static = json.dumps(report, sort_keys=True)
    attach_live_probes(report, [_outcome('analytics-declined', 'Confirmed')])
    attach_live_probes(report, [_outcome('analytics-declined', 'Refuted')])
    assert [p['status'] for p in _row(report, 'enforced server-side')['live_probes']] == ['Not Confirmed']
    attach_live_probes(report, [])
    assert json.dumps(report, sort_keys=True) == static


def test_trackmyrupee_probe_outcomes_name_a_criterion():
    from auditor.consent.criteria import _CRITERIA
    from auditor.probes.trackmyrupee import run_browser
    names = {name for name, *_ in _CRITERIA}
    results = run_browser('http://127.0.0.1:1')
    assert {item['assertion'] for item in results} >= {'consent-after-withdrawal', 'comparable-ease',
                                                      'analytics-declined', 'withdrawal-data-removal'}
    assert all(item['criterion'] in names and item['finding_id'] is None for item in results)


def test_probed_report_validates_and_renders_live_probe_line(tmp_path):
    from auditor.report import render_markdown
    from auditor.schema import validate_report
    from test_schema import make_report
    probed = _report()
    attach_live_probes(probed, [_outcome('analytics-declined', 'Confirmed', purpose='Analytics')],
                       observed_at='2026-11-23T00:00:00+00:00')
    report = make_report(target={'name': 'trackmyrupee', 'source': 'targets/trackmyrupee', 'kind': 'path',
                                 'commit': probed['target']['commit']},
                         consent_assessment=probed['consent_assessment'])
    validate_report(report)
    markdown = render_markdown(report)
    assert 'Live Probe (trackmyrupee @ 47990e4f19d7, 2026-11-23T00:00:00+00:00): Confirmed (violation observed)' in markdown
    assert 'analytics-declined' in markdown
