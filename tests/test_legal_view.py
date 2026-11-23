"""Legal view: ceiling lookup, no summation, and enforcement phases against a fixed reference date."""
import datetime as dt
import json

import pytest
from fastapi.testclient import TestClient

from auditor import legal_view
from auditor.registry import load_registry
from auditor.report import SECTIONS, render_html, render_markdown
from dashboard.backend.app import create_app

TODAY = dt.date(2026, 6, 1)


def finding(fid, primary, other=(), band="high", status="open"):
    registry = load_registry()
    p = registry[primary]
    return {"id": fid, "primary_provision": primary, "other_provisions": list(other),
            "severity": {"band": band}, "enforceable_from": p.enforceable_from.isoformat(), "status": status,
            "penalty_ceiling": {"parent_section": p.penalty_parent,
                                "amount_inr_crore": p.penalty_ceiling_inr_crore}}


def report(*findings):
    return {"scan": {"finished_at": "2026-06-01T10:00:00+00:00"}, "findings": list(findings)}


@pytest.fixture(scope="module")
def registry():
    return load_registry()


def test_ceiling_lookup_per_provision_with_schedule_entry_and_severity_mix(registry):
    rep = report(finding("A", "DPDP-Act-8(5)", ["CWE-209"], "critical"),
                 finding("B", "DPDP-Act-8(5)", [], "low"),
                 finding("C", "DPDP-Act-6(1)", [], "medium"),
                 finding("D", "DPDP-Act-9", [], "high"))
    rows = {r["provision"]: r for r in legal_view.ceiling_rows(rep, registry)}
    assert "CWE-209" not in rows  # allied law has no Schedule entry
    row = rows["DPDP-Act-8(5)"]
    assert row["statutory_maximum_inr_crore"] == 250
    assert row["schedule_entry"] == "Schedule, item 1"
    assert row["finding_ids"] == ["A", "B"]
    assert row["severity_mix"] == {"critical": 1, "high": 0, "medium": 0, "low": 1}
    assert rows["DPDP-Act-6(1)"]["statutory_maximum_inr_crore"] == 50
    assert rows["DPDP-Act-6(1)"]["schedule_entry"] == "Schedule, item 7"
    assert rows["DPDP-Act-9"]["statutory_maximum_inr_crore"] == 200
    assert rows["DPDP-Act-9"]["schedule_entry"] == "Schedule, item 3"
    assert list(rows)[0] == "DPDP-Act-8(5)"  # highest ceiling first


def test_section_15_has_no_crore_ceiling(registry):
    rows = legal_view.ceiling_rows(report(finding("A", "DPDP-Act-15")), registry)
    assert rows[0]["statutory_maximum_inr_crore"] is None
    assert rows[0]["schedule_entry"] == "Schedule, item 5"
    assert "ten thousand rupees" in rows[0]["statutory_maximum_text"]
    assert legal_view.highest_applicable_ceiling(rows) is None


def test_highest_applicable_ceiling_is_never_a_sum(registry):
    rep = report(finding("A", "DPDP-Act-8(5)"), finding("B", "DPDP-Act-9"), finding("C", "DPDP-Act-6(1)"))
    view = legal_view.legal_view(rep, registry, as_of=TODAY)
    assert view["highest_applicable_ceiling"]["amount_inr_crore"] == 250  # not 250 + 200 + 50
    assert view["highest_applicable_ceiling"]["finding_ids"] == ["A"]
    assert not any("total" in key for key in view)
    assert "250" in json.dumps(view) and "500" not in json.dumps(view)
    assert "not a predicted or estimated fine" in view["note"]
    assert "section 33(2)" in view["note"]
    assert registry[view["section_33_2"]].citation == "Section 33(2)"


def test_transfer_disclosure_does_not_establish_an_applicable_ceiling(registry):
    from auditor.remediation import load_catalogue

    issue = load_catalogue()["TRF-02"]
    disclosure = finding("TRF-02", issue.primary, issue.related, status="needs-legal-review")
    rep = report(disclosure)
    view = legal_view.legal_view(rep, registry)
    assert view["highest_applicable_ceiling"] is None
    rows = {row["provision"]: row["finding_ids_by_applicability"] for row in view["ceilings"]}
    assert rows["DPDP-Act-16(1)"]["needs_legal_review"] == ["TRF-02"]
    assert rows["DPDP-Rule-15"]["related"] == ["TRF-02"]
    assert rows["DPDP-Rule-13(4)"]["conditional"] == ["TRF-02"]
    blocks = str(legal_view.report_blocks(rep, registry))
    assert "Highest applicable ceiling: none" in blocks
    assert "Conditional Provision: TRF-02" in blocks
    assert "Needs Legal Review (breach not established): TRF-02" in blocks


def test_applicability_is_per_citation_not_per_provision(registry):
    view = legal_view.legal_view(report(
        finding("applicable", "DPDP-Act-6(1)", ["DPDP-Act-8(5)"]),
        finding("related", "DPDP-Act-15", ["DPDP-Act-6(1)"]),
        finding("review", "DPDP-Act-6(1)", status="needs-legal-review"),
        finding("conditional", "DPDP-Act-9", status="conditional"),
        finding("sdf", "DPDP-Rule-13(4)"),
    ), registry)
    rows = {row["provision"]: row["finding_ids_by_applicability"] for row in view["ceilings"]}
    assert rows["DPDP-Act-6(1)"] == {
        "applicable_primary": ["applicable"], "related": ["related"],
        "conditional": [], "needs_legal_review": ["review"],
    }
    assert rows["DPDP-Act-9"]["conditional"] == ["conditional"]
    assert rows["DPDP-Rule-13(4)"]["conditional"] == ["sdf"]
    assert view["highest_applicable_ceiling"] == {
        "amount_inr_crore": 50, "provisions": ["DPDP-Act-6(1)"], "finding_ids": ["applicable"],
    }


def test_phase_grouping_with_fixed_today(registry):
    rep = report(finding("A", "DPDP-Rule-1"), finding("B", "DPDP-Rule-4"),
                 finding("C", "DPDP-Act-8(5)"), finding("D", "DPDP-Act-9"))
    phases = legal_view.timeline(rep, registry, TODAY)
    assert [p["enforceable_from"] for p in phases] == ["2025-11-13", "2026-11-13", "2027-05-13"]
    assert [p["finding_ids"] for p in phases] == [["A"], ["B"], ["C", "D"]]
    assert [p["days_until"] for p in phases] == [-200, 165, 346]
    assert [p["already_enforceable"] for p in phases] == [True, False, False]
    assert phases[2]["basis"]


def test_enforceable_on_the_day_and_default_reference_is_scan_date(registry):
    rep = report(finding("B", "DPDP-Rule-4"))
    on_day = legal_view.timeline(rep, registry, dt.date(2026, 11, 13))[0]
    assert on_day["days_until"] == 0 and on_day["already_enforceable"]
    assert legal_view.legal_view(rep, registry)["as_of"] == "2026-06-01"


def test_empty_report_has_empty_view(registry):
    view = legal_view.legal_view(report(), registry)
    assert view["ceilings"] == [] and view["timeline"] == [] and view["highest_applicable_ceiling"] is None


def test_report_section_present_in_markdown_and_html(registry):
    from test_schema import make_report, finding as schema_finding
    rep = make_report([schema_finding()])
    assert legal_view.SECTION_TITLE in SECTIONS
    for text in (render_markdown(rep), render_html(rep)):
        assert legal_view.SECTION_TITLE in text
        assert "not a predicted or estimated fine" in text
        assert "Highest applicable ceiling" in text


def test_endpoint_for_completed_run_and_replay_mode(tmp_path):
    client = TestClient(create_app(reports_dir=tmp_path))
    started = client.post("/api/replays/juice-shop")
    assert started.status_code == 202
    run_id = started.json()["run_id"]
    # replay playback has not finished yet; the endpoint refuses until the run completes
    # (the e2e spec covers the completed Replay Mode path)
    response = client.get(f"/api/scans/{run_id}/legal")
    assert response.status_code in (200, 409)
    assert client.get("/api/scans/unknown/legal").status_code == 404


def test_completed_legal_endpoint_includes_finding_applicability(tmp_path):
    from types import SimpleNamespace

    from fastapi import FastAPI

    from dashboard.backend.legal import router

    rep = report(finding("disclosure", "DPDP-Act-16(1)", ["DPDP-Rule-13(4)"], status="needs-legal-review"))
    (tmp_path / "report.json").write_text(json.dumps(rep), encoding="utf-8")
    app = FastAPI()
    app.include_router(router(lambda _: SimpleNamespace(status="completed", report_dir=tmp_path)))
    response = TestClient(app).get("/api/scans/run/legal")
    assert response.status_code == 200
    payload = response.json()
    assert payload["highest_applicable_ceiling"] is None
    assert payload["ceilings"][0]["finding_ids_by_applicability"]["conditional"] == ["disclosure"]
