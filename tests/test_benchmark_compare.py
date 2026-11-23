"""Tests for benchmark/compare.py on tiny synthetic inputs (no Target code, no secrets)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmark"))

import compare  # noqa: E402


def semgrep_result(path, start, end, check_id, cwe=(), severity="WARNING", dataflow=None):
    extra = {"severity": severity, "metadata": {"cwe": list(cwe)}}
    if dataflow is not None:
        extra["dataflow_trace"] = dataflow
    return {"check_id": check_id, "path": path, "start": {"line": start}, "end": {"line": end}, "extra": extra}


def test_groups_join_rules_on_identical_lines_and_keep_highest_severity():
    raw = {"results": [
        semgrep_result("a.ts", 3, 3, "r1", ["CWE-798: Use of Hard-coded Credentials"], "WARNING"),
        semgrep_result("a.ts", 3, 3, "r2", [], "ERROR"),
        semgrep_result("a.ts", 4, 4, "r3", [], "INFO"),
    ]}
    groups = compare.semgrep_groups(raw)
    assert [(g["start_line"], g["severity"], g["rules"]) for g in groups] == [
        (3, "ERROR", ["r1", "r2"]),
        (4, "INFO", ["r3"]),
    ]
    assert groups[0]["cwes"] == ["CWE-798"]


def test_cwe_route_predicts_only_linked_groups_and_location_route_predicts_all():
    groups = [
        {"file": "a.ts", "start_line": 3, "end_line": 3, "rules": ["r1"], "cwes": ["CWE-798"], "severity": "WARNING"},
        {"file": "a.ts", "start_line": 9, "end_line": 9, "rules": ["r2"], "cwes": [], "severity": "INFO"},
    ]
    index = compare.cwe_index()
    assert index["CWE-798"] == ["SEC-05"]
    assert [p["issue_type"] for p in compare.semgrep_predictions(groups, index, location_only=False)] == ["SEC-05"]
    assert [p["issue_type"] for p in compare.semgrep_predictions(groups, index, location_only=True)] == ["*", "*"]


def test_location_scoring_matches_overlapping_lines_whatever_the_issue_type():
    reference = {
        "target": {"name": "synthetic", "commit": "0" * 40},
        "entries": [
            {"id": "REF-1", "issue_type": "SEC-05", "file": "a.ts", "start_line": 3, "end_line": 5,
             "status": "confirmed"},
            {"id": "REF-2", "issue_type": "SEC-01", "file": "b.ts", "start_line": 1, "end_line": 1,
             "status": "confirmed"},
        ],
    }
    groups = [{"file": "a.ts", "start_line": 4, "end_line": 4, "rules": ["r1"], "cwes": [], "severity": "ERROR"}]
    index = compare.cwe_index()
    located = compare.score(compare.semgrep_predictions(groups, index, location_only=True),
                            compare.reference_variant(reference, location_only=True))
    assert (located["tp"], located["fn"], located["matched"]) == (1, 1, ["REF-1"])
    typed = compare.score(compare.semgrep_predictions(groups, index, location_only=False),
                          compare.reference_variant(reference, location_only=False))
    assert (typed["tp"], typed["matched"]) == (0, [])


def test_overlap_counts_touching_lines_and_rejects_other_files():
    assert compare.overlaps(compare.span("a.ts", 1, 3), compare.span("a.ts", 3, 9))
    assert not compare.overlaps(compare.span("a.ts", 1, 3), compare.span("a.ts", 4, 9))
    assert not compare.overlaps(compare.span("a.ts", 1, 3), compare.span("b.ts", 1, 3))


def test_foreign_paths_reports_only_dataflow_into_other_files():
    cross = {"taint_source": {"location": {"path": "b.ts"}}, "taint_sink": {"location": {"path": "a.ts"}}}
    local = {"taint_source": {"location": {"path": "a.ts"}}, "taint_sink": {"location": {"path": "a.ts"}}}
    assert compare.foreign_paths(semgrep_result("a.ts", 4, 4, "r", dataflow=cross)) == {"b.ts"}
    assert compare.foreign_paths(semgrep_result("a.ts", 4, 4, "r", dataflow=local)) == set()
    assert compare.foreign_paths(semgrep_result("a.ts", 4, 4, "r")) == set()


def test_severity_crosstab_uses_highest_overlapping_severity():
    report = {"findings": [
        {"id": "F1", "issue_type": "SEC-05", "severity": {"band": "high"},
         "evidence": [{"file": "a.ts", "start_line": 4, "end_line": 4}]},
        {"id": "F2", "issue_type": "SEC-05", "severity": {"band": "low"},
         "evidence": [{"file": "c.ts", "start_line": 1, "end_line": 1}]},
    ]}
    groups = [
        {"file": "a.ts", "start_line": 3, "end_line": 5, "rules": [], "cwes": [], "severity": "WARNING"},
        {"file": "a.ts", "start_line": 4, "end_line": 4, "rules": [], "cwes": [], "severity": "ERROR"},
    ]
    assert compare.severity_crosstab(groups, report) == {"high": {"ERROR": 1}}


def test_auditor_stats_counts_multi_file_findings_and_justifications():
    report = {"findings": [
        {"issue_type": "SEC-07", "primary_provision": "DPDP-Rule-6(1)(b)",
         "severity": {"band": "high", "justification": "reason"},
         "evidence": [{"file": "a.ts", "start_line": 1, "end_line": 1},
                      {"file": "b.ts", "start_line": 2, "end_line": 2}]},
        {"issue_type": "CON-01", "primary_provision": "DPDP-Act-6(1)", "severity": {"band": "low"},
         "evidence": [{"file": "c.ts", "start_line": 1, "end_line": 1}]},
    ]}
    stats = compare.auditor_stats(report)
    assert stats["multi_file_findings"] == 1
    assert stats["justified"] == 1
    assert stats["consent_or_erasure"] == 1
    assert stats["evidence_items"] == 3


@pytest.mark.parametrize(("run", "report_commit", "reference_commit", "error"), [
    ({"commit": "a", "dirty_checkout": True}, "a", "a", "dirty"),
    ({"commit": "a"}, "a", "a", "cleanliness"),
    ({"commit": "a", "dirty_checkout": False}, "b", "a", "Auditor report"),
    ({"commit": "a", "dirty_checkout": False}, "a", "b", "reference pin"),
])
def test_provenance_rejects_unsafe_comparisons(run, report_commit, reference_commit, error):
    with pytest.raises(ValueError, match=error):
        compare.validate_provenance("juice-shop", run, {"target": {"commit": report_commit}},
                                    {"target": {"commit": reference_commit}})


def test_provenance_accepts_matching_clean_commits():
    compare.validate_provenance("juice-shop", {"commit": "a", "dirty_checkout": False},
                                {"target": {"commit": "a"}}, {"target": {"commit": "a"}})
