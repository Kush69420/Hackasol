from pathlib import Path
import re
from copy import deepcopy
from dataclasses import replace

import pytest

from auditor.rules.context import build_context
from auditor.rules import secrets_logging as rules


@pytest.fixture(scope='module')
def context():
    return build_context(Path('targets/juice-shop'), 'juice-shop')


def test_query_and_log_flows(context):
    url = rules.query_secrets(context)
    logs = rules.logged_secrets(context)
    assert len(url) >= 3 and len(logs) >= 3
    assert {m.element['name'] for m in url} >= {
        'param:GET /rest/user/change-password?current',
        'param:GET /rest/user/change-password?new',
        'param:GET /rest/user/change-password?repeat',
    }
    assert all(any(e['file'].endswith('user.service.ts') and e['start_line'] <= 55 <= e['end_line'] for e in m.evidence) for m in url)
    assert all(any(s['evidence']['file'] == 'server.ts' and s['evidence']['start_line'] == 370 and s['operation'] == 'Log' for s in m.data_flow) for m in logs)
    assert [m.evidence for m in url] == [m.evidence for m in logs]


def test_retention(context):
    matches = rules.short_retention(context)
    assert matches
    assert all(m.classification == 'compliance-gap' and m.base_vector is None and m.gate_evidence for m in matches)
    assert any(e['file'] == 'server.ts' and e['start_line'] <= 368 <= e['end_line'] for m in matches for e in m.evidence)
    assert all('terraform' not in e['file'] for m in matches for e in m.evidence)


def test_hash_and_signing(context):
    hashing = rules.weak_password_hash(context)
    signing = rules.hardcoded_jwt(context)
    assert any(e['file'] == 'lib/insecurity.ts' and e['start_line'] == 41 for m in hashing for e in m.evidence)
    assert any(e['file'] == 'models/user.ts' and e['start_line'] <= 73 <= e['end_line'] for m in hashing for e in m.evidence)
    assert any(e['file'] == 'lib/insecurity.ts' and e['start_line'] == 21 for m in signing for e in m.evidence)
    assert any('model:User.password' in m.nexus_elements for m in signing)
    assert all('BEGIN RSA PRIVATE KEY' not in e['excerpt'] and 'fixture-signing-material' not in e['excerpt'] for m in signing for e in m.evidence)


def test_storage(context):
    matches = rules.storage_header(context)
    by_element = {m.element['name']: m for m in matches}
    assert len(matches) == len(by_element) == 2
    email = by_element['storage:localStorage.email']
    token = by_element['storage:localStorage.token']
    assert any(e['file'].endswith('login.component.ts') and e['start_line'] == 106 for e in email.evidence)
    assert any(e['file'].endswith('request.interceptor.ts') and e['start_line'] == 23 for e in email.evidence)
    assert len(token.evidence) == 5
    assert [(e['file'], e['start_line']) for e in token.evidence[:-1]] == sorted(
        (e['file'], e['start_line']) for e in token.evidence[:-1])
    assert token.evidence[-1]['file'].endswith('request.interceptor.ts')
    assert token.evidence[-1]['start_line'] == 16


def test_guarded_headers_do_not_suppress_authentication_secret_storage(context):
    inventory = deepcopy(context.inventory)
    for header in inventory['outbound_headers']:
        header['origin_guard'] = True
    matches = rules.storage_header(replace(context, inventory=inventory))
    assert [m.element['name'] for m in matches] == ['storage:localStorage.token']

def test_no_signing_material_in_evidence(context):
    source = (context.root / 'lib/insecurity.ts').read_text()
    literal = re.search(r"const privateKey\s*=\s*'([^']+)'", source).group(1)
    detectors = (rules.query_secrets, rules.logged_secrets, rules.short_retention,
                 rules.weak_password_hash, rules.hardcoded_jwt, rules.storage_header)
    for detect in detectors:
        for match in detect(context):
            for evidence in [*match.evidence, *(match.gate_evidence or []),
                             *(step['evidence'] for step in match.data_flow)]:
                assert literal not in evidence['excerpt']
