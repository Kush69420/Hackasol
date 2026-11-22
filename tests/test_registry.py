"""Loader and data tests for auditor.registry. Loader tests use synthetic YAML; data tests read the shipped files."""

from __future__ import annotations

import dataclasses
import datetime as dt

import pytest
import yaml

from auditor.registry import Provision, build_registry, get, load_registry

EARLY = dt.date(2025, 11, 14)
ONE_YEAR = dt.date(2026, 11, 14)
EIGHTEEN_MONTHS = dt.date(2027, 5, 14)

RULE_PENALTY = [
    ("DPDP-Rule-1", "DPDP-Act-Schedule-7", 50),
    ("DPDP-Rule-2", "DPDP-Act-Schedule-7", 50),
    ("DPDP-Rule-3", "DPDP-Act-5", 50),
    ("DPDP-Rule-4", "DPDP-Act-6", 50),
    ("DPDP-Rule-5", "DPDP-Act-7", 50),
    ("DPDP-Rule-6", "DPDP-Act-8(5)", 250),
    ("DPDP-Rule-7", "DPDP-Act-8(6)", 200),
    ("DPDP-Rule-8", "DPDP-Act-8(7)", 50),
    ("DPDP-Rule-9", "DPDP-Act-8(9)", 50),
    ("DPDP-Rule-10", "DPDP-Act-9", 200),
    ("DPDP-Rule-11", "DPDP-Act-9", 200),
    ("DPDP-Rule-12", "DPDP-Act-9", 200),
    ("DPDP-Rule-13", "DPDP-Act-10", 150),
    ("DPDP-Rule-14", "DPDP-Act-13", 50),
    ("DPDP-Rule-15", "DPDP-Act-16", 50),
    ("DPDP-Rule-16", "DPDP-Act-17", 50),
    ("DPDP-Rule-17", "DPDP-Act-27", 50),
    ("DPDP-Rule-18", "DPDP-Act-27", 50),
    ("DPDP-Rule-19", "DPDP-Act-27", 50),
    ("DPDP-Rule-20", "DPDP-Act-27", 50),
    ("DPDP-Rule-21", "DPDP-Act-27", 50),
    ("DPDP-Rule-22", "DPDP-Act-33", 50),
    ("DPDP-Rule-23", "DPDP-Act-36", 50),
]

RULE_COMMENCEMENT = {
    **{f"DPDP-Rule-{n}": EARLY for n in (1, 2, 17, 18, 19, 20, 21)},
    "DPDP-Rule-4": ONE_YEAR,
    **{f"DPDP-Rule-{n}": EIGHTEEN_MONTHS for n in (3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 22, 23)},
}

SCHEDULE_MAP = {
    "DPDP-Rules-Schedule-First": ("DPDP-Act-6", 50, ONE_YEAR),
    "DPDP-Rules-Schedule-Second": ("DPDP-Act-17", 50, EIGHTEEN_MONTHS),
    "DPDP-Rules-Schedule-Third": ("DPDP-Act-8(7)", 50, EIGHTEEN_MONTHS),
    "DPDP-Rules-Schedule-Fourth": ("DPDP-Act-9", 200, EIGHTEEN_MONTHS),
    "DPDP-Rules-Schedule-Fifth": ("DPDP-Act-27", 50, EARLY),
    "DPDP-Rules-Schedule-Sixth": ("DPDP-Act-27", 50, EARLY),
    "DPDP-Rules-Schedule-Seventh": ("DPDP-Act-36", 50, EIGHTEEN_MONTHS),
}

CWE_IDS = {f"CWE-{n}" for n in (209, 213, 250, 311, 319, 489, 532, 598, 614, 639, 798, 916, 922, 942)}
ALLIED_IDS = {"Aadhaar-Act-29", "Aadhaar-SIR-2016", "ITAct-43A", "OWASP-API1-2023", "OWASP-API3-2023"}


def _entry(**overrides: object) -> dict:
    base: dict = {
        "id": "CWE-1",
        "instrument": "CWE",
        "kind": "cwe",
        "citation": "CWE-1",
        "title": "Synthetic",
        "excerpt": "Synthetic excerpt.",
        "parent": None,
        "penalty_parent": None,
        "penalty_ceiling_inr_crore": None,
        "enforceable_from": None,
        "enforceable_basis": None,
        "source": {"document": "Synthetic", "url": "https://example.test/x"},
        "verified": False,
    }
    base.update(overrides)
    return base


def _dpdp(**overrides: object) -> dict:
    base = _entry(
        id="DPDP-Act-5",
        instrument="DPDP Act 2023",
        kind="dpdp-act",
        citation="Section 5",
        penalty_parent="DPDP-Act-Schedule",
        penalty_ceiling_inr_crore=50,
        enforceable_from=EIGHTEEN_MONTHS,
        enforceable_basis="Synthetic basis",
    )
    base.update(overrides)
    return base


def _schedule() -> dict:
    return _dpdp(
        id="DPDP-Act-Schedule",
        citation="Schedule",
        penalty_parent=None,
        penalty_ceiling_inr_crore=None,
    )


def _docs(*entries: dict) -> dict[str, str]:
    return {"synthetic.yaml": yaml.safe_dump(list(entries))}


def test_build_registry_indexes_valid_entries():
    registry = build_registry(_docs(_schedule(), _dpdp()))
    assert set(registry) == {"DPDP-Act-Schedule", "DPDP-Act-5"}
    assert isinstance(registry["DPDP-Act-5"], Provision)
    assert registry["DPDP-Act-5"].penalty_parent == "DPDP-Act-Schedule"
    assert registry["DPDP-Act-5"].enforceable_from == EIGHTEEN_MONTHS


def test_duplicate_ids_rejected_across_files():
    docs = {"a.yaml": yaml.safe_dump([_entry()]), "b.yaml": yaml.safe_dump([_entry()])}
    with pytest.raises(ValueError, match="duplicate provision id 'CWE-1'"):
        build_registry(docs)


def test_unresolved_parent_rejected():
    entry = _dpdp(id="DPDP-Rule-2", instrument="DPDP Rules 2025", kind="dpdp-rule", parent="DPDP-Rule-9")
    with pytest.raises(ValueError, match="parent 'DPDP-Rule-9' does not resolve"):
        build_registry(_docs(_schedule(), entry))


def test_unresolved_penalty_parent_rejected():
    with pytest.raises(ValueError, match="penalty_parent 'DPDP-Act-404' does not resolve"):
        build_registry(_docs(_dpdp(penalty_parent="DPDP-Act-404")))


def test_ceiling_must_be_a_contract_value():
    with pytest.raises(ValueError, match="penalty_ceiling_inr_crore 100 is not one of"):
        build_registry(_docs(_schedule(), _dpdp(penalty_ceiling_inr_crore=100)))


def test_dpdp_entry_needs_commencement():
    with pytest.raises(ValueError, match="need enforceable_from"):
        build_registry(_docs(_dpdp(enforceable_from=None)))


def test_dpdp_ceiling_required_except_section_15_and_schedule():
    with pytest.raises(ValueError, match="penalty_ceiling_inr_crore is required"):
        build_registry(_docs(_schedule(), _dpdp(penalty_ceiling_inr_crore=None)))
    with pytest.raises(ValueError, match="penalty_parent is required when a ceiling applies"):
        build_registry(_docs(_schedule(), _dpdp(penalty_parent=None)))
    build_registry(_docs(_schedule(), _dpdp(id="DPDP-Act-15", penalty_parent=None, penalty_ceiling_inr_crore=None)))


def test_non_dpdp_entries_must_not_carry_dpdp_fields():
    with pytest.raises(ValueError, match="penalty_ceiling_inr_crore must be null"):
        build_registry(_docs(_entry(penalty_ceiling_inr_crore=50)))
    with pytest.raises(ValueError, match="enforceable_from must be null"):
        build_registry(_docs(_entry(enforceable_from=EIGHTEEN_MONTHS)))


def test_unknown_instrument_kind_and_missing_fields_rejected():
    with pytest.raises(ValueError, match="unknown instrument 'Made Up'"):
        build_registry(_docs(_entry(instrument="Made Up")))
    with pytest.raises(ValueError, match="unknown kind 'weird'"):
        build_registry(_docs(_entry(kind="weird")))
    entry = _entry()
    del entry["title"]
    with pytest.raises(ValueError, match="missing fields"):
        build_registry(_docs(entry))


def test_provision_is_frozen():
    provision = build_registry(_docs(_entry()))["CWE-1"]
    with pytest.raises(dataclasses.FrozenInstanceError):
        provision.title = "changed"  # type: ignore[misc]


def test_shipped_rules_file_has_54_entries():
    rules = [p for p in load_registry().values() if p.instrument == "DPDP Rules 2025"]
    assert len(rules) == 54


@pytest.mark.parametrize(("rule_id", "penalty_parent", "ceiling"), RULE_PENALTY)
def test_rule_penalty_mapping(rule_id, penalty_parent, ceiling):
    provision = get(rule_id)
    assert provision.penalty_parent == penalty_parent
    assert provision.penalty_ceiling_inr_crore == ceiling


@pytest.mark.parametrize(("rule_id", "enforceable_from"), sorted(RULE_COMMENCEMENT.items()))
def test_rule_commencement(rule_id, enforceable_from):
    assert get(rule_id).enforceable_from == enforceable_from


@pytest.mark.parametrize(
    ("schedule_id", "penalty_parent", "ceiling", "enforceable_from"),
    [(key, *value) for key, value in SCHEDULE_MAP.items()],
)
def test_rule_schedules(schedule_id, penalty_parent, ceiling, enforceable_from):
    provision = get(schedule_id)
    assert provision.penalty_parent == penalty_parent
    assert provision.penalty_ceiling_inr_crore == ceiling
    assert provision.enforceable_from == enforceable_from


def test_rule_6_1_e_maps_to_section_8_5_at_250_crore():
    provision = get("DPDP-Rule-6(1)(e)")
    assert provision.parent == "DPDP-Rule-6(1)"
    assert provision.penalty_parent == "DPDP-Act-8(5)"
    assert provision.penalty_ceiling_inr_crore == 250
    assert provision.enforceable_from == EIGHTEEN_MONTHS


def test_rule_subunits_share_parent_penalty_mapping():
    registry = load_registry()
    for provision in registry.values():
        if provision.instrument == "DPDP Rules 2025" and provision.parent is not None:
            parent = registry[provision.parent]
            assert provision.penalty_parent == parent.penalty_parent, provision.id
            assert provision.penalty_ceiling_inr_crore == parent.penalty_ceiling_inr_crore, provision.id


@pytest.mark.parametrize(
    ("act_id", "ceiling"),
    [("DPDP-Act-9(1)", 200), ("DPDP-Act-10", 150), ("DPDP-Act-6(4)", 50)],
)
def test_act_ceilings(act_id, ceiling):
    assert get(act_id).penalty_ceiling_inr_crore == ceiling


def test_section_15_has_no_crore_ceiling():
    assert get("DPDP-Act-15").penalty_ceiling_inr_crore is None


def test_allied_and_cwe_entries_are_present():
    assert ALLIED_IDS | CWE_IDS <= set(load_registry())


def test_excerpt_status_matches_verified_flag():
    for provision in load_registry().values():
        if provision.kind not in {"dpdp-rule", "allied", "cwe", "owasp"}:
            continue
        assert len(provision.excerpt) <= 500, provision.id
        if provision.verified:
            assert not provision.excerpt.startswith("NOT "), provision.id
        else:
            assert provision.excerpt.startswith("NOT "), provision.id


def test_shipped_rules_are_transcribed_and_links_resolve():
    registry = load_registry()
    rules = [p for p in registry.values() if p.instrument == "DPDP Rules 2025"]
    assert all(p.verified and not p.excerpt.startswith("NOT ") for p in rules)
    for rule in rules:
        assert rule.parent is None or rule.parent in registry
        assert rule.penalty_parent in registry
    assert registry["DPDP-Rule-6(1)(f)"].excerpt.startswith("(f) appropriate provision in the contract")
    assert "technical and organisational measures" in registry["DPDP-Rule-6(1)(g)"].excerpt


def test_schedule_excerpts_separate_breach_from_penalty():
    for n in range(1, 8):
        assert " … " in get(f"DPDP-Act-Schedule-{n}").excerpt


def test_verified_rule_13_text_is_verbatim():
    rule_13 = get("DPDP-Rule-13")
    rule_13_4 = get("DPDP-Rule-13(4)")
    assert rule_13.verified and rule_13_4.verified
    assert "shall, once in every period of twelve months" in rule_13.excerpt
    assert "not transferred outside the territory of India" in rule_13_4.excerpt


def test_get_unknown_id_raises_keyerror():
    with pytest.raises(KeyError, match="unknown provision id"):
        get("DPDP-Act-999")


def test_load_registry_is_cached():
    assert load_registry() is load_registry()
