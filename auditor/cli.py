"""Command line entry point for the Auditor."""

import argparse
import json
from pathlib import Path
import subprocess
import sys

from auditor.scan import run_scan
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
    args = parser.parse_args(argv)
    try:
        report = run_scan(args.target, commit=args.commit, provider=args.provider,
                          model=args.model, cache_dir=args.cache_dir)
        destination = args.out or Path("reports") / report["target"]["name"] / "report.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except (OSError, ValueError, subprocess.CalledProcessError, ReportValidationError) as exc:
        detail = exc.stderr if isinstance(exc, subprocess.CalledProcessError) else str(exc)
        print(f"dpdp-audit: {detail.strip()}", file=sys.stderr)
        return 1
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
