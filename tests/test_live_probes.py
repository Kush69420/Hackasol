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


@pytest.mark.parametrize(('enforced', 'images', 'profile_mismatch', 'expected'), [
    (False, 0, False, 'Confirmed'),
    (True, 170, False, 'Refuted'),
    (True, 0, True, 'inconclusive'),
])
def test_assertions_playwright_withdrawal_and_masking(enforced, images, profile_mismatch, expected, capsys, monkeypatch):
    monkeypatch.setattr('auditor.probes.trackmyrupee.SETTLE', 0)
    spec = importlib.util.spec_from_file_location('consent_fixture', Path(__file__).parent / 'fixtures/probes/consent_server.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    server = module.Server(enforced=enforced, images=images, profile_mismatch=profile_mismatch)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        report = {'target': {'name': 'trackmyrupee', 'commit': '47990e4f19d7debea70c5d56bab77e3c3f051546'}, 'findings': []}
        outcomes = run(report, f'http://127.0.0.1:{server.server_port}')
        assert outcomes[0]['result'] == expected
        assert outcomes[1]['result'] == 'inconclusive'
        assert server.withdrawal_form_read
        if profile_mismatch:
            assert not server.withdrawn
            assert 'no withdrawal POST was sent' in outcomes[0]['reason']
        else:
            assert server.withdrawn
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


@pytest.fixture
def tmr_consent(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location('tmr_consent_fixture', Path(__file__).parent / 'fixtures/probes/tmr_consent_server.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr('auditor.probes.trackmyrupee.SETTLE', 0.3)
    started = []

    def start(mode, *, sink_response='scoped', **kwargs):
        sink = module.Sink(sink_response)
        server = module.Server(mode, sink, str(tmp_path / f'{mode}.sqlite3'), **kwargs)
        for item in (sink, server):
            thread = Thread(target=item.serve_forever, daemon=True)
            thread.start()
            started.append((item, thread))
        return server, f'http://127.0.0.1:{server.server_port}', f'http://127.0.0.1:{sink.server_port}'
    yield start
    for item, thread in started:
        item.shutdown()
        thread.join()
        item.server_close()


def _consent_results(server, origin, sink):
    from auditor.probes.trackmyrupee import run_consent
    return {item['assertion']: item for item in run_consent(origin, sink, server.db_path)}


def test_tmr_verifies_its_account_and_grants_consent_before_withdrawing(tmr_consent, monkeypatch, caplog):
    server, origin, sink = tmr_consent('enforced', verification=True, consent_redirect=True)
    monkeypatch.setenv('DPDP_TMR_MAIL_DIR', str(server.mailbox))
    caplog.set_level('INFO', logger='httpx')
    results = _consent_results(server, origin, sink)
    assert server.verification_posts == server.consent_posts == server.withdrawal_posts == 1
    assert all(item['result'] == 'Refuted' for item in results.values())
    assert server.verification_keys and all(key not in json.dumps(results) + caplog.text
                                            for key in server.verification_keys)


@pytest.mark.parametrize('mailbox_configured', [False, True])
def test_tmr_pending_verification_cookie_does_not_authorize_withdrawal(tmr_consent, monkeypatch, mailbox_configured):
    server, origin, sink = tmr_consent('enforced', verification=True, foreign_confirmation=True)
    if mailbox_configured:
        monkeypatch.setenv('DPDP_TMR_MAIL_DIR', str(server.mailbox))
    else:
        monkeypatch.delenv('DPDP_TMR_MAIL_DIR', raising=False)
    results = _consent_results(server, origin, sink)
    assert server.verification_posts == server.consent_posts == server.withdrawal_posts == 0
    assert results['withdrawal-data-removal']['result'] == 'inconclusive'
    assert 'verification' in results['withdrawal-data-removal']['reason']


def test_tmr_consent_not_confirmed_when_enforced(tmr_consent):
    server, origin, sink = tmr_consent('enforced')
    results = _consent_results(server, origin, sink)
    assert server.withdrawal_posts == 1
    assert {name: item['result'] for name, item in results.items()} == {
        'consent-declined:consent_email': 'Refuted', 'consent-declined:consent_transactions': 'Refuted',
        'consent-declined:consent_device': 'Refuted', 'analytics-declined': 'Refuted',
        'analytics-withdrawn': 'Refuted', 'withdrawal-data-removal': 'Refuted'}
    assert 'granted control produced 1' in results['analytics-withdrawn']['reason']
    assert all(item['finding_id'] is None and item['criterion'] == 'enforced server-side' for item in results.values())


def test_tmr_consent_confirmed_violation_and_masking(tmr_consent, caplog):
    caplog.set_level('DEBUG')
    server, origin, sink = tmr_consent('violating')
    results = _consent_results(server, origin, sink)
    assert {name: item['result'] for name, item in results.items()} == {
        'consent-declined:consent_email': 'Confirmed', 'consent-declined:consent_transactions': 'Confirmed',
        'consent-declined:consent_device': 'Confirmed', 'analytics-declined': 'Confirmed',
        'analytics-withdrawn': 'Confirmed', 'withdrawal-data-removal': 'Confirmed'}
    assert 'remained after withdrawal' in results['withdrawal-data-removal']['reason'] or 'still authenticated' in results['withdrawal-data-removal']['reason']
    import sqlite3
    with sqlite3.connect(server.db_path) as conn:
        names = [row[0] for row in conn.execute('SELECT username FROM auth_user')]
        passwords = [row[0] for row in conn.execute('SELECT password FROM auth_user')]
    serialized = json.dumps(results) + caplog.text
    assert names and all(value not in serialized for value in names + passwords)
    assert all(scope not in serialized for scope, _ in server.sink.events)


def test_tmr_consent_inconclusive_without_observation_points(tmr_consent):
    from auditor.probes.trackmyrupee import run_consent
    _, origin, _ = tmr_consent('enforced')
    results = {item['assertion']: item for item in run_consent(origin, None, None)}
    assert results['analytics-declined']['result'] == 'inconclusive'
    assert 'unavailable' in results['analytics-declined']['reason']
    assert results['withdrawal-data-removal']['result'] == 'inconclusive'
    assert 'read-only row count' in results['withdrawal-data-removal']['reason']
    assert results['consent-declined:consent_email']['result'] == 'Refuted'


def test_tmr_consent_inconclusive_when_control_signup_fails(tmr_consent):
    results = _consent_results(*tmr_consent('limited'))
    assert all(item['result'] == 'inconclusive' for item in results.values())
    assert 'control signup' in results['consent-declined:consent_device']['reason']


def test_tmr_withdrawal_skips_session_with_mismatched_profile(tmr_consent, monkeypatch):
    server, origin, sink = tmr_consent('profile-mismatch', verification=True, consent_redirect=True)
    monkeypatch.setenv('DPDP_TMR_MAIL_DIR', str(server.mailbox))
    results = _consent_results(server, origin, sink)
    assert server.verification_posts == server.consent_posts == 1
    assert server.withdrawal_form_read
    assert server.withdrawal_posts == 0
    assert results['withdrawal-data-removal']['result'] == 'inconclusive'
    assert 'profile' in results['withdrawal-data-removal']['reason']


@pytest.mark.parametrize('sink_response', ['malformed', 'unscoped', 'invalid-count'])
def test_tmr_analytics_needs_well_formed_scoped_counts(tmr_consent, sink_response):
    results = _consent_results(*tmr_consent('enforced', sink_response=sink_response))
    assert results['analytics-declined']['result'] == 'inconclusive'
    assert results['analytics-withdrawn']['result'] == 'inconclusive'
    assert results['withdrawal-data-removal']['result'] == 'Refuted'


@pytest.mark.parametrize(('mode', 'failed_choice'), [
    ('enforced', 'declined'), ('violating', 'declined'), ('violating', 'accepted'),
])
def test_tmr_analytics_needs_both_login_actions(tmr_consent, mode, failed_choice):
    server, origin, sink = tmr_consent(mode, fail_login=failed_choice)
    results = _consent_results(server, origin, sink)
    assert results['analytics-declined']['result'] == 'inconclusive'
    assert results['analytics-withdrawn']['result'] == 'inconclusive'
    assert server.withdrawal_posts == 1


def test_tmr_analytics_ignores_other_accounts_and_late_events_from_another_action(tmr_consent):
    server, origin, sink = tmr_consent('enforced', noise=True, delayed_control=True)
    results = _consent_results(server, origin, sink)
    assert any(scope == 'another-account' for scope, _ in server.sink.events)
    assert server.pending_control is None  # granted retry arrived during the withdrawn login
    assert results['analytics-declined']['result'] == 'Refuted'
    assert results['analytics-withdrawn']['result'] == 'Refuted'


@pytest.mark.parametrize(('control', 'observed', 'expected'), [
    (1, 0, 'Refuted'), (0, 0, 'inconclusive'), (None, 0, 'inconclusive'), (1, None, 'inconclusive'),
    (0, 2, 'Confirmed'), (None, 2, 'inconclusive'),
])
def test_tmr_declined_processing_branches(control, observed, expected):
    from auditor.probes.assessments import declined_processing
    assert declined_processing(control, observed)[0] == expected
