from pathlib import Path

import pytest

from auditor.mapping import assemble
from auditor.rules.context import build_context
from auditor.rules.retention_rights import purpose_end, erasure_notice, grievance, nomination


@pytest.fixture(scope='module')
def ctx():
    return build_context(Path('targets/juice-shop'), 'juice-shop')


def test_retention_gate(ctx):
    matches = purpose_end(ctx)
    assert matches and all(not m.gate_evidence for m in matches)
    assert any('erasure' in m.evidence[0]['file'].lower() or 'erasure' in m.evidence[0]['excerpt'].lower() for m in matches)
    assert assemble(matches).not_determinable


def test_notice_is_conditional(ctx):
    matches = erasure_notice(ctx)
    assert matches and all(m.status_hint == 'conditional' for m in matches)
    assert all(f['status'] == 'conditional' for f in assemble(matches).findings)


def test_grievance_available(ctx):
    assert grievance(ctx) == []


def test_nomination_gate_unresolved(ctx):
    matches = nomination(ctx)
    assert matches and all(not m.gate_evidence for m in matches)
    assert any('GDPR' in m.evidence[0]['excerpt'] for m in matches)
    assert assemble(matches).not_determinable
