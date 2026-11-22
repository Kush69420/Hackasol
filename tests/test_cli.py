import json
from pathlib import Path
import subprocess

import pytest

from auditor import cli, scan
from auditor.exclusions import exclusions_for, iter_target_files
from auditor.inputs import resolve_target
from auditor.schema import ReportValidationError, validate_report


def git(*args, cwd=None):
    return subprocess.run(["git", *map(str, args)], cwd=cwd, check=True,
                          capture_output=True, text=True).stdout.strip()


def make_repo(path):
    path.mkdir()
    git("init", path)
    git("-C", path, "config", "user.email", "test@example.invalid")
    git("-C", path, "config", "user.name", "Test")
    (path / "app.txt").write_text("application", encoding="utf-8")
    git("-C", path, "add", "app.txt")
    git("-C", path, "commit", "-m", "initial")
    return git("-C", path, "rev-parse", "HEAD")


def test_local_inputs(tmp_path):
    repo = tmp_path / "app"
    commit = make_repo(repo)
    target = resolve_target(str(repo))
    assert target.root == repo.resolve()
    assert target.kind == "path" and target.commit == commit
    plain = tmp_path / "plain"
    plain.mkdir()
    assert resolve_target(str(plain)).commit is None


def test_git_url_clone_and_reuse(tmp_path):
    repo = tmp_path / "source"
    first = make_repo(repo)
    (repo / "app.txt").write_text("changed", encoding="utf-8")
    git("-C", repo, "commit", "-am", "second")
    second = git("-C", repo, "rev-parse", "HEAD")
    bare = tmp_path / "source.git"
    git("clone", "--bare", repo, bare)
    url = bare.as_uri()
    targets = tmp_path / "targets"
    target = resolve_target(url, commit=first, targets_dir=targets)
    assert target.root == targets / "source"
    assert target.kind == "git" and target.commit == first
    assert resolve_target(url, commit=second, targets_dir=targets).commit == second


def test_git_url_fetches_missing_commit(tmp_path):
    repo = tmp_path / "source"
    make_repo(repo)
    bare = tmp_path / "source.git"
    git("clone", "--bare", repo, bare)
    targets = tmp_path / "targets"
    resolve_target(bare.as_uri(), targets_dir=targets)
    (repo / "app.txt").write_text("new", encoding="utf-8")
    git("-C", repo, "commit", "-am", "new")
    latest = git("-C", repo, "rev-parse", "HEAD")
    git("-C", repo, "push", str(bare), "HEAD:refs/heads/main")
    assert resolve_target(bare.as_uri(), commit=latest, targets_dir=targets).commit == latest


def test_exclusions(tmp_path):
    names = ["test/cypress/sentinel", "data/static/codefixes/sentinel", "frontend/x.spec.ts",
             "frontend/nested/y.spec.ts", ".git/config", "nested/node_modules/package/a.js",
             "frontend/app.ts"]
    for name in names:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("sentinel", encoding="utf-8")
    included, excluded = iter_target_files(tmp_path, "juice-shop")
    assert included == [tmp_path / "frontend/app.ts"]
    assert excluded == 6
    assert "frontend/**/*.spec.ts" in exclusions_for("juice-shop")


@pytest.mark.parametrize("mode", ["live", "cache-only"])
def test_report_and_cli(tmp_path, monkeypatch, capsys, mode):
    class FakeSession:
        @classmethod
        def from_env(cls, cache_dir, provider=None, model=None):
            return cls()

        def probe(self):
            pass

        def summary(self):
            return {"mode": mode, "provider": "openai", "model": "test-model",
                    "prompt_versions": {}, "cache_hits": 0, "cache_misses": 0,
                    "not_assessed": 0, "reason": "unreachable" if mode == "cache-only" else None}

    monkeypatch.setattr(scan, "LLMSession", FakeSession)
    target = tmp_path / "app"
    target.mkdir()
    (target / "app.txt").write_text("application", encoding="utf-8")
    destination = tmp_path / "reports" / "report.json"
    assert cli.main(["scan", str(target), "--out", str(destination)]) == 0
    report = json.loads(destination.read_text(encoding="utf-8"))
    validate_report(report)
    assert report["llm"]["mode"] == mode
    assert report["scan"]["files_scanned"] == 1
    assert report["findings"] == []
    assert [item["id"] for item in report["applicability_assumptions"]] == ["AA-1", "AA-2", "AA-3", "AA-4"]
    captured = capsys.readouterr()
    assert str(destination) in captured.out
    assert ("cache-only" in captured.err) == (mode == "cache-only")


def test_validation_failure_does_not_write(tmp_path, monkeypatch, capsys):
    def invalid(*args, **kwargs):
        raise ReportValidationError(["invalid Report"])

    monkeypatch.setattr(cli, "run_scan", invalid)
    destination = tmp_path / "report.json"
    assert cli.main(["scan", str(tmp_path), "--out", str(destination)]) == 1
    assert not destination.exists()
    assert "invalid Report" in capsys.readouterr().err
