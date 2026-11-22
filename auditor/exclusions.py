"""Target Application profiles applied before processing files."""

from pathlib import Path
import os

ALWAYS_EXCLUDED = (".git/**", "node_modules/**")
PROFILES = {
    "juice-shop": ("data/static/codefixes/**", "test/**", "frontend/**/*.spec.ts"),
}


def exclusions_for(profile: str) -> list[str]:
    return [*ALWAYS_EXCLUDED, *PROFILES.get(profile, ())]


def _excluded(relative: Path, profile: str) -> bool:
    parts = relative.parts
    if ".git" in parts or "node_modules" in parts:
        return True
    if profile == "juice-shop":
        return (parts[:3] == ("data", "static", "codefixes")
                or parts[:1] == ("test",)
                or (parts[:1] == ("frontend",) and relative.name.endswith(".spec.ts")))
    return False


def iter_target_files(root: Path, profile: str) -> tuple[list[Path], int]:
    """List included regular files and count excluded files without reading them."""
    included = []
    excluded = 0
    for directory, dirs, files in os.walk(root, followlinks=False):
        dirs.sort()
        for name in sorted(files):
            path = Path(directory) / name
            if _excluded(path.relative_to(root), profile):
                excluded += 1
            elif path.is_file() and not path.is_symlink():
                included.append(path)
    return included, excluded
