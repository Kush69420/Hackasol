"""Target Applications on the dashboard: the recorded list, live scans of local clones, and recent runs.

Everything listed comes from `manifest.json` and the recording bundles; nothing is invented. A live scan
starts only for a name in the fixed TARGETS allowlist, never for a path the client supplies.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from dashboard.backend.replay import ARTIFACTS, RecordingError, load_recording

# replay name (manifest `name`) -> (human label, clone directory under targets/)
TARGETS = {
    "juice-shop": ("Juice Shop", "juice-shop"),
    "trackmyrupee": ("TrackMyRupee", "trackmyrupee"),
    "ai-kyc-platform": ("ai-kyc-platform", "ai-kyc-platform"),
    "singharya-e-kyc": ("singharya E-KYC", "singharya-e-kyc"),
}
SEVERITIES = ("critical", "high", "medium", "low")
RUNS_DEFAULT = 10
RUNS_CAP = 50
_RUN_ID = re.compile(r"[0-9a-f]{32}")
_UTC = dt.timezone.utc


def label_for(name: str | None) -> str | None:
    if not isinstance(name, str):
        return None
    return TARGETS[name][0] if name in TARGETS else name


def utc_now_iso() -> str:
    return dt.datetime.now(_UTC).isoformat()


def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def severity_counts(report) -> dict | None:
    """Count the Report's Findings by Severity band; None when the Report has no Findings list."""
    findings = report.get("findings") if isinstance(report, dict) else None
    if not isinstance(findings, list):
        return None
    counts = {band: 0 for band in SEVERITIES}
    for finding in findings:
        severity = finding.get("severity") if isinstance(finding, dict) else None
        band = severity.get("band") if isinstance(severity, dict) else None
        if band in counts:
            counts[band] += 1
    return {**counts, "total": len(findings)}


def _manifest_entries(recordings_dir: Path) -> list[dict]:
    data = _read_json(Path(recordings_dir) / "manifest.json")
    entries = data.get("entries") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        return []
    return [entry for entry in entries if isinstance(entry, dict)]


def _parse_time(value) -> dt.datetime:
    try:
        parsed = dt.datetime.fromisoformat(value) if isinstance(value, str) else None
    except ValueError:
        parsed = None
    if parsed is None:
        return dt.datetime.min.replace(tzinfo=_UTC)
    return parsed.replace(tzinfo=_UTC) if parsed.tzinfo is None else parsed


def _finding_count(events) -> int | None:
    for event in events:
        if event.get("type") == "completed":
            return event.get("finding_count")
    return None


def _persisted_target(report: dict) -> str | None:
    target = report.get("target") if isinstance(report.get("target"), dict) else {}
    source = target.get("source")
    if isinstance(source, str) and Path(source).parent.name == "uploads":
        try:
            names = [p.name for p in Path(source).iterdir()]
        except OSError:
            names = []
        return "snippet" if any(n.startswith("snippet.") for n in names) else "upload"
    return label_for(target.get("name"))


def router(*, runs: dict, launch, targets_dir: Path, recordings_dir: Path, bundle_for,
           reports_dir: Path) -> APIRouter:
    api = APIRouter()
    persisted_cache: dict[str, tuple[tuple, dict]] = {}

    @api.get("/api/targets")
    def list_targets():
        rows = []
        for entry in _manifest_entries(Path(recordings_dir)):
            name = entry.get("name")
            if name not in TARGETS or any(row["name"] == name for row in rows):
                continue
            label, clone = TARGETS[name]
            bundle = bundle_for(name)
            if not (Path(bundle) / "recording.json").is_file():
                continue
            try:
                load_recording(bundle)
                replay_available = True
            except RecordingError:
                replay_available = False
            provenance = entry.get("provenance") if isinstance(entry.get("provenance"), dict) else {}
            report = _read_json(Path(bundle) / ARTIFACTS["json"])
            rows.append({
                "name": name,
                "label": label,
                "replay_available": replay_available,
                "live_available": (Path(targets_dir) / clone).is_dir(),
                "scan_date": provenance.get("scan_started_at"),
                "llm": {"provider": provenance.get("llm_provider"), "model": provenance.get("llm_model")},
                "counts": severity_counts(report),
                "summary_source": "recording",
            })
        return rows

    @api.post("/api/targets/{name}/scan", status_code=202)
    def scan_target(name: str):
        if name not in TARGETS:
            raise HTTPException(404, "Unknown Target Application")
        label, clone = TARGETS[name]
        clone_dir = Path(targets_dir) / clone
        if not clone_dir.is_dir():
            raise HTTPException(409, f"{label} is not cloned at {clone_dir}; clone it per README Set-up")
        return launch(str(clone_dir), display=label)

    def in_memory_row(run) -> dict:
        replay = run.mode == "recorded"
        return {"run_id": run.run_id, "mode": "replay" if replay else "live", "target": run.display,
                "status": run.status, "started_at": run.started_at,
                "finding_count": _finding_count(list(run.events))}

    def persisted_row(directory: Path) -> dict:
        complete = all((directory / name).is_file() for name in ARTIFACTS.values())
        report_path = directory / ARTIFACTS["json"]
        try:
            dir_mtime = directory.stat().st_mtime
            report_stat = report_path.stat()
            signature = (report_stat.st_mtime_ns, report_stat.st_size)
        except OSError:
            dir_mtime, signature = None, None
        key = str(directory)
        cached = persisted_cache.get(key)
        if signature is not None and cached is not None and cached[0] == signature:
            data = cached[1]
        else:
            report = _read_json(report_path) if signature is not None else None
            if not isinstance(report, dict):
                report = {}
            scan = report.get("scan") if isinstance(report.get("scan"), dict) else {}
            started = scan.get("started_at")
            if not isinstance(started, str) and dir_mtime is not None:
                started = dt.datetime.fromtimestamp(dir_mtime, _UTC).isoformat()
            findings = report.get("findings")
            data = {"started_at": started,
                    "target": _persisted_target(report),
                    "finding_count": len(findings) if isinstance(findings, list) else None}
            if signature is not None:
                persisted_cache[key] = (signature, data)
        return {"run_id": directory.name, "mode": "live", "target": data["target"],
                "status": "completed" if complete else "failed", "started_at": data["started_at"],
                "finding_count": data["finding_count"]}

    @api.get("/api/runs")
    def list_runs(limit: int = Query(RUNS_DEFAULT, ge=1)):
        live = {run_id: in_memory_row(run) for run_id, run in list(runs.items())}
        rows = list(live.values())
        root = Path(reports_dir)
        try:
            children = sorted(root.iterdir()) if root.is_dir() else []
        except OSError:
            children = []
        for child in children:
            try:
                if child.name in live or not _RUN_ID.fullmatch(child.name) or not child.is_dir():
                    continue
                rows.append(persisted_row(child))
            except OSError:
                continue
        rows.sort(key=lambda row: _parse_time(row["started_at"]), reverse=True)
        return rows[:min(limit, RUNS_CAP)]

    return api
