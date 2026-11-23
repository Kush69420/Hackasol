"""Report parity, statutory coverage and Evidence disclosure tests."""
import json
import subprocess

import pytest

from auditor.masking import mask_for_report
from auditor.registry import load_registry
from auditor.report import SECTIONS, _dependent, coverage_matrix, executive_summary, render_html, write_reports
from auditor.rules import load_rules
from auditor.schema import validate_report
from test_accuracy import accuracy_report
from test_schema import finding, make_report


def pdf_text(path):
    return subprocess.run(["pdftotext", "-layout", str(path), "-"], check=True,
                          capture_output=True, text=True).stdout


@pytest.mark.parametrize("empty", [False, True])
def test_parity(tmp_path, empty):
    findings = [] if empty else [finding(status="conditional"), finding(id="SEC-01-abcdefabcdef")]
    report = make_report(findings, mode="cache-only", reason="Provider unavailable",
                         accuracy=accuracy_report()["accuracy"])
    report["executive_summary"] = executive_summary(report)
    validate_report(report)
    paths = write_reports(report, tmp_path / "custom.json")
    assert [p.name for p in paths] == ["custom.json", "custom.md", "custom.html", "custom.pdf"]
    texts = [paths[1].read_text(), paths[2].read_text(), pdf_text(paths[3])]
    assert json.loads(paths[0].read_text()) == report
    for text in texts:
        cursor = 0
        for section in SECTIONS:
            cursor = text.index(section, cursor) + len(section)
        positions = [text.index(item["id"]) for item in findings]
        assert positions == sorted(positions)
        for item in findings:
            assert item["primary_provision"] in text
        assert "not assessed" in text
        assert "0.6667" in text
    if findings:
        assert all("conditional" in text for text in texts)


def test_parity_dependent_findings():
    base = finding()
    sdf = finding(id="SEC-01-000000000001", primary_provision="DPDP-Act-10")
    schedule = finding(id="SEC-01-000000000002", primary_provision="DPDP-Rule-8(2)")
    consent = finding(id="SEC-01-000000000003", primary_provision="DPDP-Act-6(1)")
    assert [_dependent("AA-1", f) for f in (base, sdf, schedule, consent)] == [True] * 4
    assert [_dependent("AA-2", f) for f in (base, sdf, schedule, consent)] == [False, True, False, False]
    assert [_dependent("AA-3", f) for f in (base, sdf, schedule, consent)] == [False, False, True, False]
    assert [_dependent("AA-4", f) for f in (base, sdf, schedule, consent)] == [False, False, False, True]


def test_coverage_registry_and_unmet_gates():
    registry = load_registry()
    rules = load_rules()
    gated_rule = next(rid for rid, (spec, _) in rules.items() if spec.issue_type == "RIG-02")
    rows = coverage_matrix(registry, rules, [{"rule_id": gated_rule, "issue_type": "RIG-02", "reason": "Gate Evidence missing"}], [])
    index = {row["provision"]: row for row in rows}
    assert set(index) == {pid for pid, entry in registry.items() if entry.kind in ("dpdp-act", "dpdp-rule")}
    for pid in ("DPDP-Act-8(2)", "DPDP-Act-8(3)", "DPDP-Act-8(6)", "DPDP-Rule-7"):
        assert index[pid]["classification"] == "not code-checkable"
    assert index["DPDP-Act-12(2)"]["classification"] == "not determinable"
    assert gated_rule in index["DPDP-Act-12(2)"]["not_determinable_rules"]
    assert index["DPDP-Act-9"]["annotation"] == "covered, not exercised on a real Target"
    assert "not determinable" in render_html(make_report(coverage_matrix=rows))


def test_masking_and_html_escaping(tmp_path):
    raw = 'password="my-authentication-value"\n-----BEGIN PRIVATE KEY-----\nprivate-key-material\n-----END PRIVATE KEY-----\nAadhaar: 1234 5678 9010\n<script>alert(1)</script>'
    item = finding()
    item["evidence"][0]["excerpt"] = mask_for_report(raw)
    report = make_report([item])
    validate_report(report)
    paths = write_reports(report, tmp_path / "report.json")
    for text in [p.read_text() for p in paths[:3]] + [pdf_text(paths[3])]:
        for value in ("my-authentication-value", "private-key-material", "1234 5678 9010"):
            assert value not in text
    assert "<script>" not in paths[2].read_text()
    assert "&lt;script&gt;" in paths[2].read_text()
