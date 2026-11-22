from pathlib import Path

import pytest

from auditor.mapping import assemble
from auditor.rules.context import build_context
from auditor.rules.consent import (enforcement, bundled, default_true, withdrawal,
                                   processor, consent_record, notice, excess)


@pytest.fixture(scope='module')
def ctx():
    return build_context(Path('targets/juice-shop'), 'juice-shop')


@pytest.mark.parametrize('detect', [enforcement, bundled, default_true, withdrawal,
                                    processor, consent_record, notice, excess])
def test_primary_target_outcome(ctx, detect):
    # The Primary Target does not expose a supported consent control or grant,
    # nor an evidenced optional processing route in the Rule's supported shape.
    assert detect(ctx) == []


@pytest.mark.parametrize('rule_id', [
    'CON-01-express-enforcement', 'CON-02-angular-bundled-purposes',
    'CON-03-angular-default-true', 'CON-04-express-withdrawal-path',
    'CON-05-express-processor-withdrawal', 'CON-06-sequelize-consent-record',
    'CON-07-angular-consent-notice', 'CON-08-angular-excess-elements',
])
def test_positive_has_gate_and_assembles(rule_id):
    from auditor.rules import load_rules
    _, detect = load_rules()[rule_id]
    context = build_context(Path('corpus') / rule_id / 'positive', 'corpus')
    matches = detect(context)
    assert matches and all(m.gate_evidence for m in matches)
    assert assemble(matches).findings
