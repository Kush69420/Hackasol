"""Application inventory: what exists in a Target Application, before any judgement.

Combines the TypeScript AST analyser (``auditor/ts``) with the Python configuration
analysers. Both receive only the in-scope file list, so excluded paths never
populate the inventory.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from auditor.analysers.config import analyse_config

TS_ENTRY = Path(__file__).resolve().parent / "ts" / "src" / "main.mjs"

INVENTORY_KEYS = (
    "routes", "logging", "models", "collections", "forms", "templates", "service_calls",
    "client_storage", "outbound_headers", "docker", "config_files", "app_json", "env_files", "terraform",
)


def build_inventory(root: Path, files: list[Path], commit: str | None) -> dict:
    rel = [p.relative_to(root).as_posix() for p in files]
    result = subprocess.run(
        ["node", str(TS_ENTRY)],
        input=json.dumps({"root": str(root), "files": rel}),
        text=True, capture_output=True, check=True,
    )
    inventory = {"commit": commit, **json.loads(result.stdout), **analyse_config(root, rel)}
    missing = [k for k in INVENTORY_KEYS if k not in inventory]
    if missing:
        raise ValueError(f"inventory analysers did not produce: {', '.join(missing)}")
    return inventory
