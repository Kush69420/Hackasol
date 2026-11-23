import copy
import json
import subprocess
from pathlib import Path

import pytest

from auditor.exclusions import iter_target_files
from auditor.flows import trace_flows

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/flows'
TARGET = ROOT / 'targets/juice-shop'


def inventory(root):
    files, _ = iter_target_files(root, 'juice-shop')
    request = {'root': str(root), 'files': [p.relative_to(root).as_posix() for p in files]}
    result = subprocess.run(['node', str(ROOT / 'auditor/ts/src/main.mjs')], input=json.dumps(request), text=True, capture_output=True, check=True)
    return files, json.loads(result.stdout)


def test_fixture_join_and_negatives():
    files, data = inventory(FIXTURE)
    flows = trace_flows(FIXTURE, files, data)
    flow = next(f for f in flows if f['element_id'] == 'model:Thing.email')
    assert [s['stage'] for s in flow['steps']] == ['form', 'component', 'service', 'route', 'handler', 'model', 'response', 'response']
    assert [s['operation'] for s in flow['steps'][:6]] == ['Collect'] * 5 + ['Store']
    assert flow['steps'][4]['relation'] == 'inferred'
    for key, value in [('method', 'PATCH'), ('normalised_path', '/api/Other'), ('model', 'OtherModel')]:
        changed = copy.deepcopy(data)
        for route in changed['routes']:
            route[key] = value
        assert not trace_flows(FIXTURE, files, changed)

@pytest.mark.parametrize(
    ('handler', 'expected_line', 'masked'),
    [('excluded', None, False), ('included', 10, False), ('mapped', 17, False),
     ('omitted', None, False), ('masked', 30, True), ('unmasked', 37, False),
     ('objectOmitted', None, False), ('maskFunction', 49, True)],
)
def test_response_projections_and_field_masking(handler, expected_line, masked):
    files, data = inventory(FIXTURE)
    lines = (FIXTURE / 'routes/response.ts').read_text().splitlines()
    start = next(i for i, line in enumerate(lines, 1) if line.startswith(f'export function {handler}('))
    end = next(i for i in range(start + 1, len(lines) + 1) if lines[i - 1] == '}')
    data['routes'].append({
        'method': 'GET', 'origin': 'explicit', 'normalised_path': '/response/' + handler,
        'handler': {'file': 'routes/response.ts', 'start_line': start, 'end_line': end},
    })
    flow = next(f for f in trace_flows(FIXTURE, files, data) if f['element_id'] == 'model:Thing.email')
    exposed = [s for s in flow['steps'] if s['stage'] == 'response' and s['source']['file'] == 'routes/response.ts']
    if expected_line is None:
        assert not exposed
    else:
        assert len(exposed) == 1
        assert exposed[0]['source']['start_line'] == expected_line
        assert (exposed[0]['note'] == 'masked') == masked


def test_finale_wrapper_keeps_elements_without_duplicate_steps(tmp_path):
    import shutil

    shutil.copytree(FIXTURE, tmp_path, dirs_exist_ok=True)
    shutil.copyfile(FIXTURE / 'wrapper/server.ts', tmp_path / 'server.ts')
    files, data = inventory(tmp_path)
    flow = next(f for f in trace_flows(tmp_path, files, data) if f['element_id'] == 'model:Thing.email')
    exposed = [s for s in flow['steps'] if s['operation'] == 'Expose']
    assert len(exposed) == 1
    assert exposed[0]['source']['file'] == 'server.ts'
    assert exposed[0]['source']['start_line'] == 5
    assert exposed[0]['source']['end_line'] == 8
    assert 'wrapper' in exposed[0]['note']


@pytest.mark.skipif(not TARGET.exists(), reason='Primary Target unavailable')
def test_primary_target_flows():
    files, data = inventory(TARGET)
    flows = trace_flows(TARGET, files, data)
    cases = [
        ('model:User.email', 'register/register.component.html', 16, 'register/register.component.ts', 95, 106, 'Services/user.service.ts', 25, 41, 'models/user.ts', 56, 69, None),
        ('model:Address.streetAddress', 'address-create/address-create.component.html', 53, 'address-create/address-create.component.ts', 90, 96, 'Services/address.service.ts', 17, 35, 'models/address.ts', 58, 62, 'routes/address.ts'),
        ('model:Card.cardNum', 'payment-method/payment-method.component.html', 62, 'payment-method/payment-method.component.ts', 76, 84, 'Services/payment.service.ts', 17, 30, 'models/card.ts', 38, 45, 'routes/payment.ts'),
    ]
    for element, html, line, component, a, b, service, c, d, model, e, f, response in cases:
        candidates = [flow for flow in flows if flow['element_id'] == element]
        assert candidates, element
        def has(steps, stage, suffix, start, end):
            return any(s['stage'] == stage and s['source']['file'].endswith(suffix) and s['source']['start_line'] <= end and s['source']['end_line'] >= start for s in steps)
        assert any(has(x['steps'], 'form', html, line, line) and has(x['steps'], 'component', component, a, b) and has(x['steps'], 'service', service, c, d) and has(x['steps'], 'model', model, e, f) and has(x['steps'], 'route', 'server.ts', 394, 546) for x in candidates)
        if response:
            responses = [s for x in candidates for s in x['steps'] if s['stage'] == 'response' and s['source']['file'] == response]
            assert responses
            if element == 'model:Card.cardNum':
                assert all(s['note'] == 'masked' for s in responses)


@pytest.mark.skipif(not TARGET.exists(), reason='Primary Target unavailable')
def test_review_author_collection_flow():
    files, data = inventory(TARGET)
    flows = trace_flows(TARGET, files, data)
    flow = next(f for f in flows if f['element_id'] == 'collection:reviewsCollection.author')
    assert flow['derived_from'] == ['model:User.email']
    def has(operation, stage, file, first, last):
        return any(s['operation'] == operation and s['stage'] == stage
                   and s['origin'] == 'ts-join' and s['relation'] == 'evidenced'
                   and s['source']['file'] == file and s['source']['start_line'] <= last
                   and s['source']['end_line'] >= first for s in flow['steps'])
    assert has('Collect', 'component', 'frontend/src/app/product-details/product-details.component.ts', 77, 93)
    assert has('Collect', 'service', 'frontend/src/app/Services/product-review.service.ts', 28, 30)
    assert has('Collect', 'route', 'server.ts', 673, 673)
    assert has('Store', 'storage', 'routes/createProductReviews.ts', 23, 29)
    assert has('Expose', 'response', 'routes/showProductReviews.ts', 36, 45)
    assert any(s['operation'] == 'Expose' and 'not projected out' in s['note'] for s in flow['steps'])
    for mutation in ('method', 'path', 'collection'):
        changed = copy.deepcopy(data)
        if mutation == 'method':
            for route in changed['routes']:
                if (route.get('handler') or {}).get('name') == 'createProductReviews':
                    route['method'] = 'POST'
        elif mutation == 'path':
            for route in changed['routes']:
                if (route.get('handler') or {}).get('name') == 'showProductReviews':
                    route['normalised_path'] = '/unrelated'
        else:
            changed['collections'] = [c for c in changed['collections'] if c['name'] != 'reviewsCollection']
        assert not any(f['element_id'] == flow['element_id'] for f in trace_flows(TARGET, files, changed))
