from pathlib import Path

import pytest

from auditor.mapping import assemble
from auditor.rules.context import build_context
from auditor.rules.security_config import (aadhaar_storage, error_disclosure, access_logging,
                                           missing_backup, public_store, public_storage, root_container)


@pytest.fixture(scope='module')
def ctx():
    return build_context(Path('targets/juice-shop'), 'juice-shop')


def test_aadhaar_not_raised(ctx):
    assert not aadhaar_storage(ctx)


def test_verbose_errors_without_demonstrated_nexus(ctx):
    # Middleware emits errors, but a Personal Data-bearing error must be demonstrated.
    assert not error_disclosure(ctx)
    assert any('errorhandler()' in (ctx.root / p).read_text(errors='replace')
               for p in ctx.rel_files if p.endswith('.ts'))


def test_access_logging_configured(ctx):
    assert any(entry.get('kind') == 'morgan' for entry in ctx.inventory['logging'])
    assert not access_logging(ctx)


def test_persistent_store_backup(ctx):
    # The same unbacked store recurs once per Terraform deployment tree: one Finding per tree.
    matches = missing_backup(ctx)
    assert len(matches) == 2
    trees = {m.evidence[0]['file'].rsplit('/networking.tf', 1)[0] for m in matches}
    assert trees == {'terraform', 'infrastructure/terraform'}
    for m in matches:
        tree = m.evidence[0]['file'].rsplit('/networking.tf', 1)[0]
        assert m.evidence[0]['file'] == tree + '/networking.tf'
        assert any(e['file'] == tree + '/main.tf' for e in m.evidence)
        assert m.gate_evidence
    assert len([f for f in assemble(matches).findings if f['issue_type'] == 'SEC-14']) == 2


def test_no_public_personal_data_store(ctx):
    assert not public_store(ctx)
    assert not public_storage(ctx)
    assert not root_container(ctx)
