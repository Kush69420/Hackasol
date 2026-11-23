"""Command line entry point for the Auditor."""

import argparse
import json
from pathlib import Path
import shlex
import subprocess
import sys

from auditor.accuracy import (CACHE_DIR, CorpusError, REFERENCE_PATH, RESULTS_PATH, evaluate_corpus, load_reference,
                              run_accuracy, summary_lines, write_results)
from auditor.masking import public_source
from auditor.report import write_reports
from auditor.rules_list import generate_rules_list
from auditor.scan import run_inventory, run_scan
from auditor.schema import ReportValidationError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dpdp-audit")
    commands = parser.add_subparsers(dest="command", required=True)
    scan = commands.add_parser("scan", help="scan a Target Application")
    scan.add_argument("target", help="local directory or Git URL")
    scan.add_argument("--format", choices=["json", "sarif"], default="json")
    scan.add_argument("--out", type=Path, help="Report destination")
    scan.add_argument("--commit", help="Git commit to check out for a Git URL")
    scan.add_argument("--provider", choices=["anthropic", "openai", "gemini", "ollama", "omp"])
    scan.add_argument("--model")
    scan.add_argument("--cache-dir", type=Path, default=Path(".dpdp-cache"))
    scan.add_argument("--inventory-only", action="store_true",
                      help="write the source-anchored application inventory instead of a Report")
    accuracy = commands.add_parser("accuracy", help="measure precision and recall (Reference Target and Labelled Corpus)")
    accuracy.add_argument("target", nargs="?", help="Reference Target Application (local directory); not needed with --corpus-only")
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
    accuracy.add_argument("--results", type=Path, default=RESULTS_PATH,
                          help="write the reproducible results summary here (default accuracy/results.md)")
    probe = commands.add_parser("probe", help="run bounded Live Probes on a dedicated instance")
    probe.add_argument("--target", required=True, help="authorized instance origin")
    probe.add_argument("--report", required=True, type=Path, help="existing Report JSON")
    probe.add_argument("--allow-origin", action="append", default=[], help="additional explicitly authorized origin")
    fix = commands.add_parser("fix", help="generate and re-scan Fix Patches")
    fix_commands = fix.add_subparsers(dest="fix_command", required=True)
    generate = fix_commands.add_parser("generate")
    generate.add_argument("target", help="clean Target Application at the Report revision")
    generate.add_argument("--report", type=Path, required=True)
    generate.add_argument("--finding", required=True)
    generate.add_argument("--out", type=Path, required=True)
    generate.add_argument("--provider", choices=["anthropic", "openai", "gemini", "ollama", "omp"], default="omp")
    generate.add_argument("--model")
    verify = fix_commands.add_parser("verify")
    verify.add_argument("target")
    verify.add_argument("--report", type=Path, required=True)
    verify.add_argument("--patch", type=Path, action="append", required=True)
    verify.add_argument("--provider", choices=["anthropic", "openai", "gemini", "ollama", "omp"], default="omp")
    verify.add_argument("--model")
    verify.add_argument("--test-command", nargs="+", action="append", default=[])
    publish = fix_commands.add_parser("publish")
    publish.add_argument("target")
    publish.add_argument("--report", type=Path, required=True)
    publish.add_argument("--patch", type=Path, action="append", required=True)
    publish.add_argument("--destination", required=True)
    publish.add_argument("--base", default="dpdp-pinned-base")
    publish.add_argument("--branch", required=True)
    publish.add_argument("--authorize", action="store_true")
    publish.add_argument("--provider", choices=["anthropic", "openai", "gemini", "ollama", "omp"], default="omp")
    publish.add_argument("--model")
    publish.add_argument("--test-command", nargs="+", action="append", default=[])
    rules = commands.add_parser("rules", help="Rules shipped with the Auditor")
    rules.add_subparsers(dest="rules_command", required=True).add_parser(
        "list", help="print the Rules List (RULES.md) generated from the Rule files")
    args = parser.parse_args(argv)
    if args.command == "rules":
        sys.stdout.write(generate_rules_list())
        return 0
    if args.command == "accuracy":
        return _accuracy(args, parser)
    if args.command == "probe":
        from auditor.probes import probe_report
        try:
            results = probe_report(args.report, args.target, tuple(args.allow_origin))
        except (OSError, ValueError, ReportValidationError) as exc:
            print(f"dpdp-audit: {exc}", file=sys.stderr)
            return 1
        print(f"{sum(item['finding_id'] is not None for item in results)} matched Live Probe outcomes; {args.report}")
        for item in results:
            print(f"{item['assertion']}: {item['result']} — {item['reason']}")
        return 0
    if args.command == "fix":
        from auditor.fixpatch import generate_review, verify as verify_patches
        from auditor.fixpatch.publish import publish as publish_patches
        try:
            report = json.loads(args.report.read_text(encoding="utf-8"))
            if args.fix_command == "generate":
                finding = next((f for f in report["findings"] if f["id"] == args.finding), None)
                if finding is None:
                    raise ValueError("Finding not present in Report")
                patch = generate_review(finding, args.target, args.provider, args.model)
                finding["fix_patch"] = {k: patch[k] for k in ("status", "diff", "reason", "provenance")}
                args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                args.out.write_text(json.dumps(patch, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                print(args.out)
                return 1 if patch["status"] == "rejected" else 0
            patches = [json.loads(path.read_text(encoding="utf-8")) for path in args.patch]
            if args.fix_command == "publish":
                result = publish_patches(args.target, report, patches, destination=args.destination,
                                         base=args.base, branch=args.branch, authorized=args.authorize,
                                         scan_options={"provider": args.provider, "model": args.model},
                                         test_commands=args.test_command)
                print(result["url"])
                return 0
            result = verify_patches(args.target, report, patches,
                                    scan_options={"provider": args.provider, "model": args.model},
                                    test_commands=args.test_command)
            reason = json.dumps({"remaining": result["remaining"], "new": result["new"],
                                 "target_tests": result["target_tests"]}, ensure_ascii=False)
            for path, patch in zip(args.patch, patches):
                patch["status"] = result["status"]
                path.write_text(json.dumps(patch, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                ids = patch.get("finding_ids", [patch.get("finding_id")])
                for finding in report["findings"]:
                    if finding["id"] in ids:
                        finding["fix_patch"] = {"status": result["status"], "diff": patch["diff"],
                                                "reason": reason, "provenance": patch.get("provenance", "authored")}
            args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0 if result["status"] == "accepted" else 1
        except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
            print(f"dpdp-audit: {type(exc).__name__}", file=sys.stderr)
            return 1
        return 0
    try:
        if args.inventory_only:
            report = run_inventory(args.target, commit=args.commit)
            default_name = "inventory.json"
        else:
            report = run_scan(args.target, commit=args.commit, provider=args.provider,
                              model=args.model, cache_dir=args.cache_dir)
            default_name = "report.sarif" if args.format == "sarif" else "report.json"
        destination = args.out or Path("reports") / report["target"]["name"] / default_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        if args.inventory_only:
            destination.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        elif args.format == "sarif":
            from auditor.sarif import to_sarif
            destination.write_text(json.dumps(to_sarif(report), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
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
        if args.results:
            parts = [public_source(args.target), "--cache-only", "--cache-dir", args.cache_dir.as_posix(),
                     "--reference", Path(args.reference).as_posix(), "--results", args.results.as_posix()]
            if report["target"].get("kind") == "git" and report["target"].get("commit"):
                parts += ["--commit", report["target"]["commit"]]
            parts += ["--provider", report["llm"]["provider"], "--model", report["llm"]["model"]]
            command = "dpdp-audit accuracy " + " ".join(shlex.quote(p) for p in parts)
            write_results(report, load_reference(args.reference), command=command, path=args.results)
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError, ReportValidationError, CorpusError) as exc:
        detail = exc.stderr if isinstance(exc, subprocess.CalledProcessError) else str(exc)
        print(f"dpdp-audit: {detail.strip()}", file=sys.stderr)
        return 1
    print("\n".join(summary_lines(report["accuracy"])))
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
