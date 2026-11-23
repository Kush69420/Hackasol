"""Target Application profiles applied before processing files."""

from fnmatch import fnmatchcase
from pathlib import Path
import os

ALWAYS_EXCLUDED = ("**/.git/**", "**/node_modules/**")
PROFILES = {
    "juice-shop": ("data/static/codefixes/**", "test/**", "frontend/**/*.spec.ts"),
    "ai-kyc-platform": ("backend/venv/**", "**/__pycache__/**", "**/*.pyc"),
}


def exclusions_for(profile: str) -> list[str]:
    return [*ALWAYS_EXCLUDED, *PROFILES.get(profile, ())]


def _matches(parts: tuple[str, ...], pattern: tuple[str, ...]) -> bool:
    """Match path segments against glob segments; `**` spans zero or more segments."""
    if not pattern:
        return not parts
    if pattern[0] == "**":
        return any(_matches(parts[i:], pattern[1:]) for i in range(len(parts) + 1))
    return bool(parts) and fnmatchcase(parts[0], pattern[0]) and _matches(parts[1:], pattern[1:])


def is_excluded(relative: Path, profile: str) -> bool:
    """The globs reported in `scan.exclusions` are the only exclusion rules applied."""
    return any(_matches(relative.parts, tuple(glob.split("/"))) for glob in exclusions_for(profile))


def iter_target_files(root: Path, profile: str) -> tuple[list[Path], int]:
    """List included regular files and count excluded files without reading them."""
    included = []
    excluded = 0
    for directory, dirs, files in os.walk(root, followlinks=False):
        dirs.sort()
        for name in sorted(files):
            path = Path(directory) / name
            if is_excluded(path.relative_to(root), profile):
                excluded += 1
            elif path.is_file() and not path.is_symlink():
                included.append(path)
    return included, excluded
