"""Build the foundation Report for a Target Application."""

from datetime import datetime, timezone
from pathlib import Path
import sys

from auditor import __version__
from auditor.exclusions import exclusions_for, iter_target_files
from auditor.inputs import resolve_target
from auditor.inventory import build_inventory
from auditor.llm import LLMSession
from auditor.mapping import assemble
from auditor.registry import load_registry
from auditor.report import coverage_matrix, executive_summary
from auditor.rules import load_rules
from auditor.rules.context import build_context
from auditor.schema import SCHEMA_VERSION, validate_report


ASSUMPTIONS = (
    ("AA-1", "The Act applies: the Target Application processes digital Personal Data in India, or offers goods or services to Data Principals in India.", ["DPDP-Act-3"]),
    ("AA-2", "The Data Fiduciary is not a Significant Data Fiduciary; its duties are shown as conditional.", ["DPDP-Act-10"]),
    ("AA-3", "The Data Fiduciary is not a Third Schedule class; its duties are shown as conditional.", ["DPDP-Rule-8(1)", "DPDP-Rules-Schedule-Third"]),
    ("AA-4", "Processing relies on consent unless the code shows a section 7 legitimate use, such as processing an order the Data Principal placed.", ["DPDP-Act-7"]),
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_inventory(source: str, *, commit: str | None = None,
                  targets_dir: Path = Path("targets")) -> dict:
    """Inventory diagnostic: source-anchored facts only, no Findings and no LLM."""
    target = resolve_target(source, commit=commit, targets_dir=targets_dir)
    files, _ = iter_target_files(target.root, target.name)
    return {"target": {"name": target.name, "source": target.source, "kind": target.kind,
                       "commit": target.commit},
            "exclusions": exclusions_for(target.name),
            "inventory": build_inventory(target.root, files, target.commit)}


def run_scan(source: str, *, commit: str | None = None, provider: str | None = None,
             model: str | None = None, cache_dir: Path = Path(".dpdp-cache"),
             targets_dir: Path = Path("targets")) -> dict:
    started = _now()
    target = resolve_target(source, commit=commit, targets_dir=targets_dir)
    files, excluded = iter_target_files(target.root, target.name)
    session = LLMSession.from_env(cache_dir=cache_dir, provider=provider, model=model)
    session.probe()
    probed = session.summary()
    if probed["mode"] == "cache-only":
        print(f"LLM cache-only mode: {probed['reason']}", file=sys.stderr)

    ctx = build_context(target.root, target.name, llm=session)
    rules = load_rules()
    matches = [m for _, detect in rules.values() for m in detect(ctx)]
    assembled = assemble(matches, llm=session)

    report = {
        "schema_version": SCHEMA_VERSION,
        "tool": {"name": "dpdp-audit", "version": __version__},
        "target": {"name": target.name, "source": target.source, "kind": target.kind, "commit": target.commit},
        "scan": {"started_at": started, "finished_at": _now(),
                 "exclusions": exclusions_for(target.name), "files_scanned": len(files),
                 "files_excluded": excluded, "rule_count": len(rules)},
        "llm": session.summary(),
        "applicability_assumptions": [{"id": id_, "text": text, "provisions": list(provisions)}
                                      for id_, text, provisions in ASSUMPTIONS],
        "personal_data_map": ctx.personal_data_map,
        "findings": assembled.findings, "observations": assembled.observations,
        "coverage_matrix": coverage_matrix(load_registry(), rules, assembled.not_determinable, assembled.findings),
        "consent_assessment": None,
    }
    report["executive_summary"] = executive_summary(report)
    validate_report(report)
    return report
