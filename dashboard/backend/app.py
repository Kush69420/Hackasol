"""Local Dashboard service: an adapter from the Auditor to HTTP + SSE. Bind to 127.0.0.1 only."""

from __future__ import annotations

import asyncio
import datetime as dt
import json
import re
import threading
import time
import uuid
from pathlib import Path

from fastapi import File, FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, StrictStr

from auditor import scan as scan_module
from auditor.masking import mask_for_report
from auditor.registry import load_registry
from auditor.report import write_reports
from dashboard.backend import inputs as inputs_module
from dashboard.backend import replay as replay_module
from dashboard.backend.replay import ARTIFACTS, Clock, RecordingError, SystemClock
from dashboard.backend.targets import input_kind, label_for

STAGES = ("inventory", "elements", "data_flows", "findings")
MEDIA_TYPES = {"json": "application/json", "md": "text/markdown",
               "html": "text/html", "pdf": "application/pdf"}
FRONTEND_DIST = Path(__file__).resolve().parents[1] / "frontend" / "dist"
EXCERPT_LIMIT = 600
_UNSAFE = re.compile(r"[\s\x00-\x1f\x7f]")


class ScanRequest(BaseModel):
    target: StrictStr


class SnippetRequest(BaseModel):
    code: StrictStr
    language: StrictStr


def validate_target(value: str) -> str:
    """Accept only an existing local directory or an https Git URL; never anything shell-shaped."""
    if not value or value.startswith("-") or _UNSAFE.search(value):
        raise ValueError("target must be a path or https Git URL without whitespace or control characters")
    if value.startswith("https://"):
        if len(value) <= len("https://") or "/" not in value[len("https://"):]:
            raise ValueError("target must be a Git URL of the form https://host/owner/repo")
        return value
    if not Path(value).expanduser().is_dir():
        raise ValueError("target must be an existing directory or an https Git URL")
    return value


class ScanRun:
    """One run's ordered events. Written by one worker thread, read by SSE streams."""

    def __init__(self, run_id: str, target: str, mode: str = "live", display: str | None = None):
        self.run_id = run_id
        self.target = target
        self.display = display or target
        self.started_at = dt.datetime.now(dt.timezone.utc).isoformat()
        self.mode = mode
        self.status = "running"
        self.events: list[dict] = []
        self.report_dir: Path | None = None
        self._lock = threading.Lock()
        self._started = time.monotonic()

    def _emit(self, event: dict) -> None:
        with self._lock:
            event = {"run_id": self.run_id, "ordinal": len(self.events), "mode": self.mode,
                     "elapsed_ms": int((time.monotonic() - self._started) * 1000), **event}
            self.events.append(event)

    def stage(self, name: str) -> None:
        seen = [e["stage"] for e in self.events if e["type"] == "stage"]
        if self.status == "running" and len(seen) < len(STAGES) and name == STAGES[len(seen)]:
            self._emit({"type": "stage", "stage": name})

    def complete(self, mode: str, finding_count: int) -> None:
        self.mode = mode
        # status flips before the event is visible, so a client that sees `completed` can download
        self.status = "completed"
        self._emit({"type": "completed", "finding_count": finding_count})

    def fail(self, message: str) -> None:
        self.status = "failed"
        self._emit({"type": "failed", "message": mask_for_report(message)[:300]})

    def snapshot(self, start: int) -> list[dict]:
        with self._lock:
            return self.events[start:]


def execute_scan(run: ScanRun, source: str, out_dir: Path, *, cache_dir: Path = Path(".dpdp-cache"),
                 targets_dir: Path = Path("targets")) -> None:
    """Run the Auditor entry point; complete only once every Report artifact exists."""
    try:
        report = scan_module.run_scan(source, cache_dir=cache_dir, targets_dir=targets_dir,
                                      on_stage=run.stage)
        write_reports(report, Path(out_dir) / ARTIFACTS["json"])
        missing = [n for n in ARTIFACTS.values() if not (Path(out_dir) / n).is_file()]
        if missing:
            raise RuntimeError(f"Report artifacts missing: {', '.join(missing)}")
        run.report_dir = Path(out_dir)
        mode = "cache-only" if report.get("llm", {}).get("mode") == "cache-only" else "live"
        run.complete(mode, len(report["findings"]))
    except Exception as exc:
        run.fail(str(exc) or type(exc).__name__)


class ReplayRun:
    """Playback of a recording; events become visible at their recorded offsets from replay start."""

    def __init__(self, run_id: str, recording, clock: Clock):
        self.run_id = run_id
        self.target = recording.target["name"]
        self.display = label_for(self.target)
        self.started_at = dt.datetime.now(dt.timezone.utc).isoformat()
        self.mode = "recorded"
        self.recording = recording
        self.clock = clock
        self.started = clock.monotonic()
        self.events = [{"run_id": run_id, **e, "mode": "recorded"} for e in recording.events]

    @property
    def status(self) -> str:
        last = self.events[-1] if self.events else None
        if last is None or round(self.elapsed_ms(), 3) < last["elapsed_ms"]:
            return "running"
        return "failed" if last["type"] == "failed" else "completed"

    def elapsed_ms(self) -> float:
        return (self.clock.monotonic() - self.started) * 1000

    @property
    def report_dir(self) -> Path:
        return self.recording.bundle


def create_app(*, clock: Clock | None = None, reports_dir: Path = Path("reports/dashboard"),
               cache_dir: Path = Path(".dpdp-cache"), targets_dir: Path = Path("targets"),
               bundle_dir: Path | None = None, recordings_dir: Path = replay_module.RECORDINGS_DIR,
               frontend_dist: Path = FRONTEND_DIST) -> FastAPI:
    app = FastAPI(title="DPDP Compliance Auditor Dashboard")
    clock = clock or SystemClock()
    runs: dict[str, ScanRun | ReplayRun] = {}

    def get_run(run_id: str):
        run = runs.get(run_id)
        if run is None:
            raise HTTPException(404, "Unknown run")
        return run
    from dashboard.backend.probes import router as probe_router; app.include_router(probe_router(get_run))
    from dashboard.backend.fixpatch import router as fixpatch_router; app.include_router(fixpatch_router(get_run))
    from dashboard.backend.legal import router as legal_router; app.include_router(legal_router(get_run))

    def launch(target: str, display: str | None = None) -> dict:
        run_id = uuid.uuid4().hex
        run = ScanRun(run_id, target, display=display)
        runs[run_id] = run
        threading.Thread(target=execute_scan, daemon=True, name=f"scan-{run_id}",
                         args=(run, target, Path(reports_dir) / run_id),
                         kwargs={"cache_dir": cache_dir, "targets_dir": targets_dir}).start()
        return {"run_id": run_id, "mode": "live"}

    @app.post("/api/scans", status_code=202)
    def start_scan(body: ScanRequest):
        try:
            target = validate_target(body.target)
        except ValueError as exc:
            raise HTTPException(422, str(exc))
        return launch(target)

    @app.post("/api/scans/upload", status_code=202)
    def start_upload_scan(file: UploadFile = File(...)):
        try:
            directory = inputs_module.store_upload(file.filename, file.file, Path(targets_dir))
        except inputs_module.InputRejected as exc:
            raise HTTPException(exc.status, exc.message)
        return launch(str(directory), display="upload")

    @app.post("/api/scans/snippet", status_code=202)
    def start_snippet_scan(body: SnippetRequest):
        try:
            directory = inputs_module.write_snippet(body.code, body.language, Path(targets_dir))
        except inputs_module.InputRejected as exc:
            raise HTTPException(exc.status, exc.message)
        return launch(str(directory), display="snippet")

    def bundle_for(name: str) -> Path:
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name):
            raise HTTPException(404, "No recording for that name")
        if name == replay_module.REFERENCE_TARGET and bundle_dir is not None:
            return Path(bundle_dir)
        return Path(recordings_dir) / name

    from dashboard.backend.targets import router as targets_router
    app.include_router(targets_router(runs=runs, launch=launch, targets_dir=Path(targets_dir),
                                      recordings_dir=Path(recordings_dir), bundle_for=bundle_for,
                                      reports_dir=Path(reports_dir)))

    @app.get("/api/replays")
    def list_replays():
        root = Path(recordings_dir)
        names = sorted(p.parent.name for p in root.glob("*/recording.json")) if root.is_dir() else []
        return {"recordings": names}

    @app.post("/api/replays/{name}", status_code=202)
    def start_replay(name: str):
        try:
            recording = replay_module.load_recording(bundle_for(name))
        except RecordingError as exc:
            raise HTTPException(404 if "No recording" in str(exc) else 409, str(exc))
        run_id = uuid.uuid4().hex
        runs[run_id] = ReplayRun(run_id, recording, clock)
        return {"run_id": run_id, "mode": "recorded"}

    @app.get("/api/scans/{run_id}")
    def scan_status(run_id: str):
        run = get_run(run_id)
        return {"run_id": run.run_id, "mode": run.mode, "status": run.status, "target": run.target,
                "input": input_kind(run.target)}

    @app.get("/api/scans/{run_id}/events")
    async def scan_events(run_id: str):
        run = get_run(run_id)

        async def live():
            sent = 0
            while True:
                batch = run.snapshot(sent)
                for event in batch:
                    yield f"data: {json.dumps(event)}\n\n"
                sent += len(batch)
                if batch and batch[-1]["type"] != "stage":
                    return
                if not batch:
                    await asyncio.sleep(0.05)

        async def playback():
            for event in run.events:
                behind_ms = round(event["elapsed_ms"] - run.elapsed_ms(), 3)
                if behind_ms > 0:
                    await run.clock.sleep(behind_ms / 1000)
                yield f"data: {json.dumps(event)}\n\n"

        stream = playback() if isinstance(run, ReplayRun) else live()
        return StreamingResponse(stream, media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache"})

    @app.get("/api/scans/{run_id}/report/{fmt}")
    def report(run_id: str, fmt: str):
        run = get_run(run_id)
        if fmt not in ARTIFACTS:
            raise HTTPException(404, "Unknown Report format")
        if run.status != "completed" or run.report_dir is None:
            raise HTTPException(409, f"Report not available: run is {run.status}")
        return FileResponse(run.report_dir / ARTIFACTS[fmt], media_type=MEDIA_TYPES[fmt])

    @app.get("/api/provisions/{provision_id}")
    def provision(provision_id: str):
        p = load_registry().get(provision_id)
        if p is None:
            raise HTTPException(404, "Unknown Provision")
        return {"id": p.id, "citation": p.citation, "title": p.title,
                "excerpt": (p.excerpt or "")[:EXCERPT_LIMIT],
                "penalty_ceiling_inr_crore": p.penalty_ceiling_inr_crore,
                "enforceable_from": p.enforceable_from.isoformat() if p.enforceable_from else None}

    @app.get("/{path:path}")
    def frontend(path: str):
        if path == "api" or path.startswith("api/") or not Path(frontend_dist, "index.html").is_file():
            return JSONResponse({"detail": "Not found"}, status_code=404)
        root = Path(frontend_dist).resolve()
        candidate = (root / path).resolve()
        if path and candidate.is_file() and candidate.is_relative_to(root):
            return FileResponse(candidate)
        return FileResponse(root / "index.html")

    return app


app = create_app()
