import json
from pathlib import Path
import subprocess

import pytest

from auditor.exclusions import iter_target_files

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/inventory_frontend'
TARGET = ROOT / 'targets/juice-shop'


def extract(root, module):
    files, _ = iter_target_files(root, 'juice-shop')
    request = {'root': str(root), 'files': [p.relative_to(root).as_posix() for p in files]}
    result = subprocess.run(['node', 'auditor/ts/src/run_module.mjs', module], cwd=ROOT,
                            input=json.dumps(request), text=True, capture_output=True, check=True)
    return json.loads(result.stdout)


def test_fixture_models_and_collections():
    inventory = extract(FIXTURE, 'models')
    model = inventory['models'][0]
    assert (model['name'], model['table'], model['options']['paranoid']) == ('Thing', 'Things', True)
    email = model['fields'][0]
    assert (email['name'], email['type'], email['allow_null'], email['unique'], email['validators']) == ('email', 'DataTypes.STRING', False, True, ['isEmail'])
    assert email['source'] == {'file': 'models/thing.ts', 'start_line': 2, 'end_line': 2}
    collection = inventory['collections'][0]
    assert collection['name'] == 'reviewsCollection'
    assert collection['source']['start_line'] == 1
    assert {field['name'] for field in collection['fields']} == {'author', 'message', 'rating'}


def test_fixture_frontend():
    inventory = extract(FIXTURE, 'frontend')
    forms = {form['style']: form for form in inventory['forms']}
    assert set(forms) == {'signal', 'untyped', 'reactive', 'ngModel'}
    assert forms['signal']['inputs'][0] == {'name': 'email', 'input_type': 'email', 'label': 'Email address', 'i18n_key': 'EMAIL', 'source': {'file': 'frontend/src/app/example/example.component.html', 'start_line': 2, 'end_line': 2}}
    assert {call['normalised_path'] for call in inventory['service_calls']} == {'/api/Things', '/api/Things/{id}'}
    headers = {header['header']: header for header in inventory['outbound_headers']}
    assert set(headers) == {'Authorization', 'X-Guarded'}
    assert "localStorage.getItem('token')" in headers['Authorization']['value_expression']
    assert headers['Authorization']['origin_guard'] is False
    assert headers['Authorization']['origin_guard_source'] is None
    assert headers['X-Guarded']['origin_guard'] is True
    assert headers['X-Guarded']['origin_guard_source'] == {
        'file': 'frontend/src/app/example/guarded.ts', 'start_line': 3, 'end_line': 3}
    assert [(item['api'], item['op'], item['key']) for item in inventory['client_storage']] == [('localStorage', 'get', 'token')]
    assert next(t for t in inventory['templates'] if t['kind'] == 'hbs')['inputs'][0]['name'] == 'email'
    assert next(t for t in inventory['templates'] if t['file'].endswith('index.html'))['scripts'][0]['inline_excerpt']
    assert '.spec.ts' not in json.dumps(inventory)


@pytest.mark.skipif(not TARGET.exists(), reason='Reference Target unavailable')
def test_reference_target_models():
    inventory = extract(TARGET, 'models')
    models = {model['name']: model for model in inventory['models']}
    assert {'User', 'Address', 'Card'} <= models.keys()
    assert models['User']['options']['paranoid'] is True
    assert {'email', 'password', 'totpSecret', 'deluxeToken', 'lastLoginIp', 'profileImage'} <= {field['name'] for field in models['User']['fields']}
    collections = {c['name']: c for c in inventory['collections']}
    assert collections['reviewsCollection']['source']['start_line'] == 9
    assert collections['ordersCollection']['source']['start_line'] == 10
    assert '.spec.ts' not in json.dumps(inventory)


@pytest.mark.skipif(not TARGET.exists(), reason='Reference Target unavailable')
def test_reference_target_frontend():
    inventory = extract(TARGET, 'frontend')
    assert {'signal', 'untyped', 'ngModel'} <= {form['style'] for form in inventory['forms']}
    calls = [c for c in inventory['service_calls'] if c['service'] == 'AddressService']
    assert {'/api/Addresss', '/api/Addresss/{id}'} <= {c['normalised_path'] for c in calls}
    auth = next(h for h in inventory['outbound_headers'] if h['header'] == 'Authorization')
    assert len(inventory['outbound_headers']) == 2
    assert auth['origin_guard'] is False
    assert auth['origin_guard_source'] is None
    assert "localStorage.getItem('token')" in auth['value_expression']
    index = next(t for t in inventory['templates'] if t['file'] == 'frontend/src/index.html')
    assert any(script['inline_excerpt'] and script['source']['start_line'] <= 17 <= script['source']['end_line'] for script in index['scripts'])
    assert '.spec.ts' not in json.dumps(inventory)
