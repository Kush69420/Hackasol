"""Dashboard Target Applications: recorded list from the manifest, live scans by allowlisted name, recent runs."""

import datetime as dt
import json
import os
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from auditor import scan as scan_module
from dashboard.backend import app as app_module
from dashboard.backend import replay as replay_module
from dashboard.backend.app import STAGES, create_app
from dashboard.backend.replay import ARTIFACTS

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = replay_module.RECORDINGS_DIR / "manifest.json"


def sse(response) -> list[dict]:
    assert response.headers["content-type"].startswith("text/event-stream")
    return [json.loads(block[len("data: "):]) for block in response.text.split("\n\n") if block.strip()]


def counts_of(report: dict) -> dict:
    bands = [f.get("severity", {}).get("band") for f in report["findings"]]
    return {"critical": bands.count("critical"), "high": bands.count("high"),
            "medium": bands.count("medium"), "low": bands.count("low"), "total": len(bands)}


@pytest.fixture
def scans(monkeypatch):
    """Stub the scan runner and report writer; record the source of each live scan."""
    calls = []

    def run_scan(source, **kwargs):
        calls.append(source)
        for stage in STAGES:
            kwargs["on_stage"](stage)
        return {"findings": [], "llm": {"mode": "cache-only"}}

    def write_reports(report, json_path):
        json_path.parent.mkdir(parents=True, exist_ok=True)
        for name in ARTIFACTS.values():
            (json_path.parent / name).write_bytes(b"stub")

    monkeypatch.setattr(scan_module, "run_scan", run_scan)
    monkeypatch.setattr(app_module, "write_reports", write_reports)
    return calls


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(reports_dir=tmp_path / "runs", cache_dir=tmp_path / "cache",
                                 targets_dir=tmp_path / "targets"))


def write_bundle(bundle: Path, findings: list[dict]) -> None:
    bundle.mkdir(parents=True)
    (bundle / "recording.json").write_text(json.dumps({
        "format_version": replay_module.FORMAT_VERSION, "target": {"name": bundle.name, "commit": "x"},
        "events": [{"type": "completed", "elapsed_ms": 0, "ordinal": 0, "finding_count": len(findings)}],
    }), encoding="utf-8")
    (bundle / ARTIFACTS["json"]).write_text(json.dumps({"findings": findings}), encoding="utf-8")
    for name in ("md", "html", "pdf"):
        (bundle / ARTIFACTS[name]).write_bytes(b"stub")


def write_run(root: Path, index: int, started: str, *, findings=0, artifacts=True, body=None) -> Path:
    directory = root / f"{index:032x}"
    directory.mkdir(parents=True)
    if body is None:
        body = {"scan": {"started_at": started}, "findings": [{"severity": {"band": "low"}}] * findings}
    (directory / ARTIFACTS["json"]).write_text(body if isinstance(body, str) else json.dumps(body),
                                               encoding="utf-8")
    if artifacts:
        for name in ("md", "html", "pdf"):
            (directory / ARTIFACTS[name]).write_bytes(b"stub")
    return directory


# ---- targets ----------------------------------------------------------------------------------

def test_targets_list_matches_the_manifest_and_the_recorded_reports(client, tmp_path):
    if not MANIFEST.is_file():
        pytest.skip("no recordings manifest")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    from dashboard.backend.targets import TARGETS
    expected = [e for e in manifest["entries"] if e["name"] in TARGETS
                and (replay_module.RECORDINGS_DIR / e["name"] / "recording.json").is_file()]
    rows = client.get("/api/targets").json()
    assert isinstance(rows, list)
    assert [r["name"] for r in rows] == [e["name"] for e in expected]
    assert "juice-shop-fork" not in {r["name"] for r in rows}
    for row, entry in zip(rows, expected):
        prov = entry["provenance"]
        assert row["scan_date"] == prov["scan_started_at"]
        assert row["llm"] == {"provider": prov["llm_provider"], "model": prov["llm_model"]}
        report = json.loads((replay_module.RECORDINGS_DIR / entry["name"] / "report.json").read_text())
        assert row["counts"] == counts_of(report)
        assert row["counts"]["total"] == len(report["findings"])
        assert row["replay_available"] is True
        assert row["live_available"] is False  # the fixture targets dir is empty
        assert row["summary_source"] == "recording"
        assert set(row) == {"name", "label", "replay_available", "live_available", "scan_date",
                            "llm", "counts", "summary_source"}


def test_targets_counts_come_from_the_recorded_findings_and_live_flag_from_disk(tmp_path):
    recordings, targets = tmp_path / "recordings", tmp_path / "targets"
    findings = [{"severity": {"band": "high"}}, {"severity": {"band": "high"}},
                {"severity": {"band": "critical"}}, {"severity": {"band": "low"}}, {"id": "no-band"}]
    write_bundle(recordings / "trackmyrupee", findings)
    write_bundle(recordings / "juice-shop-fork", findings)  # a rescan, not one of the Target Applications
    (recordings / "manifest.json").write_text(json.dumps({"format_version": 1, "entries": [
        {"name": "trackmyrupee", "provenance": {"scan_started_at": "2026-11-23T20:48:26+00:00",
                                                 "llm_provider": "omp", "llm_model": "m"}},
        {"name": "juice-shop-fork", "provenance": {}},
    ]}), encoding="utf-8")
    (targets / "trackmyrupee").mkdir(parents=True)
    client = TestClient(create_app(recordings_dir=recordings, targets_dir=targets,
                                   reports_dir=tmp_path / "runs"))
    rows = client.get("/api/targets").json()
    assert [r["name"] for r in rows] == ["trackmyrupee"]
    assert rows[0]["label"] == "TrackMyRupee"
    assert rows[0]["counts"] == {"critical": 1, "high": 2, "medium": 0, "low": 1, "total": 5}
    assert rows[0]["live_available"] is True
    assert rows[0]["llm"] == {"provider": "omp", "model": "m"}
    assert rows[0]["scan_date"] == "2026-11-23T20:48:26+00:00"


def test_targets_replay_unavailable_when_an_artifact_is_missing(tmp_path):
    recordings = tmp_path / "recordings"
    write_bundle(recordings / "singharya-e-kyc", [])
    (recordings / "singharya-e-kyc" / ARTIFACTS["pdf"]).unlink()
    (recordings / "manifest.json").write_text(json.dumps({"entries": [
        {"name": "singharya-e-kyc", "provenance": {}}]}), encoding="utf-8")
    client = TestClient(create_app(recordings_dir=recordings, targets_dir=tmp_path / "targets",
                                   reports_dir=tmp_path / "runs"))
    row = client.get("/api/targets").json()[0]
    assert row["replay_available"] is False and row["live_available"] is False
    assert row["counts"]["total"] == 0


def test_targets_tolerates_a_missing_or_corrupt_manifest(tmp_path):
    recordings = tmp_path / "recordings"
    recordings.mkdir()
    client = TestClient(create_app(recordings_dir=recordings, targets_dir=tmp_path / "targets",
                                   reports_dir=tmp_path / "runs"))
    assert client.get("/api/targets").json() == []
    (recordings / "manifest.json").write_text("{not json", encoding="utf-8")
    assert client.get("/api/targets").json() == []


# ---- live scan of a Target Application -------------------------------------------------------

def test_live_target_scan_is_404_for_unknown_names_and_never_takes_a_path(client, scans, tmp_path):
    for name in ("nope", "juice-shop-fork"):
        assert client.post(f"/api/targets/{name}/scan").status_code == 404
    # an encoded slash does not match the route at all; it must still never start a scan
    for name in ("..%2Fetc", "targets%2Fjuice-shop"):
        assert client.post(f"/api/targets/{name}/scan").status_code != 202
    assert scans == []


def test_live_target_scan_is_409_when_the_clone_is_missing(client, scans, tmp_path):
    response = client.post("/api/targets/trackmyrupee/scan")
    assert response.status_code == 409
    assert "clone it per README Set-up" in response.json()["detail"]
    assert scans == []


def test_live_target_scan_is_202_and_scans_the_allowlisted_clone(scans, tmp_path):
    targets = tmp_path / "targets"
    (targets / "singharya-e-kyc").mkdir(parents=True)
    client = TestClient(create_app(reports_dir=tmp_path / "runs", cache_dir=tmp_path / "cache",
                                   targets_dir=targets))
    response = client.post("/api/targets/singharya-e-kyc/scan")
    assert response.status_code == 202
    body = response.json()
    assert body["mode"] == "live" and set(body) == {"run_id", "mode"}
    events = sse(client.get(f"/api/scans/{body['run_id']}/events"))
    assert events[-1]["type"] == "completed" and events[-1]["mode"] == "cache-only"
    assert scans == [str(targets / "singharya-e-kyc")]
    rows = client.get("/api/runs").json()
    assert rows[0]["run_id"] == body["run_id"]
    assert rows[0]["target"] == "singharya E-KYC" and rows[0]["mode"] == "live"
    assert rows[0]["status"] == "completed" and rows[0]["finding_count"] == 0


# ---- recent runs ------------------------------------------------------------------------------

def test_runs_are_newest_first_capped_and_tolerate_corrupt_or_partial_dirs(tmp_path):
    reports = tmp_path / "runs"
    base = dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc)
    for i in range(55):
        write_run(reports, i, (base + dt.timedelta(hours=i)).isoformat(), findings=i % 3)
    write_run(reports, 100, "2019-06-01T00:00:00+00:00", artifacts=False)   # interrupted: no artifacts
    corrupt = write_run(reports, 101, "", body="{not json")              # corrupt Report, dated by its mtime
    os.utime(corrupt, (dt.datetime(2019, 1, 1).timestamp(),) * 2)
    (reports / "not-a-run-id").mkdir()                                     # foreign directory
    (reports / "stray.txt").write_text("x", encoding="utf-8")
    client = TestClient(create_app(reports_dir=reports, cache_dir=tmp_path / "cache",
                                   targets_dir=tmp_path / "targets"))
    rows = client.get("/api/runs", params={"limit": 500}).json()
    assert len(rows) == 50
    starts = [r["started_at"] for r in rows]
    assert starts == sorted(starts, reverse=True)
    assert rows[0]["run_id"] == f"{54:032x}" and rows[0]["finding_count"] == 54 % 3
    assert all(r["mode"] == "live" for r in rows)
    assert all(r["run_id"] != "not-a-run-id" for r in rows)
    default = client.get("/api/runs").json()
    assert len(default) == 10
    assert client.get("/api/runs", params={"limit": 2}).json()[0]["run_id"] == rows[0]["run_id"]
    assert len(client.get("/api/runs", params={"limit": 2}).json()) == 2
    assert client.get("/api/runs", params={"limit": 0}).status_code == 422


def test_persisted_corrupt_and_partial_runs_report_honestly(tmp_path):
    reports = tmp_path / "runs"
    write_run(reports, 1, "", body="{not json")
    write_run(reports, 2, "2020-01-02T00:00:00+00:00", artifacts=False, findings=2)
    client = TestClient(create_app(reports_dir=reports, cache_dir=tmp_path / "cache",
                                   targets_dir=tmp_path / "targets"))
    by_id = {r["run_id"]: r for r in client.get("/api/runs").json()}
    assert by_id[f"{1:032x}"]["finding_count"] is None and by_id[f"{1:032x}"]["status"] == "completed"
    assert by_id[f"{2:032x}"]["status"] == "failed" and by_id[f"{2:032x}"]["finding_count"] == 2
    assert by_id[f"{2:032x}"]["started_at"] == "2020-01-02T00:00:00+00:00"


def test_persisted_upload_and_snippet_runs_are_labelled_by_their_input(tmp_path):
    reports, targets = tmp_path / "runs", tmp_path / "targets"
    snippet_dir = targets / "uploads" / uuid.uuid4().hex
    snippet_dir.mkdir(parents=True)
    (snippet_dir / "snippet.py").write_text("x = 1\n", encoding="utf-8")
    upload_dir = targets / "uploads" / uuid.uuid4().hex
    upload_dir.mkdir(parents=True)
    (upload_dir / "app.py").write_text("x = 1\n", encoding="utf-8")
    write_run(reports, 3, "2020-01-03T00:00:00+00:00", body={
        "scan": {"started_at": "2020-01-03T00:00:00+00:00"}, "findings": [],
        "target": {"name": snippet_dir.name, "source": str(snippet_dir)}})
    write_run(reports, 4, "2020-01-04T00:00:00+00:00", body={
        "scan": {"started_at": "2020-01-04T00:00:00+00:00"}, "findings": [],
        "target": {"name": upload_dir.name, "source": str(upload_dir)}})
    write_run(reports, 5, "2020-01-05T00:00:00+00:00", body={
        "scan": {"started_at": "2020-01-05T00:00:00+00:00"}, "findings": [],
        "target": {"name": "juice-shop", "source": "targets/juice-shop"}})
    client = TestClient(create_app(reports_dir=reports, cache_dir=tmp_path / "cache", targets_dir=targets))
    by_id = {r["run_id"]: r["target"] for r in client.get("/api/runs").json()}
    assert by_id[f"{3:032x}"] == "snippet"
    assert by_id[f"{4:032x}"] == "upload"
    assert by_id[f"{5:032x}"] == "Juice Shop"


def test_runs_include_replays_and_each_live_run_once(client, scans, tmp_path):
    if not (replay_module.RECORDINGS_DIR / "trackmyrupee" / "recording.json").is_file():
        pytest.skip("no shipped trackmyrupee recording")
    replay = client.post("/api/replays/trackmyrupee")
    assert replay.status_code == 202
    (tmp_path / "targets" / "trackmyrupee").mkdir(parents=True)
    live = client.post("/api/targets/trackmyrupee/scan").json()
    sse(client.get(f"/api/scans/{live['run_id']}/events"))
    rows = client.get("/api/runs", params={"limit": 50}).json()
    ids = [r["run_id"] for r in rows]
    assert len(ids) == len(set(ids))
    by_id = {r["run_id"]: r for r in rows}
    assert by_id[replay.json()["run_id"]]["mode"] == "replay"
    assert by_id[replay.json()["run_id"]]["target"] == "TrackMyRupee"
    assert by_id[live["run_id"]]["mode"] == "live"
    assert by_id[live["run_id"]]["target"] == "TrackMyRupee"
    assert by_id[live["run_id"]]["finding_count"] == 0
