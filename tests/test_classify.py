import json
from pathlib import Path
import subprocess

import pytest

from auditor.classify import classify, extract_elements
from auditor.exclusions import iter_target_files
from auditor.validators import is_aadhaar, is_card, is_email, is_ifsc, is_indian_phone, is_ip, is_pan, is_vpa

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'targets/juice-shop'
SOURCE = {'file': 'models/example.ts', 'start_line': 1, 'end_line': 1}


def inventory_fields(model, names):
    return {'models': [{'name': model, 'fields': [{'name': name, 'source': SOURCE} for name in names]}]}


def categories(model, names):
    return {e['name']: e['data_category'] for e in classify(extract_elements(inventory_fields(model, names)))}


@pytest.mark.parametrize(('name', 'category'), [
    ('aadhaar', 'Government Identifier'), ('aadhar', 'Government Identifier'), ('adhaar', 'Government Identifier'),
    ('uid_number', 'Government Identifier'), ('pan_no', 'Government Identifier'), ('pancard', 'Government Identifier'),
    ('passport', 'Government Identifier'), ('voter', 'Government Identifier'), ('epic', 'Government Identifier'),
    ('driving_licence', 'Government Identifier'), ('dl_no', 'Government Identifier'), ('abha', 'Government Identifier'),
    ('health_id', 'Government Identifier'), ('mobile_no', 'Contact'), ('phone_no', 'Contact'), ('pata', 'Contact'),
    ('naam', 'Profile'), ('janam_tithi', 'Profile'), ('date_of_birth', 'Profile'),
    ('ifsc', 'Financial'), ('upi', 'Financial'), ('account_no', 'Financial'), ('khata', 'Financial'),
    ('fingerprint', 'Biometric'), ('iris', 'Biometric'), ('blood_group', 'Health'), ('passwd', 'Authentication Secret'),
])
def test_dictionary_variants(name, category):
    assert categories('User', [name])[name] == category


def test_lookalikes_and_person_context():
    assert categories('Product', ['panel', 'company', 'zip', 'ship', 'name', 'id']) == {}
    assert categories('Address', ['zip', 'name']) == {'zip': 'Contact', 'name': 'Profile'}
    assert categories('User', ['lastLoginIp'])['lastLoginIp'] == 'Profile'
    dob = extract_elements(inventory_fields('User', ['dob']))[0]
    assert 'possible Child Data' in dob['signals']


@pytest.mark.parametrize(('function', 'valid', 'invalid'), [
    (is_email, 'person@example.org', 'person@invalid'),
    (is_card, '4111 1111 1111 1111', '4111 1111 1111 1112'),
    (is_indian_phone, '+91 9876543210', '+91 1234567890'),
    (is_ip, '2001:db8::1', '999.1.1.1'),
    (is_aadhaar, '234567890124', '234567890123'),
    (is_pan, 'ABCDE1234F', 'ABCDE12345'),
    (is_ifsc, 'SBIN0001234', 'SBIN1001234'),
    (is_vpa, 'alice@upi', 'alice@'),
])
def test_validators(function, valid, invalid):
    assert function(valid)
    assert not function(invalid)


def test_format_needs_context_and_ui_label_is_a_signal():
    inventory = inventory_fields('Product', ['part'])
    inventory['models'][0]['fields'][0]['default'] = '4111111111111111'
    inventory['forms'] = [{'inputs': [{'name': 'contactValue', 'label': 'Email address', 'source': SOURCE}]}]
    elements = extract_elements(inventory)
    assert [e['id'] for e in elements] == ['form:models/example.ts#contactValue']
    assert elements[0]['data_category'] == 'Contact'
    assert 'label:email' in elements[0]['signals']


def test_identities_and_sources_for_each_inventory_kind():
    config_source = {'file': '.env', 'start_line': 3, 'end_line': 3}
    inventory = inventory_fields('User', ['email'])
    inventory.update({'env_files': [{'source': config_source, 'entries': [{'key': 'email', 'source': config_source}]}],
                      'collections': [{'name': 'reviews', 'fields': [{'name': 'email', 'source': SOURCE}]}],
                      'client_storage': [{'api': 'localStorage', 'key': 'email', 'source': SOURCE}],
                      'outbound_headers': [{'header': 'X-User-Email', 'source': SOURCE}],
                      'routes': [{'method': 'GET', 'normalised_path': '/rest/change-password', 'registration': SOURCE,
                                  'query_params': [{'name': 'current', 'source': config_source}],
                                  'body_params': [{'name': 'email', 'source': config_source}]}]})
    by_id = {e['id']: e for e in extract_elements(inventory)}
    assert {'model:User.email', 'config:.env#email', 'collection:reviews.email', 'storage:localStorage.email',
            'header:X-User-Email', 'param:GET /rest/change-password?current',
            'param:GET /rest/change-password#body.email'} <= by_id.keys()
    assert by_id['param:GET /rest/change-password?current']['data_category'] == 'Authentication Secret'
    assert by_id['param:GET /rest/change-password?current']['source'] == config_source
    assert by_id['param:GET /rest/change-password#body.email']['source'] == config_source
    assert by_id['config:.env#email']['source'] == config_source


class FakeSession:
    def __init__(self, verdict):
        self.verdict = verdict
        self.calls = []

    def ask(self, *args):
        self.calls.append(args)
        return self.verdict


def test_llm_assessed_and_cache_miss():
    candidate = extract_elements(inventory_fields('User', ['occupation']))
    assessed = FakeSession({'status': 'assessed', 'value': {'data_category': 'Profile', 'reason': 'occupation'}})
    item = classify(candidate, assessed)[0]
    assert (item['status'], item['data_category']) == ('llm', 'Profile')
    assert assessed.calls[0][0] == 'classification'
    missing = FakeSession({'status': 'not assessed'})
    item = classify(candidate, missing)[0]
    assert (item['status'], item['data_category'], item['llm']['status']) == ('unresolved', None, 'not assessed')
    null = FakeSession({'status': 'assessed', 'value': {'data_category': None, 'reason': 'not personal'}})
    assert classify(candidate, null)[0]['status'] == 'llm'
    assert not assessed.calls[0][1].count('person@example.org')


@pytest.mark.skipif(not TARGET.exists(), reason='Reference Target unavailable')
def test_reference_target_model_classifications():
    files, _ = iter_target_files(TARGET, 'juice-shop')
    request = {'root': str(TARGET), 'files': [p.relative_to(TARGET).as_posix() for p in files]}
    result = subprocess.run(['node', 'auditor/ts/src/run_module.mjs', 'models'], cwd=ROOT,
                            input=json.dumps(request), text=True, capture_output=True, check=True)
    elements = {e['id']: e for e in classify(extract_elements(json.loads(result.stdout)))}
    for identity, category in {'model:User.email': 'Contact', 'model:User.password': 'Authentication Secret',
                               'model:User.totpSecret': 'Authentication Secret', 'model:User.deluxeToken': 'Authentication Secret',
                               # A login IP describes activity, not a communication address.
                               'model:User.lastLoginIp': 'Profile', 'model:Card.cardNum': 'Financial',
                               'model:Address.streetAddress': 'Contact'}.items():
        assert elements[identity]['data_category'] == category
    assert 'model:Product.name' not in elements


@pytest.mark.skipif(not TARGET.exists(), reason='Reference Target unavailable')
def test_reference_target_password_query_elements():
    files, _ = iter_target_files(TARGET, 'juice-shop')
    request = {'root': str(TARGET), 'files': [p.relative_to(TARGET).as_posix() for p in files]}
    result = subprocess.run(['node', 'auditor/ts/src/run_module.mjs', 'routes'], cwd=ROOT,
                            input=json.dumps(request), text=True, capture_output=True, check=True)
    elements = {e['id']: e for e in extract_elements(json.loads(result.stdout))}
    for name in ('current', 'new', 'repeat'):
        item = elements[f'param:GET /rest/user/change-password?{name}']
        assert item['data_category'] == 'Authentication Secret'
        assert item['source']['file'] == 'routes/changePassword.ts'
