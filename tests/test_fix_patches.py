import json
import subprocess
from pathlib import Path

import jsonschema

import pytest

from auditor.fixpatch import generate, verify
from auditor.fixpatch.publish import publish
from auditor.sarif import to_sarif


def test_publish_requires_authorization_and_rejects_upstream_and_rejected(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('No process may run before authorization and validation')
    monkeypatch.setattr(subprocess, 'run', forbidden)
    patch = {'status': 'accepted', 'finding_id': 'SEC-01-a', 'diff': DIFF}
    kwargs = dict(target='unused', baseline={}, patches=[patch], destination='TanKaizokuO/juice-shop',
                  base='dpdp-pinned-base', branch='review')
    with pytest.raises(ValueError, match='authorization'):
        publish(**kwargs)
    with pytest.raises(ValueError, match='Destination'):
        publish(**{**kwargs, 'destination': 'juice-shop/juice-shop', 'authorized': True})
    with pytest.raises(ValueError, match='accepted'):
        publish(**{**kwargs, 'patches': [{**patch, 'status': 'rejected'}], 'authorized': True})


def finding(line=1):
    return {'id': 'SEC-01-a', 'issue_type': 'SEC-01', 'rules_fired': ['rule-1'],
            'evidence': [{'file': 'app.txt', 'start_line': line, 'end_line': line, 'excerpt': 'bad'}],
            'recommended_fix': {'guidance': 'remove bad'},
            'severity': {'band': 'high', 'justification': 'bad'}}


@pytest.fixture
def target(tmp_path):
    root = tmp_path / 'target'
    root.mkdir()
    (root / 'app.txt').write_text('bad\n')
    def git(*args):
        return subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True, text=True).stdout.strip()
    git('init')
    git('add', 'app.txt')
    git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-m', 'base')
    return root, git('rev-parse', 'HEAD')


def report(commit, findings):
    return {'target': {'name': 'target', 'commit': commit}, 'scan': {'exclusions': []}, 'findings': findings}


DIFF = '--- a/app.txt\n+++ b/app.txt\n@@ -1 +1 @@\n-bad\n+good\n'


def test_rescan_removal_and_line_movement(target):
    root, commit = target
    before = report(commit, [finding()])
    def removed(path, **kwargs):
        assert (root / 'app.txt').read_text() == 'bad\n'
        return report(None, [])
    patch = [{'finding_id': 'SEC-01-a', 'diff': DIFF}]
    assert verify(root, before, patch, scan=removed)['status'] == 'accepted'
    assert verify(root, before, patch, scan=lambda *a, **kw: report(None, [finding(20)]))['status'] == 'rejected'
    new = finding()
    new['issue_type'] = 'SEC-13'
    assert verify(root, before, patch, scan=lambda *a, **kw: report(None, [new]))['status'] == 'rejected'


def test_rescan_secondary_evidence_changes_not_new(target):
    root, commit = target
    other = finding()
    other['id'], other['issue_type'] = 'RET-03-b', 'RET-03'
    other['evidence'].append({'file': 'related.txt', 'start_line': 1, 'end_line': 1, 'excerpt': 'before'})
    updated = json.loads(json.dumps(other))
    updated['evidence'][1]['excerpt'] = 'after'
    result = verify(root, report(commit, [finding(), other]), [{'finding_id': 'SEC-01-a', 'diff': DIFF}],
                    scan=lambda *a, **kw: report(None, [updated]))
    assert result['status'] == 'accepted'


def test_rescan_combined_interaction(target):
    root, commit = target
    undo = '--- a/app.txt\n+++ b/app.txt\n@@ -1 +1 @@\n-good\n+bad\n'
    patches = [{'finding_id': 'SEC-01-a', 'diff': DIFF}, {'finding_id': 'SEC-01-a', 'diff': undo}]
    def rescan(path, **kwargs):
        return report(None, [finding()] if (Path(path) / 'app.txt').read_text() == 'bad\n' else [])
    assert verify(root, report(commit, [finding()]), patches, scan=rescan)['status'] == 'rejected'


def test_target_tests_failure_is_nonblocking(target):
    root, commit = target
    result = verify(root, report(commit, [finding()]), [{'finding_id': 'SEC-01-a', 'diff': DIFF}],
                    scan=lambda *a, **kw: report(None, []), test_commands=[['false']])
    assert result['status'] == 'accepted'
    assert result['target_tests'][0]['exit_status'] != 0


def test_sarif_locations():
    result = to_sarif(report('abc', [finding(7)]))
    assert result['version'] == '2.1.0'
    schema = json.loads((Path(__file__).parent / 'fixtures/fixpatch/sarif-2.1.0.schema.json').read_text())
    jsonschema.validate(result, schema)
    item = result['runs'][0]['results'][0]
    assert item['ruleId'] == 'rule-1'
    assert item['locations'][0]['physicalLocation']['region']['startLine'] == 7


def test_generate_masks_and_uses_fake_provider(monkeypatch, tmp_path):
    class Fake:
        def __init__(self, model):
            self.model = model
        def complete(self, system, payload):
            assert 'alice@example.com' not in payload
            return '```json\n' + json.dumps({'diff': DIFF}) + '\n```'
    monkeypatch.setitem(__import__('auditor.fixpatch', fromlist=['PROVIDERS']).PROVIDERS, 'fake', Fake)
    value = finding()
    value['evidence'][0]['excerpt'] = 'alice@example.com'
    assert generate(value, provider='fake', model='fake', cache_dir=tmp_path) == DIFF


def test_rescan_generate_retries_failed_application(monkeypatch, target, tmp_path):
    from auditor.fixpatch import generate_review
    calls = []
    class Fake:
        def __init__(self, model):
            self.model = model
        def complete(self, system, payload):
            calls.append(json.loads(payload))
            return json.dumps({'diff': DIFF.replace('-bad', '-missing') if len(calls) == 1 else DIFF})
    monkeypatch.setitem(__import__('auditor.fixpatch', fromlist=['PROVIDERS']).PROVIDERS, 'fake', Fake)
    root, _ = target
    patch = generate_review(finding(), root, provider='fake', model='fake', cache_dir=tmp_path / 'cache')
    assert patch['status'] == 'generated'
    assert len(calls) == 2 and 'apply_error' in calls[1]


def test_generate_review_sends_numbered_context_and_retries_at_most_twice(monkeypatch, target, tmp_path):
    from auditor.fixpatch import generate_review
    calls = []
    class Fake:
        def __init__(self, model):
            self.model = model
        def complete(self, system, payload):
            calls.append(json.loads(payload))
            return json.dumps({'diff': DIFF.replace('-bad', '-missing')})
    monkeypatch.setitem(__import__('auditor.fixpatch', fromlist=['PROVIDERS']).PROVIDERS, 'fake', Fake)
    root, _ = target
    patch = generate_review(finding(), root, provider='fake', model='fake', cache_dir=tmp_path / 'cache')
    assert patch['status'] == 'rejected' and patch['provenance'] == 'generated'
    assert len(calls) == 3 and patch['attempts'] == 3
    assert calls[0]['files'] == [{'path': 'app.txt', 'total_lines': 1, 'first_line': 1, 'content': '1: bad'}]
    assert 'apply_error' not in calls[0]
    assert all('apply_error' in c and c['files'] == calls[0]['files'] for c in calls[1:])
    assert patch['provider'] == 'fake' and patch['cache_key']


def test_generate_review_caches_only_the_diff_that_applies(monkeypatch, target, tmp_path):
    from auditor.fixpatch import generate_review
    calls = []
    class Fake:
        def __init__(self, model):
            self.model = model
        def complete(self, system, payload):
            calls.append(1)
            return json.dumps({'diff': DIFF.replace('-bad', '-missing') if len(calls) == 1 else DIFF})
    monkeypatch.setitem(__import__('auditor.fixpatch', fromlist=['PROVIDERS']).PROVIDERS, 'fake', Fake)
    root, _ = target
    first = generate_review(finding(), root, provider='fake', model='fake', cache_dir=tmp_path / 'cache')
    second = generate_review(finding(), root, provider='fake', model='fake', cache_dir=tmp_path / 'cache')
    assert first['status'] == second['status'] == 'generated' and first['attempts'] == 2
    assert second['attempts'] == 0 and len(calls) == 2 and second['diff'] == DIFF
