"""Command line entry point for the Auditor."""

import argparse
import json
from pathlib import Path
import subprocess
import sys

from auditor.accuracy import (CACHE_DIR, CorpusError, REFERENCE_PATH, evaluate_corpus, run_accuracy,
                              summary_lines)
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
    accuracy = commands.add_parser("accuracy", help="measure precision and recall (Primary Target and Labelled Corpus)")
    accuracy.add_argument("target", nargs="?", help="Primary Target Application (local directory); not needed with --corpus-only")
    accuracy.add_argument("--cache-only", action="store_true", default=True,
                          help="replay cached LLM verdicts without contacting a provider (always on)")
    accuracy.add_argument("--corpus-only", action="store_true",
                          help="evaluate only the Labelled Corpus; exit non-zero when a pair is missing")
    accuracy.add_argument("--reference", type=Path, default=REFERENCE_PATH, help="hand-checked reference list")
    accuracy.add_argument("--out", type=Path, help="Report destination (default reports/<target>/report.json)")
    accuracy.add_argument("--commit", help="Git commit to check out for a Git URL")
    accuracy.add_argument("--provider", choices=["anthropic", "openai", "gemini", "ollama", "omp"])
    accuracy.add_argument("--model")
    accuracy.add_argument("--cache-dir", type=Path, default=CACHE_DIR)
    accuracy.add_argument("--write-manifest", action="store_true",
                          help="record the replay manifest in the cache dir (regeneration after a Rule or prompt change)")
    rules = commands.add_parser("rules", help="Rules shipped with the Auditor")
    rules.add_subparsers(dest="rules_command", required=True).add_parser(
        "list", help="print the Rules List (RULES.md) generated from the Rule files")
    args = parser.parse_args(argv)
    if args.command == "rules":
        sys.stdout.write(generate_rules_list())
        return 0
    if args.command == "accuracy":
        return _accuracy(args, parser)
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


def _accuracy(args, parser) -> int:
    try:
        if args.corpus_only:
            corpus = evaluate_corpus()
            print("\n".join(summary_lines({"labelled_corpus": corpus})))
            return 0
        if not args.target:
            parser.error("accuracy needs a target unless --corpus-only is given")
        report = run_accuracy(args.target, reference_path=args.reference, cache_dir=args.cache_dir,
                              provider=args.provider, model=args.model, commit=args.commit,
                              write_manifest_file=args.write_manifest)
        destination = args.out or Path("reports") / report["target"]["name"] / "report.json"
        write_reports(report, destination)
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError, ReportValidationError, CorpusError) as exc:
        detail = exc.stderr if isinstance(exc, subprocess.CalledProcessError) else str(exc)
        print(f"dpdp-audit: {detail.strip()}", file=sys.stderr)
        return 1
    print("\n".join(summary_lines(report["accuracy"])))
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
