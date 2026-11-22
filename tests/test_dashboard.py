"""Dashboard service: live runs, Replay Mode and masking (issue #8)."""

import asyncio
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from auditor import scan as scan_module
from dashboard.backend import app as app_module
from dashboard.backend import replay as replay_module
from dashboard.backend.app import STAGES, create_app

ROOT = Path(__file__).resolve().parents[1]
JUICE = ROOT / "targets" / "juice-shop"
BUNDLE = replay_module.BUNDLE_DIR
FORMATS = {"json": "application/json", "md": "text/markdown", "html": "text/html", "pdf": "application/pdf"}


def sse(response) -> list[dict]:
    assert response.headers["content-type"].startswith("text/event-stream")
    return [json.loads(block[len("data: "):]) for block in response.text.split("\n\n") if block.strip()]


def fixture_report() -> dict:
    for path in (BUNDLE / "report.json", ROOT / "reports" / "juice-shop" / "report.json"):
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    pytest.skip("no Report fixture available")


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(reports_dir=tmp_path / "runs", cache_dir=tmp_path / "cache",
                                 targets_dir=tmp_path / "targets"))


def fake_scan(report, calls=None):
    def run(source, **kwargs):
        if calls is not None:
            calls.append((source, kwargs))
        for stage in STAGES:
            kwargs["on_stage"](stage)
        return report
    return run


# ---- live -----------------------------------------------------------------------------------

def test_live_local_path_streams_four_stages_then_completes(tmp_path, monkeypatch):
    monkeypatch.setenv("DPDP_LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:1")
    if not JUICE.is_dir():
        pytest.skip("targets/juice-shop is not checked out")
    client = TestClient(create_app(reports_dir=tmp_path / "runs"))
    started = client.post("/api/scans", json={"target": "targets/juice-shop"})
    assert started.status_code == 202 and started.json()["mode"] == "live"
    run_id = started.json()["run_id"]
    events = sse(client.get(f"/api/scans/{run_id}/events"))
    assert [e["ordinal"] for e in events] == list(range(5))
    assert [e["stage"] for e in events[:4]] == list(STAGES)
    assert events[4]["type"] == "completed" and events[4]["finding_count"] > 0
    assert events[4]["mode"] in {"live", "cache-only"}
    assert [e["elapsed_ms"] for e in events] == sorted(e["elapsed_ms"] for e in events)
    assert client.get(f"/api/scans/{run_id}").json()["status"] == "completed"
    for fmt, media in FORMATS.items():
        r = client.get(f"/api/scans/{run_id}/report/{fmt}")
        assert r.status_code == 200 and r.headers["content-type"].startswith(media)
    # a late client still receives every event from ordinal 0
    assert sse(client.get(f"/api/scans/{run_id}/events")) == events


def test_live_git_url_reaches_the_same_scan_interface(client, monkeypatch):
    calls = []
    monkeypatch.setattr(scan_module, "run_scan", fake_scan(fixture_report(), calls))
    run_id = client.post("/api/scans", json={"target": "https://github.com/example/app.git"}).json()["run_id"]
    events = sse(client.get(f"/api/scans/{run_id}/events"))
    assert events[-1]["type"] == "completed"
    assert calls[0][0] == "https://github.com/example/app.git"
    assert calls[0][1]["cache_dir"] == Path(".dpdp-cache") or calls[0][1]["cache_dir"].name == "cache"
    assert client.get(f"/api/scans/{run_id}/report/json").status_code == 200


def test_live_invalid_resolution_fails_without_counterfeit_completion(client, tmp_path, monkeypatch):
    # the directory vanishes between validation and the scan: the Auditor's own resolution fails
    monkeypatch.setattr(app_module, "validate_target", lambda value: value)
    run_id = client.post("/api/scans", json={"target": str(tmp_path / "gone")}).json()["run_id"]
    events = sse(client.get(f"/api/scans/{run_id}/events"))
    assert events[-1]["type"] == "failed" and not any(e["type"] == "completed" for e in events)
    assert client.get(f"/api/scans/{run_id}").json()["status"] == "failed"
    assert client.get(f"/api/scans/{run_id}/report/json").status_code == 409


@pytest.mark.parametrize("body", [{}, {"target": ""}, {"target": 7}, {"target": None},
                                  {"target": "/definitely/not/a/dir"}, {"target": "--upload-pack=x"},
                                  {"target": "https://x/y z"}, {"target": "http://x/y"},
                                  {"target": "https://"}])
def test_live_bad_input_is_422(client, body):
    assert client.post("/api/scans", json=body).status_code == 422


def test_live_unknown_id_and_format_are_404_and_serve_no_files(client, monkeypatch):
    assert client.get("/api/scans/nope").status_code == 404
    assert client.get("/api/scans/nope/events").status_code == 404
    assert client.get("/api/scans/nope/report/json").status_code == 404
    monkeypatch.setattr(scan_module, "run_scan", fake_scan(fixture_report()))
    run_id = client.post("/api/scans", json={"target": "https://github.com/example/app"}).json()["run_id"]
    sse(client.get(f"/api/scans/{run_id}/events"))
    for fmt in ("txt", "..%2f..%2fpyproject.toml", "py"):
        assert client.get(f"/api/scans/{run_id}/report/{fmt}").status_code == 404
    assert "dpdp-auditor" not in client.get("/pyproject.toml").text
    assert client.get("/%2e%2e/pyproject.toml").status_code in (200, 404)
    assert "dpdp-auditor" not in client.get("/%2e%2e/pyproject.toml").text
    assert client.get("/api/provisions/not-a-provision").status_code == 404


def test_live_provision_excerpt(client):
    from auditor.registry import load_registry
    pid = next(iter(load_registry()))
    body = client.get(f"/api/provisions/{pid}").json()
    assert body["id"] == pid and len(body["excerpt"]) <= 600
    assert set(body) == {"id", "citation", "title", "excerpt", "penalty_ceiling_inr_crore", "enforceable_from"}


# ---- replay ---------------------------------------------------------------------------------

class FakeClock:
    def __init__(self):
        self.now = 100.0
        self.sleeps = []

    def monotonic(self):
        return self.now

    async def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


def make_bundle(tmp_path, events, version=1):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    for name, data in (("report.json", b'{"k": 1}\n'), ("report.md", b"# md\n"),
                       ("report.html", b"<p>h</p>"), ("report.pdf", b"%PDF-fake\x00\xff")):
        (bundle / name).write_bytes(data)
    (bundle / "recording.json").write_text(json.dumps({
        "format_version": version, "target": {"name": "juice-shop", "commit": "c" * 40}, "events": events}))
    return bundle


RECORDED = [
    {"ordinal": 0, "mode": "cache-only", "type": "stage", "stage": "inventory", "elapsed_ms": 1500},
    {"ordinal": 1, "mode": "cache-only", "type": "stage", "stage": "elements", "elapsed_ms": 4000},
    {"ordinal": 2, "mode": "cache-only", "type": "stage", "stage": "data_flows", "elapsed_ms": 4100},
    {"ordinal": 3, "mode": "cache-only", "type": "stage", "stage": "findings", "elapsed_ms": 20000},
    {"ordinal": 4, "mode": "cache-only", "type": "completed", "elapsed_ms": 20050, "finding_count": 3},
]


def test_replay_emits_recorded_elapsed_times_on_the_injected_clock(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("scanner or LLM called during Replay Mode")
    monkeypatch.setattr(scan_module, "run_scan", boom)
    monkeypatch.setattr("auditor.llm.LLMSession.from_env", boom)
    clock = FakeClock()
    client = TestClient(create_app(clock=clock, bundle_dir=make_bundle(tmp_path, RECORDED)))
    started = client.post("/api/replays/juice-shop")
    assert started.status_code == 202 and started.json()["mode"] == "recorded"
    run_id = started.json()["run_id"]
    assert client.get(f"/api/scans/{run_id}").json()["status"] == "running"
    assert client.get(f"/api/scans/{run_id}/report/json").status_code == 409
    events = sse(client.get(f"/api/scans/{run_id}/events"))
    assert [e["ordinal"] for e in events] == [0, 1, 2, 3, 4]
    assert [e.get("stage") for e in events[:4]] == list(STAGES)
    assert [e["elapsed_ms"] for e in events] == [1500, 4000, 4100, 20000, 20050]
    assert {e["mode"] for e in events} == {"recorded"} and {e["run_id"] for e in events} == {run_id}
    # sleeps are the gaps between recorded offsets, measured from replay start
    assert [round(s, 3) for s in clock.sleeps] == [1.5, 2.5, 0.1, 15.9, 0.05]
    assert clock.now == pytest.approx(100.0 + 20.05)
    assert client.get(f"/api/scans/{run_id}").json()["status"] == "completed"
    # a late client replays the already-elapsed events without waiting
    clock.sleeps.clear()
    assert sse(client.get(f"/api/scans/{run_id}/events")) == events and clock.sleeps == []


def test_replay_downloads_are_byte_identical_to_the_bundle(tmp_path):
    bundle = make_bundle(tmp_path, RECORDED)
    client = TestClient(create_app(clock=FakeClock(), bundle_dir=bundle))
    run_id = client.post("/api/replays/juice-shop").json()["run_id"]
    sse(client.get(f"/api/scans/{run_id}/events"))
    for fmt, name in replay_module.ARTIFACTS.items():
        r = client.get(f"/api/scans/{run_id}/report/{fmt}")
        assert r.status_code == 200 and r.content == (bundle / name).read_bytes()


def test_replay_rejects_incompatible_or_missing_bundle(tmp_path):
    bad = TestClient(create_app(bundle_dir=make_bundle(tmp_path, RECORDED, version=99)))
    assert bad.post("/api/replays/juice-shop").status_code == 409
    assert TestClient(create_app(bundle_dir=tmp_path / "none")).post("/api/replays/juice-shop").status_code == 404


def test_replay_shipped_recording_never_scans(monkeypatch):
    if not (BUNDLE / "recording.json").is_file():
        pytest.skip("recording not generated")

    def boom(*a, **k):
        raise AssertionError("scanner or LLM called during Replay Mode")
    monkeypatch.setattr(scan_module, "run_scan", boom)
    monkeypatch.setattr("auditor.llm.LLMSession.from_env", boom)
    clock = FakeClock()
    client = TestClient(create_app(clock=clock, targets_dir=Path("/nonexistent")))
    run_id = client.post("/api/replays/juice-shop").json()["run_id"]
    events = sse(client.get(f"/api/scans/{run_id}/events"))
    recorded = json.loads((BUNDLE / "recording.json").read_text())
    assert recorded["format_version"] == 1
    assert recorded["target"]["commit"] == "c9f99228d9d56afb5f5ca7925376292f7fa44b13"
    assert [e["stage"] for e in events if e["type"] == "stage"] == list(STAGES)
    assert events[-1]["type"] == "completed"
    assert [e["elapsed_ms"] for e in events] == [e["elapsed_ms"] for e in recorded["events"]]
    assert {e["mode"] for e in events} == {"recorded"}
    for fmt, name in replay_module.ARTIFACTS.items():
        assert client.get(f"/api/scans/{run_id}/report/{fmt}").content == (BUNDLE / name).read_bytes()


# ---- masking --------------------------------------------------------------------------------

# Synthetic Stripe-shaped secret, assembled at runtime so no key-shaped literal is committed.
SECRET = "_".join(("sk", "live", "Zq81JkX7vN3mPw5TrB9cYd2e"))
AADHAAR = "2345 6789 0124"


def test_masking_secret_and_aadhaar_never_reach_events_bundle_or_downloads(tmp_path, monkeypatch):
    monkeypatch.setenv("DPDP_LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:1")
    target = tmp_path / "leaky"
    target.mkdir()
    (target / "server.js").write_text(
        "const express = require('express')\n"
        "const app = express()\n"
        f"const STRIPE_SECRET_KEY = '{SECRET}'\n"
        f"const aadhaar = '{AADHAAR}'\n"
        "app.post('/api/users', (req, res) => {\n"
        "  console.log('signup', req.body.email, aadhaar, STRIPE_SECRET_KEY)\n"
        "  res.json({ ok: true })\n"
        "})\n")
    forms = (SECRET, AADHAAR, AADHAAR.replace(" ", ""))

    bundle = tmp_path / "bundle"
    replay_module.record(str(target), bundle, cache_dir=tmp_path / "cache")
    blobs = [p.read_bytes() for p in bundle.iterdir() if p.suffix != ".pdf"]
    assert any(b"report" in p.name.encode() for p in bundle.iterdir())
    for blob in blobs:
        for raw in forms:
            assert raw.encode() not in blob

    client = TestClient(create_app(reports_dir=tmp_path / "runs", cache_dir=tmp_path / "cache"))
    run_id = client.post("/api/scans", json={"target": str(target)}).json()["run_id"]
    events = sse(client.get(f"/api/scans/{run_id}/events"))
    assert events[-1]["type"] == "completed"
    payload = json.dumps(events)
    for fmt in FORMATS:
        body = client.get(f"/api/scans/{run_id}/report/{fmt}").content
        for raw in forms:
            if fmt != "pdf":  # PDF text is compressed; its HTML source is checked above
                assert raw.encode() not in body
    for raw in forms:
        assert raw not in payload


def test_masking_failed_event_message_is_masked(client, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError(f"cannot parse STRIPE_SECRET_KEY = '{SECRET}' for {AADHAAR}")
    monkeypatch.setattr(scan_module, "run_scan", boom)
    run_id = client.post("/api/scans", json={"target": "https://github.com/example/app"}).json()["run_id"]
    events = sse(client.get(f"/api/scans/{run_id}/events"))
    assert events[-1]["type"] == "failed"
    assert SECRET not in events[-1]["message"] and AADHAAR not in events[-1]["message"]
