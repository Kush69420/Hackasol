"""Tests for auditor.severity: ADR 0002 tables, CVSS 4.0 scores, and report order."""

import logging

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from auditor import severity
from auditor.schema import report_schema

SCHEMA = report_schema()
DEFS = SCHEMA["$defs"]

# CVSS 4.0 base score 8.7; CR:H leaves it unchanged.
BASE = "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N"
ZERO = "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:N/VI:N/VA:N/SC:N/SI:N/SA:N"

EXPOSURES = ("Public", "Cross-Border", "Third-Party", "Internal-Broad", "Internal-Restricted")

# ADR 0002 Risk Matrix: one row per tier, bands in EXPOSURES order.
ADR_ROWS = {
    "A": ("critical", "critical", "critical", "high", "medium"),
    "B": ("critical", "high", "high", "high", "medium"),
    "C": ("high", "medium", "medium", "medium", "low"),
}
ADR_CELL = {
    (tier, exposure): band
    for tier, row in ADR_ROWS.items()
    for exposure, band in zip(EXPOSURES, row)
}
ADR_CELLS = [(tier, exposure, band) for (tier, exposure), band in ADR_CELL.items()]

# ADR 0002 tier and Environmental Confidentiality Requirement for each Data Category.
ADR_TIER = {
    "Government Identifier": "A",
    "Biometric": "A",
    "Financial": "A",
    "Health": "A",
    "Child Data": "A",
    "Authentication Secret": "B",
    "Contact": "C",
    "Profile": "C",
}
ADR_CR = {
    "Government Identifier": "H",
    "Biometric": "H",
    "Financial": "H",
    "Health": "H",
    "Child Data": "H",
    "Authentication Secret": "M",
    "Contact": "M",
    "Profile": "L",
}
REPRESENTATIVE = {"A": "Government Identifier", "B": "Authentication Secret", "C": "Profile"}

# CVSS v4.0 examples from FIRST (v1.9): name, base vector, published base score.
FIRST_EXAMPLES = (
    ("CVE-2022-26134", "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N", 9.3),
    ("CVE-2022-41741", "CVSS:4.0/AV:L/AC:L/AT:P/PR:L/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N", 7.3),
    ("CVE-2020-3549", "CVSS:4.0/AV:N/AC:L/AT:P/PR:N/UI:P/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N", 7.7),
    ("CVE-2023-3089", "CVSS:4.0/AV:N/AC:L/AT:P/PR:N/UI:N/VC:H/VI:L/VA:L/SC:N/SI:N/SA:N", 8.3),
    ("CVE-2021-44714", "CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:A/VC:L/VI:N/VA:N/SC:N/SI:N/SA:N", 4.6),
    ("CVE-2022-21830", "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:A/VC:N/VI:N/VA:N/SC:L/SI:L/SA:N", 5.1),
    ("CVE-2022-22186", "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:N/VI:N/VA:N/SC:L/SI:L/SA:N", 6.9),
    ("CVE-2023-21989", "CVSS:4.0/AV:L/AC:L/AT:N/PR:H/UI:N/VC:N/VI:N/VA:N/SC:H/SI:N/SA:N", 5.9),
    ("CVE-2020-3947", "CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:H/SI:H/SA:H", 9.4),
    ("unnamed-row-6.4", "CVSS:4.0/AV:A/AC:L/AT:N/PR:N/UI:N/VC:N/VI:L/VA:N/SC:H/SI:N/SA:H", 6.4),
    ("unnamed-row-10.0", "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:H/SI:H/SA:H", 10.0),
)


def _validator(ref: str) -> Draft202012Validator:
    sub = {"$schema": SCHEMA["$schema"], "$defs": DEFS, "$ref": ref}
    return Draft202012Validator(sub, format_checker=FormatChecker())


def _finding(id_, band, cell, exposure, amount, **extra):
    return {
        "id": id_,
        "severity": {"band": band, "justification": "test"},
        "risk_matrix": {"tier": "A", "exposure": exposure, "cell": cell},
        "penalty_ceiling": {"parent_section": "s33", "amount_inr_crore": amount},
        **extra,
    }


def test_vocabularies_match_schema():
    categories = set(DEFS["dataCategory"]["enum"])
    assert set(severity.TIER_BY_CATEGORY) == categories
    assert set(severity.CR_BY_CATEGORY) == categories
    assert set(severity.CATEGORY_RANK) == categories
    exposures = set(DEFS["exposureLevel"]["enum"])
    assert set(severity.EXPOSURE_RANK) == exposures
    assert set(severity.RISK_MATRIX) == {"A", "B", "C"}
    for tier in severity.RISK_MATRIX:
        assert set(severity.RISK_MATRIX[tier]) == exposures
    assert set(severity.BAND_RANK) == set(DEFS["band"]["enum"])
    classification = DEFS["finding"]["properties"]["classification"]["enum"]
    assert set(severity.CLASSIFICATIONS) == set(classification)


@pytest.mark.parametrize(("tier", "exposure", "band"), ADR_CELLS)
def test_compliance_gap_band_is_adr_cell(tier, exposure, band):
    cvss_field, risk_matrix, got = severity.assess(
        "compliance-gap", None, REPRESENTATIVE[tier], exposure
    )
    assert cvss_field["status"] == "n/a"
    assert risk_matrix == {"tier": tier, "exposure": exposure, "cell": band}
    assert got == band


@pytest.mark.parametrize(("tier", "exposure", "band"), ADR_CELLS)
def test_technical_finding_records_matrix_cell(tier, exposure, band):
    _, risk_matrix, _ = severity.assess("technical", BASE, REPRESENTATIVE[tier], exposure)
    assert risk_matrix == {"tier": tier, "exposure": exposure, "cell": band}


@pytest.mark.parametrize("exposure", EXPOSURES)
@pytest.mark.parametrize("category", list(ADR_TIER))
def test_category_and_exposure_resolve_to_adr_tier_and_cell(category, exposure):
    tier = ADR_TIER[category]
    _, risk_matrix, _ = severity.assess("compliance-gap", None, category, exposure)
    assert risk_matrix == {"tier": tier, "exposure": exposure, "cell": ADR_CELL[(tier, exposure)]}


@pytest.mark.parametrize("category", list(ADR_CR))
def test_vector_states_cr_for_category(category):
    assert severity.score_cvss(BASE, category)["vector"] == f"{BASE}/CR:{ADR_CR[category]}"


def test_cr_high_scores_above_low_on_same_base():
    high = severity.score_cvss(BASE, "Government Identifier")["score"]
    medium = severity.score_cvss(BASE, "Contact")["score"]
    low = severity.score_cvss(BASE, "Profile")["score"]
    assert high == pytest.approx(8.7)
    assert high > medium >= low


@pytest.mark.parametrize(
    "vector",
    [
        BASE + "/CR:H",
        BASE + "/E:P",
        BASE.replace("CVSS:4.0", "CVSS:4.1"),
        "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
        "AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N",
        "not a vector",
        "",
    ],
)
def test_score_cvss_rejects_non_base_vectors(vector):
    with pytest.raises(ValueError):
        severity.score_cvss(vector, "Profile")


def test_score_cvss_rejects_unknown_category():
    with pytest.raises(ValueError):
        severity.score_cvss(BASE, "Passport Number")


@pytest.mark.parametrize(
    ("vector", "published"),
    [(vector, published) for _, vector, published in FIRST_EXAMPLES],
    ids=[name for name, _, _ in FIRST_EXAMPLES],
)
def test_scores_match_first_examples(vector, published):
    # CR:H leaves the base score unchanged, so these match FIRST's published values.
    score = severity.score_cvss(vector, "Government Identifier")["score"]
    assert score == pytest.approx(published)


def test_low_band_scores_from_library_alone():
    # FIRST's examples publish no base score below 4.6, so this value comes from the library.
    vector = "CVSS:4.0/AV:L/AC:H/AT:P/PR:H/UI:A/VC:L/VI:N/VA:N/SC:N/SI:N/SA:N"
    score = severity.score_cvss(vector, "Government Identifier")["score"]
    assert score == pytest.approx(1.0)
    assert severity.band_for_score(score) == "low"


@pytest.mark.parametrize(
    ("vector", "band"),
    [
        ("CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N", "critical"),  # 9.3
        ("CVSS:4.0/AV:N/AC:L/AT:P/PR:N/UI:N/VC:H/VI:L/VA:L/SC:N/SI:N/SA:N", "high"),  # 8.3
        ("CVSS:4.0/AV:N/AC:L/AT:P/PR:N/UI:P/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N", "high"),  # 7.7
        ("CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:A/VC:L/VI:N/VA:N/SC:N/SI:N/SA:N", "medium"),  # 4.6
        ("CVSS:4.0/AV:A/AC:L/AT:N/PR:N/UI:N/VC:N/VI:L/VA:N/SC:H/SI:N/SA:H", "medium"),  # 6.4
    ],
)
def test_technical_band_follows_cvss_score(vector, band):
    cvss_field, _, got = severity.assess("technical", vector, "Government Identifier", "Public")
    assert cvss_field["vector"] == f"{vector}/CR:H"
    assert got == band


@pytest.mark.parametrize(
    ("score", "band"),
    [
        (0.0, "low"),
        (0.1, "low"),
        (3.9, "low"),
        (4.0, "medium"),
        (6.9, "medium"),
        (7.0, "high"),
        (8.9, "high"),
        (9.0, "critical"),
        (10.0, "critical"),
    ],
)
def test_band_for_score_boundaries(score, band):
    assert severity.band_for_score(score) == band


@pytest.mark.parametrize("score", [-0.1, 10.1])
def test_band_for_score_rejects_out_of_range(score):
    with pytest.raises(ValueError):
        severity.band_for_score(score)


def test_zero_score_bands_low_and_logs(caplog):
    with caplog.at_level(logging.WARNING, logger="auditor.severity"):
        cvss_field, _, band = severity.assess("technical", ZERO, "Government Identifier", "Public")
    assert cvss_field["score"] == 0.0
    assert band == "low"
    assert "banded low" in caplog.text


def test_compliance_gap_has_no_cvss_score_and_uses_matrix_band():
    cvss_field, risk_matrix, band = severity.assess("compliance-gap", None, "Profile", "Public")
    assert cvss_field["status"] == "n/a"
    assert cvss_field["reason"]
    assert risk_matrix["cell"] == "high"
    assert band == "high"


@pytest.mark.parametrize(
    ("category", "exposure", "cell", "band"),
    [
        ("Government Identifier", "Cross-Border", "critical", "medium"),
        ("Government Identifier", "Internal-Broad", "high", "medium"),
        ("Government Identifier", "Internal-Restricted", "medium", "medium"),
        ("Profile", "Public", "high", "medium"),
        ("Profile", "Internal-Restricted", "low", "low"),
    ],
)
def test_disclosure_band_is_matrix_cell_capped_at_medium(category, exposure, cell, band):
    cvss_field, risk_matrix, got = severity.assess("disclosure", None, category, exposure)
    assert cvss_field["status"] == "n/a"
    assert risk_matrix["cell"] == cell
    assert got == band


@pytest.mark.parametrize(
    ("classification", "vector", "category", "exposure"),
    [
        ("technical", None, "Profile", "Public"),
        ("compliance-gap", BASE, "Profile", "Public"),
        ("disclosure", BASE, "Profile", "Public"),
        ("gap", None, "Profile", "Public"),
        ("technical", BASE, "Passport Number", "Public"),
        ("compliance-gap", None, "Profile", "Nowhere"),
    ],
)
def test_assess_rejects_inconsistent_or_unknown_inputs(classification, vector, category, exposure):
    with pytest.raises(ValueError):
        severity.assess(classification, vector, category, exposure)


@pytest.mark.parametrize(
    ("classification", "vector", "category", "exposure"),
    [
        ("technical", BASE, "Government Identifier", "Public"),
        ("technical", ZERO, "Profile", "Internal-Restricted"),
        ("compliance-gap", None, "Authentication Secret", "Cross-Border"),
        ("disclosure", None, "Child Data", "Third-Party"),
    ],
)
def test_outputs_validate_against_schema(classification, vector, category, exposure):
    cvss_field, risk_matrix, band = severity.assess(classification, vector, category, exposure)
    _validator("#/$defs/finding/properties/cvss").validate(cvss_field)
    _validator("#/$defs/finding/properties/risk_matrix").validate(risk_matrix)
    _validator("#/$defs/band").validate(band)


@pytest.mark.parametrize(
    ("categories", "expected"),
    [
        (["Profile", "Health", "Contact"], "Health"),
        (["Authentication Secret", "Contact"], "Authentication Secret"),
        (["Child Data", "Financial"], "Financial"),
        (["Profile"], "Profile"),
    ],
)
def test_highest_category_follows_sensitivity_order(categories, expected):
    assert severity.highest_category(categories) == expected


def test_highest_category_rejects_empty_and_unknown():
    with pytest.raises(ValueError):
        severity.highest_category([])
    with pytest.raises(ValueError):
        severity.highest_category(["Profile", "Passport Number"])


def test_sort_key_orders_by_band_cell_exposure_penalty_then_id():
    findings = [
        _finding("F-g", "medium", "low", "Internal-Restricted", 50),
        _finding("F-d", "high", "critical", "Public", 250),
        _finding("F-c", "critical", "critical", "Third-Party", 250),
        _finding("F-f", "critical", "critical", "Public", 50),
        _finding("F-e", "critical", "high", "Public", 250),
        _finding("F-b", "critical", "critical", "Public", 250),
        _finding("F-a", "critical", "critical", "Public", 250),
    ]
    ordered = [f["id"] for f in sorted(findings, key=severity.sort_key)]
    assert ordered == ["F-a", "F-b", "F-f", "F-c", "F-e", "F-d", "F-g"]


def test_sort_key_ignores_enforceable_from():
    expected = ["F-2", "F-1"]  # larger Penalty Ceiling first
    plain = [
        _finding("F-1", "high", "high", "Public", 200),
        _finding("F-2", "high", "high", "Public", 250),
    ]
    dated = [
        _finding("F-1", "high", "high", "Public", 200, enforceable_from="2025-05-13"),
        _finding("F-2", "high", "high", "Public", 250, enforceable_from="2030-01-01"),
    ]
    assert [f["id"] for f in sorted(plain, key=severity.sort_key)] == expected
    assert [f["id"] for f in sorted(dated, key=severity.sort_key)] == expected
