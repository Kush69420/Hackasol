from copy import deepcopy
from pathlib import Path

import pytest

from auditor.analysers.log_flows import access_log_profile, log_operations
from auditor.analysers.region import storage_regions
from auditor.exclusions import iter_target_files

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/config_flows'
TARGET = ROOT / 'targets/juice-shop'


def inventory(root):
    pytest.importorskip('auditor.analysers.config', reason='configuration inventory analyser is absent')
    from auditor.inventory import build_inventory
    files, _ = iter_target_files(root, 'juice-shop')
    return build_inventory(root, files, None)


def element(path, key):
    return {'id': f'param:GET {path}?{key}', 'kind': 'route-param'}


@pytest.fixture(scope='module')
def fixture_inventory():
    return inventory(FIXTURE)


def test_combined_collects_and_logs_only_covered_route(fixture_inventory):
    elements = [element('/before', 'value'), element('/after', 'value')]
    steps = log_operations(fixture_inventory, elements)
    assert [(s['element_id'], s['operation']) for s in steps] == [
        ('param:GET /after?value', 'Collect'), ('param:GET /after?value', 'Log')]
    profile = access_log_profile(fixture_inventory)
    assert profile['format'] == 'combined'
    assert {'method', 'url', 'remote-addr', 'user-agent', 'referrer'} <= set(profile['fields_logged'])
    assert profile['file_pattern'] == 'logs/access.%DATE%'
    assert profile['retention_days'] == 14
    assert profile['source_rotation']['file'] == 'server.ts'


def test_custom_format_and_unlinked_or_absent_rotation(fixture_inventory):
    data = deepcopy(fixture_inventory)
    morgan = next(r for r in data['logging'] if r['kind'] == 'morgan')
    morgan['format'] = ':method :req[x-request-id] :status'
    assert 'req[x-request-id]' in access_log_profile(data)['fields_logged']
    assert [s['operation'] for s in log_operations(data, [element('/after', 'value')])] == ['Collect']
    morgan['format'] = ':method :url'
    morgan['stream'] = 'differentStream'
    assert access_log_profile(data)['source_rotation'] is None
    assert access_log_profile(data)['retention_days'] is None
    assert [s['operation'] for s in log_operations(data, [element('/after', 'value')])] == ['Collect', 'Log']
    data['logging'] = [morgan]
    assert access_log_profile(data)['file_pattern'] is None
    data['logging'] = []
    assert access_log_profile(data) is None


def test_regions_resolve_defaults_and_keep_log_groups_separate(fixture_inventory):
    regions = storage_regions(fixture_inventory)
    assert len(regions) == 1
    region = regions[0]
    assert region['region'] == 'eu-west-1'
    assert any(s['file'] == 'terraform/variables.tf' for s in region['resolved_from'])
    assert [(s['type'], s['name']) for s in region['storage']] == [('aws_efs_file_system', 'data')]
    assert region['log_groups'][0]['retention_in_days'] == 30
    assert all('element_id' not in item for item in region['log_groups'])


def test_literal_and_unresolved_region(fixture_inventory):
    data = deepcopy(fixture_inventory)
    provider = next(r for r in data['terraform'] if r['type'] == 'provider')
    provider['attributes']['region'] = 'ap-south-1'
    assert storage_regions(data)[0]['region'] == 'ap-south-1'
    provider['attributes']['region'] = 'var.missing'
    unresolved = storage_regions(data)[0]
    assert unresolved['region'] is None
    assert unresolved['storage'][0]['name'] == 'data'
    assert all(s['file'] != 'terraform/variables.tf' for s in unresolved['resolved_from'])


@pytest.mark.skipif(not TARGET.is_dir(), reason='Primary Target is absent')
def test_primary_target_password_logging_and_region():
    data = inventory(TARGET)
    elements = [element('/rest/user/change-password', key) for key in ('current', 'new', 'repeat')]
    steps = log_operations(data, elements)
    for item in elements:
        own = [s for s in steps if s['element_id'] == item['id']]
        assert [s['operation'] for s in own] == ['Collect', 'Log']
        assert own[0]['source']['file'] == 'frontend/src/app/Services/user.service.ts'
        assert own[0]['source']['start_line'] == 54
        assert own[1]['source']['file'] == 'server.ts'
        assert own[1]['source']['start_line'] == 370
        assert 'logs/access.log.%DATE%' in own[1]['note']
    profile = access_log_profile(data)
    assert profile['format'] == 'combined'
    assert profile['retention_days'] == 2
    regions = storage_regions(data)
    region = next(r for r in regions if r['region'] == 'eu-west-1')
    assert any(s['file'] == 'terraform/variables.tf' for s in region['resolved_from'])
    assert any(s['type'] == 'aws_efs_file_system' and s['name'] == 'juice_shop_data' for s in region['storage'])
    assert any(g['retention_in_days'] == 30 for g in region['log_groups'])
    assert all('element_id' not in group for group in region['log_groups'])
