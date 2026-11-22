"""Labelled Corpus: every Rule fires on its true positive and stays silent on its near-miss negative.

Each Rule owns ``corpus/<rule-id>/positive/`` and ``corpus/<rule-id>/negative/``: small Target
Application trees run through the same deterministic core as a scan (``build_context``).
Run one Rule with ``pytest tests/test_labelled_corpus.py -k <rule-id>``.
"""

from functools import cache
from pathlib import Path

import pytest

from auditor.rules import load_rules
from auditor.rules.context import build_context

REPO = Path(__file__).resolve().parents[1]
RULES = load_rules()


@cache
def _context(path: Path):
    return build_context(path, "corpus")


def _corpus(rule_id: str, label: str) -> Path:
    path = REPO / "corpus" / rule_id / label
    assert path.is_dir(), f"{rule_id} has no Labelled Corpus {label} at {path.relative_to(REPO)}"
    return path


@pytest.mark.parametrize("rule_id", sorted(RULES))
def test_positive_fires(rule_id):
    spec, detect = RULES[rule_id]
    matches = [m for m in detect(_context(_corpus(rule_id, "positive"))) if m.rule_id == rule_id]
    assert matches, f"{rule_id} did not fire on its true positive"
    for m in matches:
        assert m.issue_type == spec.issue_type
        # A Rule may pick a residual-risk vector when mitigating Evidence exists (severity_note).
        assert (m.base_vector or "").startswith("CVSS:4.0/") == (spec.base_vector is not None)
        assert m.classification == spec.classification
        assert m.evidence and all(e["file"] and e["start_line"] for e in m.evidence)


@pytest.mark.parametrize("rule_id", sorted(RULES))
def test_negative_is_silent(rule_id):
    _, detect = RULES[rule_id]
    matches = [m for m in detect(_context(_corpus(rule_id, "negative"))) if m.rule_id == rule_id]
    assert not matches, f"{rule_id} fired on its near-miss negative: {[m.evidence[0] for m in matches]}"
