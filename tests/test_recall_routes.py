"""Route-exposure Rules: anchors on the Juice Shop Target and Rule-specific behaviours."""

from dataclasses import replace
from functools import cache
from pathlib import Path
from shutil import copytree

import pytest

from auditor.rules import load_rules
from auditor.rules.context import build_context

REPO = Path(__file__).resolve().parents[1]
RULES = load_rules()
IDS = ['SEC-07-ts-unscoped-authenticated-read', 'SEC-07-ts-unauthenticated-record-read', 'SEC-07-ts-lossy-owner-key',
       'SEC-07-ts-public-personal-data-directory', 'SEC-08-ts-whole-model-serialisation', 'SEC-09-ts-query-personal-data']


@cache
def _corpus(rule_id, label):
    return build_context(REPO / 'corpus' / rule_id / label, 'corpus')


def _run(rule_id, ctx):
    return [m for m in RULES[rule_id][1](ctx) if m.rule_id == rule_id]


def test_rules_registered():
    assert all(i in RULES for i in IDS)


def test_lossy_key_cites_the_masking_line():
    [match] = _run('SEC-07-ts-lossy-owner-key', _corpus('SEC-07-ts-lossy-owner-key', 'positive'))
    lines = {(e['file'], e['start_line']) for e in match.evidence}
    assert ('routes/history.ts', 5) in lines and ('routes/history.ts', 4) in lines


def test_guarded_lossy_key_does_not_cross_data_principals():
    rule_id = 'SEC-07-ts-lossy-owner-key'
    assert not _run(rule_id, _corpus(rule_id, 'negative'))


@pytest.mark.parametrize(('before', 'after'), [
    ('return res.sendStatus(409)', 'res.sendStatus(409)'),
    ("security.hash(other.email).slice(0, 4)", "security.hash(other.email).slice(0, 3)"),
    ('security.hash(address)', 'security.hash(req.query.email)'),
    ('other.id !== principal.data.id', 'other.id === principal.data.id'),
    ('paranoid: false', 'paranoid: false, limit: 1'),
    ('.slice(0, 4)', '.trim()'),
    ('res.json(owned)', 'res.json(rows)'),
    ('res.json(owned)', 'res.json({ owned, rows })'),
])
def test_lossy_key_still_fires_without_complete_disambiguation(tmp_path, before, after):
    rule_id = 'SEC-07-ts-lossy-owner-key'
    target = tmp_path / 'target'
    copytree(REPO / 'corpus' / rule_id / 'negative', target)
    fixture = target / 'routes' / 'guarded.ts'
    fixture.write_text(fixture.read_text().replace(before, after))
    [match] = _run(rule_id, build_context(target, 'corpus'))
    assert match.evidence[0]['file'] == 'routes/guarded.ts'


def test_public_directory_flags_write_and_mount():
    matches = _run('SEC-07-ts-public-personal-data-directory', _corpus('SEC-07-ts-public-personal-data-directory', 'positive'))
    anchors = {(m.evidence[0]['file'], m.evidence[0]['start_line']) for m in matches}
    assert ('routes/order.ts', 5) in anchors and ('server.ts', 6) in anchors


@pytest.mark.parametrize('rule_id', [IDS[0], IDS[1], IDS[4]])
def test_only_serialized_rows_from_the_query_count_as_exposure(rule_id):
    assert not _run(rule_id, _corpus(rule_id, 'negative'))


def test_dynamic_field_reads_outside_handlers_are_ignored():
    ctx = _corpus(IDS[4], 'negative')
    assert not ctx.inventory['dynamic_field_reads']
    # Ignore unscoped facts even when they are present in an inventory.
    inventory = {**ctx.inventory, 'dynamic_field_reads': [{'enclosing': None}]}
    assert not _run(IDS[4], replace(ctx, inventory=inventory))


@pytest.mark.skipif(not (REPO / 'targets' / 'juice-shop').is_dir(), reason='Juice Shop Target not present')
def test_juice_shop_anchors():
    ctx = build_context(REPO / 'targets' / 'juice-shop', 'juice-shop')
    found = {(i, m.evidence[0]['file'], m.evidence[0]['start_line']) for i in IDS for m in _run(i, ctx)}
    for expected in [('SEC-07-ts-unscoped-authenticated-read', 'server.ts', 395),
                     ('SEC-07-ts-unscoped-authenticated-read', 'server.ts', 413),
                     ('SEC-07-ts-unscoped-authenticated-read', 'routes/authenticatedUsers.ts', 12),
                     ('SEC-07-ts-unauthenticated-record-read', 'routes/recycles.ts', 12),
                     ('SEC-07-ts-public-personal-data-directory', 'routes/order.ts', 45),
                     ('SEC-08-ts-whole-model-serialisation', 'routes/saveLoginIp.ts', 33),
                     ('SEC-09-ts-query-personal-data', 'routes/changePassword.ts', 14)]:
        assert expected in found, expected
