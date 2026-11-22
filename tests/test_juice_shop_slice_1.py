"""Issue #5 acceptance: every Slice 1 case on the pinned Primary Target, by Rule and Evidence.

Runs one full scan with the LLM unreachable (cache-only), so Findings are deterministic.
Skipped when the pinned clone is absent (targets/ is git-ignored).
"""

import json
import re
from pathlib import Path

import pytest

from auditor.scan import run_scan

REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / "targets" / "juice-shop"
PIN = "c9f99228d9d56afb5f5ca7925376292f7fa44b13"

pytestmark = pytest.mark.skipif(not (TARGET / "server.ts").exists(), reason="pinned Juice Shop clone absent")

# (Issue Type, Rules that must fire together, Evidence file the Finding is anchored in)
CASES = [
    ("SEC-07", {"SEC-07-ts-unchecked-nested-records", "SEC-08-ts-nested-records"}, "routes/memory.ts"),
    ("SEC-01", {"SEC-01-ts-morgan-query-secrets", "SEC-09-ts-query-authentication-secret"}, "frontend/src/app/Services/user.service.ts"),
    ("SEC-13", {"SEC-13-ts-access-log-retention"}, "server.ts"),
    ("SEC-08", {"SEC-08-ts-account-list"}, "routes/authenticatedUsers.ts"),
    ("SEC-08", {"SEC-08-ts-review-author"}, "routes/showProductReviews.ts"),
    ("SEC-02", {"SEC-02-sequelize-plain-fields"}, "models/user.ts"),
    ("SEC-02", {"SEC-02-sequelize-plain-fields"}, "models/card.ts"),
    ("SEC-04", {"SEC-04-ts-md5-password-hash"}, "models/user.ts"),
    ("SEC-05", {"SEC-05-ts-hardcoded-jwt-key"}, "lib/insecurity.ts"),
    ("SEC-10", {"SEC-10-ts-storage-header"}, "frontend/src/app/login/login.component.ts"),
    ("RET-02", {"RET-02-express-erasure-request"}, "routes/dataErasure.ts"),
    ("RIG-01", {"RIG-01-express-incomplete-export"}, "routes/dataExport.ts"),
    ("RIG-02", {"RIG-02-express-email-correction"}, "routes/updateUserProfile.ts"),
    ("TRF-02", {"TRF-02-terraform-storage-region"}, "terraform/variables.tf"),
    ("SEC-11", {"SEC-11-ts-wildcard-cors"}, "server.ts"),
]
CEILING = {"SEC": 250, "RIG": 50, "RET": 50, "TRF": 50}
EXCLUDED = re.compile(r"^(data/static/codefixes/|test/)|^frontend/.*\.spec\.ts$")


@pytest.fixture(scope="module")
def report(tmp_path_factory, monkeypatch_module):
    monkeypatch_module.setenv("OLLAMA_HOST", "http://127.0.0.1:1")
    report = run_scan(str(TARGET), provider="ollama",
                      cache_dir=tmp_path_factory.mktemp("cache"), targets_dir=REPO / "targets")
    assert report["target"]["commit"] == PIN, "targets/juice-shop is not at the pinned commit"
    return report


@pytest.fixture(scope="module")
def monkeypatch_module():
    with pytest.MonkeyPatch.context() as mp:
        yield mp


def _finding(report, issue_type, rules, file):
    hits = [f for f in report["findings"] if f["issue_type"] == issue_type
            and rules <= set(f["rules_fired"]) and f["evidence"][0]["file"] == file]
    assert hits, f"no {issue_type} Finding from {sorted(rules)} anchored in {file}"
    return hits[0]


@pytest.mark.parametrize("issue_type,rules,file", CASES, ids=[f"{c[0]}:{c[2]}" for c in CASES])
def test_case_reported_with_legal_and_severity_fields(report, issue_type, rules, file):
    f = _finding(report, issue_type, rules, file)
    assert f["penalty_ceiling"]["amount_inr_crore"] == CEILING[issue_type[:3]]
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", f["enforceable_from"])
    assert f["severity"]["justification"] and f["recommended_fix"]["guidance"]
    assert all(e["file"] and e["start_line"] >= 1 for e in f["evidence"])


def test_report_runs_cache_only_and_llm_never_invents_findings(report):
    assert report["llm"]["mode"] == "cache-only"
    assert {r for f in report["findings"] for r in f["rules_fired"]} <= {r for _, rs, _ in CASES for r in rs}


def test_trf02_is_disclosure_capped_and_needs_legal_review(report):
    f = _finding(report, "TRF-02", {"TRF-02-terraform-storage-region"}, "terraform/variables.tf")
    assert f["classification"] == "disclosure" and f["status"] == "needs-legal-review"
    assert f["severity"]["band"] in {"info", "low", "medium"}
    assert len(f["legal_review"]["readings"]) >= 2


def test_account_list_is_public_through_open_registration(report):
    f = _finding(report, "SEC-08", {"SEC-08-ts-account-list"}, "routes/authenticatedUsers.ts")
    assert f["exposure"]["level"] == "Public"
    assert any("/api/Users" in e["excerpt"] for e in f["exposure"]["derived_from"])


def test_no_sec16_and_no_unlinked_cloudwatch_claim(report):
    assert not [f for f in report["findings"] if f["issue_type"] == "SEC-16"]
    sec13 = [f for f in report["findings"] if f["issue_type"] == "SEC-13"]
    assert sec13 and not any("retention_in_days" in e["excerpt"] for f in sec13 for e in f["evidence"])


def test_no_evidence_from_excluded_paths(report):
    files = {e["file"] for f in report["findings"]
             for e in [*f["evidence"], *(step["evidence"] for step in f["data_flow"])]}
    assert not [p for p in files if EXCLUDED.search(p)]


def test_secrets_never_reach_the_report(report):
    text = json.dumps(report)
    key = re.search(r"privateKey\s*=\s*'([^']+)'", (TARGET / "lib/insecurity.ts").read_text())
    assert key and key.group(1)[30:80] not in text
