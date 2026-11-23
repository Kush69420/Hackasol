"""Framework coverage: Prisma, Mongoose, React, Django, Kubernetes and nginx analysers and their Rules."""
from __future__ import annotations

import json
import shutil
from functools import cache
from pathlib import Path

import pytest

from auditor.analysers.framework_flows import trace
from auditor.exclusions import iter_target_files
from auditor.inventory import build_inventory
from auditor.mapping import assemble
from auditor.registry import load_registry
from auditor.rules import load_rules
from auditor.rules.context import build_context
from auditor.schema import validate_report

REPO = Path(__file__).resolve().parents[1]
FIXTURES = REPO / 'tests' / 'fixtures' / 'frameworks'
NEW_RULES = ('SEC-01-nginx-query-logging', 'SEC-16-kubernetes-privileged-store', 'SEC-16-kubernetes-public-store')


def inventory(root: Path) -> dict:
    files, _ = iter_target_files(root, 'corpus')
    return build_inventory(root, files, None)


@cache
def fixture_inventory(name: str) -> dict:
    return inventory(FIXTURES / name)


def flows(name: str) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for flow in trace(fixture_inventory(name)):
        out.setdefault(flow['element_id'], []).append(flow)
    return out


def stages(flow: dict) -> list[tuple]:
    return [(s['stage'], s['source']['file'], s['source']['start_line']) for s in flow['steps']]


def fire(root: Path, rule_id: str) -> list:
    _, detect = load_rules()[rule_id]
    return [m for m in detect(build_context(root, 'corpus')) if m.rule_id == rule_id]


# ---- Prisma ----------------------------------------------------------------------------------

def test_prisma_schema_models_exclude_relations_and_read_datasource():
    inv = fixture_inventory('prisma')
    models = {m['name']: m for m in inv['models'] if m['kind'] == 'prisma'}
    assert set(models) == {'User', 'Post', 'Lead'}
    assert [f['name'] for f in models['User']['fields']] == ['id', 'email', 'phone']
    assert models['User']['fields'][2]['allow_null'] is True
    assert models['User']['fields'][1]['unique'] is True
    assert [f['name'] for f in models['Post']['fields']] == ['id', 'title', 'authorId']
    assert inv['prisma_datasources'][0]['url_env'] == 'DATABASE_URL'
    assert inv['prisma_datasources'][0]['provider'] == 'postgresql'


def test_prisma_orm_write_resolves_to_declared_model_only():
    found = flows('prisma')
    assert sorted(found) == ['model:User.email', 'model:User.phone']
    email = found['model:User.email'][0]
    assert stages(email) == [('model', 'prisma/schema.prisma', 8)]
    assert 'services/users.ts:4' in email['steps'][-1]['note']
    # near misses: an undeclared delegate and a local object named like a delegate never join a model.
    assert not any('customer' in key.lower() for key in found)
    assert all(step['source']['file'] != 'services/other.ts' for fl in found.values() for f in fl for step in f['steps'])


def test_prisma_reads_are_not_write_flows():
    inv = fixture_inventory('prisma')
    reads = [o for o in inv['orm_operations'] if o['access'] == 'read']
    assert reads and reads[0]['source']['file'] == 'services/users.ts'
    assert 'model:User.id' not in flows('prisma')


# ---- Mongoose --------------------------------------------------------------------------------

def test_mongoose_models_resolved_by_import_identity():
    inv = fixture_inventory('mongoose')
    models = {m['name']: m for m in inv['models'] if m['kind'] == 'mongoose'}
    assert set(models) == {'User', 'Staff', 'Lead'}
    assert {f['name'] for f in models['User']['fields']} >= {'email', 'phone'}
    assert inv['orm_connections'][0]['env'] == 'MONGO_URL'
    found = flows('mongoose')
    # Staff and User both declare `email`; only the model actually written is joined.
    assert stages(found['model:User.email'][0])[-1] == ('model', 'models/User.ts', 4)
    assert stages(found['model:Staff.name'][0])[-1] == ('model', 'models/Staff.ts', 3)
    assert 'model:Staff.email' not in found
    assert 'model:User.phone' not in found


def test_mongoose_whole_body_write_maps_only_route_read_keys():
    found = flows('mongoose')
    lead = found['model:Lead.email'][0]
    assert stages(lead)[0][:2] == ('route', 'server.ts')
    assert stages(lead)[-1] == ('model', 'models/Lead.js', 2)
    # Ghost is imported from a non-model file: no flow names it.
    assert not any('Ghost' in key for key in found)


# ---- React -----------------------------------------------------------------------------------

def test_react_form_joins_request_route_and_prisma_element():
    found = flows('react')
    email = found['model:User.email']
    assert len(email) == 1
    assert stages(email[0]) == [
        ('form', 'src/SignupForm.tsx', 9), ('component', 'src/SignupForm.tsx', 6), ('service', 'src/SignupForm.tsx', 6),
        ('route', 'server.ts', 6), ('handler', 'routes/users.ts', 6), ('model', 'prisma/schema.prisma', 8)]
    assert stages(found['model:User.phone'][0])[0] == ('form', 'src/SignupForm.tsx', 10)


def test_react_same_field_name_on_another_model_is_not_cross_bound():
    found = flows('react')
    lead = found['model:Lead.email']
    assert [stages(f)[0] for f in lead] == [('form', 'src/NewsletterForm.tsx', 9)]
    assert all(stages(f)[0][1] == 'src/SignupForm.tsx' for f in found['model:User.email'])


def test_react_dynamic_url_is_unresolved_not_guessed():
    inv = fixture_inventory('react')
    requests = {r['component']: r for r in inv['react_requests']}
    assert requests['DynamicForm']['unresolved'] is True
    assert requests['DynamicForm']['normalised_path'] is None
    assert requests['NewsletterForm']['unresolved'] is False
    used = {step['source']['file'] for fl in flows('react').values() for f in fl for step in f['steps']}
    assert 'src/DynamicForm.tsx' not in used


def test_react_method_mismatch_gives_no_join():
    used = {step['source']['file'] for fl in flows('react').values() for f in fl for step in f['steps']}
    assert 'src/WrongMethodForm.tsx' not in used
    request = {r['component']: r for r in fixture_inventory('react')['react_requests']}['WrongMethodForm']
    assert request['http_method'] == 'PUT'


# ---- Django (existing analyser only) -----------------------------------------------------------

def test_django_regression_uses_existing_analyser_only():
    inv = inventory(REPO / 'tests' / 'fixtures' / 'django')
    assert {m['name'] for m in inv['models']} >= {'Person', 'Document'}
    assert ('POST', '/api/persons') in {(r['method'], r['path']) for r in inv['routes']}
    assert {s['origin'] for f in inv['python_flows'] for s in f['steps']} == {'django'}
    assert not (REPO / 'auditor' / 'analysers' / 'django_framework.py').exists()
    assert not any(inv.get(key) for key in ('orm_operations', 'react_requests', 'kubernetes', 'nginx', 'prisma_datasources'))


# ---- Kubernetes ------------------------------------------------------------------------------

def k8s(name: str) -> dict:
    return {(r['kind'], r['name']): r for r in fixture_inventory(f'kubernetes/{name}')['kubernetes']}


def test_kubernetes_records_security_storage_and_direction():
    records = k8s('store-root')
    api = records[('Deployment', 'api')]
    container = api['workload']['containers'][0]
    assert container['security']['settings']['run_as_user'] == 0
    assert container['mounts'][0]['claim'] == 'user-data' and container['mounts'][0]['persistent'] is True
    assert container['env'][0]['value_kind'] == 'secret' and 'value' not in container['env'][0]
    service = records[('Service', 'api')]
    assert [(n['direction'], n['scope']) for n in service['network']] == [('inbound', 'internal')]
    public = k8s('store-public')[('Service', 'api')]
    assert [(n['direction'], n['scope']) for n in public['network']] == [('inbound', 'public')]


def test_kubernetes_outbound_and_secret_handling(tmp_path):
    canary = '_'.join(['canary', 'value', 'x9'])
    (tmp_path / 'm.yaml').write_text(
        'apiVersion: v1\nkind: Service\nmetadata:\n  name: ext\nspec:\n  type: ExternalName\n  externalName: api.partner.example\n---\n'
        f'apiVersion: v1\nkind: Secret\nmetadata:\n  name: s\nstringData:\n  token: {canary}\n---\n'
        'apiVersion: networking.k8s.io/v1\nkind: NetworkPolicy\nmetadata:\n  name: p\nspec:\n  podSelector: {}\n  policyTypes: [Egress]\n  egress:\n    - ports:\n        - port: 443\n')
    inv = inventory(tmp_path)
    by_kind = {r['kind']: r for r in inv['kubernetes']}
    assert 'Secret' not in by_kind
    assert [(n['direction'], n['scope']) for n in by_kind['Service']['network']] == [('outbound', 'external')]
    assert by_kind['NetworkPolicy']['network'][0]['direction'] == 'outbound'
    assert canary not in json.dumps(inv)


def test_kubernetes_rules_fire_only_with_personal_data_nexus():
    assert len(fire(FIXTURES / 'kubernetes' / 'store-root', 'SEC-16-kubernetes-privileged-store')) == 1
    assert len(fire(FIXTURES / 'kubernetes' / 'store-public', 'SEC-16-kubernetes-public-store')) == 1
    for name in ('store-hardened', 'unrelated'):
        for rule_id in NEW_RULES[1:]:
            assert fire(FIXTURES / 'kubernetes' / name, rule_id) == [], (name, rule_id)


def test_kubernetes_unrelated_config_yields_no_safeguard_findings():
    root = FIXTURES / 'kubernetes' / 'unrelated'
    ctx = build_context(root, 'corpus')
    matches = [m for _, detect in load_rules().values() for m in detect(ctx)]
    result = assemble(matches)
    assert [f for f in result.findings if f['issue_type'].startswith('SEC-')] == []
    assert k8s('unrelated')[('Deployment', 'worker')]['workload']['containers'][0]['security']['settings']['privileged'] is True


# ---- nginx -----------------------------------------------------------------------------------

def nginx(name: str) -> dict:
    return fixture_inventory(f'nginx/{name}')['nginx'][0]


def test_nginx_separates_inbound_listen_from_outbound_proxy_and_resolves_logs():
    record = nginx('logging')
    assert [(n['direction'], n['via']) for n in record['network']] == [('inbound', 'listen'), ('outbound', 'proxy_pass')]
    assert record['network'][1]['scope'] == 'internal'
    api, static = record['servers'][0]['locations']
    assert api['proxy']['kind'] == 'upstream' and api['access_log']['format'] == 'main'
    assert static['proxy'] is None and static['access_log']['path'] == '/var/log/nginx/access.log'
    assert record['log_formats'][0]['variables'] == ['remote_addr', 'request', 'status']
    assert nginx('access-off')['servers'][0]['locations'][0]['access_log']['off'] is True
    assert nginx('unlogged')['servers'][0]['locations'][0]['access_log'] is None


def test_nginx_rule_fires_on_logged_request_line_only():
    matches = fire(FIXTURES / 'nginx' / 'logging', 'SEC-01-nginx-query-logging')
    assert len(matches) == 1
    assert [(e['file'], e['start_line']) for e in matches[0].evidence] == [('server.ts', 4), ('nginx/nginx.conf', 3), ('nginx/nginx.conf', 2)]
    for name in ('access-off', 'no-uri-format', 'unlogged', 'unrelated'):
        assert fire(FIXTURES / 'nginx' / name, 'SEC-01-nginx-query-logging') == [], name


# ---- Corpus and report -----------------------------------------------------------------------

@pytest.mark.parametrize('rule_id', NEW_RULES)
def test_corpus_pair_exists_and_matches_rule(rule_id):
    assert rule_id in load_rules()
    for label, expect in (('positive', True), ('negative', False)):
        root = REPO / 'corpus' / rule_id / label
        assert root.is_dir() and any(root.rglob('*'))
        assert bool(fire(root, rule_id)) is expect


@pytest.mark.parametrize('rule_id', NEW_RULES)
def test_corpus_positive_assembles_with_registry_provisions(rule_id):
    spec, _ = load_rules()[rule_id]
    registry = load_registry()
    result = assemble(fire(REPO / 'corpus' / rule_id / 'positive', rule_id))
    assert not result.not_determinable
    assert result.findings, 'a nexus-bearing match must become a Finding'
    for finding in result.findings:
        assert finding['issue_type'] == spec.issue_type
        assert {finding['primary_provision'], *finding['other_provisions']} <= set(registry)


def test_report_no_secret_or_raw_value_reaches_findings(tmp_path):
    canary = '_'.join(['canary', 'literal', 'k7'])
    root = tmp_path / 'target'
    shutil.copytree(FIXTURES / 'kubernetes' / 'store-root', root)
    manifest = root / 'k8s' / 'app.yaml'
    manifest.write_text(manifest.read_text().replace('          securityContext:', f'            - name: API_TOKEN\n              value: {canary}\n          securityContext:'))
    inv = inventory(root)
    assert canary not in json.dumps(inv)
    result = assemble(fire(root, 'SEC-16-kubernetes-privileged-store'))
    assert result.findings
    assert canary not in json.dumps(result.findings)


def test_report_singharya_artifacts_are_schema_valid_and_honest():
    directory = REPO / 'reports' / 'singharya-e-kyc'
    for name in ('report.json', 'report.md', 'report.html', 'report.pdf'):
        assert (directory / name).stat().st_size > 0, name
    report = json.loads((directory / 'report.json').read_text())
    validate_report(report)
    assert report['scan']['exclusions'][-3:] == ['tests/**', '**/__pycache__/**', '**/*.pyc']
    # None of the new framework Rules claims coverage the Target does not have.
    fired = {rid for f in report['findings'] for rid in f.get('rules_fired', [])}
    assert not fired & set(NEW_RULES)
