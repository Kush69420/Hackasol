"""Submission package (issue #15): manifest, README links, Replay Mode parity and masking.

Select with `-k manifest`, `-k replay` or `-k masking`.
"""

import copy
import hashlib
import json
import re
import shutil
import socket
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from auditor import scan as scan_module
from auditor.masking import _aadhaar, _luhn
from dashboard.backend import app as app_module
from dashboard.backend import replay as replay_module
from dashboard.backend.app import STAGES, create_app

ROOT = Path(__file__).resolve().parents[1]
RECORDINGS = ROOT / "dashboard" / "recordings"
MANIFEST = RECORDINGS / "manifest.json"
PINS = {
    "juice-shop": "c9f99228d9d56afb5f5ca7925376292f7fa44b13",
    "ai-kyc-platform": "70a821487c193be445810d836dd9b9b9ae22eb18",
    "trackmyrupee": "47990e4f19d7debea70c5d56bab77e3c3f051546",
    "singharya-e-kyc": "e6e78d53edd30fd5be88dcd82d5afc1a2010d025",
}
FORK = "juice-shop-fork"
FORK_PR_HEAD = "2a66c603ea543aea6ab642c472431a27846b9e63"
VOLATILE = ("started_at", "finished_at")
TEXT_SUFFIXES = {".json", ".md", ".html"}


def load_manifest(path: Path = MANIFEST) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def content_sha256(path: Path) -> str:
    """Digest of a Report without its scan timestamps, which change on every re-run."""
    report = json.loads(path.read_text(encoding="utf-8"))
    for key in VOLATILE:
        report["scan"].pop(key)
    return hashlib.sha256(json.dumps(report, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def check_entry(entry: dict, root: Path = ROOT) -> list[str]:
    """Every way a manifest entry can disagree with the files it names."""
    errors: list[str] = []
    name = entry["name"]
    for label, rel in entry["report"].items():
        if label in ("json", "md", "html", "pdf") and not (root / rel).is_file():
            errors.append(f"{name}: Report {label} {rel} is absent")
    bundle = root / entry["recording"]["dir"]
    for artifact in ("recording.json", *replay_module.ARTIFACTS.values()):
        if not (bundle / artifact).is_file():
            errors.append(f"{name}: recording file {artifact} is absent")
    if errors:
        return errors
    report = json.loads((root / entry["report"]["json"]).read_text(encoding="utf-8"))
    recorded_report = json.loads((bundle / "report.json").read_text(encoding="utf-8"))
    recording = json.loads((bundle / "recording.json").read_text(encoding="utf-8"))
    if report["target"]["commit"] != entry["pinned_revision"]:
        errors.append(f"{name}: Report revision {report['target']['commit']} != pin {entry['pinned_revision']}")
    if recorded_report["target"]["commit"] != entry["pinned_revision"]:
        errors.append(f"{name}: recorded Report revision differs from the pin")
    if recording["target"] != {"name": report["target"]["name"], "commit": entry["pinned_revision"]}:
        errors.append(f"{name}: recording target differs from the Report target")
    if entry["report"]["content_sha256"] != content_sha256(root / entry["report"]["json"]):
        errors.append(f"{name}: Report digest differs from the manifest")
    if entry["recording"]["recording_sha256"] != sha256(bundle / "recording.json"):
        errors.append(f"{name}: recording digest differs from the manifest")
    if entry["recording"]["report_sha256"] != sha256(bundle / "report.json"):
        errors.append(f"{name}: recorded Report digest differs from the manifest")
    if entry["recording"]["events"] != len(recording["events"]):
        errors.append(f"{name}: event count differs from the manifest")
    return errors


# ---- manifest -------------------------------------------------------------------------------

def test_manifest_has_one_pinned_recording_and_report_per_submission_scan():
    manifest = load_manifest()
    entries = {e["name"]: e for e in manifest["entries"]}
    assert len(entries) == len(manifest["entries"]), "duplicate manifest entries"
    assert set(entries) == {*PINS, FORK}
    for name, pin in PINS.items():
        assert entries[name]["pinned_revision"] == pin
    assert entries[FORK]["pinned_revision"] == FORK_PR_HEAD
    for entry in entries.values():
        assert check_entry(entry) == []
        prov = entry["provenance"]
        assert prov["llm_mode"] in ("live", "cache-only") and prov["scan_started_at"]
        assert {"llm_provider", "llm_model", "prompt_versions", "cached_verdicts_used"} <= prov.keys()
    bundles = [e["recording"]["dir"] for e in entries.values()]
    assert len(set(bundles)) == len(bundles)


def test_manifest_fork_rescan_pairs_with_the_pinned_baseline():
    manifest = load_manifest()
    entries = {e["name"]: e for e in manifest["entries"]}
    rescan = entries[FORK]["rescan"]
    assert rescan["baseline"] == "juice-shop" and rescan["base_revision"] == PINS["juice-shop"]
    assert rescan["head_revision"] == entries[FORK]["pinned_revision"]
    assert rescan["pull_request"] == "https://github.com/TanKaizokuO/juice-shop/pull/1"
    import sys
    sys.path.insert(0, str(ROOT / "demo"))
    from compare_reports import compare
    before = json.loads((ROOT / entries["juice-shop"]["report"]["json"]).read_text(encoding="utf-8"))
    after = json.loads((ROOT / entries[FORK]["report"]["json"]).read_text(encoding="utf-8"))
    result = compare(before, after)
    assert [i.split("-")[0] for i in result["gone"]] == ["RET", "SEC", "SEC"]
    assert result["new"] == []
    assert not any(i.startswith("SEC-09") for i in result["gone"]), "the pinned Report emits no SEC-09 Finding"


def test_manifest_juice_shop_recording_differs_from_the_report_only_by_live_probe_outcomes():
    entry = next(e for e in load_manifest()["entries"] if e["name"] == "juice-shop")
    overlay = entry["recording"]["live_probe_overlay"]
    static = json.loads((ROOT / entry["report"]["json"]).read_text(encoding="utf-8"))
    recorded = json.loads((ROOT / entry["recording"]["dir"] / "report.json").read_text(encoding="utf-8"))
    static_by_id = {f["id"]: f for f in static["findings"]}
    recorded_by_id = {f["id"]: f for f in recorded["findings"]}
    assert set(recorded_by_id) - set(static_by_id) == set(overlay["added_finding_ids"])
    assert set(static_by_id) <= set(recorded_by_id)
    for finding_id, finding in static_by_id.items():
        assert {**recorded_by_id[finding_id], "live_probe": None} == {**finding, "live_probe": None}
    confirmed = {i for i, f in recorded_by_id.items() if (f["live_probe"] or {}).get("result") == "Confirmed"}
    assert confirmed == set(overlay["confirmed_finding_ids"])
    for finding_id in confirmed:
        assert recorded_by_id[finding_id]["live_probe"]["image_revision"] == PINS["juice-shop"]
    assert any(recorded_by_id[i]["live_probe"]["route"] == "/rest/memories" for i in confirmed)


def test_manifest_non_probe_reports_are_the_recorded_reports():
    for entry in load_manifest()["entries"]:
        if entry["name"] != "juice-shop":
            assert entry["report"]["content_sha256"] == content_sha256(ROOT / entry["recording"]["dir"] / "report.json")
            for fmt in ("report.md", "report.html"):
                assert (ROOT / entry["report"]["json"]).parent.joinpath(fmt).read_bytes() == \
                    (ROOT / entry["recording"]["dir"] / fmt).read_bytes()


def test_manifest_revision_mismatch_fails(tmp_path):
    entry = next(e for e in load_manifest()["entries"] if e["name"] == "trackmyrupee")
    root = tmp_path
    for rel in (*entry["report"].values(), entry["recording"]["dir"]):
        if rel.startswith(("reports/", "dashboard/")):
            src, dst = ROOT / rel, root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src, dst) if src.is_dir() else shutil.copy(src, dst)
    assert check_entry(entry, root) == []
    wrong = copy.deepcopy(entry)
    wrong["pinned_revision"] = "0" * 40
    assert any("revision" in e for e in check_entry(wrong, root))
    # a recording regenerated for another revision no longer pairs with the Report
    path = root / entry["recording"]["dir"] / "recording.json"
    data = json.loads(path.read_text())
    data["target"]["commit"] = "1" * 40
    path.write_text(json.dumps(data))
    assert any("recording" in e for e in check_entry(entry, root))
    (root / entry["report"]["md"]).unlink()
    assert any("absent" in e for e in check_entry(entry, root))


README = (ROOT / "README.md").read_text(encoding="utf-8")


def local_links(text: str) -> list[str]:
    links = re.findall(r"\]\(([^)\s]+)\)", text)
    return [l.split("#")[0] for l in links if not re.match(r"[a-z]+:", l) and l.split("#")[0]]


def test_manifest_readme_deliverable_links_resolve_in_a_fresh_checkout():
    links = local_links(README)
    required = ["auditor/", "reports/juice-shop/report.md", "RULES.md", "docs/live-probes.md",
                "docs/fix-patches.md", "demo/script.md", "docs/plan.md", "CONTEXT.md",
                "docs/targets/ai-kyc-platform.md", "docs/targets/trackmyrupee.md", "docs/targets/singharya-e-kyc.md"]
    for rel in required:
        assert rel in links, f"README does not link {rel}"
    for rel in links:
        assert (ROOT / rel).exists(), f"README link {rel} does not resolve"
    # a path ignored by git would be absent from a fresh clone
    paths = [r for r in links if (ROOT / r).exists()]
    for entry in load_manifest()["entries"]:
        paths += [r for r in entry["report"].values() if r.startswith("reports/")]
    ignored = subprocess.run(["git", "check-ignore", *paths], cwd=ROOT, capture_output=True, text=True)
    assert ignored.returncode == 1 and ignored.stdout == "", f"git-ignored: {ignored.stdout}"


def test_manifest_demo_script_has_eight_steps_with_live_and_recorded_states():
    script = (ROOT / "demo" / "script.md").read_text(encoding="utf-8")
    steps = re.split(r"^## Step (\d)\b", script, flags=re.M)
    numbers = steps[1::2]
    assert numbers == [str(i) for i in range(1, 9)]
    for body in steps[2::2]:
        assert "**Live:**" in body and "**Recorded:**" in body and "**Expected state:**" in body
    plan = (ROOT / "docs" / "plan.md").read_text(encoding="utf-8")
    for fragment in ("scan Juice Shop", "Personal Data Map", "/rest/memories", "Coverage Matrix",
                     "Consent Assessment (TrackMyRupee)", "Live Probe Confirm", "Open PR", "re-scan"):
        assert fragment in plan
    assert "Replay Mode" in script and "never publishes" in script
    for rel in local_links(script):
        assert (ROOT / "demo" / rel).exists() or (ROOT / rel).exists(), rel


# ---- replay ---------------------------------------------------------------------------------

class FakeClock:
    def __init__(self):
        self.now = 100.0
        self.sleeps: list[float] = []

    def monotonic(self):
        return self.now

    async def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


def sse(response) -> list[dict]:
    assert response.headers["content-type"].startswith("text/event-stream")
    return [json.loads(b[len("data: "):]) for b in response.text.split("\n\n") if b.strip()]


@pytest.fixture
def isolated(monkeypatch):
    """Fail on any scanner, provider, subprocess or network use."""
    def boom(*a, **k):
        raise AssertionError("Replay Mode reached the scanner, provider, a subprocess or the network")
    monkeypatch.setattr(scan_module, "run_scan", boom)
    monkeypatch.setattr(app_module, "execute_scan", boom)
    monkeypatch.setattr("auditor.llm.LLMSession.from_env", boom)
    monkeypatch.setattr(subprocess, "Popen", boom)
    monkeypatch.setattr(socket, "create_connection", boom)
    monkeypatch.setattr("httpx.AsyncClient.send", boom)
    monkeypatch.setattr("auditor.probes.run", boom)
    monkeypatch.setattr("dashboard.backend.probes.run", boom)
    monkeypatch.setattr("dashboard.backend.fixpatch.publish", boom)


def tree_digest(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): sha256(p) for p in sorted(root.rglob("*")) if p.is_file()}


ENTRY_NAMES = [e["name"] for e in load_manifest()["entries"]]


@pytest.mark.parametrize("name", ENTRY_NAMES)
def test_replay_events_offsets_and_report_match_the_recording(name, isolated, tmp_path):
    bundle = RECORDINGS / name
    recorded = json.loads((bundle / "recording.json").read_text(encoding="utf-8"))
    events = recorded["events"]
    assert [e["ordinal"] for e in events] == list(range(len(events)))
    offsets = [e["elapsed_ms"] for e in events]
    assert offsets == sorted(offsets), "timestamps are not in captured order"
    assert [e["stage"] for e in events if e["type"] == "stage"] == list(STAGES)
    assert events[-1]["type"] == "completed"

    clock = FakeClock()
    before = tree_digest(RECORDINGS)
    client = TestClient(create_app(clock=clock, targets_dir=tmp_path / "absent",
                                   reports_dir=tmp_path / "reports"))
    assert name in client.get("/api/replays").json()["recordings"]
    started = client.post(f"/api/replays/{name}")
    assert started.status_code == 202 and started.json()["mode"] == "recorded"
    run_id = started.json()["run_id"]
    status = client.get(f"/api/scans/{run_id}").json()
    assert status["mode"] == "recorded" and status["target"] == name
    played = sse(client.get(f"/api/scans/{run_id}/events"))
    assert [{k: v for k, v in e.items() if k not in ("run_id", "mode")} for e in played] == \
        [{k: v for k, v in e.items() if k != "mode"} for e in events]
    assert {e["mode"] for e in played} == {"recorded"}
    expected_gaps = [round((b - a) / 1000, 3) for a, b in zip([0, *offsets], offsets) if b > a]
    assert [round(s, 3) for s in clock.sleeps] == expected_gaps
    assert clock.now == pytest.approx(100.0 + offsets[-1] / 1000)
    for fmt, artifact in replay_module.ARTIFACTS.items():
        body = client.get(f"/api/scans/{run_id}/report/{fmt}")
        assert body.status_code == 200 and body.content == (bundle / artifact).read_bytes()
    report = json.loads(client.get(f"/api/scans/{run_id}/report/json").content)
    entry = next(e for e in load_manifest()["entries"] if e["name"] == name)
    assert report["target"]["commit"] == entry["pinned_revision"]
    assert sha256(bundle / "report.json") == entry["recording"]["report_sha256"]
    assert tree_digest(RECORDINGS) == before and not (tmp_path / "reports").exists()


def test_replay_mode_is_labelled_in_the_dashboard_and_the_script():
    app_source = (ROOT / "dashboard" / "frontend" / "src" / "App.tsx").read_text(encoding="utf-8")
    assert 'mode === "recorded") return "Replay Mode"' in app_source
    assert "/api/replays/${name}" in app_source
    assert "Replay Mode" in (ROOT / "demo" / "script.md").read_text(encoding="utf-8")


def test_replay_cannot_write_probe_or_open_a_pull_request(isolated, tmp_path):
    client = TestClient(create_app(clock=FakeClock(), targets_dir=tmp_path / "absent"))
    run_id = client.post("/api/replays/juice-shop-fork").json()["run_id"]
    sse(client.get(f"/api/scans/{run_id}/events"))
    assert client.get(f"/api/scans/{run_id}").json() == {
        "run_id": run_id, "mode": "recorded", "status": "completed", "target": "juice-shop-fork"}
    before = tree_digest(RECORDINGS)
    pr = client.post(f"/api/scans/{run_id}/fix-patches/publish",
                     json={"authorized": True, "finding_ids": [], "destination": "x", "branch": "b"})
    probe = client.post(f"/api/scans/{run_id}/probes", json={"authorized": True, "target": "http://127.0.0.1:3000"})
    assert pr.status_code == 409 and probe.status_code == 409
    assert tree_digest(RECORDINGS) == before


def test_replay_rejects_unknown_or_unsafe_recording_names(tmp_path):
    client = TestClient(create_app(clock=FakeClock()))
    assert client.post("/api/replays/not-recorded").status_code == 404
    assert client.post("/api/replays/Juice_Shop").status_code == 404


# ---- masking --------------------------------------------------------------------------------

# Canary values are assembled at runtime so no key-shaped literal is committed.
CANARY_KEY = "-----BEGIN RSA PRIVATE KEY-----\n" + "_".join(("canary", "key", "body")) + "\n-----END RSA PRIVATE KEY-----"
CANARY_JWT = ".".join(("eyJ" + "hbGciOiJSUzI1NiJ9", "eyJ" + "zdWIiOiJjYW5hcnkifQ", "c2lnbmF0dXJlLWNhbmFyeQ"))
CANARY_AWS = "AKIA" + "ABCDEFGHIJKLMNOP"
CANARY_PROVIDER = "_".join(("sk", "live", "Zq81JkX7vN3mPw5TrB9cYd2e"))
CANARY_BEARER = "Bearer " + "abcdefghijklmnop1234567890"
CANARY_AADHAAR = "2345 6789 0124"
CANARY_CARD = "4111 1111 1111 1111"
SECRET_SHAPES = {
    "private key": r"-----BEGIN [^-\n]*PRIVATE KEY-----",
    "JWT": r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]+",
    "AWS access key": r"\bAKIA[0-9A-Z]{16}\b",
    "provider key": r"\b(?:sk_live|sk_test|ghp|gho|xox[bp])[_-][A-Za-z0-9-]{10,}",
    "bearer token": r"\bBearer[ \t]+[A-Za-z0-9._~+/=-]{16,}",
}


def leaks(text: str) -> list[str]:
    found = [label for label, pattern in SECRET_SHAPES.items() if re.search(pattern, text)]
    if any(_aadhaar(m) for m in re.findall(r"(?<!\d)\d{4}[ -]?\d{4}[ -]?\d{4}(?!\d)", text)):
        found.append("Aadhaar")
    if any(_luhn(m) for m in re.findall(r"(?<![0-9A-Za-z])(?:\d[ -]?){12,18}\d(?![0-9A-Za-z])", text)):
        found.append("card number")
    return found


def package_texts() -> dict[str, str]:
    paths = [p for p in RECORDINGS.rglob("*") if p.suffix in TEXT_SUFFIXES]
    paths += [p for p in (ROOT / "reports").glob("*/report.*") if p.suffix in TEXT_SUFFIXES and "dashboard" not in p.parts]
    paths += [ROOT / "demo" / "script.md", ROOT / "README.md"]
    paths += [p for p in (ROOT / "demo").glob("*") if p.is_file() and p.suffix in {".json", ".md", ".txt"}]
    return {str(p.relative_to(ROOT)): p.read_text(encoding="utf-8") for p in sorted(set(paths))}


def test_masking_detector_catches_every_canary_class():
    for canary in (CANARY_KEY, CANARY_JWT, CANARY_AWS, CANARY_PROVIDER, CANARY_BEARER, CANARY_AADHAAR, CANARY_CARD):
        assert leaks(f'"excerpt": "value = {canary}"'), canary
    assert leaks("«SECRET» «AADHAAR» 2345 6789 0123") == []


def test_masking_no_canary_in_reports_recordings_or_script():
    texts = package_texts()
    assert any(k.startswith("dashboard/recordings/juice-shop/") for k in texts) and "demo/script.md" in texts
    for path, text in texts.items():
        assert leaks(text) == [], f"{path} contains an unmasked secret or identifier"
    # a canary injected into a copy of any artifact is what the check exists to fail on
    for canary in (CANARY_KEY, CANARY_AWS, CANARY_AADHAAR):
        assert leaks(next(iter(texts.values())) + canary)


def test_masking_pinned_juice_shop_signing_key_is_absent():
    source = ROOT / "targets" / "juice-shop" / "lib" / "insecurity.ts"
    if not source.is_file():
        pytest.skip("Juice Shop clone not present")
    match = re.search(r"const privateKey = '(?:-----BEGIN RSA PRIVATE KEY-----\\r\\n)?([A-Za-z0-9+/=]{40})", source.read_text(encoding="utf-8"))
    assert match, "private key literal not found in the pinned source"
    for path, text in package_texts().items():
        assert match.group(1) not in text, path
    for path in RECORDINGS.rglob("report.pdf"):
        assert match.group(1).encode() not in path.read_bytes(), path
