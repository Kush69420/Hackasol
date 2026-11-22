from dataclasses import replace
from pathlib import Path

import pytest

from auditor import rules_list
from auditor.remediation import load_catalogue
from auditor.registry import load_registry
from auditor.rules import load_rules


ROOT = Path(__file__).resolve().parents[1]


def test_rules_list_matches_generated_document_and_contains_all_rules():
    result = rules_list.generate_rules_list()
    assert (ROOT / "RULES.md").read_text(encoding="utf-8") == result
    assert result == rules_list.generate_rules_list()
    for rule_id in load_rules():
        assert f"### {rule_id} —" in result
    for issue_id in load_catalogue():
        assert f"## {issue_id} —" in result


def test_rules_list_uses_metadata_and_masks_corpus(monkeypatch, tmp_path):
    spec, detector = next(iter(load_rules().values()))
    spec = replace(spec, title="Changed Rule title", engine="changed-engine",
                   languages=("changed-language",), classification="technical",
                   base_vector="changed-vector")
    issue = replace(load_catalogue()[spec.issue_type], title="Changed Issue Type",
                    gate="Changed Gate", primary="DPDP-Act-4(1)",
                    related=("CWE-798",))
    corpus = tmp_path / "corpus"
    positive = corpus / spec.id / "positive"
    positive.mkdir(parents=True)
    (positive / "server.ts").write_text(
        'password = "raw-password-value"\n' + ''.join(f'line {i}\n' for i in range(20)),
        encoding="utf-8",
    )
    monkeypatch.setattr(rules_list, "CORPUS", corpus)
    monkeypatch.setattr(rules_list, "load_rules", lambda: {spec.id: (spec, detector)})
    monkeypatch.setattr(rules_list, "load_catalogue", lambda: {issue.id: issue})
    result = rules_list.generate_rules_list()
    assert "Changed Issue Type" in result
    assert "Changed Rule title" in result
    assert "changed-engine" in result and "changed-language" in result
    assert "changed-vector" in result and "Changed Gate" in result
    assert load_registry()[issue.primary].citation in result
    assert load_registry()["CWE-798"].citation in result
    assert "CWE: CWE-798" in result
    assert "«SECRET»" in result and "raw-password-value" not in result
    assert "line 10" in result and "line 11" not in result


def test_rules_list_marks_unimplemented_issue_type(monkeypatch):
    issue = next(iter(load_catalogue().values()))
    monkeypatch.setattr(rules_list, "load_rules", lambda: {})
    monkeypatch.setattr(rules_list, "load_catalogue", lambda: {issue.id: issue})
    assert "No Rule implemented at this slice" in rules_list.generate_rules_list()


def test_rules_list_rejects_unknown_issue_type(monkeypatch):
    spec, detector = next(iter(load_rules().values()))
    spec = replace(spec, issue_type="missing")
    monkeypatch.setattr(rules_list, "load_rules", lambda: {spec.id: (spec, detector)})
    with pytest.raises(ValueError, match="unknown Issue Type missing"):
        rules_list.generate_rules_list()


@pytest.mark.parametrize("field", ["primary", "related"])
def test_rules_list_rejects_unknown_provisions(monkeypatch, field):
    spec, detector = next(iter(load_rules().values()))
    issue = load_catalogue()[spec.issue_type]
    issue = replace(issue, **{field: "missing" if field == "primary" else ("missing",)})
    monkeypatch.setattr(rules_list, "load_rules", lambda: {spec.id: (spec, detector)})
    monkeypatch.setattr(rules_list, "load_catalogue", lambda: {issue.id: issue})
    with pytest.raises(ValueError, match="unknown Provision missing"):
        rules_list.generate_rules_list()
