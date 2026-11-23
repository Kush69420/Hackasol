"""Replay Mode: record a Report-producing scan with its stage timing, and play it back.

A recording bundle is `recording.json` plus the exact Report artifacts. Playback reads only
the bundle: it never calls the scanner or the LLM and needs no Target Application checkout.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Protocol

FORMAT_VERSION = 1
REFERENCE_TARGET = "juice-shop"
REFERENCE_COMMIT = "c9f99228d9d56afb5f5ca7925376292f7fa44b13"
RECORDINGS_DIR = Path(__file__).resolve().parents[1] / "recordings"
BUNDLE_DIR = RECORDINGS_DIR / REFERENCE_TARGET
ARTIFACTS = {"json": "report.json", "md": "report.md", "html": "report.html", "pdf": "report.pdf"}


class Clock(Protocol):
    def monotonic(self) -> float: ...
    async def sleep(self, seconds: float) -> None: ...


class SystemClock:
    def monotonic(self) -> float:
        return time.monotonic()

    async def sleep(self, seconds: float) -> None:
        await asyncio.sleep(seconds)


class RecordingError(Exception):
    """The bundle is missing or was written in an incompatible format."""


class Recording:
    def __init__(self, bundle: Path, target: dict, events: list[dict]):
        self.bundle = bundle
        self.target = target
        self.events = events

    def artifact(self, fmt: str) -> Path:
        return self.bundle / ARTIFACTS[fmt]


def load_recording(bundle: Path = BUNDLE_DIR) -> Recording:
    path = Path(bundle) / "recording.json"
    if not path.is_file():
        raise RecordingError(f"No recording at {bundle}; regenerate it with "
                             f"`python -m dashboard.backend.replay record targets/{REFERENCE_TARGET}`")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("format_version") != FORMAT_VERSION:
        raise RecordingError(f"Recording format {data.get('format_version')!r} is incompatible "
                             f"with format {FORMAT_VERSION}; regenerate it from the pinned Target Application")
    missing = [name for name in ARTIFACTS.values() if not (Path(bundle) / name).is_file()]
    if missing:
        raise RecordingError(f"Recording is missing Report artifacts: {', '.join(missing)}")
    return Recording(Path(bundle), data["target"], data["events"])


def record(source: str, out_dir: Path = BUNDLE_DIR, *, cache_dir: Path = Path(".dpdp-cache"),
           targets_dir: Path = Path("targets")) -> Path:
    """Scan `source` once, store the stage events with elapsed times and the final Report artifacts."""
    from dashboard.backend.app import ScanRun, execute_scan

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    run = ScanRun("recording", source)
    execute_scan(run, source, out_dir, cache_dir=cache_dir, targets_dir=targets_dir)
    if run.status != "completed":
        raise RecordingError(f"Scan failed, nothing recorded: {run.events[-1].get('message', '')}")
    report = json.loads((out_dir / ARTIFACTS["json"]).read_text(encoding="utf-8"))
    target = {"name": report["target"]["name"], "commit": report["target"]["commit"]}
    if target["name"] == REFERENCE_TARGET and target["commit"] != REFERENCE_COMMIT:
        raise RecordingError(f"Reference Target is at {target['commit']}, not the pinned {REFERENCE_COMMIT}")
    # every event of a recorded run carries the run's final mode (cache-only or live)
    events = [{**{k: v for k, v in e.items() if k != "run_id"}, "mode": run.mode} for e in run.events]
    bundle = {"format_version": FORMAT_VERSION, "target": target, "events": events}
    path = out_dir / "recording.json"
    path.write_text(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m dashboard.backend.replay")
    commands = parser.add_subparsers(dest="command", required=True)
    rec = commands.add_parser("record", help="scan a Target Application and write a Replay Mode bundle")
    rec.add_argument("target")
    rec.add_argument("--out", type=Path,
                     help="bundle directory (default dashboard/recordings/<target directory name>)")
    args = parser.parse_args(argv)
    try:
        out = args.out or RECORDINGS_DIR / Path(args.target.rstrip("/")).name.removesuffix(".git")
        print(record(args.target, out))
    except Exception as exc:  # report and exit non-zero; nothing partial is a valid bundle
        print(f"replay: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
