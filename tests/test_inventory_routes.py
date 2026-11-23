import json
import shutil
import subprocess
from pathlib import Path

import pytest

from auditor.exclusions import iter_target_files

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/inventory_routes'
TARGET = ROOT / 'targets/juice-shop'


def extract(root):
    files, _ = iter_target_files(root, 'juice-shop')
    request = {'root': str(root), 'files': [p.relative_to(root).as_posix() for p in files]}
    result = subprocess.run(['node', str(ROOT / 'auditor/ts/src/run_module.mjs'), 'routes'],
                            input=json.dumps(request), text=True, capture_output=True, check=True)
    return json.loads(result.stdout)


def test_fixture(tmp_path):
    shutil.copytree(FIXTURE, tmp_path, dirs_exist_ok=True)
    sentinel = tmp_path / 'test/sentinel.ts'
    sentinel.parent.mkdir()
    sentinel.write_text("app.get('/excluded', handler())")
    (tmp_path / 'routes/handlers.ts').write_text(
        "export function show () { return (req, res) => {\n"
        "  const x = req.query.first; const y = req.query['second'];\n"
        "  const { third, fourth: renamed } = req.query;\n"
        "  const { email: address } = req.body; const z = req.body['phone'];\n"
        "} }\n"
        "export function create () { return ({ query, body }, res) => {\n"
        "  const x = query.search; const y = body.value;\n"
        "} }\n"
    )
    result = extract(tmp_path)
    routes = result['routes']
    explicit = [r for r in routes if r['origin'] == 'explicit']
    assert [(r['method'], r['path']) for r in explicit] == [
        ('GET', '/before'), ('POST', '/before'), ('PUT', '/before'),
        ('DELETE', '/before'), ('PATCH', '/before'), ('GET', '/chain'),
        ('POST', '/chain'), ('GET', '/mounted/thing')]
    assert explicit[0]['handler'] == {'name': 'show', 'file': 'routes/handlers.ts', 'start_line': 1, 'end_line': 5}
    assert [p['name'] for p in explicit[0]['query_params']] == ['first', 'second', 'third', 'fourth']
    assert [p['name'] for p in explicit[0]['body_params']] == ['email', 'phone']
    assert explicit[0]['query_params'][0]['source'] == {'file': 'routes/handlers.ts', 'start_line': 2, 'end_line': 2}
    assert [p['name'] for p in explicit[1]['query_params']] == ['search']
    assert [p['name'] for p in explicit[1]['body_params']] == ['value']
    assert all(r['query_params'] == [] and r['body_params'] == [] for r in routes if r['handler'] is None)
    assert explicit[-1]['middleware'][-1]['role'] == 'authentication'
    generated = [r for r in routes if r['origin'] == 'finale']
    assert [(r['method'], r['normalised_path']) for r in generated] == [
        ('GET', '/api/Users'), ('POST', '/api/Users'), ('GET', '/api/Users/{id}'),
        ('PUT', '/api/Users/{id}'), ('DELETE', '/api/Users/{id}')]
    assert generated[0]['finale']['exclude_attributes'] == ['password']
    assert generated[0]['finale']['include'] == ['OtherModel']
    assert generated[2]['middleware'][-1]['expression'] == 'security.isAuthorized()'
    assert routes[-1]['origin'] == 'swagger-only'
    assert routes[-1]['path'] == '/b2b/v2/missing'
    assert routes[-1]['swagger']['summary'] == 'Missing operation'
    assert {x['kind'] for x in result['logging']} == {'morgan', 'rotation'}
    assert all(not r['registration']['file'].startswith('test/') for r in routes)


@pytest.mark.skipif(not TARGET.is_dir(), reason='Reference Target is absent')
def test_reference_target():
    result = extract(TARGET)
    routes = result['routes']
    auth = next(r for r in routes if r['method'] == 'GET' and r['path'] == '/rest/user/authentication-details')
    assert any(m['expression'] == 'security.isAuthorized()' and m['role'] == 'authentication' for m in auth['middleware'])
    password = next(r for r in routes if r['method'] == 'GET' and r['path'] == '/rest/user/change-password')
    assert [p['name'] for p in password['query_params']] == ['current', 'new', 'repeat']
    generated = [r for r in routes if r['origin'] == 'finale']
    for name in ('Users', 'Addresss', 'Cards'):
        assert {(r['method'], r['normalised_path']) for r in generated if r['path'].startswith('/api/' + name)} == {
            ('GET', '/api/' + name), ('POST', '/api/' + name), ('GET', '/api/' + name + '/{id}'),
            ('PUT', '/api/' + name + '/{id}'), ('DELETE', '/api/' + name + '/{id}')}
    assert len({r['model'] for r in generated}) == 14
    assert len(generated) == 70
    assert len([r for r in routes if r['origin'] == 'explicit' and r['path'] == '/api/Users' and r['method'] == 'GET']) == 1
    assert any(x['kind'] == 'morgan' and x['format'] == 'combined' for x in result['logging'])
    assert any(x['kind'] == 'rotation' and x['frequency'] == 'daily' and x['max_logs'] == '2d' for x in result['logging'])
    assert any(r['path'] == '/b2b/v2/orders' and r['swagger'] is not None for r in routes)
    print(f"routes={len(routes)} finale={len(generated)} logging={len(result['logging'])}")
