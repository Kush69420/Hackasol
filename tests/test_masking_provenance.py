from types import SimpleNamespace

from auditor import scan


def test_public_report_and_inventory_source(tmp_path, monkeypatch):
    private = 'https://dep%2Floy:synthetic-token@host/repo.git'
    target = SimpleNamespace(root=tmp_path, name='repo', source=private, kind='git', commit='abc')
    monkeypatch.setattr(scan, 'resolve_target', lambda source, **kw: target)
    monkeypatch.setattr(scan, 'iter_target_files', lambda *a: ([], 0))
    monkeypatch.setattr(scan, 'exclusions_for', lambda *a: [])
    monkeypatch.setattr(scan, 'build_inventory', lambda *a: {})
    assert scan.run_inventory(private)['target']['source'] == 'https://host/repo.git'

    session = SimpleNamespace(probe=lambda: None, summary=lambda: {'mode': 'online'})
    monkeypatch.setattr(scan.LLMSession, 'from_env', lambda **kw: session)
    monkeypatch.setattr(scan, 'build_context', lambda *a, **kw: SimpleNamespace(personal_data_map=[]))
    monkeypatch.setattr(scan, 'load_rules', lambda: {})
    monkeypatch.setattr(scan, 'assemble', lambda *a, **kw: SimpleNamespace(findings=[], observations=[], not_determinable=[]))
    monkeypatch.setattr(scan, 'build_graph', lambda *a: {})
    monkeypatch.setattr(scan, 'assess_consent', lambda *a: {})
    monkeypatch.setattr(scan, 'coverage_matrix', lambda *a: [])
    monkeypatch.setattr(scan, 'load_registry', lambda: {})
    monkeypatch.setattr(scan, 'executive_summary', lambda *a: {})
    monkeypatch.setattr(scan, 'validate_report', lambda *a: None)
    assert scan.run_scan(private)['target']['source'] == 'https://host/repo.git'


def test_clone_uses_private_input_but_sanitizes_origin(tmp_path, monkeypatch):
    import subprocess
    from auditor import inputs

    private = 'https://user:synthetic-token@host/repo.git'
    calls = []
    def git(*args, check=True):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, stdout='abc\n', stderr='')
    monkeypatch.setattr(inputs, '_git', git)
    target = inputs.resolve_target(private, targets_dir=tmp_path)
    assert ('clone', '--', private, str(tmp_path / 'repo')) in calls
    assert ('-C', str(tmp_path / 'repo'), 'remote', 'set-url', 'origin',
            'https://host/repo.git') in calls
    assert target.source == private


def test_git_error_does_not_expose_url_userinfo(monkeypatch):
    import subprocess
    import pytest
    from auditor import inputs

    private = 'https://user:synthetic-token@host/repo.git'
    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(1, ['git', 'clone', private], stderr='failed: ' + private)
    monkeypatch.setattr(inputs.subprocess, 'run', fail)
    with pytest.raises(subprocess.CalledProcessError) as caught:
        inputs._git('clone', private)
    assert 'synthetic-token' not in str(caught.value)
    assert 'synthetic-token' not in caught.value.stderr
