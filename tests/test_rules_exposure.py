from pathlib import Path

import pytest

from auditor.rules.context import build_context
from auditor.rules.exposure_rules import (
    detect_account_list, detect_cors, detect_nested, detect_review_author, detect_unchecked_nested,
)


@pytest.fixture(scope='module')
def ctx():
    return build_context(Path('targets/juice-shop'), 'juice-shop')


def _anchor(matches, file, start, end):
    assert any(e['file'] == file and e['start_line'] <= end and e['end_line'] >= start
               for match in matches for e in match.evidence)
    for match in matches:
        for evidence in match.evidence:
            path = evidence['file']
            assert not path.startswith(('test/', 'data/static/codefixes/'))
            assert not path.endswith('.spec.ts')


def test_nested_records_share_anchor(ctx):
    unchecked = detect_unchecked_nested(ctx)
    nested = detect_nested(ctx)
    _anchor(unchecked, 'routes/memory.ts', 24, 25)
    _anchor(nested, 'routes/memory.ts', 24, 25)
    a = next(m for m in unchecked if m.evidence[0]['file'] == 'routes/memory.ts')
    b = next(m for m in nested if m.evidence[0]['file'] == 'routes/memory.ts')
    assert a.evidence[0] == b.evidence[0]
    assert {'model:User.email', 'model:User.password', 'model:User.totpSecret'} <= set(a.nexus_elements)
    assert a.exposure.level == 'Public'
    # Network reachable, no authentication or interaction, confidentiality impact only.
    assert a.base_vector == 'CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N'


def test_account_list(ctx):
    matches = detect_account_list(ctx)
    _anchor(matches, 'routes/authenticatedUsers.ts', 12, 28)
    match = next(m for m in matches if m.evidence[0]['file'] == 'routes/authenticatedUsers.ts')
    assert {'model:User.email', 'model:User.lastLoginIp'} <= set(match.nexus_elements)
    assert 'model:User.password' not in match.nexus_elements
    assert 'model:User.totpSecret' not in match.nexus_elements
    assert match.exposure.level == 'Public'
    assert any(e['file'] == 'server.ts' and 440 <= e['start_line'] <= 546 for e in match.exposure.derived_from)
    # The route requires authentication even though registration is open.
    assert '/PR:L/' in match.base_vector


def test_review_author(ctx):
    matches = detect_review_author(ctx)
    _anchor(matches, 'routes/showProductReviews.ts', 36, 45)
    match = next(m for m in matches if m.evidence[0]['file'] == 'routes/showProductReviews.ts')
    assert any(step['operation'] == 'Collect' for step in match.data_flow)
    assert any(step['operation'] == 'Store' and step['evidence']['file'] == 'routes/createProductReviews.ts' for step in match.data_flow)
    assert any(step['operation'] == 'Expose' for step in match.data_flow)


def test_cors_has_personal_data_nexus(ctx):
    matches = detect_cors(ctx)
    _anchor(matches, 'server.ts', 183, 185)
    match = next(m for m in matches if m.evidence[0]['file'] == 'server.ts')
    assert 'model:User.email' in match.nexus_elements
    for line in (640, 670, 672):
        assert any(e['file'] == 'server.ts' and e['start_line'] <= line <= e['end_line'] for e in match.evidence)
