"""Checks the Issue Type catalogue against docs/issue-types.md and the Provision registry."""

import subprocess
import sys

import pytest

from auditor.remediation import guidance_for, load_catalogue

ISSUE_TYPE_IDS = (
    *(f"SEC-{n:02d}" for n in range(1, 17)),
    *(f"CON-{n:02d}" for n in range(1, 9)),
    *(f"RET-{n:02d}" for n in range(1, 4)),
    *(f"RIG-{n:02d}" for n in range(1, 5)),
    *(f"CHI-{n:02d}" for n in range(1, 3)),
    *(f"TRF-{n:02d}" for n in range(1, 3)),
    "MON-01",
)
KINDS = {"dpdp-obligation", "security-personal-data", "safeguard"}


def test_catalogue_has_one_entry_per_issue_type():
    catalogue = load_catalogue()

    assert len(ISSUE_TYPE_IDS) == 36
    assert sorted(catalogue) == sorted(ISSUE_TYPE_IDS)


@pytest.mark.parametrize("issue_type_id", ISSUE_TYPE_IDS)
def test_entry_is_complete(issue_type_id):
    issue = load_catalogue()[issue_type_id]

    assert issue.title
    assert issue.group
    assert issue.guidance.strip()
    assert issue.kind_default in KINDS
    assert issue.verify
    assert set(issue.verify) <= {"static", "live"}


def test_safeguard_kind_matches_nexus_gate():
    catalogue = load_catalogue()
    safeguards = {i.id for i in catalogue.values() if i.kind_default == "safeguard"}
    nexus = {i.id for i in catalogue.values() if i.gate == "nexus"}

    assert safeguards == nexus == {"SEC-05", "SEC-06", "SEC-11", "SEC-16"}


def test_guidance_for_needs_no_llm_configuration(monkeypatch):
    monkeypatch.delenv("DPDP_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("DPDP_LLM_MODEL", raising=False)

    assert guidance_for("SEC-01") == load_catalogue()["SEC-01"].guidance


def test_guidance_for_unknown_id_raises():
    with pytest.raises(KeyError):
        guidance_for("SEC-99")


def test_loader_does_not_import_llm_layer():
    code = "import sys; import auditor.remediation; assert 'auditor.llm' not in sys.modules"

    subprocess.run([sys.executable, "-c", code], check=True)


def test_grievance_and_contact_provisions_match_their_duties():
    from auditor.registry import get

    issue = load_catalogue()["RIG-03"]
    assert issue.primary == "DPDP-Act-8(10)"
    assert "grievances" in get(issue.primary).excerpt
    assert "DPDP-Act-8(9)" in issue.related
    assert "contact" in get("DPDP-Act-8(9)").excerpt


def test_transfer_title_uses_domain_term():
    assert "third-party" not in load_catalogue()["TRF-01"].title.lower()


@pytest.mark.parametrize("issue_type_id", ISSUE_TYPE_IDS)
def test_provision_ids_resolve_in_registry(issue_type_id):
    # Imported here so the catalogue tests above still run before the registry exists.
    from auditor import registry

    issue = load_catalogue()[issue_type_id]
    for provision_id in (issue.primary, *issue.related, issue.ceiling_parent):
        registry.get(provision_id)
