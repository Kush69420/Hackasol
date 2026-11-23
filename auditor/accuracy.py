"""Measured accuracy: Reference Target scoring, Labelled Corpus evaluation and cache replay provenance.

Two separate populations are scored and never merged:

* Reference Target: canonical Report Findings against the hand-checked reference list.
* Labelled Corpus: each Rule's true positive and near-miss negative, counting Rule emissions.

Everything here is deterministic. Heavy imports (the scan, the Rules) are lazy so the Report
renderer can use `ratio_text` without an import cycle.
"""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
from pathlib import Path, PurePosixPath

from auditor.llm import ROLES, role_overrides

REPO = Path(__file__).resolve().parents[1]
REFERENCE_PATH = Path("accuracy/juice-shop.json")
CACHE_DIR = Path("accuracy/cache")
MANIFEST_NAME = "manifest.json"
CACHE_IDENTITY = "sha256(masked snippet + NUL + prompt version + NUL + model [+ NUL + masked context JSON])"

METHOD = (
    "Reference Target: each canonical Finding is one prediction. It matches a confirmed reference entry "
    "when the Issue Type and normalised file path are equal and any Finding Evidence range overlaps the "
    "entry's reviewed anchor range. Matching is one-to-one, in Finding id order, each prediction taking the "
    "lowest-id unmatched entry; a second prediction for a matched entry is a false positive. A Finding that "
    "merges several Rules is one prediction. Labelled Corpus: for each Rule, the positive counts as a true "
    "positive if the Rule emits there (else a false negative) and the negative counts as a false positive if "
    "the Rule emits there (else a true negative); Rule emissions are counted, not merged Findings. "
    "Precision = TP/(TP+FP); recall = TP/(TP+FN); a zero denominator is N/A."
)
LIMITATIONS = (
    "The Reference Target reference list covers one Target Application at one pinned revision; the figures say nothing about any Secondary Target.",
    "The reference list is hand-checked by the authors, so omissions and judgement calls bias recall and precision; entries that could not be determined are excluded, not scored.",
    "A Finding whose only overlapping same-Issue-Type reference entries are not-determinable is neither a true nor a false positive; it is listed as an excluded prediction.",
    "Labelled Corpus cases are small designed fixtures: one pair per Rule shows the Rule works on that pair, not how often it is right on real code.",
    "LLM verdicts are replayed from a versioned cache and never change which Findings exist; a cache miss is 'not assessed' and the run does not reproduce the published figures.",
)


class CorpusError(ValueError):
    """A required Labelled Corpus pair is missing."""


def ratio(numerator: int, denominator: int) -> float | None:
    """Exact ratio rounded to four places; None when the denominator is zero."""
    return None if denominator == 0 else round(numerator / denominator, 4)


def ratio_text(value: float | None, numerator: int | None = None, denominator: int | None = None) -> str:
    text = "N/A" if value is None else f"{value:.4f}"
    return text if numerator is None else f"{text} ({numerator}/{denominator})"


def _metrics(tp: int, fp: int, fn: int) -> dict:
    return {"precision": ratio(tp, tp + fp), "recall": ratio(tp, tp + fn)}


def _normalise(path: str) -> str:
    return str(PurePosixPath(path.replace("\\", "/")))


# --- reference list -------------------------------------------------------------------------

def load_reference(path: Path = REFERENCE_PATH) -> dict:
    path = Path(path)
    if not path.is_absolute() and not path.exists():
        path = REPO / path
    try:
        reference = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"cannot read reference list {path}: {exc}") from exc
    ids = [entry["id"] for entry in reference["entries"]]
    if len(ids) != len(set(ids)):
        raise ValueError("reference list has duplicate entry ids")
    for entry in reference["entries"]:
        if entry["status"] == "not-determinable" and not entry.get("reason"):
            raise ValueError(f"{entry['id']} is not-determinable and needs a reason")
    return reference


# --- Reference Target scoring ---------------------------------------------------------------

def score_findings(findings: list[dict], reference: dict, *, reference_path: str = str(REFERENCE_PATH)) -> dict:
    confirmed = sorted((e for e in reference["entries"] if e["status"] == "confirmed"), key=lambda e: e["id"])
    excluded = [{"reference_id": e["id"], "reason": e.get("reason") or "not determinable"}
                for e in sorted(reference["entries"], key=lambda e: e["id"]) if e["status"] != "confirmed"]
    excluded_entries = [e for e in reference["entries"] if e["status"] != "confirmed"]

    def overlaps(finding: dict, entry: dict) -> bool:
        return finding["issue_type"] == entry["issue_type"] and any(
            _normalise(ev["file"]) == _normalise(entry["file"])
            and ev["start_line"] <= entry["end_line"] and entry["start_line"] <= ev["end_line"]
            for ev in finding["evidence"])

    matched: dict[str, str] = {}  # reference id -> finding id
    matches, unmatched, excluded_predictions = [], [], []
    for finding in sorted(findings, key=lambda f: f["id"]):
        candidates = [e for e in confirmed if overlaps(finding, e)]
        free = [e for e in candidates if e["id"] not in matched]
        if free:
            matched[free[0]["id"]] = finding["id"]
            matches.append({"finding_id": finding["id"], "reference_id": free[0]["id"]})
        elif candidates:
            unmatched.append({"finding_id": finding["id"], "issue_type": finding["issue_type"],
                              "reason": f"duplicate of {candidates[0]['id']}"})
        elif any(overlaps(finding, e) for e in excluded_entries):
            entry = sorted((e for e in excluded_entries if overlaps(finding, e)), key=lambda e: e["id"])[0]
            excluded_predictions.append({"finding_id": finding["id"], "reference_id": entry["id"],
                                         "reason": f"overlaps only not-determinable entry {entry['id']}: "
                                                   f"{entry.get('reason') or 'not determinable'}"})
        else:
            unmatched.append({"finding_id": finding["id"], "issue_type": finding["issue_type"],
                              "reason": "no reference entry with this Issue Type at this anchor"})
    missed = [e["id"] for e in confirmed if e["id"] not in matched]
    tp, fp, fn = len(matches), len(unmatched), len(missed)
    return {"target": reference["target"]["name"], "commit": reference["target"]["commit"],
            "reference": reference_path, "tp": tp, "fp": fp, "fn": fn, **_metrics(tp, fp, fn),
            "matches": matches, "unmatched_predictions": unmatched,
            "excluded_predictions": excluded_predictions,
            "unmatched_references": missed, "excluded": excluded}


# --- Labelled Corpus ------------------------------------------------------------------------

def evaluate_corpus(corpus_dir: Path | None = None, rules: dict | None = None) -> dict:
    """Evaluate every Rule's Labelled Corpus pair; raises CorpusError when a pair is missing."""
    from auditor.rules import load_rules
    from auditor.rules.context import build_context

    corpus_dir = Path(corpus_dir) if corpus_dir else REPO / "corpus"
    rules = load_rules() if rules is None else rules
    missing = [f"{rule_id}/{label}" for rule_id in sorted(rules) for label in ("positive", "negative")
               if not (corpus_dir / rule_id / label).is_dir()]
    if missing:
        raise CorpusError("missing Labelled Corpus pair(s): " + ", ".join(missing))

    def emits(rule_id: str, label: str) -> bool:
        detect = rules[rule_id][1]
        ctx = build_context(corpus_dir / rule_id / label, "corpus")
        return any(m.rule_id == rule_id for m in detect(ctx))

    from auditor.exclusions import iter_target_files
    from auditor.rules.context import SEMGREP_DIR
    from auditor.semgrep import prewarm_semgrep
    from concurrent.futures import ThreadPoolExecutor
    import os

    # One batched Semgrep run for every fixture; each fixture is still cached and evaluated on its own files.
    prewarm_semgrep([(root, [p.relative_to(root) for p in iter_target_files(root, "corpus")[0]])
                     for root in (corpus_dir / r / label for r in sorted(rules) for label in ("positive", "negative"))],
                    [SEMGREP_DIR])

    ids = sorted(rules)
    jobs = [(rule_id, label) for rule_id in ids for label in ("positive", "negative")]
    with ThreadPoolExecutor(max_workers=min(len(jobs), os.cpu_count() or 4)) as pool:  # Semgrep subprocess bound
        emitted = dict(zip(jobs, pool.map(lambda job: emits(*job), jobs)))
    rows = []
    for rule_id in ids:
        pos, neg = emitted[(rule_id, "positive")], emitted[(rule_id, "negative")]
        tp, fn, fp, tn = int(pos), int(not pos), int(neg), int(not neg)
        rows.append({"rule_id": rule_id, "tp": tp, "fp": fp, "fn": fn, "tn": tn, **_metrics(tp, fp, fn)})
    totals = {key: sum(r[key] for r in rows) for key in ("tp", "fp", "fn", "tn")}
    return {"rules": rows, "totals": {**totals, **_metrics(totals["tp"], totals["fp"], totals["fn"])}}


# --- cache replay manifest ------------------------------------------------------------------

def rules_digest(repo: Path = REPO) -> str:
    """sha256 over the Rule source files and the Semgrep YAML, in path order."""
    files = sorted([*(repo / "auditor" / "rules").glob("*.py"),
                    *(p for p in (repo / "rules" / "semgrep").rglob("*") if p.suffix in (".yml", ".yaml"))])
    digest = hashlib.sha256()
    for path in files:
        digest.update(path.relative_to(repo).as_posix().encode() + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def prompt_version(llm: dict) -> str:
    return ", ".join(f"{k}: {v}" for k, v in sorted(llm["prompt_versions"].items()))


def build_manifest(report: dict, cache_dir: Path = CACHE_DIR) -> dict:
    llm = report["llm"]
    return {"format_version": 1,
            "target": {"name": report["target"]["name"], "commit": report["target"]["commit"]},
            "rules_digest": rules_digest(),
            "provider": llm["provider"], "model": llm["model"],
            "roles": {role: {"provider": route["provider"], "model": route["model"]} for role, route in llm["roles"].items()},
            "prompt_version": prompt_version(llm), "prompt_versions": dict(llm["prompt_versions"]),
            "cache_identity": CACHE_IDENTITY, "cache_dir": Path(cache_dir).as_posix(),
            # Fields the published run itself left unassessed (provider gave no valid verdict); a replay
            # reproduces it only with the same counts, and any extra miss is reported.
            "published_cache_misses": llm["cache_misses"], "published_not_assessed": llm["not_assessed"]}


def write_manifest(report: dict, cache_dir: Path = CACHE_DIR) -> Path:
    path = Path(cache_dir) / MANIFEST_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build_manifest(report, cache_dir), indent=2) + "\n", encoding="utf-8")
    return path


def replay_status(report: dict, cache_dir: Path = CACHE_DIR) -> dict:
    """The `accuracy.llm` object: provenance, cache counters and whether the run reproduces the pinned one."""
    llm = report["llm"]
    problems = []
    try:
        manifest = json.loads((Path(cache_dir) / MANIFEST_NAME).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        manifest = None
        problems.append(f"no replay manifest at {Path(cache_dir) / MANIFEST_NAME}")
    if manifest:
        # A manifest written before per-role routing has no roles: every role then ran on the top-level route.
        manifest_roles = manifest.get("roles") or {
            role: {"provider": manifest["provider"], "model": manifest["model"]} for role in ROLES}
        expected = {"target commit": (manifest["target"]["commit"], report["target"]["commit"]),
                    "Rules digest": (manifest["rules_digest"], rules_digest()),
                    "provider": (manifest["provider"], llm["provider"]),
                    "model": (manifest["model"], llm["model"]),
                    "prompt version": (manifest["prompt_version"], prompt_version(llm))}
        for role in ROLES:
            expected[f"{role} provider"] = (manifest_roles[role]["provider"], llm["roles"][role]["provider"])
            expected[f"{role} model"] = (manifest_roles[role]["model"], llm["roles"][role]["model"])
        problems += [f"{name} differs from the manifest" for name, (want, got) in expected.items() if want != got]
    if llm["mode"] != "cache-only":
        problems.append("run was not cache-only")
    allowed = (manifest or {}).get("published_cache_misses", 0), (manifest or {}).get("published_not_assessed", 0)
    if (llm["cache_misses"], llm["not_assessed"]) != allowed:
        problems.append(f"{llm['cache_misses']} cache miss(es), {llm['not_assessed']} field(s) not assessed"
                        f" (published run: {allowed[0]} and {allowed[1]})")
    return {"mode": llm["mode"], "provider": llm["provider"], "model": llm["model"],
            "prompt_version": prompt_version(llm), "cache_hits": llm["cache_hits"],
            "cache_misses": llm["cache_misses"], "not_assessed": llm["not_assessed"],
            "reproduces_published_run": not problems,
            "replay_problems": problems,
            "roles": {role: dict(route) for role, route in llm["roles"].items()}}


# --- cache-only scan and full accuracy block ------------------------------------------------

@contextmanager
def forced_cache_only():
    """Make every LLMSession probe cache-only so no provider is contacted."""
    from unittest import mock

    from auditor.llm import LLMSession

    def probe(self):
        self.force_cache_only("forced by dpdp-audit accuracy --cache-only")

    with mock.patch.object(LLMSession, "probe", probe):
        yield


def build_accuracy(report: dict, reference: dict, corpus: dict, *, reference_path: str = str(REFERENCE_PATH),
                   cache_dir: Path = CACHE_DIR) -> dict:
    """Score a scanned Report and return the canonical `accuracy` object (not yet attached)."""
    if report["target"]["commit"] != reference["target"]["commit"]:
        raise ValueError(f"Target revision {report['target']['commit']} does not match the reference pin "
                         f"{reference['target']['commit']}")
    return {"reference_target": score_findings(report["findings"], reference, reference_path=reference_path),
            "labelled_corpus": corpus, "llm": replay_status(report, cache_dir),
            "method": METHOD, "limitations": list(LIMITATIONS)}


def run_accuracy(target: str, *, reference_path: Path = REFERENCE_PATH, cache_dir: Path = CACHE_DIR,
                 provider: str | None = None, model: str | None = None, commit: str | None = None,
                 role_models: dict | None = None, write_manifest_file: bool = False) -> dict:
    """Cache-only scan, scoring and corpus evaluation; returns the validated Report with `accuracy`."""
    from concurrent.futures import ThreadPoolExecutor

    from auditor.scan import run_scan
    from auditor.schema import validate_report

    reference = load_reference(reference_path)
    # The corpus uses its own fixtures and no LLM; it can run while the Target is scanned.
    with forced_cache_only(), ThreadPoolExecutor(max_workers=1) as pool:
        target_report = pool.submit(run_scan, target, commit=commit, provider=provider, model=model,
                                    role_models=role_models, cache_dir=cache_dir)
        corpus = evaluate_corpus()
        report = target_report.result()
    if write_manifest_file:
        write_manifest(report, cache_dir)
    report["accuracy"] = build_accuracy(report, reference, corpus, reference_path=Path(reference_path).as_posix(),
                                        cache_dir=cache_dir)
    validate_report(report)
    return report


def summary_lines(accuracy: dict) -> list[str]:
    lines = []
    primary = accuracy.get("reference_target")
    if primary:
        lines += [f"Reference Target {primary['target']} @ {primary['commit'][:8]} (canonical Findings vs {primary['reference']})",
                  f"  TP={primary['tp']} FP={primary['fp']} FN={primary['fn']}",
                  f"  precision {ratio_text(primary['precision'], primary['tp'], primary['tp'] + primary['fp'])}",
                  f"  recall    {ratio_text(primary['recall'], primary['tp'], primary['tp'] + primary['fn'])}"]
    corpus = accuracy["labelled_corpus"]
    lines.append("Labelled Corpus (Rule emissions on fixtures)")
    for row in [*corpus["rules"], {"rule_id": "TOTAL", **corpus["totals"]}]:
        lines.append(f"  {row['rule_id']}: TP={row['tp']} FP={row['fp']} FN={row['fn']} TN={row['tn']} "
                     f"precision {ratio_text(row['precision'], row['tp'], row['tp'] + row['fp'])} "
                     f"recall {ratio_text(row['recall'], row['tp'], row['tp'] + row['fn'])}")
    llm = accuracy.get("llm")
    if llm:
        lines.append(f"LLM {llm['mode']} {llm['provider']}/{llm['model']} prompts [{llm['prompt_version']}]: "
                     f"{llm['cache_hits']} hit(s), {llm['cache_misses']} miss(es), {llm['not_assessed']} not assessed; "
                     f"reproduces published run: {'yes' if llm['reproduces_published_run'] else 'no'}")
        lines += [f"  - {p}" for p in llm["replay_problems"]]
        lines += [f"LLM role {role}: {route['provider']}/{route['model']}" for role, route in role_overrides(llm).items()]
    return lines


# --- accuracy/results.md ---------------------------------------------------------------------

RESULTS_PATH = Path("accuracy/results.md")


def _f1(tp: int, fp: int, fn: int) -> float | None:
    """F1 = 2TP / (2TP + FP + FN); None when there is nothing to score."""
    return ratio(2 * tp, 2 * tp + fp + fn)


def per_issue_type(primary: dict, reference: dict) -> dict[str, dict]:
    """Static TP/FP/FN, precision, recall and F1 for every Issue Type that appears in the scoring."""
    kind = {e["id"]: e["issue_type"] for e in reference["entries"]}
    rows: dict[str, dict] = {}

    def row(issue_type: str) -> dict:
        return rows.setdefault(issue_type, {"tp": 0, "fp": 0, "fn": 0})

    for match in primary["matches"]:
        row(kind[match["reference_id"]])["tp"] += 1
    for pred in primary["unmatched_predictions"]:
        row(pred["issue_type"])["fp"] += 1
    for ref_id in primary["unmatched_references"]:
        row(kind[ref_id])["fn"] += 1
    for issue_type, r in rows.items():
        r.update(_metrics(r["tp"], r["fp"], r["fn"]))
        r["f1"] = _f1(r["tp"], r["fp"], r["fn"])
    return dict(sorted(rows.items()))


def _live_probe_counts(findings: list[dict]) -> dict[str, dict]:
    counts: dict[str, dict] = {}
    for finding in findings:
        probe = finding.get("live_probe")
        if probe:
            bucket = counts.setdefault(finding["issue_type"], {"Confirmed": 0, "Refuted": 0, "inconclusive": 0})
            bucket[probe["result"]] += 1
    return counts


def _fmt(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.4f}"


def render_results_markdown(report: dict, reference: dict, *, command: str, digest: str) -> str:
    """Deterministic `accuracy/results.md` from a scored Report; Live Probe outcomes stay out of static figures."""
    accuracy = report["accuracy"]
    primary, corpus, llm = accuracy["reference_target"], accuracy["labelled_corpus"], accuracy["llm"]
    target = report["target"]
    confirmed = [e for e in reference["entries"] if e["status"] == "confirmed"]
    undeterminable = [e for e in reference["entries"] if e["status"] != "confirmed"]
    by_type = per_issue_type(primary, reference)
    probes = _live_probe_counts(report.get("findings", []))
    probe_run = any(f.get("live_probe") for f in report.get("findings", []))
    f1 = _f1(primary["tp"], primary["fp"], primary["fn"])

    def ids(values: list[str]) -> str:
        return ", ".join(values) if values else "none"

    lines = ["# Measured accuracy", "",
             f"- Target: {target['name']} pinned at `{target['commit']}`",
             f"- Reference: `{primary['reference']}` ({len(confirmed)} confirmed, "
             f"{len(undeterminable)} not-determinable and excluded from scoring)",
             f"- Command: `{command}`",
             f"- Rules digest: `{digest}`", "",
             "## Static scoring (Reference Target)", "",
             "Static figures count only deterministic Findings. Live Probe outcomes are never added to them.", "",
             "| Issue Type | TP | FP | FN | Precision | Recall | F1 | Live Probe confirmations |",
             "|---|---|---|---|---|---|---|---|"]

    def probe_cell(issue_type: str) -> str:
        if not probe_run:
            return "not run"
        c = probes.get(issue_type)
        return "none" if not c else f"{c['Confirmed']} confirmed, {c['Refuted']} refuted, {c['inconclusive']} inconclusive"

    for issue_type, r in by_type.items():
        lines.append(f"| {issue_type} | {r['tp']} | {r['fp']} | {r['fn']} | {_fmt(r['precision'])} | "
                     f"{_fmt(r['recall'])} | {_fmt(r['f1'])} | {probe_cell(issue_type)} |")
    lines.append(f"| **Overall** | {primary['tp']} | {primary['fp']} | {primary['fn']} | {_fmt(primary['precision'])} | "
                 f"{_fmt(primary['recall'])} | {_fmt(f1)} | "
                 + ("not run" if not probe_run else
                    f"{sum(c['Confirmed'] for c in probes.values())} confirmed (not in static figures)") + " |")
    lines += ["", "## Reference entries", "",
              f"- Matched ({len(primary['matches'])}): " + ids([m["reference_id"] for m in primary["matches"]]),
              f"- Missed ({len(primary['unmatched_references'])}): " + ids(primary["unmatched_references"]),
              f"- Not-determinable, excluded ({len(undeterminable)}): " + ids(sorted(e["id"] for e in undeterminable)),
              f"- Unmatched predictions ({len(primary['unmatched_predictions'])}): "
              + ids([f"{p['finding_id']} ({p['reason']})" for p in primary["unmatched_predictions"]]),
              f"- Excluded predictions ({len(primary['excluded_predictions'])}): "
              + ids([p["finding_id"] for p in primary["excluded_predictions"]]),
              "", "## Live Probe confirmations", ""]
    if not probe_run:
        lines.append("not run: no Finding in this Report carries a Live Probe outcome.")
    else:
        lines += ["| Issue Type | Confirmed | Refuted | inconclusive |", "|---|---|---|---|"]
        lines += [f"| {t} | {c['Confirmed']} | {c['Refuted']} | {c['inconclusive']} |" for t, c in sorted(probes.items())]
    totals = corpus["totals"]
    lines += ["", "## Labelled Corpus", "",
              f"{len(corpus['rules'])} Rules, one positive and one near-miss negative each (Rule emissions on fixtures).", "",
              "| | TP | FP | FN | TN | Precision | Recall |", "|---|---|---|---|---|---|---|",
              f"| **Total** | {totals['tp']} | {totals['fp']} | {totals['fn']} | {totals['tn']} | "
              f"{_fmt(totals['precision'])} | {_fmt(totals['recall'])} |"]
    failing = [r["rule_id"] for r in corpus["rules"] if r["fp"] or r["fn"]]
    lines += ["", "Rules with a corpus FP or FN: " + ids(failing),
              "", "## LLM replay", "",
              f"- Mode: {llm['mode']} ({llm['provider']}/{llm['model']}); prompts: {llm['prompt_version']}",
              f"- Cache: {llm['cache_hits']} hit(s), {llm['cache_misses']} miss(es), {llm['not_assessed']} not assessed",
              f"- Reproduces published run: {'yes' if llm['reproduces_published_run'] else 'no'}"]
    lines += [f"  - {p}" for p in llm["replay_problems"]]
    lines += [f"- LLM role {role}: {route['provider']}/{route['model']}" for role, route in role_overrides(llm).items()]
    lines += ["", "## Method", "", accuracy["method"], "", "## Limitations", ""]
    lines += [f"- {item}" for item in accuracy["limitations"]]
    return "\n".join(lines) + "\n"


def write_results(report: dict, reference: dict, *, command: str, path: Path = RESULTS_PATH) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_results_markdown(report, reference, command=command, digest=rules_digest()),
                    encoding="utf-8")
    return path
