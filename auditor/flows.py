"""Cross-file Data Flows derived from the in-scope TypeScript inventory."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

_ENTRY = Path(__file__).resolve().parent / "ts" / "src" / "flows_cli.mjs"


def trace_flows(root: Path, files: list[Path], inventory: dict) -> list[dict]:
    """Join in-scope Angular, Express and Sequelize records into Data Flows."""
    result = subprocess.run(
        ["node", str(_ENTRY)],
        input=json.dumps({"root": str(root), "files": [p.relative_to(root).as_posix() for p in files], "inventory": inventory}),
        text=True, capture_output=True, check=True,
    )
    return json.loads(result.stdout)["flows"]
