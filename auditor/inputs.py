"""Resolve Target Application inputs without changing local Target code."""

from dataclasses import dataclass
from pathlib import Path
import subprocess
from urllib.parse import urlsplit, unquote


@dataclass(frozen=True)
class Target:
    root: Path
    name: str
    source: str
    kind: str
    commit: str | None


def _git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], text=True, capture_output=True, check=check)


def _is_git_url(source: str) -> bool:
    return source.startswith(("https://", "http://", "ssh://", "git://", "file://", "git@")) or source.endswith(".git")


def _repo_name(source: str) -> str:
    path = urlsplit(source).path if "://" in source else source.rsplit(":", 1)[-1]
    name = Path(unquote(path).rstrip("/")).name
    if name.endswith(".git"):
        name = name[:-4]
    if not name or name in {".", ".."}:
        raise ValueError("Git URL must contain a Target Application name")
    return name


def resolve_target(source: str, commit: str | None = None, targets_dir: Path = Path("targets")) -> Target:
    """Resolve an input; clones are stored beneath the injectable targets directory."""
    if not _is_git_url(source):
        root = Path(source).expanduser().resolve(strict=True)
        if not root.is_dir():
            raise ValueError("Target Application path must be a directory")
        if commit is not None:
            raise ValueError("--commit is supported only for Git URLs")
        result = _git("-C", str(root), "rev-parse", "--verify", "HEAD^{commit}", check=False)
        return Target(root, root.name, source, "path", result.stdout.strip() if result.returncode == 0 else None)

    name = _repo_name(source)
    root = (targets_dir / name).resolve()
    if not root.exists():
        root.parent.mkdir(parents=True, exist_ok=True)
        _git("clone", "--", source, str(root))
    else:
        origin = _git("-C", str(root), "remote", "get-url", "origin").stdout.strip()
        if origin != source:
            raise ValueError(f"Existing Target clone {root} has a different origin: {origin}")
    if commit is not None:
        if _git("-C", str(root), "rev-parse", "--verify", f"{commit}^{{commit}}", check=False).returncode:
            _git("-C", str(root), "fetch", "origin")
        _git("-C", str(root), "checkout", "--detach", commit)
    resolved = _git("-C", str(root), "rev-parse", "--verify", "HEAD^{commit}").stdout.strip()
    return Target(root, name, source, "git", resolved)
