"""Issue #7 acceptance: Slice 2 outcomes on the pinned Primary Target, corpus breadth and legal framing.

`-k pinned` scans the pinned Juice Shop once in cache-only mode; `-k corpus` and `-k legal`
need no Target.
"""

import re
from pathlib import Path

import pytest

from auditor.mapping import Match, assemble
from auditor.exposure import ExposureDecision
from auditor.registry import load_registry
from auditor.remediation import load_catalogue
from auditor.rules import load_rules
from auditor.scan import run_scan

REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / "targets" / "juice-shop"
PIN = "c9f99228d9d56afb5f5ca7925376292f7fa44b13"
RULES = load_rules()
EXCLUDED = re.compile(r"^(data/static/codefixes/|test/)|^frontend/.*\.spec\.ts$")

# Slice 1 Finding identities at their anchors (issue #5); Slice 2 must not move them.
SLICE1 = {"SEC-07", "SEC-01", "SEC-13", "SEC-08", "SEC-02", "SEC-04", "SEC-05", "SEC-10",
          "RET-02", "RIG-01", "RIG-02", "TRF-02", "SEC-11"}


def _rules_for(issue_type):
    return {rid for rid, (spec, _) in RULES.items() if spec.issue_type == issue_type}


@pytest.fixture(scope="module")
def pinned_report(tmp_path_factory):
    if not (TARGET / "server.ts").exists():
        pytest.skip("pinned Juice Shop clone absent")
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("OLLAMA_HOST", "http://127.0.0.1:1")
        report = run_scan(str(TARGET), provider="ollama", cache_dir=tmp_path_factory.mktemp("cache"),
                          targets_dir=REPO / "targets")
    assert report["target"]["commit"] == PIN
    return report


def _issue_types(report, status=None):
    return {f["issue_type"] for f in report["findings"] if status is None or f["status"] == status}


def _not_determinable(report):
    return {rid for row in report["coverage_matrix"] for rid in row.get("not_determinable_rules", [])}


@pytest.mark.parametrize("issue_type", ["SEC-14", "MON-01"])
def test_pinned_fires(pinned_report, issue_type):
    assert issue_type in _issue_types(pinned_report)


@pytest.mark.parametrize("issue_type", ["SEC-15", "RIG-03", "SEC-12", "SEC-16", "SEC-03"])
def test_pinned_not_raised(pinned_report, issue_type):
    assert issue_type not in _issue_types(pinned_report)


@pytest.mark.parametrize("issue_type", ["RIG-04", "CHI-01"])
def test_pinned_not_determinable(pinned_report, issue_type):
    assert issue_type not in _issue_types(pinned_report)
    assert _rules_for(issue_type) & _not_determinable(pinned_report)


def test_pinned_ret03_only_conditional(pinned_report):
    ret03 = [f for f in pinned_report["findings"] if f["issue_type"] == "RET-03"]
    assert ret03 and all(f["status"] == "conditional" for f in ret03)


def test_pinned_slice1_preserved_and_no_excluded_evidence(pinned_report):
    assert SLICE1 <= _issue_types(pinned_report)
    files = {e["file"] for f in pinned_report["findings"]
             for e in [*f["evidence"], *(s["evidence"] for s in f["data_flow"])]}
    assert not [p for p in files if EXCLUDED.search(p)]


def test_corpus_every_catalogue_issue_type_has_a_rule_and_pair():
    covered = {spec.issue_type for spec, _ in RULES.values()}
    assert set(load_catalogue()) <= covered
    for rid in RULES:
        assert (REPO / "corpus" / rid / "positive").is_dir() and (REPO / "corpus" / rid / "negative").is_dir(), rid


def test_corpus_child_and_aadhaar_cases_are_synthetic_only(pinned_report):
    assert not {"SEC-03", "CHI-01", "CHI-02"} & _issue_types(pinned_report)
    child = [row for row in pinned_report["coverage_matrix"] if row["provision"].startswith(("DPDP-Act-9", "DPDP-Rule-10"))]
    assert child and all(row.get("annotation") == "covered, not exercised on a real Target"
                         or "covered, not exercised on a real Target" in str(row) for row in child)


CEILINGS = {"SEC": 250, "MON": 250, "CHI": 200}


def test_legal_ceilings_follow_the_schedule():
    registry = load_registry()
    for issue_type, issue in load_catalogue().items():
        parent = registry[issue.primary].penalty_ceiling_inr_crore if registry[issue.primary].penalty_ceiling_inr_crore else None
        expected = CEILINGS.get(issue_type[:3], 50)
        assert parent == expected, f"{issue_type} primary {issue.primary} ceiling {parent} != {expected}"


def _match(issue_type, classification, vector=None, nexus=(), gate=True, element=True):
    ev = {"file": "server.ts", "start_line": 1, "end_line": 1, "excerpt": "app.use(x)"}
    return Match(rule_id=f"{issue_type}-test", issue_type=issue_type, evidence=[ev], classification=classification,
                 base_vector=vector, element={"name": "model:User.email", "data_category": "Contact", "evidence": ev} if element else None,
                 data_category="Contact", protected_categories=("Contact",), processing_operation="Transfer",
                 data_flow=[], exposure=ExposureDecision("Third-Party", [ev]), nexus_elements=tuple(nexus),
                 gate_evidence=[ev] if gate else None)


def test_legal_disclosures_capped_and_labelled():
    result = assemble([_match("TRF-01", "disclosure")])
    (finding,) = result.findings
    assert finding["classification"] == "disclosure" and finding["primary_provision"] == "DPDP-Act-11(1)(b)"
    assert finding["severity"]["band"] in {"info", "low", "medium"}


def test_legal_safeguard_without_nexus_is_observation_without_provision():
    result = assemble([_match("SEC-05", "technical", "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N", element=False)])
    assert not result.findings and result.observations
    assert not any(str(r).startswith("DPDP-") for r in result.observations[0]["references"])


def test_legal_missing_gate_is_not_determinable():
    result = assemble([_match("RIG-04", "compliance-gap", gate=False)])
    assert not result.findings and result.not_determinable


def test_legal_not_code_checkable_entries(pinned_report):
    rows = {row["provision"]: row["classification"] for row in pinned_report["coverage_matrix"]}
    for pid in ("DPDP-Act-8(3)", "DPDP-Act-8(6)", "DPDP-Rule-7", "DPDP-Act-8(2)"):
        if pid in rows:
            assert rows[pid] == "not code-checkable", pid
