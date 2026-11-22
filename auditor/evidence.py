"""Turn analyser source coordinates into schema Evidence with masked excerpts."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from auditor.masking import mask_for_report

MAX_EXCERPT_LINES = 12


@lru_cache(maxsize=2048)
def _lines(path: Path) -> tuple[str, ...]:
    return tuple(path.read_text(encoding="utf-8", errors="replace").splitlines())


def evidence(root: Path, coord: dict) -> dict:
    """Schema Evidence for a coord ``{file, start_line, end_line}``.

    The excerpt is capped at MAX_EXCERPT_LINES (the line range is kept intact) and
    masked for the Report: Authentication Secrets, keys and Government Identifiers.
    """
    lines = _lines(root / coord["file"])
    start, end = coord["start_line"], max(coord["end_line"], coord["start_line"])
    shown = lines[start - 1:min(end, start - 1 + MAX_EXCERPT_LINES)]
    excerpt = "\n".join(shown)
    if end - start + 1 > MAX_EXCERPT_LINES:
        excerpt += "\n…"
    return {"file": coord["file"], "start_line": start, "end_line": end,
            "excerpt": mask_for_report(excerpt)}
