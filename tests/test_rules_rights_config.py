from pathlib import Path
import shutil

import pytest

from auditor.rules.context import build_context
from auditor.rules.rights_config import plain_fields, erasure_request, incomplete_export, email_correction, outside_storage


@pytest.fixture(scope='module')
def ctx():
    return build_context(Path('targets/juice-shop'), 'juice-shop')


def test_plain_fields(ctx):
    matches = plain_fields(ctx)
    names = {m.element['name'] for m in matches}
    assert {'model:User.totpSecret', 'model:Card.cardNum'} <= names
    assert not names.intersection({'model:Card.expMonth', 'model:Card.expYear', 'model:Wallet.balance'})
    for match in matches:
        if match.element['name'] in {'model:User.totpSecret', 'model:Card.cardNum'}:
            assert any(e['file'] == 'terraform/networking.tf' for e in match.evidence)


def test_erasure(ctx):
    assert any(any(e['file'] == 'routes/dataErasure.ts' and e['start_line'] == 85 for e in m.evidence) for m in erasure_request(ctx))


def test_export(ctx):
    matches = incomplete_export(ctx)
    assert len(matches) == 1
    assert matches[0].evidence[0]['file'] == 'routes/dataExport.ts'
    assert any(any(e['file'] == 'models/card.ts' for e in m.evidence) for m in matches)


def test_correction(ctx):
    matches = email_correction(ctx)
    assert len(matches) == 1
    assert matches[0].evidence[0]['file'] == 'routes/updateUserProfile.ts'
    assert any(e['file'] == 'server.ts' and e['start_line'] == 396 for e in matches[0].evidence)
    assert any(e['file'] == 'server.ts' and e['start_line'] == 707 for e in matches[0].evidence)
    assert any(e['file'] == 'server.ts' and e['start_line'] == 636 for e in matches[0].gate_evidence)
    assert any(e['file'] == 'server.ts' and e['start_line'] == 482 for e in matches[0].gate_evidence)
    assert not any(e['file'] == 'server.ts' and e['start_line'] in (342, 343) for e in matches[0].evidence[:2])


def test_region(ctx):
    # One Finding per Terraform deployment tree; identical declarations inside a tree stay merged.
    matches = outside_storage(ctx)
    assert len(matches) == 2
    for tree, match in zip(('infrastructure/terraform', 'terraform'), sorted(matches, key=lambda m: m.evidence[0]['file'])):
        assert any(e['file'] == tree + '/variables.tf' for e in match.evidence)
        assert all(e['file'].startswith(tree + '/') for e in match.evidence)
        assert match.exposure.level == 'Cross-Border'
        assert match.status_hint == 'needs-legal-review'


def test_region_requires_storage_in_each_foreign_module(tmp_path):
    corpus = Path('corpus/TRF-02-terraform-storage-region')
    shutil.copytree(corpus / 'positive', tmp_path, dirs_exist_ok=True)
    shutil.copytree(corpus / 'negative' / 'unrelated', tmp_path / 'unrelated')
    matches = outside_storage(build_context(tmp_path, 'corpus'))
    assert len(matches) == 1
    assert all(not e['file'].startswith('unrelated/') for e in matches[0].evidence)
