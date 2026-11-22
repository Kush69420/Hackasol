"""Build the foundation Report for a Target Application."""

from datetime import datetime, timezone
from pathlib import Path
import sys

from auditor import __version__
from auditor.exclusions import exclusions_for, iter_target_files
from auditor.inputs import resolve_target
from auditor.llm import LLMSession
from auditor.schema import SCHEMA_VERSION, validate_report


ASSUMPTIONS = (
    ("AA-1", "The Act applies: the Target Application processes digital Personal Data in India, or offers goods or services to Data Principals in India.", ["DPDP-Act-3"]),
    ("AA-2", "The Data Fiduciary is not a Significant Data Fiduciary; its duties are shown as conditional.", ["DPDP-Act-10"]),
    ("AA-3", "The Data Fiduciary is not a Third Schedule class; its duties are shown as conditional.", ["DPDP-Rule-8(1)", "DPDP-Rules-Schedule-Third"]),
    ("AA-4", "Processing relies on consent unless the code shows a section 7 legitimate use, such as processing an order the Data Principal placed.", ["DPDP-Act-7"]),
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_scan(source: str, *, commit: str | None = None, provider: str | None = None,
             model: str | None = None, cache_dir: Path = Path(".dpdp-cache"),
             targets_dir: Path = Path("targets")) -> dict:
    started = _now()
    target = resolve_target(source, commit=commit, targets_dir=targets_dir)
    files, excluded = iter_target_files(target.root, target.name)
    session = LLMSession.from_env(cache_dir=cache_dir, provider=provider, model=model)
    session.probe()
    llm = session.summary()
    if llm["mode"] == "cache-only":
        print(f"LLM cache-only mode: {llm['reason']}", file=sys.stderr)
    rules_dir = Path(__file__).resolve().parent.parent / "rules" / "semgrep"
    report = {
        "schema_version": SCHEMA_VERSION,
        "tool": {"name": "dpdp-audit", "version": __version__},
        "target": {"name": target.name, "source": target.source, "kind": target.kind, "commit": target.commit},
        "scan": {"started_at": started, "finished_at": _now(),
                 "exclusions": exclusions_for(target.name), "files_scanned": len(files),
                 "files_excluded": excluded, "rule_count": sum(1 for path in rules_dir.rglob("*.yaml") if path.is_file())},
        "llm": llm,
        "applicability_assumptions": [{"id": id_, "text": text, "provisions": list(provisions)}
                                      for id_, text, provisions in ASSUMPTIONS],
        "personal_data_map": [], "findings": [], "observations": [],
        "coverage_matrix": [], "consent_assessment": None,
    }
    validate_report(report)
    return report
