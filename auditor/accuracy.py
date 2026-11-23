"""Measured accuracy: Primary Target scoring, Labelled Corpus evaluation and cache replay provenance.

Two separate populations are scored and never merged:

* Primary Target: canonical Report Findings against the hand-checked reference list.
* Labelled Corpus: each Rule's true positive and near-miss negative, counting Rule emissions.

Everything here is deterministic. Heavy imports (the scan, the Rules) are lazy so the Report
renderer can use `ratio_text` without an import cycle.
"""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
from pathlib import Path, PurePosixPath

REPO = Path(__file__).resolve().parents[1]
REFERENCE_PATH = Path("accuracy/juice-shop.json")
CACHE_DIR = Path("accuracy/cache")
MANIFEST_NAME = "manifest.json"
CACHE_IDENTITY = "sha256(masked snippet + NUL + prompt version + NUL + model [+ NUL + masked context JSON])"

METHOD = (
    "Primary Target: each canonical Finding is one prediction. It matches a confirmed reference entry "
    "when the Issue Type and normalised file path are equal and any Finding Evidence range overlaps the "
    "entry's reviewed anchor range. Matching is one-to-one, in Finding id order, each prediction taking the "
    "lowest-id unmatched entry; a second prediction for a matched entry is a false positive. A Finding that "
    "merges several Rules is one prediction. Labelled Corpus: for each Rule, the positive counts as a true "
    "positive if the Rule emits there (else a false negative) and the negative counts as a false positive if "
    "the Rule emits there (else a true negative); Rule emissions are counted, not merged Findings. "
    "Precision = TP/(TP+FP); recall = TP/(TP+FN); a zero denominator is N/A."
)
LIMITATIONS = (
    "The Primary Target reference list covers one Target Application at one pinned revision; the figures say nothing about any Secondary Target.",
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


# --- Primary Target scoring -----------------------------------------------------------------

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

    rows = []
    for rule_id in sorted(rules):
        pos, neg = emits(rule_id, "positive"), emits(rule_id, "negative")
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
        expected = {"target commit": (manifest["target"]["commit"], report["target"]["commit"]),
                    "Rules digest": (manifest["rules_digest"], rules_digest()),
                    "provider": (manifest["provider"], llm["provider"]),
                    "model": (manifest["model"], llm["model"]),
                    "prompt version": (manifest["prompt_version"], prompt_version(llm))}
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
            "replay_problems": problems}


# --- cache-only scan and full accuracy block ------------------------------------------------

@contextmanager
def forced_cache_only():
    """Make every LLMSession probe cache-only so no provider is contacted."""
    from unittest import mock

    from auditor.llm import LLMSession

    def probe(self):
        self.mode, self.reason = "cache-only", "forced by dpdp-audit accuracy --cache-only"

    with mock.patch.object(LLMSession, "probe", probe):
        yield


def build_accuracy(report: dict, reference: dict, corpus: dict, *, reference_path: str = str(REFERENCE_PATH),
                   cache_dir: Path = CACHE_DIR) -> dict:
    """Score a scanned Report and return the canonical `accuracy` object (not yet attached)."""
    if report["target"]["commit"] != reference["target"]["commit"]:
        raise ValueError(f"Target revision {report['target']['commit']} does not match the reference pin "
                         f"{reference['target']['commit']}")
    return {"primary_target": score_findings(report["findings"], reference, reference_path=reference_path),
            "labelled_corpus": corpus, "llm": replay_status(report, cache_dir),
            "method": METHOD, "limitations": list(LIMITATIONS)}


def run_accuracy(target: str, *, reference_path: Path = REFERENCE_PATH, cache_dir: Path = CACHE_DIR,
                 provider: str | None = None, model: str | None = None, commit: str | None = None,
                 write_manifest_file: bool = False) -> dict:
    """Cache-only scan, scoring and corpus evaluation; returns the validated Report with `accuracy`."""
    from auditor.scan import run_scan
    from auditor.schema import validate_report

    reference = load_reference(reference_path)
    corpus = evaluate_corpus()
    with forced_cache_only():
        report = run_scan(target, commit=commit, provider=provider, model=model, cache_dir=cache_dir)
    if write_manifest_file:
        write_manifest(report, cache_dir)
    report["accuracy"] = build_accuracy(report, reference, corpus, reference_path=Path(reference_path).as_posix(),
                                        cache_dir=cache_dir)
    validate_report(report)
    return report


def summary_lines(accuracy: dict) -> list[str]:
    lines = []
    primary = accuracy.get("primary_target")
    if primary:
        lines += [f"Primary Target {primary['target']} @ {primary['commit'][:8]} (canonical Findings vs {primary['reference']})",
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
    return lines
