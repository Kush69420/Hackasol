import json
import subprocess
from pathlib import Path

from auditor.analysers.fastapi import analyse

ROOT = Path(__file__).resolve().parents[1]


def test_fastapi_models_routes_and_operations():
    root = ROOT / 'tests/fixtures/fastapi'
    result = analyse(root, ['main.py'])
    routes = {r['normalised_path']: r for r in result['routes']}
    doc = routes['/api/verify/document']
    assert doc['middleware'][0]['role'] == 'authentication'
    assert doc['response_model'] == 'Identity'
    assert result['models'][0]['fields'][0]['name'] == 'aadhaar_number'
    assert result['models'][0]['fields'][0]['source']['start_line'] == 9
    assert 'biometric_evidence' not in doc['body_params'][0]
    assert routes['/api/verify/face']['body_params'][0]['biometric_evidence'][0]['start_line'] == 20
    flow = next(f for f in result['flows'] if f['element_id'].endswith('#body.email'))
    assert {'Collect', 'Log', 'Transfer', 'Expose'} <= {s['operation'] for s in flow['steps']}
    collection = next(c for c in result['collections'] if c['name'] == 'OCR')
    assert collection['fields'][0]['source']['start_line'] == 37
    flow = next(f for f in result['flows'] if f['element_id'] == 'collection:OCR.aadhaar_number')
    assert flow['steps'][0]['operation'] == 'Expose'
    assert flow['steps'][0]['source']['start_line'] == 45


def test_nextjs_inventory():
    root = ROOT / 'tests/fixtures/nextjs'
    files = [p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()]
    result = subprocess.run(['node', str(ROOT / 'auditor/ts/src/main.mjs')], input=json.dumps({'root': str(root), 'files': files}), text=True, capture_output=True, check=True)
    inventory = json.loads(result.stdout)
    assert any(r['normalised_path'] == '/' for r in inventory['routes'])
    fields = inventory['forms'][0]['inputs']
    assert fields[0]['name'] == 'email' and fields[0]['label'] == 'Email address'
    assert fields[1]['input_type'] == 'file'
    assert inventory['service_calls'][0]['normalised_path'] == '/api/verify/submit'
    assert inventory['service_calls'][0]['http_method'] == 'POST'
    assert inventory['client_storage'][0]['key'] == 'email'
