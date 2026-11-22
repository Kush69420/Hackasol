"""Personal Data Map: every classified Personal Data Element and its evidenced Processing Operations."""

from __future__ import annotations

from pathlib import Path

from auditor.evidence import evidence

# Element kinds that are declarations of where a Data Principal's Personal Data is held or
# collected. Other kinds (config values, which in practice are seed/demo data) are mapped
# only when an operation on them is evidenced.
DECLARED_KINDS = {"model-field", "collection-field", "form-input", "route-param", "storage-key", "header"}


def _key(coord: dict) -> tuple[str, int, int]:
    return coord["file"], coord["start_line"], coord["end_line"]


def build_personal_data_map(root: Path, elements: list[dict], flows: list[dict],
                            steps: list[dict]) -> tuple[list[dict], dict[str, list[dict]]]:
    """Return (schema ``personal_data_map`` entries, ordered steps per Element id).

    ``flows`` are ordered cross-file Data Flows; ``steps`` are extra operation steps
    (Semgrep, configuration) appended after the flow's own steps. A form input whose
    declaration is already a step of a model Element's flow is not mapped twice.
    """
    by_id = {e["id"]: e for e in elements if e["data_category"]}
    ordered: dict[str, list[dict]] = {}
    for flow in flows:
        if flow["element_id"] in by_id:
            ordered.setdefault(flow["element_id"], []).extend(flow["steps"])
    for step in steps:
        if step["element_id"] in by_id:
            ordered.setdefault(step["element_id"], []).append(step)

    covered = {_key(s["source"]) for eid, ss in ordered.items() for s in ss
               if by_id[eid]["kind"] == "model-field"}
    entries = []
    for eid, element in by_id.items():
        own = ordered.get(eid, [])
        if element["kind"] not in DECLARED_KINDS and not own:
            continue
        if element["kind"] == "form-input" and not own and _key(element["source"]) in covered:
            continue
        seen: set[tuple] = set()
        operations = []
        for step in own:
            k = (step["operation"], *_key(step["source"]))
            if k in seen:
                continue
            seen.add(k)
            note = f"{step['stage']}; {step['origin']}; {step['relation']}"
            if step.get("note"):
                note += f"; {step['note']}"
            operations.append({"operation": step["operation"], "evidence": evidence(root, step["source"]),
                               "note": note})
        entries.append({
            "element": {"name": eid, "data_category": element["data_category"],
                        "evidence": evidence(root, element["source"])},
            "operations": operations,
        })
    entries.sort(key=lambda e: (e["element"]["evidence"]["file"], e["element"]["evidence"]["start_line"],
                                e["element"]["name"]))
    return entries, ordered
