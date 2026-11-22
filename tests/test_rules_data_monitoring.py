import sqlite3
from pathlib import Path

import pytest

from auditor.mapping import assemble
from auditor.rules.context import build_context
from auditor.rules.data_monitoring import (
    child_consent, child_tracking, committed_data, monitoring, undisclosed_transfer,
)


@pytest.fixture(scope='module')
def ctx():
    return build_context(Path('targets/juice-shop'), 'juice-shop')


def test_seeded_accounts_are_not_reported(ctx):
    assert not any(m.evidence[0]['file'] == 'data/static/users.yml' for m in committed_data(ctx))


def test_dashboard_does_not_monitor_access_or_authentication(ctx):
    matches = monitoring(ctx)
    dashboard = next(m for m in matches if m.evidence[0]['file'] == 'monitoring/grafana-dashboard.json')
    assert dashboard.gate_evidence
    assert dashboard.nexus_elements
    assert any(f['issue_type'] == 'MON-01' for f in assemble([dashboard]).findings)


def test_no_transfer_in_recorded_data_flows(ctx):
    assert undisclosed_transfer(ctx) == []


def test_child_gate_not_determinable(ctx):
    matches = child_consent(ctx)
    assert matches and all(not m.gate_evidence for m in matches)
    assert assemble(matches).not_determinable
    assert not child_tracking(ctx)


def test_committed_values_are_not_exempt_by_extension(tmp_path):
    (tmp_path / 'accounts.yml').write_text('email: synthetic.person@acme-corp.com\n')
    ctx = build_context(tmp_path, 'corpus')
    assert committed_data(ctx)


def test_reserved_domain_is_exempt_without_seed_context(tmp_path):
    (tmp_path / 'records.json').write_text('{"email": "person@example.org"}')
    ctx = build_context(tmp_path, 'corpus')
    assert not committed_data(ctx)


def test_seed_loader_alone_does_not_exempt_valid_values(tmp_path):
    records = tmp_path / 'data' / 'static'
    records.mkdir(parents=True)
    (records / 'accounts.yml').write_text('email: synthetic.person@acme-corp.com\n')
    (tmp_path / 'loader.ts').write_text(
        "function loadStaticData(file: string) { return path.resolve('./data/static/' + file + '.yml') }\n"
        "function loadAccounts() { return loadStaticData('accounts') }\n"
    )
    (tmp_path / 'create.ts').write_text(
        'async function createAccounts() { const accounts = loadAccounts(); await Account.bulkCreate(accounts) }\n'
    )
    assert committed_data(build_context(tmp_path, 'corpus'))


def test_monitoring_absent_is_not_a_finding(tmp_path):
    (tmp_path / 'server.ts').write_text('const app = express()\n')
    ctx = build_context(tmp_path, 'corpus')
    assert not monitoring(ctx)


@pytest.mark.parametrize('value,expected', [
    ('synthetic.person@acme-corp.com', True),
    ('person@example.org', False),
])
def test_sqlite_committed_data_pair(tmp_path, value, expected):
    path = tmp_path / 'accounts.db'
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE accounts (id INTEGER, email TEXT)')
        db.execute('INSERT INTO accounts VALUES (?, ?)', (1, value))
    matches = committed_data(build_context(tmp_path, 'corpus'))
    assert bool(matches) is expected
    if expected:
        assert matches[0].evidence[0]['file'] == 'accounts.db'
        assert value not in matches[0].evidence[0]['excerpt']


@pytest.mark.parametrize('filename,content,expected', [
    ('dump.sql', "INSERT INTO accounts (email) VALUES ('synthetic.person@acme-corp.com');", True),
    ('dump.sql', "INSERT INTO accounts (email) VALUES ('person@example.org');", False),
    ('access.log', 'request by synthetic.person@acme-corp.com', True),
    ('access.log', 'request by person@example.org from 192.0.2.1', False),
])
def test_dump_and_log_pairs(tmp_path, filename, content, expected):
    (tmp_path / filename).write_text(content)
    assert bool(committed_data(build_context(tmp_path, 'corpus'))) is expected
