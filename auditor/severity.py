"""Severity for Findings: CVSS 4.0 bands, Risk Matrix cells, and report order.

ADR 0002 (docs/adr/0002-severity-model.md) sets the rules. A technical Finding's band comes
from its CVSS 4.0 score, and its Data Category sets the Environmental Confidentiality
Requirement (CR). A Compliance Gap has no CVSS score, so its band is its Risk Matrix cell.
A Disclosure Finding's band is its Risk Matrix cell capped at Medium. The Risk Matrix and
Penalty Ceiling only order Findings within a band.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable, Mapping
from typing import Any

import cvss

logger = logging.getLogger(__name__)

CLASSIFICATIONS = ("technical", "compliance-gap", "disclosure")

# Data Category -> Risk Matrix tier.
TIER_BY_CATEGORY = {
    "Government Identifier": "A",
    "Biometric": "A",
    "Financial": "A",
    "Health": "A",
    "Child Data": "A",
    "Authentication Secret": "B",
    "Contact": "C",
    "Profile": "C",
}

# Data Category -> Environmental Confidentiality Requirement.
CR_BY_CATEGORY = {
    "Government Identifier": "H",
    "Biometric": "H",
    "Financial": "H",
    "Health": "H",
    "Child Data": "H",
    "Authentication Secret": "M",
    "Contact": "M",
    "Profile": "L",
}

# Tier -> Exposure -> band.
RISK_MATRIX = {
    "A": {
        "Public": "critical",
        "Cross-Border": "critical",
        "Third-Party": "critical",
        "Internal-Broad": "high",
        "Internal-Restricted": "medium",
    },
    "B": {
        "Public": "critical",
        "Cross-Border": "high",
        "Third-Party": "high",
        "Internal-Broad": "high",
        "Internal-Restricted": "medium",
    },
    "C": {
        "Public": "high",
        "Cross-Border": "medium",
        "Third-Party": "medium",
        "Internal-Broad": "medium",
        "Internal-Restricted": "low",
    },
}

# A Disclosure Finding's band is never above this.
DISCLOSURE_CAP = "medium"

# Sort ranks: a lower rank sorts first.
CATEGORY_RANK = {  # most to least sensitive, in the order CONTEXT.md lists them
    "Government Identifier": 0,
    "Biometric": 1,
    "Financial": 2,
    "Health": 3,
    "Child Data": 4,
    "Authentication Secret": 5,
    "Contact": 6,
    "Profile": 7,
}
EXPOSURE_RANK = {  # most to least exposed
    "Public": 0,
    "Cross-Border": 1,
    "Third-Party": 2,
    "Internal-Broad": 3,
    "Internal-Restricted": 4,
}
BAND_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}

# CVSS 4.0 base metrics only. Callers never supply CR; score_cvss adds it.
_BASE_VECTOR = re.compile(
    r"CVSS:4\.0/AV:[NALP]/AC:[LH]/AT:[NP]/PR:[NLH]/UI:[NPA]"
    r"/VC:[HLN]/VI:[HLN]/VA:[HLN]/SC:[HLN]/SI:[HLN]/SA:[HLN]"
)


def _tier_for(category: str) -> str:
    if category not in TIER_BY_CATEGORY:
        raise ValueError(f"unknown Data Category: {category!r}")
    return TIER_BY_CATEGORY[category]


def score_cvss(base_vector: str, category: str) -> dict[str, Any]:
    """Score a CVSS 4.0 base vector with the CR that the Data Category sets.

    CR is always written into the vector so anyone can reproduce the score in the FIRST
    calculator. CVSS 4.0 treats a missing CR as High, so omitting it would score a Profile
    as High.
    """
    if category not in CR_BY_CATEGORY:
        raise ValueError(f"unknown Data Category: {category!r}")
    if not _BASE_VECTOR.fullmatch(base_vector):
        raise ValueError(f"not a CVSS 4.0 base vector: {base_vector!r}")
    vector = f"{base_vector}/CR:{CR_BY_CATEGORY[category]}"
    return {"status": "scored", "vector": vector, "score": cvss.CVSS4(vector).scores()[0]}


def band_for_score(score: float) -> str:
    """Map a CVSS 4.0 score to a Severity band using the FIRST qualitative ratings.

    The CVSS rating None (0.0) has no band in the schema, so it is banded low.
    """
    if not 0.0 <= score <= 10.0:
        raise ValueError(f"CVSS score out of range: {score!r}")
    if score < 4.0:
        return "low"
    if score < 7.0:
        return "medium"
    if score < 9.0:
        return "high"
    return "critical"


def assess(
    classification: str,
    base_vector: str | None,
    category: str,
    exposure: str,
) -> tuple[dict[str, Any], dict[str, str], str]:
    """Return (cvss, risk_matrix, band) for one Finding.

    base_vector is the CVSS 4.0 base vector of a technical Finding and None otherwise.
    """
    if classification not in CLASSIFICATIONS:
        raise ValueError(f"unknown classification: {classification!r}")
    tier = _tier_for(category)
    if exposure not in EXPOSURE_RANK:
        raise ValueError(f"unknown Exposure level: {exposure!r}")
    cell = RISK_MATRIX[tier][exposure]
    risk_matrix = {"tier": tier, "exposure": exposure, "cell": cell}

    if classification == "technical":
        if base_vector is None:
            raise ValueError("technical Finding needs a CVSS base vector")
        cvss_field = score_cvss(base_vector, category)
        if cvss_field["score"] == 0.0:
            logger.warning(
                "CVSS score 0.0 has no Severity band, so it is banded low: %s",
                cvss_field["vector"],
            )
        return cvss_field, risk_matrix, band_for_score(cvss_field["score"])

    if base_vector is not None:
        raise ValueError(f"{classification} Finding must not carry a CVSS base vector")
    if classification == "compliance-gap":
        reason = "Compliance Gap: no CVSS score, so the band is the Risk Matrix cell"
        return {"status": "n/a", "reason": reason}, risk_matrix, cell
    reason = "Disclosure Finding: processing presumed lawful, owed to the Data Principal"
    band = max(cell, DISCLOSURE_CAP, key=BAND_RANK.__getitem__)
    return {"status": "n/a", "reason": reason}, risk_matrix, band


def highest_category(categories: Iterable[str]) -> str:
    """Return the most sensitive Data Category given.

    ADR 0002: a Finding with no single Personal Data Element takes the highest Data Category
    among the Elements the weakened resource protects.
    """
    present = list(categories)
    if not present:
        raise ValueError("no Data Category given")
    for category in present:
        if category not in CATEGORY_RANK:
            raise ValueError(f"unknown Data Category: {category!r}")
    return min(present, key=CATEGORY_RANK.__getitem__)


def sort_key(finding: Mapping[str, Any]) -> tuple[int, int, int, int, str]:
    """Order Findings by band, Risk Matrix cell, Exposure, Penalty Ceiling (larger first), id.

    enforceable_from does not affect the order.
    """
    matrix = finding["risk_matrix"]
    return (
        BAND_RANK[finding["severity"]["band"]],
        BAND_RANK[matrix["cell"]],
        EXPOSURE_RANK[matrix["exposure"]],
        -finding["penalty_ceiling"]["amount_inr_crore"],
        finding["id"],
    )
