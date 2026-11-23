"""Render the canonical Report without rescanning or changing engine assessments.

PDF generation requires WeasyPrint and its native Pango/font libraries. External
resources are disabled: Target Application text is never interpreted as markup.
"""
from __future__ import annotations

from collections import Counter
from html import escape
import json
import re
from pathlib import Path

from auditor import legal_view
from auditor.accuracy import ratio_text
from auditor.registry import load_registry
from auditor.remediation import load_catalogue


SECTIONS = ("Applicability Assumptions", "Executive summary", "Personal Data Map",
            "Findings", "Consent Assessment", "Coverage Matrix", legal_view.SECTION_TITLE,
            "Method, accuracy and limitations")
_NON_CODE = {"DPDP-Act-8(2)", "DPDP-Act-8(3)", "DPDP-Act-8(6)", "DPDP-Rule-7"}


def executive_summary(report: dict) -> dict:
    """Summarise engine values, without calculating or altering Severity."""
    findings = report["findings"]
    severities = Counter(f["severity"]["band"] for f in findings)
    kinds = Counter(f["kind"] for f in findings)
    ceilings = [f["penalty_ceiling"]["amount_inr_crore"] for f in findings]
    return {
        "counts_by_severity": {band: severities[band] for band in ("critical", "high", "medium", "low")},
        "counts_by_kind": {
            "DPDP obligation": kinds["dpdp-obligation"],
            "security dependent on Personal Data": kinds["security-personal-data"],
            "Safeguard": kinds["safeguard"],
        },
        "highest_penalty_ceiling_inr_crore": max(ceilings) if ceilings else None,
        "fix_before_13_may_2027": [f["id"] for f in findings if f["enforceable_from"] == "2027-05-13"],
        "penalty_note": "Penalty Ceilings are statutory maximums, not amounts imposed; the Data Protection Board determines the actual amount under section 33.",
    }


def coverage_matrix(registry, rules, not_determinable, findings) -> list[dict]:
    """Map statutory Provisions to Rules, retaining unresolved absence Gates.

    Coverage of a child Provision also covers its registered ancestors. A missing
    Finding is not evidence that a Gate was met or an obligation satisfied.
    """
    catalogue = load_catalogue()
    by_provision = {}
    capabilities = {}
    for issue in catalogue.values():
        for pid in (issue.primary, *issue.related):
            seen = set()
            while pid in registry and pid not in seen:
                seen.add(pid)
                capabilities.setdefault(pid, set()).update(issue.verify)
                pid = registry[pid].parent
    unresolved = {item["rule_id"] for item in not_determinable}
    fired = {rid for finding in findings for rid in finding["rules_fired"]}
    for rule_id, value in rules.items():
        spec = value[0] if isinstance(value, tuple) else value
        issue = catalogue[spec.issue_type]
        for pid in (issue.primary, *issue.related):
            seen = set()
            while pid in registry and pid not in seen:
                seen.add(pid)
                by_provision.setdefault(pid, {})[rule_id] = issue
                pid = registry[pid].parent
    matrix = []
    for pid, provision in registry.items():
        if provision.kind not in ("dpdp-act", "dpdp-rule"):
            continue
        covered = by_provision.get(pid, {})
        blocked = [rid for rid, issue in covered.items()
                   if rid in unresolved or (issue.gate and issue.gate != "nexus" and rid not in fired)]
        if any(pid == p or pid.startswith(p + "(") for p in _NON_CODE):
            classification = "not code-checkable"
        elif blocked:
            classification = "not determinable"
        elif covered:
            classification = "static"
        elif "static" in capabilities.get(pid, set()):
            classification = "not determinable"
        elif "live" in capabilities.get(pid, set()):
            classification = "live-testable"
        else:
            classification = "not code-checkable"
        row = {"provision": pid, "citation": provision.citation, "title": provision.title,
               "classification": classification, "rules": sorted(covered)}
        if blocked:
            row["not_determinable_rules"] = sorted(blocked)
        if any(issue.id.startswith("CHI-") for issue in covered.values()) or pid.startswith(("DPDP-Act-9", "DPDP-Rule-10", "DPDP-Rule-12")):
            row["annotation"] = "covered, not exercised on a real Target"
        matrix.append(row)
    return matrix


def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def _provisions(finding):
    return [finding["primary_provision"], *finding["other_provisions"]]


def _dependent(assumption_id, finding):
    provisions = _provisions(finding)
    def cites(prefix):
        return any(p == prefix or p.startswith(prefix + "(") or p.startswith(prefix + "-")
                   for p in provisions)
    if assumption_id == "AA-1":
        return (finding["kind"] in ("dpdp-obligation", "security-personal-data")
                and any(p.startswith(("DPDP-Act-", "DPDP-Rule-")) for p in provisions))
    if assumption_id == "AA-2":
        return cites("DPDP-Act-10") or cites("DPDP-Rule-13")
    if assumption_id == "AA-3":
        return any(cites(p) for p in ("DPDP-Rule-8(1)", "DPDP-Rule-8(2)", "DPDP-Rules-Schedule-Third"))
    if assumption_id == "AA-4":
        return finding["issue_type"].startswith("CON-") or cites("DPDP-Act-6") or cites("DPDP-Act-7")
    return False


def _citation(pid, registry):
    entry = registry.get(pid)
    return f"{pid} — {entry.citation}" if entry else pid


def _location(ev):
    return f"{ev['file']}:{ev['start_line']}–{ev['end_line']}"


def _sections(report):
    """Build one format-independent sequence of display blocks per section."""
    findings = report["findings"]
    registry = load_registry()
    catalogue = load_catalogue()
    sections = [[] for _ in SECTIONS]
    assumptions, summary, data_map, details, consent, matrix, legal, method = sections
    legal.extend(legal_view.report_blocks(report, registry))
    for item in report["applicability_assumptions"]:
        dependent = [f["id"] for f in findings if _dependent(item["id"], f)]
        assumptions.append(("list", [f"{item['id']}: {item['text']} Provisions: "
                                    + ", ".join(_citation(p, registry) for p in item["provisions"])
                                    + ". Dependent Findings: " + (", ".join(dependent) or "none")]))
    kinds = ("dpdp-obligation", "security-personal-data", "safeguard")
    bands = ("critical", "high", "medium", "low")
    summary.append(("table", (["Severity", "DPDP obligation", "security dependent on Personal Data", "Safeguard"],
                               [[band, *[str(sum(f["severity"]["band"] == band and f["kind"] == kind
                                                   for f in findings)) for kind in kinds]] for band in bands])))
    ceilings = sorted({f["penalty_ceiling"]["amount_inr_crore"] for f in findings}, reverse=True)
    summary.append(("p", "Penalty Ceilings: " + (", ".join(f"₹{v} crore" for v in ceilings) or "none")
                    + "; statutory maximum under the Schedule; the Board sets any amount."))
    summary.append(("h", "Fix before 13 May 2027"))
    summary.append(("list", [f"{f['id']} — Enforceable From {f['enforceable_from']}" for f in findings
                             if f["enforceable_from"] == "2027-05-13"] or ["None identified."]))
    rows = []
    for entry in report["personal_data_map"]:
        element = entry["element"]
        operations = "; ".join(f"{step['operation']} ({_location(step['evidence'])})"
                               for step in entry["operations"]) or "None recorded"
        rows.append([element["name"], element["data_category"], operations])
    data_map.append(("table", (["Element", "Data Category", "Processing Operations (Evidence)"], rows)))
    if not findings:
        details.append(("p", "No Findings."))
    for finding in findings:
        issue = catalogue.get(finding["issue_type"])
        details.append(("h", f"{finding['id']} — {issue.title if issue else finding['issue_type']}"))
        score = finding["cvss"]
        scoring = (f"CVSS {score['vector']}, score {score['score']}" if score["status"] == "scored"
                   else f"CVSS N/A ({score['reason']}); Risk Matrix cell {finding['risk_matrix']['cell']} "
                        f"({finding['risk_matrix']['tier']}, {finding['risk_matrix']['exposure']})")
        details.append(("p", f"Severity: {finding['severity']['band']}; {scoring}. {finding['severity']['justification']}"))
        details.append(("p", f"Exposure: {finding['exposure']['level']}; Evidence: "
                        + ", ".join(_location(ev) for ev in finding["exposure"]["derived_from"])))
        details.append(("p", "Primary Provision: " + _citation(finding["primary_provision"], registry)))
        details.append(("p", "Other Provisions: " + (", ".join(_citation(p, registry) for p in finding["other_provisions"]) or "none")))
        ceiling = finding["penalty_ceiling"]
        details.append(("p", f"Penalty Ceiling: ₹{ceiling['amount_inr_crore']} crore ({ceiling['parent_section']}); Enforceable From: {finding['enforceable_from']}."))
        status = {"needs-legal-review": "Needs Legal Review"}.get(finding["status"], finding["status"])
        details.append(("p", f"Status: {status}."))
        for reading in (finding.get("legal_review") or {}).get("readings", []):
            details.append(("p", f"Legal reading — {_citation(reading['provision'], registry)}: {reading['reading']}"))
        details.append(("p", "Evidence:"))
        for ev in finding["evidence"]:
            details.extend((("p", _location(ev)), ("code", ev["excerpt"])))
        probe = finding.get("live_probe")
        if probe:
            details.append(("p", f"Live Probe: {probe['result']} — {probe['method']} {probe['route']}; {probe['reason']}"))
            details.append(("code", f"Request: {probe['request']}\nResponse: {probe['response']}"))
        details.append(("p", "Data Flow:"))
        details.append(("list", [f"{step['operation']} — {_location(step['evidence'])}"
                                  + (f"; {step['note']}" if step.get("note") else "")
                                  for step in finding["data_flow"]] or ["None recorded."]))
        fix = finding["recommended_fix"]
        tailored = fix["tailored"]
        details.append(("p", f"Recommended fix: {fix['guidance']} Tailored: "
                        + (str(tailored["value"]) if tailored["status"] == "assessed" else "not assessed")))
        patch = finding.get("fix_patch")
        if patch:
            details.append(("p", f"Fix Patch: {patch['status']} — {patch['reason']}"))
            details.append(("code", patch["diff"]))
        triage = finding["llm_triage"]
        details.append(("p", "LLM triage: " + (f"{triage['value']['verdict']} — {triage['value']['reason']}"
                        if triage["status"] == "assessed" else "not assessed") + f"; cache key: {triage['cache_key']}"))
        if triage["status"] == "assessed" and triage["value"].get("citations"):
            details.append(("p", "LLM triage citations: "
                            + ", ".join(_citation(pid, registry) for pid in triage["value"]["citations"])))
    details.append(("h", "Observations"))
    if not report["observations"]:
        details.append(("p", "No Observations."))
    for observation in report["observations"]:
        details.append(("p", f"{observation['id']} — {observation['title']}; Rules: {', '.join(observation['rules_fired'])}. Recommended fix: {observation['recommended_fix']}"))
        for ev in observation["evidence"]:
            details.extend((("p", _location(ev)), ("code", ev["excerpt"])))
    assessment = report.get("consent_assessment")
    if assessment:
        for row in assessment["criteria"]:
            consent.append(("h", row["criterion"]))
            consent.append(("p", f"Applicability: {row['applicability']} — {row['reason']} Assessment: {row['assessment']}"))
            consent.append(("p", "Issue Types: " + ", ".join(row["issue_types"])))
            consent.append(("p", "Linked identifiers: " + (", ".join(row["linked_identifiers"]) or "none")))
            if row["step_counts"] is not None:
                consent.append(("p", "Static step counts: " + _json(row["step_counts"])))
            for probe in row.get("live_probes", []):
                run = assessment.get("live_probe_run") or {}
                consent.append(("p", f"Live Probe ({run.get('target')} @ {(run.get('commit') or 'unknown')[:12]}, "
                                     f"{run.get('observed_at')}): {probe['status']} ({probe['meaning']}) — "
                                     f"{probe['assertion']}: {probe['reason']} Static verdict above is unchanged."))
            for ev in row["evidence"]:
                consent.extend((("p", _location(ev)), ("code", ev["excerpt"])))
        for banner in assessment["graph"].get("banners", []):
            for ev in banner["evidence"]:
                consent.extend((("p", "Banner Evidence (not a grant): " + _location(ev)), ("code", ev["excerpt"])))
        reasoning = assessment["llm_reasoning"]
        consent.append(("p", "LLM reasoning: " + (reasoning["value"]["assessment"] if reasoning["status"] == "assessed" else "not assessed") + "; cache key: " + reasoning["cache_key"]))
        if reasoning["status"] == "assessed":
            value = reasoning["value"]
            if value.get("citations"):
                consent.append(("p", "LLM reasoning citations: "
                                + ", ".join(_citation(pid, registry) for pid in value["citations"])))
            for row in value.get("criteria", []):
                consent.append(("p", f"LLM reading — {row['criterion']}: {row['reading']}. {row['reason']}"))
                if row["citations"]:
                    consent.append(("p", "LLM reading citations: "
                                    + ", ".join(_citation(pid, registry) for pid in row["citations"])))
        for limitation in assessment["graph"].get("limitations", []):
            consent.append(("p", "Limitation: " + limitation))
    else:
        consent.append(("p", "Not assessed."))
    matrix.append(("table", (["Provision", "Citation", "Classification", "Covering Rules"],
                              [[row["provision"], row.get("citation", ""), row["classification"]
                                + (f"; {row['annotation']}" if row.get("annotation") else ""),
                                ", ".join(row["rules"]) or "none"] for row in report["coverage_matrix"]])))
    scan, llm, target = report["scan"], report["llm"], report["target"]
    method.append(("p", "Static Rules use Semgrep, TypeScript AST and configuration analysers. "
                   "Cache-only mode replays matching cached LLM fields; uncached fields are not assessed. "
                   "Live Probe outcomes, when available, appear with their Findings."))
    method_rows = [
        ["Target Application", target["name"]], ["Target revision", target["commit"] or "not available"],
        ["Target source", target["source"]], ["Exclusions", ", ".join(scan["exclusions"]) or "none"],
        ["Files scanned", str(scan["files_scanned"])], ["Files excluded", str(scan["files_excluded"])],
        ["Rule count", str(scan["rule_count"])], ["LLM provider", llm["provider"]], ["LLM model", llm["model"]],
        ["Prompt versions", ", ".join(f"{k}: {v}" for k, v in llm["prompt_versions"].items()) or "none"],
        ["LLM mode", llm["mode"]], ["Cache hits", str(llm["cache_hits"])],
        ["Cache misses", str(llm["cache_misses"])], ["LLM fields not assessed", str(llm["not_assessed"])],
        ["Cache-only reason", llm["reason"] or "not applicable"],
    ]
    method.append(("table", (["Method", "Value"], method_rows)))
    if "accuracy" in report:
        method.extend(_accuracy_blocks(report["accuracy"]))
    return sections


def _accuracy_blocks(accuracy: dict) -> list:
    """Measured accuracy: Reference Target and Labelled Corpus stay in separate tables."""
    primary, corpus, llm = accuracy["reference_target"], accuracy["labelled_corpus"], accuracy["llm"]
    blocks = [("h", "Measured accuracy"), ("p", accuracy["method"])]
    blocks.append(("p", f"Reference Target: canonical Findings for {primary['target']} at {primary['commit']} "
                        f"against {primary['reference']}."))
    blocks.append(("table", (["Reference Target", "TP", "FP", "FN", "Precision", "Recall"],
                             [[primary["target"], str(primary["tp"]), str(primary["fp"]), str(primary["fn"]),
                               ratio_text(primary["precision"], primary["tp"], primary["tp"] + primary["fp"]),
                               ratio_text(primary["recall"], primary["tp"], primary["tp"] + primary["fn"])]])))
    blocks.append(("list", [f"Matched: {m['finding_id']} = {m['reference_id']}" for m in primary["matches"]]
                   + [f"Unmatched prediction: {u['finding_id']} ({u['issue_type']}): {u['reason']}"
                      for u in primary["unmatched_predictions"]]
                   + [f"Excluded prediction: {x['finding_id']} ({x['reference_id']}): {x['reason']}"
                      for x in primary["excluded_predictions"]]
                   + [f"Unmatched reference: {r}" for r in primary["unmatched_references"]]
                   + [f"Excluded reference: {e['reference_id']}: {e['reason']}" for e in primary["excluded"]]
                   or ["No matches, unmatched entries or exclusions."]))
    blocks.append(("p", "Labelled Corpus: Rule emissions on designed fixtures, one true positive and one near-miss negative per Rule."))
    rows = [[row.get("rule_id", "Total"), str(row["tp"]), str(row["fp"]), str(row["fn"]), str(row["tn"]),
             ratio_text(row["precision"], row["tp"], row["tp"] + row["fp"]),
             ratio_text(row["recall"], row["tp"], row["tp"] + row["fn"])]
            for row in [*corpus["rules"], corpus["totals"]]]
    blocks.append(("table", (["Rule", "TP", "FP", "FN", "TN", "Precision", "Recall"], rows)))
    blocks.append(("table", (["Accuracy LLM provenance", "Value"], [
        ["Cache mode", llm["mode"]], ["Provider", llm["provider"]], ["Model", llm["model"]],
        ["Prompt version", llm["prompt_version"] or "none"], ["Cache hits", str(llm["cache_hits"])],
        ["Cache misses", str(llm["cache_misses"])], ["Not assessed", str(llm["not_assessed"])],
        ["Reproduces published run", "yes" if llm["reproduces_published_run"] else "no"],
        ["Replay problems", "; ".join(llm["replay_problems"]) or "none"]])))
    blocks.append(("h", "Limitations"))
    blocks.append(("list", list(accuracy["limitations"])))
    return blocks


def _md_text(text):
    return escape(str(text), quote=False).replace("|", "\\|").replace("\n", " ")


def render_markdown(report: dict) -> str:
    """Render readable Markdown from the shared section model."""
    parts = ["# Report"]
    for heading, blocks in zip(SECTIONS, _sections(report)):
        parts.append(f"## {heading}")
        for kind, value in blocks:
            if kind == "p":
                parts.append(_md_text(value))
            elif kind == "h":
                parts.append("### " + _md_text(value))
            elif kind == "list":
                parts.append("\n".join("- " + _md_text(item) for item in value))
            elif kind == "code":
                fence = "`" * max(3, max((len(run) for run in re.findall(r"`+", value)), default=0) + 1)
                parts.append(f"{fence}\n{value}\n{fence}")
            else:
                headers, rows = value
                parts.append("\n".join(["| " + " | ".join(map(_md_text, headers)) + " |",
                                         "| " + " | ".join("---" for _ in headers) + " |",
                                         *["| " + " | ".join(map(_md_text, row)) + " |" for row in rows]]))
    return "\n\n".join(parts) + "\n"


def render_html(report: dict) -> str:
    """Render the shared section model with all content HTML-escaped."""
    sections = []
    for heading, blocks in zip(SECTIONS, _sections(report)):
        body = []
        for kind, value in blocks:
            if kind in ("p", "h"):
                tag = "p" if kind == "p" else "h3"
                body.append(f"<{tag}>{escape(str(value))}</{tag}>")
            elif kind == "list":
                body.append("<ul>" + "".join(f"<li>{escape(str(item))}</li>" for item in value) + "</ul>")
            elif kind == "code":
                body.append(f"<pre><code>{escape(value)}</code></pre>")
            else:
                headers, rows = value
                head = "".join(f"<th>{escape(str(cell))}</th>" for cell in headers)
                content = "".join("<tr>" + "".join(f"<td>{escape(str(cell))}</td>" for cell in row) + "</tr>" for row in rows)
                body.append(f"<table><thead><tr>{head}</tr></thead><tbody>{content}</tbody></table>")
        sections.append(f"<section><h2>{escape(heading)}</h2>{''.join(body)}</section>")
    return ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<title>Report</title><style>body{font-family:sans-serif;margin:2em;line-height:1.4}"
            "table{border-collapse:collapse;width:100%;font-size:9pt}th,td{border:1px solid #aaa;padding:.35em;text-align:left;overflow-wrap:break-word;min-width:5.5em}"
            "pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:9pt}h2,h3{break-after:avoid}h2{font-size:1.2em}"
            "@media print{section:not(:first-of-type){break-before:page}tr,pre{break-inside:avoid}}</style></head>"
            "<body><h1>Report</h1>" + "\n".join(sections) + "</body></html>")


def render_pdf(html: str) -> bytes:
    """Print HTML using WeasyPrint, refusing every external resource request."""
    from weasyprint import HTML

    def reject_url(url, *args, **kwargs):
        raise ValueError(f"External PDF resource prohibited: {url}")

    return HTML(string=html, url_fetcher=reject_url).write_pdf()


def write_reports(report: dict, json_path: Path) -> list[Path]:
    """Write canonical JSON and presentation formats beside the given JSON path."""
    json_path = Path(json_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    html = render_html(report)
    paths = [json_path, *(json_path.with_suffix(suffix) for suffix in (".md", ".html", ".pdf"))]
    outputs = ((_json(report) + "\n").encode(), render_markdown(report).encode(),
               html.encode(), render_pdf(html))
    for path, data in zip(paths, outputs):
        path.write_bytes(data)
    return paths
