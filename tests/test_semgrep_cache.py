import json
import stat

import yaml

from auditor.semgrep import prewarm_semgrep, run_semgrep


def test_cache_is_private_and_keeps_bindings(tmp_path, monkeypatch):
    cache = tmp_path / 'cache'
    cache.mkdir(mode=0o755)
    monkeypatch.setenv('DPDP_SEMGREP_CACHE', str(cache))
    config = tmp_path / 'config'
    config.mkdir()
    (config / 'rule.yaml').write_text(yaml.safe_dump({'rules': [{
        'id': 'capture', 'languages': ['python'], 'severity': 'WARNING',
        'message': 'capture', 'pattern': 'print($X)'}]}))
    root = tmp_path / 'source'
    root.mkdir()
    (root / 'sample.py').write_text('print("synthetic-private-value")\n')
    matches = run_semgrep(root, ['sample.py'], [config])
    assert matches[0]['metavars']['$X'] == '"synthetic-private-value"'
    cached = next(cache.glob('*.json'))
    assert json.loads(cached.read_text()) == matches
    assert stat.S_IMODE(cache.stat().st_mode) == 0o700
    assert stat.S_IMODE(cached.stat().st_mode) == 0o600


def test_path_sensitive_prewarm_matches_per_root(tmp_path, monkeypatch):
    config = tmp_path / 'config'
    config.mkdir()
    (config / 'rule.yaml').write_text(yaml.safe_dump({'rules': [{
        'id': 'capture', 'languages': ['python'], 'severity': 'WARNING',
        'message': 'capture', 'pattern': 'print($X)',
        'paths': {'exclude': ['fixture/sample.py']}}]}))
    roots = [tmp_path / 'fixture', tmp_path / 'other']
    for root in roots:
        root.mkdir()
        (root / 'sample.py').write_text('print("value")\n')
    entries = [(root, ['sample.py']) for root in roots]
    monkeypatch.setenv('DPDP_SEMGREP_CACHE', str(tmp_path / 'cold'))
    cold = [run_semgrep(root, files, [config]) for root, files in entries]
    assert all(cold)
    monkeypatch.setenv('DPDP_SEMGREP_CACHE', str(tmp_path / 'warm'))
    prewarm_semgrep(entries, [config])
    assert [run_semgrep(root, files, [config]) for root, files in entries] == cold
