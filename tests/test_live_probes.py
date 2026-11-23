import json
import importlib.util
from pathlib import Path
from threading import Thread

import httpx
import pytest

from auditor.probes import ProbeClient, authorize, run


def test_safety_rejects_unallowlisted_origin():
    with pytest.raises(ValueError):
        authorize('https://example.com')
    assert authorize('http://127.0.0.1:3000') == 'http://127.0.0.1:3000'
    assert authorize('https://example.com', ('https://example.com',)) == 'https://example.com:443'


def test_safety_rejects_unowned_and_redirects():
    client = ProbeClient('http://127.0.0.1:3000')
    calls = []
    client.client.close()
    client.client = httpx.Client(transport=httpx.MockTransport(lambda r: (calls.append(r), httpx.Response(302, headers={'Location': 'https://example.com'}))[1]))
    with pytest.raises(ValueError):
        client.request('POST', '/dataerasure', account='unowned')
    assert not calls
    with pytest.raises(ValueError):
        client.request('GET', '/rest/memories')
    assert len(calls) == 1
    client.close()


@pytest.mark.parametrize(('wildcard', 'expected'), [(True, 'Confirmed'), (False, 'Refuted')])
def test_assertions_cors_and_masking(monkeypatch, wildcard, expected):
    canary = 'synthetic-canary-not-for-display'
    class FakeClient:
        def __init__(self, *args): pass
        def request(self, method, route, **kwargs):
            if method == 'POST': raise ValueError('setup failed')
            return httpx.Response(200, headers={'Access-Control-Allow-Origin': '*' if wildcard else 'https://else.invalid', 'Set-Cookie': canary}, json={'data': [canary]})
        def close(self): pass
    monkeypatch.setattr('auditor.probes.ProbeClient', FakeClient)
    report = {'target': {'name': 'juice-shop', 'commit': 'c9f99228d9d56afb5f5ca7925376292f7fa44b13'}, 'findings': [{'id': 'finding', 'issue_type': 'SEC-11', 'evidence': [{'file': 'server.ts', 'start_line': 185, 'end_line': 185}, {'file': 'server.ts', 'start_line': 670, 'end_line': 670}]}]}
    results = run(report, 'http://127.0.0.1:3000')
    assert results[0]['result'] == expected
    assert results[0]['route'] == '/rest/memories'
    assert canary not in json.dumps(report)
    assert canary not in json.dumps(results)


def test_assertions_failed_setup_is_not_confirmed(monkeypatch):
    class Failed:
        def __init__(self, *args): pass
        def request(self, *args, **kwargs): raise httpx.ConnectError('unavailable')
        def close(self): pass
    monkeypatch.setattr('auditor.probes.ProbeClient', Failed)
    report = {'target': {'name': 'juice-shop', 'commit': 'c9f99228d9d56afb5f5ca7925376292f7fa44b13'}, 'findings': []}
    results = run(report, 'http://127.0.0.1:3000')
    assert results
    assert all(item['result'] == 'inconclusive' for item in results)


@pytest.fixture
def fixture_server():
    spec = importlib.util.spec_from_file_location('probe_fixture', Path(__file__).parent / 'fixtures/probes/server.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    servers = []
    def start(**kwargs):
        server = module.Server(**kwargs)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        servers.append((server, thread))
        return server, f'http://127.0.0.1:{server.server_port}'
    yield start
    for server, thread in servers:
        server.shutdown()
        thread.join()
        server.server_close()


def report_for_fixture():
    def ev(file, line):
        return {'file': file, 'start_line': line, 'end_line': line}
    return {'target': {'name': 'juice-shop', 'commit': 'c9f99228d9d56afb5f5ca7925376292f7fa44b13'}, 'observations': [], 'findings': [
        {'id': 'memory-auth', 'issue_type': 'SEC-07', 'evidence': [ev('routes/memory.ts', 24)]},
        {'id': 'memory-fields', 'issue_type': 'SEC-08', 'evidence': [ev('routes/memory.ts', 24)]},
        {'id': 'cors', 'issue_type': 'SEC-11', 'evidence': [ev('server.ts', 185), ev('server.ts', 670)]},
        {'id': 'erasure', 'issue_type': 'RET-02', 'evidence': [ev('routes/dataErasure.ts', 85)]},
    ]}


@pytest.mark.parametrize(('exposed', 'nested', 'erases', 'auth', 'fields', 'erasure'), [
    (True, True, False, 'Confirmed', 'Confirmed', 'Confirmed'),
    (False, False, True, 'Refuted', 'inconclusive', 'inconclusive'),
    (True, False, False, 'Confirmed', 'Refuted', 'Confirmed'),
])
def test_assertions_synthetic_server_and_masking(fixture_server, exposed, nested, erases, auth, fields, erasure, capsys):
    server, origin = fixture_server(exposed=exposed, nested=nested, erases=erases)
    report = report_for_fixture()
    outcomes = run(report, origin)
    by_name = {item['assertion']: item for item in outcomes}
    assert by_name['SEC-07']['result'] == auth
    assert by_name['SEC-08']['result'] == fields
    assert by_name['RET-02']['result'] == erasure
    assert by_name['transport']['result'] == 'inconclusive'
    assert by_name['consent-after-withdrawal']['result'] == 'inconclusive'
    assert 'finale-generated' in by_name['SEC-07']['request']
    emitted = json.dumps(report) + json.dumps(outcomes) + capsys.readouterr().out
    for account in server.accounts.values():
        assert account['email'] not in emitted
        assert account['password'] not in emitted
    for token in server.tokens:
        assert token not in emitted
    for memory in server.memories:
        assert memory['caption'] not in emitted


def test_safety_rejects_cross_account_writes():
    client = ProbeClient('http://127.0.0.1:3000')
    client.accounts['1'] = {'email': 'synthetic@example.invalid', 'password': 'x', 'token': 'owned'}
    with pytest.raises(ValueError):
        client.request('POST', '/api/SecurityAnswers', account='1', json={'UserId': 2})
    with pytest.raises(ValueError):
        client.request('POST', '/dataerasure', account='1', headers={'Cookie': 'token=other'})
    assert client.count == 0
    client.close()


@pytest.mark.parametrize(('headers', 'expected'), [
    ([], 'inconclusive'),
    (['token=value; Secure; HttpOnly'], 'Refuted'),
    (['token=value; HttpOnly'], 'Confirmed'),
])
def test_assertions_cookie_flags(headers, expected):
    from auditor.probes.assessments import cookie_flags
    result, reason = cookie_flags(headers)
    assert result == expected
    assert 'value' not in reason


@pytest.mark.parametrize(('before', 'after', 'expected'), [
    (True, True, 'Confirmed'), (True, False, 'Refuted'), (False, True, 'inconclusive'), (True, None, 'inconclusive'),
])
def test_assertions_consent_enforcement(before, after, expected):
    from auditor.probes.assessments import consent_enforcement
    assert consent_enforcement(before, after)[0] == expected


@pytest.mark.parametrize(('grant', 'withdrawal', 'expected'), [
    (1, 2, 'Confirmed'), (2, 1, 'Refuted'), (None, 2, 'inconclusive'),
])
def test_assertions_interaction_counts(grant, withdrawal, expected):
    from auditor.probes.assessments import comparable_ease
    assert comparable_ease(grant, withdrawal)[0] == expected


@pytest.mark.parametrize(('enforced', 'expected'), [(False, 'Confirmed'), (True, 'Refuted')])
def test_assertions_playwright_withdrawal_and_masking(enforced, expected, capsys):
    spec = importlib.util.spec_from_file_location('consent_fixture', Path(__file__).parent / 'fixtures/probes/consent_server.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    server = module.Server(enforced=enforced)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        report = {'target': {'name': 'trackmyrupee', 'commit': '47990e4f19d7debea70c5d56bab77e3c3f051546'}, 'findings': []}
        outcomes = run(report, f'http://127.0.0.1:{server.server_port}')
        assert outcomes[0]['result'] == expected
        assert outcomes[1]['result'] == 'inconclusive'
        assert '3 interactions' in outcomes[1]['reason']
        assert 'withdrawal 2' in outcomes[1]['reason']
        serialized = json.dumps(outcomes) + capsys.readouterr().out
        for value in server.account.values():
            assert value not in serialized
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_masking_debug_logs_and_report(fixture_server, caplog, tmp_path):
    import logging
    from auditor.report import render_html, render_markdown
    server, origin = fixture_server()
    report = json.loads(Path('reports/juice-shop/report.json').read_text(encoding='utf-8'))
    caplog.set_level(logging.DEBUG)
    outcomes = run(report, origin)
    rendered = json.dumps(report) + json.dumps(outcomes) + render_html(report) + render_markdown(report) + caplog.text
    for account in server.accounts.values():
        assert account['email'] not in rendered
        assert account['password'] not in rendered
    for token in server.tokens:
        assert token not in rendered
    for memory in server.memories:
        assert memory['caption'] not in rendered


def test_safety_image_revision_checked_before_requests(monkeypatch):
    from types import SimpleNamespace
    from auditor.probes import image_metadata
    monkeypatch.setenv('JUICE_SHOP_IMAGE', 'local-image')
    def inspect(revision):
        return SimpleNamespace(stdout=json.dumps([{'Id': 'sha256:' + 'a' * 64,
            'Config': {'Labels': {'org.opencontainers.image.revision': revision}}}]))
    monkeypatch.setattr('auditor.probes.subprocess.run', lambda *args, **kwargs: inspect('wrong'))
    with pytest.raises(ValueError):
        image_metadata()
    monkeypatch.setattr('auditor.probes.subprocess.run', lambda *args, **kwargs: inspect('c9f99228'))
    assert image_metadata()['image_revision'] == 'c9f99228'


def test_assertions_unmatched_observation_respects_gate(fixture_server):
    _, origin = fixture_server()
    report = report_for_fixture()
    report['findings'] = [f for f in report['findings'] if f['issue_type'] not in ('SEC-07', 'SEC-08')]
    outcomes = run(report, origin)
    observation = next(item for item in outcomes if item['assertion'] == 'SEC-08')
    assert observation['result'] == 'Confirmed'
    assert observation['finding_id'] is None
    assert not any(f['issue_type'] == 'SEC-08' for f in report['findings'])
