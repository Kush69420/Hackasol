#!/usr/bin/env bash
# Benchmark step 1: run plain Semgrep registry rulesets over the pinned Targets.
#
# For each Target this writes, under benchmark/results/<target>/:
#   semgrep.json  Semgrep's JSON output. String values under results[] and errors[] are passed
#                 through auditor.masking.mask_for_report so secret-like matched text is not
#                 committed. Keys, paths and fingerprints are left unchanged.
#   semgrep.log   Semgrep stderr (rule counts, skipped-file summary), unmodified.
# and benchmark/results/run.json with provenance: Semgrep version, ruleset fetch time (UTC),
# checkout commit, rules run, files scanned, skip counts, error counts and the exclusion globs.
#
# Usage: bash benchmark/run_semgrep.sh   (then: .venv/bin/python benchmark/compare.py)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PYTHON="$ROOT/.venv/bin/python"
SEMGREP="$ROOT/.venv/bin/semgrep"
RESULTS="$ROOT/benchmark/results"
TARGETS=(juice-shop ai-kyc-platform trackmyrupee singharya-e-kyc)
CONFIGS=(--config p/default --config p/secrets --config p/owasp-top-ten)

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
fetched=()
for target in "${TARGETS[@]}"; do
  checkout="$ROOT/targets/$target"
  if [ ! -d "$checkout" ]; then
    echo "missing Target checkout: $checkout" >&2
    exit 1
  fi

  # Exclusion globs come from the Auditor's own profile table, so both tools skip the same paths.
  globs="$("$PYTHON" -c 'import sys; from auditor.exclusions import exclusions_for; print("\n".join(exclusions_for(sys.argv[1])))' "$target")"
  excludes=()
  while IFS= read -r glob; do
    excludes+=(--exclude "$glob")
  done <<< "$globs"

  fetched_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  fetched+=("$target=$fetched_at")
  echo "[$target] semgrep scan (fetched_at=$fetched_at)" >&2
  # Output goes to a temp dir and is published by the step below only after a clean exit,
  # so a killed scan never leaves a truncated or empty semgrep.json behind.
  status=0
  (cd "$checkout" && "$SEMGREP" scan "${CONFIGS[@]}" --json --metrics=off --no-git-ignore \
      --disable-version-check "${excludes[@]}" .) \
    > "$tmp/$target.json" 2> "$tmp/$target.log" || status=$?
  if [ "$status" -ne 0 ]; then
    trap - EXIT
    echo "[$target] semgrep exited $status; log kept at $tmp/$target.log" >&2
    exit "$status"
  fi
done

"$PYTHON" - "$ROOT" "$tmp" "$RESULTS" "${fetched[@]}" <<'PY'
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

from auditor.exclusions import exclusions_for
from auditor.masking import mask_for_report

root, tmp, results = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
fetched = dict(item.split("=", 1) for item in sys.argv[4:])
SUMMARY = re.compile(r"Ran (\d+) rules on (\d+) files: (\d+) findings")
SKIPPED = re.compile(r"^\s*◦ (.+?):\s*(\d+)\s*$", re.M)
UNMASKED_KEYS = {"fingerprint", "path", "check_id"}


def mask_strings(node):
    """Mask string values; keys and the identifier-like fields used for joins stay as Semgrep wrote them."""
    if isinstance(node, dict):
        return {k: v if k in UNMASKED_KEYS else mask_strings(v) for k, v in node.items()}
    if isinstance(node, list):
        return [mask_strings(v) for v in node]
    if isinstance(node, str):
        return mask_for_report(node)
    return node


targets, version = {}, None
for target, fetched_at in fetched.items():
    raw = json.loads((tmp / f"{target}.json").read_text(encoding="utf-8"))
    log = (tmp / f"{target}.log").read_text(encoding="utf-8")
    match = SUMMARY.search(log)
    if match is None:
        raise SystemExit(f"[{target}] no 'Ran N rules on M files' line in semgrep.log")
    rules_run, files_run, findings = (int(x) for x in match.groups())
    if findings != len(raw["results"]):
        raise SystemExit(f"[{target}] log reports {findings} findings, JSON has {len(raw['results'])}")
    scanned = len(raw["paths"]["scanned"])
    if scanned != files_run:
        raise SystemExit(f"[{target}] log reports {files_run} files, JSON paths.scanned has {scanned}")
    version = version or raw["version"]
    checkout = root / "targets" / target

    def git(*args: str) -> str:
        return subprocess.run(["git", "-C", str(checkout), *args], capture_output=True,
                              text=True, check=True).stdout.strip()

    masked = {**raw, "results": mask_strings(raw["results"]), "errors": mask_strings(raw["errors"])}
    target_dir = results / target
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "semgrep.json").write_text(json.dumps(masked, ensure_ascii=False) + "\n", encoding="utf-8")
    (target_dir / "semgrep.log").write_text(log, encoding="utf-8")

    errors = Counter(f"{e.get('level')}/{e.get('code')}" for e in raw["errors"])
    targets[target] = {
        "fetched_at_utc": fetched_at,
        "commit": git("rev-parse", "HEAD"),
        "dirty_checkout": bool(git("status", "--porcelain")),
        "exclude": exclusions_for(target),
        "rules_run": rules_run,
        "files_scanned": scanned,
        "findings": findings,
        "skipped": {re.sub(r"\s+", " ", label).strip(): int(n) for label, n in SKIPPED.findall(log)},
        "errors": {"total": len(raw["errors"]), "by_level_code": dict(sorted(errors.items()))},
    }
    print(f"[{target}] {findings} results, {rules_run} rules, {scanned} files", file=sys.stderr)

run = {
    "semgrep_version": version,
    "configs": ["p/default", "p/secrets", "p/owasp-top-ten"],
    "metrics": "off",
    "flags": ["--json", "--no-git-ignore", "--disable-version-check"],
    "masking": "auditor.masking.mask_for_report on string values under results[] and errors[]; "
               "keys path, check_id and fingerprint are unchanged",
    "targets": targets,
}
(results / "run.json").write_text(json.dumps(run, indent=2) + "\n", encoding="utf-8")
print(f"wrote {results / 'run.json'}")
PY
