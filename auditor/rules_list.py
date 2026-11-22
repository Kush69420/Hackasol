"""Generate the Rules List from Rule, Issue Type and Provision metadata."""

from pathlib import Path

from auditor.masking import mask_for_report
from auditor.registry import load_registry
from auditor.remediation import load_catalogue
from auditor.rules import load_rules


CORPUS = Path(__file__).resolve().parent.parent / "corpus"


def _example(rule_id: str) -> tuple[str, str]:
    positive = CORPUS / rule_id / "positive"
    files = sorted(path for path in positive.rglob("*") if path.is_file())
    if not files:
        raise ValueError(f"Rule {rule_id} has no positive Labelled Corpus file")
    # A root entry point is the main file when present; otherwise use the first file.
    main = next((positive / name for name in ("server.ts", "main.tf")
                 if (positive / name).is_file()), files[0])
    excerpt = "\n".join(main.read_text(encoding="utf-8").splitlines()[:12])
    return main.relative_to(CORPUS.parent).as_posix(), mask_for_report(excerpt)


def generate_rules_list() -> str:
    """Return deterministic Markdown for all Issue Types and implemented Rules."""
    catalogue = load_catalogue()
    registry = load_registry()
    grouped = {issue_id: [] for issue_id in catalogue}
    for spec, _ in load_rules().values():
        if spec.issue_type not in catalogue:
            raise ValueError(f"Rule {spec.id} has unknown Issue Type {spec.issue_type}")
        grouped[spec.issue_type].append(spec)

    lines = ["# Rules List", "", "Generated from Rule metadata, the Issue Type catalogue, the Provision registry and the Labelled Corpus.", ""]
    for issue_id, issue in catalogue.items():
        lines.extend([f"## {issue_id} — {issue.title}", ""])
        specs = sorted(grouped[issue_id], key=lambda spec: spec.id)
        if not specs:
            lines.extend(["No Rule implemented at this slice.", ""])
            continue
        provision_ids = (issue.primary, *issue.related)
        for provision_id in provision_ids:
            if provision_id not in registry:
                raise ValueError(f"Issue Type {issue_id} cites unknown Provision {provision_id}")
        primary = registry[issue.primary].citation
        related = "; ".join(registry[pid].citation for pid in issue.related) or "None"
        cwes = ", ".join(sorted(pid for pid in issue.related if pid.startswith("CWE-"))) or "None"
        for spec in specs:
            path, excerpt = _example(spec.id)
            # A fence longer than any backtick run in the example cannot be closed by it.
            fence = "```"
            while fence in excerpt:
                fence += "`"
            lines.extend([
                f"### {spec.id} — {spec.title}", "",
                f"- Engine: {spec.engine}",
                f"- Languages / file kind: {', '.join(spec.languages)}",
                f"- Classification: {spec.classification}",
            ])
            if spec.classification == "technical":
                lines.append(f"- Base CVSS vector: {spec.base_vector}")
            lines.extend([
                f"- Gate: {issue.gate or 'None'}",
                f"- Primary Provision: {primary} (`{issue.primary}`)",
                f"- Related Provisions: {related}",
                f"- CWE: {cwes}", "",
                f"Labelled Corpus example: `{path}`", "", fence, excerpt, fence, "",
            ])
    return "\n".join(lines)
