"""Recall Rules: each fires on its Labelled Corpus positive, with evidence that never carries key material."""
from pathlib import Path

import pytest

from auditor.rules import load_rules
from auditor.rules.context import build_context
from auditor.rules.recall_config import _cookie_flags

CORPUS = Path(__file__).resolve().parents[1] / 'corpus'
RULES = load_rules()
IDS = ['SEC-04-ts-constant-key-verifier', 'SEC-04-ts-md5-credential-compare', 'SEC-05-ts-hardcoded-hmac-key',
       'SEC-10-ts-token-storage-site', 'SEC-11-ts-session-cookie-flags', 'SEC-11-ts-jsonp-response',
       'SEC-11-terraform-plaintext-listener', 'RET-01-sequelize-soft-delete']


def _run(rule_id, label):
    ctx = build_context(CORPUS / rule_id / label, 'corpus')
    return [m for m in RULES[rule_id][1](ctx) if m.rule_id == rule_id]


@pytest.mark.parametrize('rule_id', IDS)
def test_rule_registered_with_corpus_pair(rule_id):
    assert rule_id in RULES
    assert _run(rule_id, 'positive') and not _run(rule_id, 'negative')


def test_hmac_key_is_masked():
    for match in _run('SEC-05-ts-hardcoded-hmac-key', 'positive'):
        assert match.evidence[0]['excerpt'] == '[hard-coded key material masked]'


def test_jsonp_scoped_to_enclosing_handler():
    # The near miss has Personal Data in a sibling handler only.
    assert not _run('SEC-11-ts-jsonp-response', 'negative')


def test_cookie_spreads_respect_order_and_unknown_values():
    text = "const defaults = { httpOnly: true, secure: true, sameSite: 'strict' };"
    assert all(_cookie_flags('{ ...defaults }', text, len(text)).values())
    assert _cookie_flags('{ ...defaults, secure: false }', text, len(text))['secure'] is False
    assert _cookie_flags('{ secure: false, ...opaque }', text, len(text))['secure'] is None
    assert _cookie_flags('{ ...opaque, secure: false }', text, len(text))['secure'] is False
