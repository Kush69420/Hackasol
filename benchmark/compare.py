"""Benchmark step 2: compare Semgrep with the Auditor reports committed at HEAD.

Reads benchmark/results/ (written by run_semgrep.sh) and the Auditor reports at HEAD, scores both
against the Primary Target reference, and writes benchmark/results/summary.json. Markdown tables
go to stdout.

Usage: .venv/bin/python benchmark/compare.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from auditor.accuracy import REFERENCE_PATH, load_reference, score_findings  # noqa: E402
from auditor.exclusions import iter_target_files  # noqa: E402
from auditor.remediation import load_catalogue  # noqa: E402

RESULTS = ROOT / "benchmark" / "results"
TARGETS = ("juice-shop", "ai-kyc-platform", "trackmyrupee", "singharya-e-kyc")
PRIMARY_TARGET = "juice-shop"  # the only Target with a labelled reference
ANY_ISSUE_TYPE = "*"  # location-only scoring treats every Issue Type alike
CWE = re.compile(r"CWE-\d+")
CONSENT_OR_ERASURE = ("CON-", "RET-")
SEVERITY_ORDER = {"INFO": 0, "WARNING": 1, "ERROR": 2}  # other values, e.g. MEDIUM, rank below INFO


def worst(severities: list[str]) -> str:
    return max(severities, key=lambda s: SEVERITY_ORDER.get(s, -1))


def load_semgrep(target: str) -> dict:
    return json.loads((RESULTS / target / "semgrep.json").read_text(encoding="utf-8"))


def load_head_report(target: str) -> dict:
    """The Auditor report as committed at HEAD, so the comparison does not depend on the working tree."""
    text = subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:reports/{target}/report.json"],
                          capture_output=True, text=True, check=True).stdout
    return json.loads(text)


def span(file: str, start_line: int, end_line: int) -> dict:
    return {"file": file, "start_line": start_line, "end_line": end_line}


def overlaps(a: dict, b: dict) -> bool:
    return a["file"] == b["file"] and a["start_line"] <= b["end_line"] and b["start_line"] <= a["end_line"]


def finding_spans(finding: dict) -> list[dict]:
    return [span(e["file"], e["start_line"], e["end_line"]) for e in finding["evidence"]]


def cwe_index() -> dict[str, list[str]]:
    """CWE id -> Issue Type ids whose catalogue entry links to it. This is the only route from Semgrep to an Issue Type."""
    index: dict[str, list[str]] = defaultdict(list)
    for issue in load_catalogue().values():
        for ref in issue.related:
            if ref.startswith("CWE-"):
                index[ref].append(issue.id)
    return dict(index)


def semgrep_groups(raw: dict) -> list[dict]:
    """One group per (file, start line, end line): Semgrep rules firing on the same lines form one group."""
    grouped: dict[tuple[str, int, int], dict] = {}
    for result in raw["results"]:
        key = (result["path"], result["start"]["line"], result["end"]["line"])
        group = grouped.setdefault(key, {"rules": [], "cwes": set(), "severities": []})
        cwe = result["extra"].get("metadata", {}).get("cwe", [])
        group["rules"].append(result["check_id"])
        group["cwes"].update(CWE.findall(" ".join([cwe] if isinstance(cwe, str) else cwe)))
        group["severities"].append(result["extra"]["severity"])
    groups = [{"file": file, "start_line": start, "end_line": end, "rules": g["rules"],
               "cwes": sorted(g["cwes"]), "severity": worst(g["severities"])}
              for (file, start, end), g in grouped.items()]
    return sorted(groups, key=lambda g: (g["file"], g["start_line"], g["end_line"]))


def semgrep_predictions(groups: list[dict], index: dict[str, list[str]], *, location_only: bool) -> list[dict]:
    """CWE route: one prediction per Issue Type that a group's CWEs link to. Location only: one per group."""
    predictions = []
    for group in groups:
        where = span(group["file"], group["start_line"], group["end_line"])
        stem = f"SG {group['file']}:{group['start_line']}-{group['end_line']}"
        if location_only:
            predictions.append({"id": stem, "issue_type": ANY_ISSUE_TYPE, "evidence": [where]})
            continue
        for issue_type in sorted({t for cwe in group["cwes"] for t in index.get(cwe, [])}):
            predictions.append({"id": f"{stem} {issue_type}", "issue_type": issue_type, "evidence": [where]})
    return predictions


def auditor_predictions(report: dict, *, location_only: bool) -> list[dict]:
    return [{"id": f["id"], "issue_type": ANY_ISSUE_TYPE if location_only else f["issue_type"],
             "evidence": f["evidence"]} for f in report["findings"]]


def reference_variant(reference: dict, *, location_only: bool) -> dict:
    if not location_only:
        return reference
    return {**reference, "entries": [{**e, "issue_type": ANY_ISSUE_TYPE} for e in reference["entries"]]}


def score(predictions: list[dict], reference: dict) -> dict:
    result = score_findings(predictions, reference, reference_path=str(REFERENCE_PATH))
    return {"tp": result["tp"], "fp": result["fp"], "fn": result["fn"], "precision": result["precision"],
            "recall": result["recall"], "excluded": len(result["excluded_predictions"]),
            "matched": sorted(m["reference_id"] for m in result["matches"])}


def reference_scores(groups: list[dict], report: dict, reference: dict, index: dict[str, list[str]]) -> dict:
    out: dict[str, Any] = {
        "reference": str(REFERENCE_PATH),
        "confirmed_entries": sum(1 for e in reference["entries"] if e["status"] == "confirmed"),
        "excluded_entries": sum(1 for e in reference["entries"] if e["status"] != "confirmed"),
    }
    for mode, location_only in (("location_only", True), ("issue_type", False)):
        ref = reference_variant(reference, location_only=location_only)
        auditor = score(auditor_predictions(report, location_only=location_only), ref)
        semgrep = score(semgrep_predictions(groups, index, location_only=location_only), ref)
        out[mode] = {"auditor": auditor, "semgrep": semgrep,
                     "covered_only_by_semgrep": sorted(set(semgrep["matched"]) - set(auditor["matched"])),
                     "covered_only_by_auditor": sorted(set(auditor["matched"]) - set(semgrep["matched"]))}
    return out


def overlap_summary(groups: list[dict], report: dict) -> dict:
    spans = [s for f in report["findings"] for s in finding_spans(f)]
    return {
        "semgrep_groups": len(groups),
        "semgrep_groups_on_auditor_evidence": sum(1 for g in groups if any(overlaps(g, s) for s in spans)),
        "auditor_findings": len(report["findings"]),
        "auditor_findings_on_semgrep_groups": sum(
            1 for f in report["findings"] if any(overlaps(s, g) for s in finding_spans(f) for g in groups)),
    }


def severity_crosstab(groups: list[dict], report: dict) -> dict[str, dict[str, int]]:
    """Auditor Findings by band, against the highest Semgrep severity on the lines their Evidence covers."""
    table: dict[str, Counter] = defaultdict(Counter)
    for finding in report["findings"]:
        spans = finding_spans(finding)
        severities = [g["severity"] for g in groups if any(overlaps(g, s) for s in spans)]
        if severities:
            table[finding["severity"]["band"]][worst(severities)] += 1
    return {band: dict(counts) for band, counts in sorted(table.items())}


def foreign_paths(result: dict) -> set[str]:
    """Paths other than the result's own file that appear in its dataflow trace."""
    found: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "path" and isinstance(value, str):
                    found.add(value)
                else:
                    walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(result["extra"].get("dataflow_trace", {}))
    found.discard(result["path"])
    return found


def auditor_stats(report: dict) -> dict:
    findings = report["findings"]
    return {
        "findings": len(findings),
        "observations": len(report.get("observations", [])),
        "evidence_items": sum(len(f["evidence"]) for f in findings),
        "multi_file_findings": sum(1 for f in findings if len({e["file"] for e in f["evidence"]}) > 1),
        "bands": dict(Counter(f["severity"]["band"] for f in findings)),
        "justified": sum(1 for f in findings if f["severity"].get("justification")),
        "primary_provisions": dict(Counter(f["primary_provision"] for f in findings)),
        "consent_or_erasure": sum(1 for f in findings if f["issue_type"].startswith(CONSENT_OR_ERASURE)),
    }


def semgrep_stats(raw: dict, run_entry: dict, groups: list[dict], index: dict[str, list[str]],
                  predictions: list[dict], catalogue: dict) -> dict:
    results = raw["results"]
    return {
        "rules_run": run_entry["rules_run"],
        "files_scanned": run_entry["files_scanned"],
        "results": len(results),
        "groups": len(groups),
        "groups_with_cwe_link": sum(1 for g in groups if any(c in index for c in g["cwes"])),
        "severity": dict(Counter(r["extra"]["severity"] for r in results)),
        "engine_kind": dict(Counter(r["extra"].get("engine_kind", "unknown") for r in results)),
        "skipped": run_entry["skipped"],
        "errors": run_entry["errors"],
        "cross_file_results": sum(1 for r in results if foreign_paths(r)),
        "cwe_route_predictions": len(predictions),
        "primary_provisions": dict(Counter(catalogue[p["issue_type"]].primary for p in predictions)),
        "consent_or_erasure": sum(1 for p in predictions if p["issue_type"].startswith(CONSENT_OR_ERASURE)),
    }


def file_sets(target: str, raw: dict, head: dict) -> dict:
    checkout = ROOT / "targets" / target
    included, excluded = iter_target_files(checkout, target)
    auditor = {p.relative_to(checkout).as_posix() for p in included}
    semgrep = set(raw["paths"]["scanned"])
    return {"auditor_walker": len(auditor), "auditor_excluded": excluded,
            "auditor_head_report": head["scan"]["files_scanned"], "semgrep_scanned": len(semgrep),
            "both": len(auditor & semgrep), "auditor_only": len(auditor - semgrep),
            "semgrep_only": len(semgrep - auditor)}


def validate_provenance(target: str, run_entry: dict, report: dict, reference: dict) -> None:
    commit = run_entry.get("commit")
    if run_entry.get("dirty_checkout") is not False:
        raise ValueError(f"{target}: Semgrep checkout was dirty or its cleanliness is unknown")
    if not commit or commit != report.get("target", {}).get("commit"):
        raise ValueError(f"{target}: Semgrep checkout commit does not match Auditor report commit")
    if target == PRIMARY_TARGET and commit != reference.get("target", {}).get("commit"):
        raise ValueError(f"{target}: checkout commit does not match labelled reference pin")


def build_summary() -> dict:
    run = json.loads((RESULTS / "run.json").read_text(encoding="utf-8"))
    index = cwe_index()
    catalogue = load_catalogue()
    reference = load_reference(ROOT / REFERENCE_PATH)
    reports = {target: load_head_report(target) for target in TARGETS}
    for target in TARGETS:
        validate_provenance(target, run["targets"][target], reports[target], reference)
    summary: dict[str, Any] = {"format_version": 1, "semgrep_version": run["semgrep_version"],
                               "configs": run["configs"], "targets": {}, "primary_reference": {},
                               "catalogue_primary_provisions": len({i.primary for i in catalogue.values()})}
    for target in TARGETS:
        raw, head, run_entry = load_semgrep(target), reports[target], run["targets"][target]
        groups = semgrep_groups(raw)
        predictions = semgrep_predictions(groups, index, location_only=False)
        summary["targets"][target] = {
            "commit": run_entry["commit"],
            "commit_matches_head_report": run_entry["commit"] == head["target"]["commit"],
            "semgrep": semgrep_stats(raw, run_entry, groups, index, predictions, catalogue),
            "auditor": auditor_stats(head),
            "overlap": overlap_summary(groups, head),
            "severity_crosstab": severity_crosstab(groups, head),
            "file_sets": file_sets(target, raw, head),
        }
        if target == PRIMARY_TARGET:
            summary["primary_reference"] = reference_scores(groups, head, reference, index)
    return summary


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return "\n".join(lines)


def ratio_cell(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2f}"


def render(summary: dict) -> str:
    targets = summary["targets"]
    ref = summary["primary_reference"]
    sections = []

    sections.append("### Run provenance\n\n" + md_table(
        ["Target", "Commit = HEAD report", "Semgrep rules", "Semgrep files", "Semgrep results",
         "Semgrep groups", "Semgrep errors", "Auditor Findings", "Auditor Evidence items"],
        [[name, "yes" if t["commit_matches_head_report"] else "no", t["semgrep"]["rules_run"],
          t["semgrep"]["files_scanned"], t["semgrep"]["results"], t["semgrep"]["groups"],
          t["semgrep"]["errors"]["total"], t["auditor"]["findings"], t["auditor"]["evidence_items"]]
         for name, t in targets.items()]))

    rows = []
    for mode, label in (("location_only", "location only"), ("issue_type", "Issue Type and location")):
        for tool in ("auditor", "semgrep"):
            s = ref[mode][tool]
            rows.append([label, tool, s["tp"], s["fp"], s["fn"], s["excluded"], ratio_cell(s["precision"]),
                         ratio_cell(s["recall"])])
    sections.append(f"### Primary Target reference: {PRIMARY_TARGET} ({ref['confirmed_entries']} confirmed entries, "
                    f"{ref['excluded_entries']} not determinable)\n\n"
                    + md_table(["Scoring", "Tool", "TP", "FP", "FN", "Excluded", "Precision", "Recall"], rows))

    sections.append("### Overlap with Auditor Evidence (location only)\n\n" + md_table(
        ["Target", "Semgrep groups", "Groups on Auditor Evidence", "Auditor Findings",
         "Findings on Semgrep groups", "Semgrep cross-file results", "Auditor multi-file Findings"],
        [[name, t["overlap"]["semgrep_groups"], t["overlap"]["semgrep_groups_on_auditor_evidence"],
          t["overlap"]["auditor_findings"], t["overlap"]["auditor_findings_on_semgrep_groups"],
          t["semgrep"]["cross_file_results"], t["auditor"]["multi_file_findings"]]
         for name, t in targets.items()]))

    sections.append(f"### Primary Provisions and consent/erasure (catalogue has {summary['catalogue_primary_provisions']} "
                    "distinct Primary Provisions)\n\n" + md_table(
        ["Target", "Auditor Primary Provisions", "Semgrep Primary Provisions (CWE route)",
         "Auditor CON/RET Findings", "Semgrep CON/RET predictions (CWE route)"],
        [[name, len(t["auditor"]["primary_provisions"]), len(t["semgrep"]["primary_provisions"]),
          t["auditor"]["consent_or_erasure"], t["semgrep"]["consent_or_erasure"]]
         for name, t in targets.items()]))

    sections.append("### File sets\n\n" + md_table(
        ["Target", "Auditor walker files", "Auditor excluded", "Auditor HEAD report files", "Semgrep scanned",
         "Both", "Auditor only", "Semgrep only"],
        [[name, f["auditor_walker"], f["auditor_excluded"], f["auditor_head_report"], f["semgrep_scanned"],
          f["both"], f["auditor_only"], f["semgrep_only"]]
         for name, f in ((n, t["file_sets"]) for n, t in targets.items())]))

    cross: dict[str, Counter] = defaultdict(Counter)
    for t in targets.values():
        for band, counts in t["severity_crosstab"].items():
            cross[band].update(counts)
    observed = sorted({s for counts in cross.values() for s in counts},
                      key=lambda s: (s not in SEVERITY_ORDER, -SEVERITY_ORDER.get(s, 0), s))
    sections.append("### Auditor Findings by band against the highest overlapping Semgrep severity (all Targets)\n\n"
                    + md_table(["Auditor band", *observed],
                               [[band, *(cross[band][s] for s in observed)] for band in sorted(cross)]))
    return "\n\n".join(sections)


def main() -> None:
    summary = build_summary()
    path = RESULTS / "summary.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(render(summary))
    print(f"\nwrote {path}")


if __name__ == "__main__":
    main()
