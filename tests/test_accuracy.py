"""Measured accuracy: scoring, publication parity, cache replay and the pinned reference list."""
import json
from pathlib import Path
import subprocess

import pytest

from auditor import accuracy as acc
from auditor.report import render_html, render_markdown, write_reports
from auditor.schema import ReportValidationError, validate_report
from test_schema import evidence, finding, make_report

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "tests" / "fixtures" / "accuracy" / "reference.json"
PIN = "c9f99228d9d56afb5f5ca7925376292f7fa44b13"


def f(fid, issue_type, file, start, end=None):
    return finding(id=fid, issue_type=issue_type, evidence=[evidence(file, start, end or start)])


def reference():
    return acc.load_reference(FIXTURE)


# --- scoring --------------------------------------------------------------------------------

def test_scoring_exact_counts_and_ratios():
    findings = [f("SEC-01-aaaaaaaaaaaa", "SEC-01", "src/log.ts", 11),      # TP REF-001
                f("SEC-08-bbbbbbbbbbbb", "SEC-08", "src/api.ts", 25),      # TP REF-002
                f("SEC-08-cccccccccccc", "SEC-08", "src/api.ts", 90)]      # FP: no entry there
    score = acc.score_findings(findings, reference())
    assert (score["tp"], score["fp"], score["fn"]) == (2, 1, 1)
    assert score["precision"] == round(2 / 3, 4) and score["recall"] == round(2 / 3, 4)
    assert score["matches"] == [{"finding_id": "SEC-01-aaaaaaaaaaaa", "reference_id": "REF-001"},
                                {"finding_id": "SEC-08-bbbbbbbbbbbb", "reference_id": "REF-002"}]
    assert score["unmatched_references"] == ["REF-003"]
    assert score["unmatched_predictions"][0]["finding_id"] == "SEC-08-cccccccccccc"
    assert score["excluded"] == [{"reference_id": "REF-004", "reason": "Sink configured outside the repository."}]


def test_scoring_duplicate_prediction_cannot_earn_second_tp():
    findings = [f("SEC-01-aaaaaaaaaaaa", "SEC-01", "src/log.ts", 10), f("SEC-01-bbbbbbbbbbbb", "SEC-01", "src/log.ts", 12)]
    score = acc.score_findings(findings, reference())
    assert (score["tp"], score["fp"]) == (1, 1)
    assert score["unmatched_predictions"] == [{"finding_id": "SEC-01-bbbbbbbbbbbb", "issue_type": "SEC-01",
                                               "reason": "duplicate of REF-001"}]


def test_scoring_merged_finding_is_one_prediction_matching_one_entry():
    merged = finding(id="SEC-08-dddddddddddd", issue_type="SEC-08", rules_fired=["R1", "R2"],
                     evidence=[evidence("src/api.ts", 21, 22), evidence("src/api.ts", 51, 52)])
    score = acc.score_findings([merged], reference())
    assert (score["tp"], score["fp"], score["fn"]) == (1, 0, 2)
    assert score["matches"] == [{"finding_id": "SEC-08-dddddddddddd", "reference_id": "REF-002"}]


def test_scoring_one_to_one_takes_lowest_unmatched_entry_in_id_order():
    findings = [f("SEC-08-aaaaaaaaaaaa", "SEC-08", "src/api.ts", 25), f("SEC-08-bbbbbbbbbbbb", "SEC-08", "src/api.ts", 52)]
    score = acc.score_findings(findings, reference())
    assert [m["reference_id"] for m in score["matches"]] == ["REF-002", "REF-003"]


def test_scoring_zero_denominators_are_none_and_render_na():
    empty = {"target": {"name": "t", "commit": PIN}, "entries": []}
    score = acc.score_findings([], empty)
    assert (score["tp"], score["fp"], score["fn"]) == (0, 0, 0)
    assert score["precision"] is None and score["recall"] is None
    assert acc.ratio_text(score["precision"], 0, 0) == "N/A (0/0)"
    only_fp = acc.score_findings([f("SEC-01-aaaaaaaaaaaa", "SEC-01", "x.ts", 1)], empty)
    assert only_fp["precision"] == 0.0 and only_fp["recall"] is None


def test_scoring_issue_type_and_anchor_must_both_match():
    findings = [f("SEC-08-aaaaaaaaaaaa", "SEC-08", "src/log.ts", 11),     # right place, wrong Issue Type
                f("SEC-01-bbbbbbbbbbbb", "SEC-01", "src/api.ts", 25),     # right Issue Type family, wrong place
                f("SEC-01-cccccccccccc", "SEC-01", "src/log.ts", 13)]     # just outside the anchor
    score = acc.score_findings(findings, reference())
    assert (score["tp"], score["fp"], score["fn"]) == (0, 3, 3)


def test_scoring_not_determinable_entries_are_excluded_and_not_false_negatives():
    score = acc.score_findings([f("SEC-01-aaaaaaaaaaaa", "SEC-01", "src/other.ts", 2)], reference())
    assert score["fn"] == 3 and "REF-004" not in score["unmatched_references"]
    assert (score["tp"], score["fp"]) == (0, 0) and score["unmatched_predictions"] == []
    assert score["precision"] is None
    assert score["excluded_predictions"] == [{
        "finding_id": "SEC-01-aaaaaaaaaaaa", "reference_id": "REF-004",
        "reason": "overlaps only not-determinable entry REF-004: Sink configured outside the repository."}]


def test_labelled_corpus_counts_per_rule_and_missing_pair_is_an_error(tmp_path):
    from auditor.rules import load_rules
    rules = load_rules()
    rule_id = sorted(rules)[0]
    result = acc.evaluate_corpus(REPO / "corpus", {rule_id: rules[rule_id]})
    assert result["rules"] == [{"rule_id": rule_id, "tp": 1, "fp": 0, "fn": 0, "tn": 1,
                                "precision": 1.0, "recall": 1.0}]
    assert result["totals"]["tp"] == 1
    (tmp_path / rule_id / "positive").mkdir(parents=True)
    with pytest.raises(acc.CorpusError, match=f"{rule_id}/negative"):
        acc.evaluate_corpus(tmp_path, {rule_id: rules[rule_id]})


# --- publication ----------------------------------------------------------------------------

CORPUS = {"rules": [{"rule_id": "SEC-01-fixture-rule", "tp": 1, "fp": 0, "fn": 0, "tn": 1,
                     "precision": 1.0, "recall": 1.0},
                    {"rule_id": "SEC-08-fixture-rule", "tp": 0, "fp": 1, "fn": 1, "tn": 0,
                     "precision": 0.0, "recall": 0.0}],
          "totals": {"tp": 1, "fp": 1, "fn": 1, "tn": 1, "precision": 0.5, "recall": 0.5}}


def accuracy_report():
    findings = [f("SEC-01-aaaaaaaaaaaa", "SEC-01", "src/log.ts", 11), f("SEC-08-bbbbbbbbbbbb", "SEC-08", "src/api.ts", 25),
                f("SEC-08-cccccccccccc", "SEC-08", "src/api.ts", 90),
                f("SEC-01-eeeeeeeeeeee", "SEC-01", "src/other.ts", 2)]  # excluded, not scored
    report = make_report(findings, mode="cache-only", reason="forced")
    report["target"]["commit"] = reference()["target"]["commit"]
    report["llm"].update(provider="anthropic", model="claude-test")
    report["llm"]["prompt_versions"] = {"triage": "triage-v2"}
    report["accuracy"] = acc.build_accuracy(report, reference(), CORPUS, reference_path="tests/fixtures/accuracy/reference.json",
                                            cache_dir=REPO / "no-such-cache")
    validate_report(report)
    return report


def test_publication_numbers_identical_across_json_markdown_html_and_pdf(tmp_path):
    report = accuracy_report()
    primary = report["accuracy"]["reference_target"]
    assert primary["precision"] == round(2 / 3, 4) and primary["recall"] == round(2 / 3, 4)
    paths = write_reports(report, tmp_path / "report.json")
    assert json.loads(paths[0].read_text())["accuracy"] == report["accuracy"]
    pdf = subprocess.run(["pdftotext", "-raw", str(paths[3]), "-"], check=True,
                         capture_output=True, text=True).stdout
    expected = [acc.ratio_text(primary["precision"], 2, 3), acc.ratio_text(primary["recall"], 2, 3),
                "SEC-01-fixture-rule", "SEC-08-fixture-rule", "Measured accuracy", "cache-only",
                "Excluded prediction: SEC-01-eeeeeeeeeeee"]
    assert primary["excluded_predictions"][0]["finding_id"] == "SEC-01-eeeeeeeeeeee"
    for text in (paths[1].read_text(), paths[2].read_text(), render_html(report)):
        for needle in expected:
            assert needle in text, needle
    pdf_text = "".join(pdf.split())  # table cells may wrap differently with other fonts
    for needle in ("0.6667", "SEC-01-fixture-rule", "Measured accuracy"):
        assert "".join(needle.split()) in pdf_text, needle


def test_publication_schema_rejects_malformed_accuracy():
    report = accuracy_report()
    report["accuracy"]["reference_target"]["precision"] = 1.5
    with pytest.raises(ReportValidationError):
        validate_report(report)
    report = accuracy_report()
    del report["accuracy"]["llm"]
    with pytest.raises(ReportValidationError):
        validate_report(report)


def test_publication_revision_mismatch_is_an_error():
    report = accuracy_report()
    report["target"]["commit"] = "f" * 40
    with pytest.raises(ValueError, match="does not match the reference pin"):
        acc.build_accuracy(report, reference(), CORPUS)


def test_publication_ci_uses_the_same_evaluator(monkeypatch, capsys):
    from auditor import cli
    sentinel = {"rules": [{"rule_id": "SEC-00-sentinel", "tp": 1, "fp": 0, "fn": 0, "tn": 1,
                           "precision": 1.0, "recall": 1.0}],
                "totals": {"tp": 1, "fp": 0, "fn": 0, "tn": 1, "precision": 1.0, "recall": 1.0}}
    monkeypatch.setattr(cli, "evaluate_corpus", lambda: sentinel)
    assert cli.main(["accuracy", "--corpus-only"]) == 0
    assert "SEC-00-sentinel" in capsys.readouterr().out
    workflow = (REPO / ".github/workflows/accuracy.yml").read_text()
    assert "dpdp-audit accuracy --corpus-only" in workflow

    def missing():
        raise acc.CorpusError("missing Labelled Corpus pair(s): X/negative")
    monkeypatch.setattr(cli, "evaluate_corpus", missing)
    assert cli.main(["accuracy", "--corpus-only"]) == 1


def test_publication_real_corpus_has_a_pair_for_every_rule():
    result = acc.evaluate_corpus()
    from auditor.rules import load_rules
    assert [r["rule_id"] for r in result["rules"]] == sorted(load_rules())
    assert all(r["tp"] == 1 and r["fp"] == 0 for r in result["rules"])


# --- cache replay ---------------------------------------------------------------------------

def synthetic_target():
    from auditor.rules import load_rules
    return REPO / "corpus" / sorted(load_rules())[0] / "positive"


def test_cache_replay_two_runs_reproduce_findings_and_record_provenance(tmp_path):
    from auditor.scan import run_scan
    runs = []
    for _ in range(2):
        with acc.forced_cache_only():
            runs.append(run_scan(str(synthetic_target()), cache_dir=tmp_path / "cache"))
    first, second = runs
    assert [x["id"] for x in first["findings"]] == [x["id"] for x in second["findings"]]
    assert first["findings"], "synthetic target should yield Findings"
    for report in runs:
        status = acc.replay_status(report, tmp_path / "cache")
        assert status["mode"] == "cache-only"
        assert status["provider"] and status["model"] and status["prompt_version"]
        assert status["cache_misses"] == report["llm"]["cache_misses"]


def test_cache_replay_missing_verdict_is_a_miss_and_not_full_reproduction(tmp_path):
    from auditor.scan import run_scan
    with acc.forced_cache_only():
        report = run_scan(str(synthetic_target()), cache_dir=tmp_path / "empty")
    assert report["llm"]["cache_misses"] > 0 and report["llm"]["not_assessed"] > 0
    status = acc.replay_status(report, tmp_path / "empty")
    assert status["reproduces_published_run"] is False
    assert any("cache miss" in p for p in status["replay_problems"])


def test_cache_replay_manifest_must_match_rules_digest_and_provenance(tmp_path):
    report = make_report(mode="cache-only", reason="forced")
    report["llm"].update(provider="anthropic", model="claude-test", cache_hits=3, cache_misses=0, not_assessed=0)
    report["llm"]["prompt_versions"] = {"triage": "triage-v2"}
    assert acc.replay_status(report, tmp_path)["reproduces_published_run"] is False  # no manifest
    acc.write_manifest(report, tmp_path)
    manifest = json.loads((tmp_path / acc.MANIFEST_NAME).read_text())
    assert manifest["rules_digest"] == acc.rules_digest() and manifest["cache_identity"]
    assert acc.replay_status(report, tmp_path)["reproduces_published_run"] is True
    manifest["rules_digest"] = "0" * 64
    (tmp_path / acc.MANIFEST_NAME).write_text(json.dumps(manifest))
    status = acc.replay_status(report, tmp_path)
    assert status["reproduces_published_run"] is False and "Rules digest differs from the manifest" in status["replay_problems"]


def test_cache_replay_manifest_checks_each_role_route(tmp_path):
    report = make_report(mode="cache-only", reason="forced")
    report["llm"].update(provider="anthropic", model="claude-test", cache_hits=3, cache_misses=0, not_assessed=0)
    report["llm"]["prompt_versions"] = {"triage": "triage-v2"}
    report["llm"]["roles"]["triage"] = {"provider": "openai", "model": "gpt-test", "mode": "cache-only", "reason": "forced"}
    acc.write_manifest(report, tmp_path)
    manifest = json.loads((tmp_path / acc.MANIFEST_NAME).read_text())
    assert manifest["roles"]["triage"]["model"] == "gpt-test"
    assert acc.replay_status(report, tmp_path)["reproduces_published_run"] is True
    manifest["roles"]["triage"]["model"] = "other"
    (tmp_path / acc.MANIFEST_NAME).write_text(json.dumps(manifest))
    status = acc.replay_status(report, tmp_path)
    assert status["reproduces_published_run"] is False
    assert "triage model differs from the manifest" in status["replay_problems"]


def test_cache_replay_manifest_without_roles_still_reproduces(tmp_path):
    report = make_report(mode="cache-only", reason="forced")
    report["llm"].update(provider="anthropic", model="claude-test", cache_hits=3, cache_misses=0, not_assessed=0)
    report["llm"]["prompt_versions"] = {"triage": "triage-v2"}
    acc.write_manifest(report, tmp_path)
    manifest = json.loads((tmp_path / acc.MANIFEST_NAME).read_text())
    del manifest["roles"]
    (tmp_path / acc.MANIFEST_NAME).write_text(json.dumps(manifest))
    assert acc.replay_status(report, tmp_path)["reproduces_published_run"] is True
    report["llm"]["roles"]["triage"]["model"] = "other"
    status = acc.replay_status(report, tmp_path)
    assert status["reproduces_published_run"] is False
    assert "triage model differs from the manifest" in status["replay_problems"]


# --- reference list -------------------------------------------------------------------------

REFERENCE = REPO / "accuracy" / "juice-shop.json"


@pytest.fixture
def pinned_reference():
    if not REFERENCE.exists():
        pytest.skip("accuracy/juice-shop.json is not present")
    return acc.load_reference(REFERENCE)


def test_reference_pin_exclusions_ids_and_anchors(pinned_reference):
    from auditor.exclusions import PROFILES, is_excluded
    ref = pinned_reference
    assert ref["target"]["commit"] == PIN
    assert list(PROFILES["juice-shop"]) == ref["exclusions"]
    ids = [e["id"] for e in ref["entries"]]
    assert len(ids) == len(set(ids))
    root = REPO / "targets" / "juice-shop"
    if not root.is_dir():
        pytest.skip("targets/juice-shop is not cloned")
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    assert head == PIN
    for entry in ref["entries"]:
        assert not is_excluded(Path(entry["file"]), "juice-shop"), entry["id"]
        lines = (root / entry["file"]).read_text(encoding="utf-8", errors="replace").splitlines()
        assert 1 <= entry["start_line"] <= entry["end_line"] <= len(lines), entry["id"]
        if entry["status"] == "not-determinable":
            assert entry["reason"], entry["id"]
