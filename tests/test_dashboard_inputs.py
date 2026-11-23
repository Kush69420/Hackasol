"""Dashboard scan inputs: uploads and pasted snippets under targets/uploads/<uuid4>/, scan runner stubbed."""

import io
import json
import stat
import uuid
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from auditor import scan as scan_module
from dashboard.backend import app as app_module
from dashboard.backend.app import STAGES, create_app
from dashboard.backend.replay import ARTIFACTS


def sse(response) -> list[dict]:
    assert response.headers["content-type"].startswith("text/event-stream")
    return [json.loads(block[len("data: "):]) for block in response.text.split("\n\n") if block.strip()]


@pytest.fixture
def scans(monkeypatch):
    """Stub the scan runner and report writer; record the source directory of each scan."""
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
    frontend = tmp_path / "dist"
    frontend.mkdir()
    (frontend / "index.html").write_text("<!doctype html><title>SPA shell</title>", encoding="utf-8")
    return TestClient(create_app(reports_dir=tmp_path / "runs", cache_dir=tmp_path / "cache",
                                 targets_dir=tmp_path / "targets", frontend_dist=frontend))


def uploads_root(tmp_path) -> Path:
    return tmp_path / "targets" / "uploads"


def zip_bytes(members: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in members.items():
            zf.writestr(name, data)
    return buf.getvalue()


def upload(client, name: str, data: bytes):
    return client.post("/api/scans/upload", files={"file": (name, data, "application/octet-stream")})


# ---- snippet --------------------------------------------------------------------------------

def test_snippet_happy_path_writes_file_and_starts_scan(client, scans, tmp_path):
    code = "import os\nprint(os.getenv('X'))\n"
    started = client.post("/api/scans/snippet", json={"code": code, "language": "Python"})
    assert started.status_code == 202
    body = started.json()
    assert set(body) == {"run_id", "mode"} and body["mode"] == "live"
    events = sse(client.get(f"/api/scans/{body['run_id']}/events"))
    assert events[-1]["type"] == "completed"
    assert len(scans) == 1
    dest = Path(scans[0])
    assert dest.parent == uploads_root(tmp_path) and uuid.UUID(dest.name).version == 4
    assert (dest / "snippet.py").read_bytes() == code.encode("utf-8")
    assert sorted(p.name for p in dest.iterdir()) == ["snippet.py"]


def test_snippet_unknown_language_is_422_and_starts_nothing(client, scans, tmp_path):
    r = client.post("/api/scans/snippet", json={"code": "x", "language": "cobol"})
    assert r.status_code == 422
    assert scans == [] and not uploads_root(tmp_path).exists()


@pytest.mark.parametrize("code", ["", "   \n\t "])
def test_snippet_empty_code_is_422(client, scans, code):
    r = client.post("/api/scans/snippet", json={"code": code, "language": "python"})
    assert r.status_code == 422 and scans == []


def test_snippet_oversized_code_is_413(client, scans, tmp_path):
    r = client.post("/api/scans/snippet", json={"code": "a" * (200 * 1024 + 1), "language": "python"})
    assert r.status_code == 413 and "200 KB" in r.json()["detail"]
    assert scans == [] and not uploads_root(tmp_path).exists()


# ---- upload ---------------------------------------------------------------------------------

def test_single_file_upload_is_stored_under_sanitised_basename(client, scans, tmp_path):
    r = upload(client, "../../evil config.yaml", b"key: value\n")
    assert r.status_code == 202 and r.json()["mode"] == "live"
    events = sse(client.get(f"/api/scans/{r.json()['run_id']}/events"))
    assert events[-1]["type"] == "completed"
    dest = Path(scans[0])
    assert dest.parent == uploads_root(tmp_path)
    assert sorted(p.name for p in dest.iterdir()) == ["evil_config.yaml"]
    assert (dest / "evil_config.yaml").read_bytes() == b"key: value\n"
    assert not (tmp_path / "targets" / "evil.yaml").exists()


def test_empty_single_file_upload_is_400(client, scans):
    assert upload(client, "empty.py", b"").status_code == 400
    assert scans == []


def test_zip_upload_is_extracted_and_scanned(client, scans, tmp_path):
    data = zip_bytes({"app/server.js": b"const x = 1\n", "README.md": b"# app\n"})
    r = upload(client, "app.zip", data)
    assert r.status_code == 202
    events = sse(client.get(f"/api/scans/{r.json()['run_id']}/events"))
    assert events[-1]["type"] == "completed"
    dest = Path(scans[0])
    assert dest.parent == uploads_root(tmp_path)
    assert (dest / "app" / "server.js").read_bytes() == b"const x = 1\n"
    assert (dest / "README.md").read_bytes() == b"# app\n"


@pytest.mark.parametrize("member", ["../evil.txt", "a/../../evil.txt", "/abs/evil.txt",
                                    "..\\evil.txt", "C:/evil.txt"])
def test_zip_slip_is_rejected_and_writes_nothing_outside(client, scans, tmp_path, member):
    data = zip_bytes({"ok.txt": b"fine", member: b"pwned"})
    r = upload(client, "bad.zip", data)
    assert r.status_code == 400 and "zip member" in r.json()["detail"]
    assert scans == []
    assert not (tmp_path / "evil.txt").exists() and not (tmp_path / "targets" / "evil.txt").exists()
    assert not Path("/abs/evil.txt").exists()
    root = uploads_root(tmp_path)
    assert not root.exists() or not any(root.iterdir())  # the half-built input directory is removed


def test_zip_symlink_member_is_rejected(client, scans):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        info = zipfile.ZipInfo("link")
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        zf.writestr(info, "/etc/passwd")
    r = upload(client, "link.zip", buf.getvalue())
    assert r.status_code == 400 and "symlink" in r.json()["detail"]
    assert scans == []


def test_upload_over_20_mb_is_413(client, scans):
    r = upload(client, "big.py", b"\0" * (20 * 1024 * 1024 + 1))
    assert r.status_code == 413 and "20 MB" in r.json()["detail"]
    assert scans == []


def test_zip_uncompressing_over_100_mb_is_413(client, scans):
    # 100 MB + 1 zero bytes deflates to about 100 KB, so the upload itself passes the 20 MB cap
    data = zip_bytes({"bomb.bin": b"\0" * (100 * 1024 * 1024 + 1)})
    assert len(data) < 20 * 1024 * 1024
    r = upload(client, "bomb.zip", data)
    assert r.status_code == 413 and "100 MB" in r.json()["detail"]
    assert scans == []


def test_zip_with_more_than_5000_members_is_413(client, scans):
    data = zip_bytes({f"f{i}.txt": b"" for i in range(5001)})
    r = upload(client, "many.zip", data)
    assert r.status_code == 413 and "5000" in r.json()["detail"]
    assert scans == []


def test_corrupt_zip_is_400(client, scans):
    r = upload(client, "broken.zip", b"PK\x03\x04 not really a zip")
    assert r.status_code == 400 and scans == []


# ---- SPA fallback ---------------------------------------------------------------------------

def test_client_route_serves_index_html_and_api_stays_json_404(client):
    r = client.get("/dashboard")
    assert r.status_code == 200 and "SPA shell" in r.text
    missing = client.get("/api/does-not-exist")
    assert missing.status_code == 404 and missing.headers["content-type"].startswith("application/json")
    assert client.get("/api").status_code == 404
