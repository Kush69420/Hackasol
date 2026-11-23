"""Django source inventory and Primary Target regression."""
from pathlib import Path
import json
import subprocess

import pytest

from auditor.exclusions import iter_target_files
from auditor.inventory import build_inventory
from auditor.scan import run_scan
from auditor.llm import LLMSession
from auditor.mapping import assemble
from auditor.masking import mask_for_report
from auditor.report import write_reports
from auditor.rules import load_rules
from auditor.rules.context import build_context
from test_schema import finding, make_report

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/django'
JUICE = ROOT / 'targets/juice-shop'
KYC = ROOT / 'targets/ai-kyc-platform'

# Cache-only scan of the pinned Primary Target before introducing Python analysers.
JUICE_SHOP_FINDING_IDS = [
    'MON-01-8c5728dfea11', 'RET-01-e43b9adccd2d', 'RET-02-4696497b9137', 'RET-03-41bffe4101f9',
    'RIG-01-a9383e4db278', 'RIG-02-f7117cbcde8b', 'SEC-01-d85a743d0415', 'SEC-02-03b1356ecc57',
    'SEC-02-0f4631e6a05d', 'SEC-02-b6efa0cd2309', 'SEC-02-e0994a7481e3', 'SEC-04-4da51857d7fb',
    'SEC-04-bebc3e7f55ae', 'SEC-04-f14b443a57f1', 'SEC-05-9922f06ca9e3', 'SEC-05-c695dda06010',
    'SEC-07-10d210fbc583', 'SEC-07-19eb83125bf7', 'SEC-07-2301fc553793', 'SEC-07-2bc6d0295d98',
    'SEC-07-2d4f025671b7', 'SEC-07-46e1db7b8927', 'SEC-07-4edf88d6607a', 'SEC-07-6462097d19a8',
    'SEC-07-84fd091ad6cb', 'SEC-07-f9f89e15bbe6', 'SEC-08-445c2a32bf62', 'SEC-08-5b7f92b613ca',
    'SEC-08-6260b655a69b', 'SEC-08-a535cd15b04b', 'SEC-08-ca532d12729b', 'SEC-08-cefb92be21c6',
    'SEC-08-d0cbdc68911f', 'SEC-08-d23c91065882', 'SEC-09-8d1d55111ce2', 'SEC-09-e51d3cb1437b',
    'SEC-10-19fa227ef322', 'SEC-10-20b8955c0a3e', 'SEC-10-49d347fcf67d', 'SEC-10-d0971bb44714',
    'SEC-10-d70f56f17198', 'SEC-11-5a71594e3942', 'SEC-11-5ab639d2a92e', 'SEC-11-7958164b1c64',
    'SEC-11-84cd32175eeb', 'SEC-11-ad5b2106f4e8', 'SEC-11-d7922190cbda', 'SEC-13-394d3dbca514',
    'SEC-14-14740ebe6dcc', 'SEC-14-c5e9ac6a126d', 'TRF-02-0ff246d3b291', 'TRF-02-56fc1119eb9b'
]


def test_django_data_flow_inventory():
    files, _ = iter_target_files(FIXTURE, 'ai-kyc-platform')
    inventory = build_inventory(FIXTURE, files, None)
    model = next(m for m in inventory['models'] if m['name'] == 'Person')
    assert model['table'] == 'people_records' and model['app'] == 'people'
    assert [(f['name'], f['source']['start_line']) for f in model['fields']] == [
        ('email', 4), ('aadhaar_number', 5), ('face_image', 6), ('private_note', 7)]
    document = next(m for m in inventory['models'] if m['name'] == 'Document')
    assert [(c['value'], c['source']['start_line']) for c in document['fields'][0]['choices']] == [
        ('aadhaar', 13), ('pan', 14)]
    assert document['fields'][1]['government_identifier_evidence'] == document['fields'][0]['choices']
    other = next(m for m in inventory['models'] if m['name'] == 'OtherDocument')
    assert 'government_identifier_evidence' not in other['fields'][1]
    routes = {(r['method'], r['normalised_path']): r for r in inventory['routes']}
    assert {('POST', '/api/submit'), ('GET', '/api/health'), ('GET', '/api/persons'),
            ('POST', '/api/persons')} <= routes.keys()
    submit = routes['POST', '/api/submit']
    assert submit['permission_classes'] == ['AllowAny'] and not submit['middleware']
    assert routes['GET', '/api/persons']['permission_classes'] == ['IsAuthenticated']
    assert routes['GET', '/api/persons']['middleware'][0]['role'] == 'authentication'
    assert submit['response_models'][0]['fields'] == ['email', 'aadhaar_number', 'face_image']
    assert inventory['logging'][0]['filename'] == 'logs/audit.log'
    flow = next(f for f in inventory['python_flows'] if f['element_id'] == 'model:Person.email')
    assert {'Collect', 'Store', 'Expose', 'Log'} <= {s['operation'] for s in flow['steps']}
    assert all(s['source']['file'] == 'backend/people/views.py' for s in flow['steps'])
    assert not any(f['element_id'] == 'model:Person.private_note' for f in inventory['python_flows'])


@pytest.mark.skipif(not (JUICE / 'server.ts').exists(), reason='pinned Primary Target absent')
def test_juice_shop_regression(tmp_path, monkeypatch):
    monkeypatch.setenv('OLLAMA_HOST', 'http://127.0.0.1:1')
    report = run_scan(str(JUICE), provider='ollama', cache_dir=tmp_path)
    assert report['llm']['mode'] == 'cache-only'
    assert sorted(f['id'] for f in report['findings']) == JUICE_SHOP_FINDING_IDS


@pytest.fixture(scope='module')
def pinned_kyc(tmp_path_factory):
    if not (KYC / 'backend/kyc/models.py').exists():
        pytest.skip('pinned Secondary Target absent')
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv('OLLAMA_HOST', 'http://127.0.0.1:1')
        return run_scan(str(KYC), provider='ollama', cache_dir=tmp_path_factory.mktemp('kyc-cache'))


def test_pinned_sec03(pinned_kyc, tmp_path):
    assert pinned_kyc['target']['commit'] == '70a821487c193be445810d836dd9b9b9ae22eb18'
    findings = [f for f in pinned_kyc['findings'] if f['issue_type'] == 'SEC-03']
    assert any(any(e['file'] == 'ai-services/services/ocr_service.py' and e['start_line'] == 182
                   for e in f['evidence']) for f in findings)
    paths = write_reports(pinned_kyc, tmp_path / 'report.json')
    for text in [p.read_text() for p in paths[:3]] + [subprocess.run(
            ['pdftotext', str(paths[3]), '-'], check=True, capture_output=True, text=True).stdout]:
        assert '1234 5678 9010' not in text


@pytest.mark.parametrize('rule_id', ['SEC-02-django-plain-fields',
    'SEC-03-django-aadhaar-storage', 'SEC-03-fastapi-aadhaar-response'])
def test_rules(rule_id):
    spec, detect = load_rules()[rule_id]
    base = ROOT / 'corpus' / rule_id
    matches = detect(build_context(base / 'positive', 'corpus'))
    assert matches and not detect(build_context(base / 'negative', 'corpus'))
    if spec.issue_type == 'SEC-03':
        f = assemble(matches).findings[0]
        assert f['primary_provision'] == 'DPDP-Rule-6(1)(a)'
        assert set(f['other_provisions']) >= {'Aadhaar-Act-29', 'Aadhaar-SIR-2016'}
        assert f['penalty_ceiling']['amount_inr_crore'] == 250
        assert f['enforceable_from'] == '2027-05-13'


def test_masking(tmp_path):
    aadhaar = '1234 5678 9010'
    payload = 'data:image/png;base64,' + 'A' * 240
    item = finding()
    item['evidence'][0]['excerpt'] = mask_for_report(f'{aadhaar} {payload}')
    report = make_report([item])
    paths = write_reports(report, tmp_path / 'report.json')
    texts = [p.read_text() for p in paths[:3]] + [subprocess.run(
        ['pdftotext', str(paths[3]), '-'], check=True, capture_output=True, text=True).stdout]
    assert all(aadhaar not in text and payload not in text for text in texts)
    sent = []
    class Provider:
        name = 'ollama'
        model = 'synthetic'
        def available(self): return True, None
        def complete(self, system, user):
            sent.append(user)
            return json.dumps({'verdict': 'true-positive', 'reason': 'synthetic'})
    session = LLMSession(tmp_path / 'cache', Provider())
    session.probe()
    session.ask('triage', f'{aadhaar} {payload}', {'embedding': [0.123456]})
    assert sent and aadhaar not in sent[0] and payload not in sent[0] and '0.123456' not in sent[0]
