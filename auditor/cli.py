"""Command line entry point for the Auditor."""

import argparse
import json
from pathlib import Path
import subprocess
import sys

from auditor.report import write_reports
from auditor.rules_list import generate_rules_list
from auditor.scan import run_inventory, run_scan
from auditor.schema import ReportValidationError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dpdp-audit")
    commands = parser.add_subparsers(dest="command", required=True)
    scan = commands.add_parser("scan", help="scan a Target Application")
    scan.add_argument("target", help="local directory or Git URL")
    scan.add_argument("--format", choices=["json"], default="json")
    scan.add_argument("--out", type=Path, help="Report destination")
    scan.add_argument("--commit", help="Git commit to check out for a Git URL")
    scan.add_argument("--provider", choices=["anthropic", "openai", "gemini", "ollama", "omp"])
    scan.add_argument("--model")
    scan.add_argument("--cache-dir", type=Path, default=Path(".dpdp-cache"))
    scan.add_argument("--inventory-only", action="store_true",
                      help="write the source-anchored application inventory instead of a Report")
    rules = commands.add_parser("rules", help="Rules shipped with the Auditor")
    rules.add_subparsers(dest="rules_command", required=True).add_parser(
        "list", help="print the Rules List (RULES.md) generated from the Rule files")
    args = parser.parse_args(argv)
    if args.command == "rules":
        sys.stdout.write(generate_rules_list())
        return 0
    try:
        if args.inventory_only:
            report = run_inventory(args.target, commit=args.commit)
            default_name = "inventory.json"
        else:
            report = run_scan(args.target, commit=args.commit, provider=args.provider,
                              model=args.model, cache_dir=args.cache_dir)
            default_name = "report.json"
        destination = args.out or Path("reports") / report["target"]["name"] / default_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        if args.inventory_only:
            destination.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        else:
            write_reports(report, destination)
    except (OSError, ValueError, subprocess.CalledProcessError, ReportValidationError) as exc:
        detail = exc.stderr if isinstance(exc, subprocess.CalledProcessError) else str(exc)
        print(f"dpdp-audit: {detail.strip()}", file=sys.stderr)
        return 1
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
