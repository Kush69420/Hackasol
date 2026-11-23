"""Derived legal view of a Report: Penalty Ceilings per Provision and an Enforceable From timeline.

Pure derivation from the Report's Findings and the Provision registry; it never
changes a Finding. Penalty Ceilings are per breach instance, so they are never
summed: the headline considers only applicable Primary Provisions.
"""
from __future__ import annotations

import datetime as dt
from collections import Counter

SECTION_TITLE = "Statutory Penalty Ceilings and Enforcement Timeline"
BANDS = ("critical", "high", "medium", "low")
CEILING_NOTE = (
    "Statutory maximum per Schedule; not a predicted or estimated fine. The actual penalty is "
    "determined by the Data Protection Board under section 33(2) factors. Ceilings apply per breach "
    "instance and are never added together. Under the Report's Applicability Assumptions, only "
    "applicable Primary Provisions contribute to the highest ceiling. Related and conditional "
    "Provisions and Findings that need legal review do not contribute."
)
SECTION_33_2 = "DPDP-Act-33(2)"
APPLICABILITY_LABELS = {
    "applicable_primary": "Applicable Primary Provision",
    "related": "Related Provision",
    "conditional": "Conditional Provision",
    "needs_legal_review": "Needs Legal Review (breach not established)",
}
# AA-3 excludes Third Schedule classes. Rule 8(3), unlike 8(1) and (2), is not limited to them.
THIRD_SCHEDULE_DUTIES = {"DPDP-Rule-8", "DPDP-Rule-8(1)", "DPDP-Rule-8(2)", "DPDP-Rules-Schedule-Third"}


def scan_date(report: dict) -> dt.date:
    """The date of the scan, taken from the Report; the reference for days-until."""
    return dt.datetime.fromisoformat(report["scan"]["finished_at"]).date()


def _schedule_entries(registry) -> dict:
    """Map a penalty parent (the section a Schedule item governs) to its Schedule item."""
    items = {}
    for pid, entry in registry.items():
        if pid.startswith("DPDP-Act-Schedule-") and entry.penalty_parent:
            items[entry.penalty_parent] = entry
    return items


def _schedule_entry(provision, registry, items):
    if provision.penalty_parent is None:
        return None
    return items.get(provision.penalty_parent) or registry.get("DPDP-Act-Schedule-7")


def _citation_applicability(provision, finding: dict) -> str:
    # AA-2 excludes Significant Data Fiduciaries, including duties under Rule 13.
    if provision.penalty_parent == "DPDP-Act-10" or provision.id in THIRD_SCHEDULE_DUTIES:
        return "conditional"
    if provision.id != finding["primary_provision"]:
        return "related"
    return {
        "open": "applicable_primary",
        "needs-legal-review": "needs_legal_review",
        "conditional": "conditional",
    }[finding["status"]]


def ceiling_rows(report: dict, registry) -> list[dict]:
    """One row per DPDP Provision cited by a Finding, ordered by ceiling then Provision."""
    items = _schedule_entries(registry)
    cited: dict[str, list[dict]] = {}
    for finding in report["findings"]:
        for pid in dict.fromkeys((finding["primary_provision"], *finding["other_provisions"])):
            cited.setdefault(pid, []).append(finding)
    rows = []
    for pid, findings in cited.items():
        provision = registry.get(pid)
        if provision is None or provision.enforceable_from is None:
            continue  # allied law (CWE/OWASP/Aadhaar/IT Act) carries no DPDP Schedule entry
        schedule = _schedule_entry(provision, registry, items)
        mix = Counter(f["severity"]["band"] for f in findings)
        by_applicability: dict[str, list[str]] = {key: [] for key in APPLICABILITY_LABELS}
        for finding in findings:
            by_applicability[_citation_applicability(provision, finding)].append(finding["id"])
        rows.append({
            "provision": pid,
            "citation": provision.citation,
            "schedule_entry": schedule.citation if schedule else None,
            "schedule_provision": schedule.id if schedule else None,
            "statutory_maximum_inr_crore": provision.penalty_ceiling_inr_crore,
            "statutory_maximum_text": (None if provision.penalty_ceiling_inr_crore is not None
                                       else (schedule.excerpt.split("… ")[-1] if schedule else None)),
            "finding_ids": [f["id"] for f in findings],
            "finding_ids_by_applicability": by_applicability,
            "severity_mix": {band: mix[band] for band in BANDS},
        })
    rows.sort(key=lambda r: (-(r["statutory_maximum_inr_crore"] or 0), r["provision"]))
    return rows


def highest_applicable_ceiling(rows: list[dict]) -> dict | None:
    """The single highest ceiling and the Provisions that reach it; deliberately not a sum."""
    eligible = [r for r in rows if r["statutory_maximum_inr_crore"] is not None
                and r["finding_ids_by_applicability"]["applicable_primary"]]
    if not eligible:
        return None
    top = max(r["statutory_maximum_inr_crore"] for r in eligible)
    highest = [r for r in eligible if r["statutory_maximum_inr_crore"] == top]
    return {"amount_inr_crore": top,
            "provisions": [r["provision"] for r in highest],
            "finding_ids": sorted({fid for r in highest
                                   for fid in r["finding_ids_by_applicability"]["applicable_primary"]})}


def timeline(report: dict, registry, as_of: dt.date) -> list[dict]:
    """Group Findings into phases by Enforceable From, earliest first."""
    phases: dict[dt.date, dict] = {}
    for finding in report["findings"]:
        date = dt.date.fromisoformat(finding["enforceable_from"])
        phase = phases.setdefault(date, {"enforceable_from": date.isoformat(), "finding_ids": [],
                                         "basis": None})
        phase["finding_ids"].append(finding["id"])
        if phase["basis"] is None:
            primary = registry.get(finding["primary_provision"])
            phase["basis"] = primary.enforceable_basis if primary else None
    result = []
    for date in sorted(phases):
        days = (date - as_of).days
        result.append({**phases[date], "days_until": days, "already_enforceable": days <= 0})
    return result


def legal_view(report: dict, registry, *, as_of: dt.date | None = None) -> dict:
    """The derived view. `as_of` defaults to the scan date recorded in the Report."""
    as_of = as_of or scan_date(report)
    rows = ceiling_rows(report, registry)
    return {
        "as_of": as_of.isoformat(),
        "title": SECTION_TITLE,
        "note": CEILING_NOTE,
        "section_33_2": SECTION_33_2,
        "ceilings": rows,
        "highest_applicable_ceiling": highest_applicable_ceiling(rows),
        "timeline": timeline(report, registry, as_of),
    }


def _amount(row: dict) -> str:
    if row["statutory_maximum_inr_crore"] is not None:
        return f"₹{row['statutory_maximum_inr_crore']} crore"
    return row["statutory_maximum_text"] or "no fixed figure"


def report_blocks(report: dict, registry) -> list[tuple]:
    """Display blocks for the Report renderers (same shape as report._sections blocks)."""
    view = legal_view(report, registry)
    blocks: list[tuple] = [("p", view["note"])]
    top = view["highest_applicable_ceiling"]
    blocks.append(("p", "Highest applicable ceiling: "
                   + (f"₹{top['amount_inr_crore']} crore ({', '.join(top['provisions'])})" if top else "none")
                   + ". Ceilings are not summed into a total exposure figure."))
    blocks.append(("table", (["Provision", "Schedule entry", "Statutory maximum", "Finding applicability", "Severity mix"],
                              [[r["provision"], r["schedule_entry"] or "none", _amount(r),
                                "; ".join(f"{label}: {', '.join(ids)}"
                                          for key, label in APPLICABILITY_LABELS.items()
                                          if (ids := r["finding_ids_by_applicability"][key])),
                                ", ".join(f"{b}: {n}" for b, n in r["severity_mix"].items() if n)]
                               for r in view["ceilings"]])))
    blocks.append(("h", f"Enforcement timeline (days relative to scan date {view['as_of']})"))
    blocks.append(("table", (["Enforceable From", "Status", "Findings"],
                              [[p["enforceable_from"],
                                "already enforceable" if p["already_enforceable"]
                                else f"enforceable in {p['days_until']} days",
                                ", ".join(p["finding_ids"])] for p in view["timeline"]])))
    return blocks
