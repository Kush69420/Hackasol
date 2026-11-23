"""Semgrep operation layer for issue #4: match Processing Operations and link them to Elements.

ADR 0003: Semgrep is intra-function only. Each match is one call site, and a match becomes an
Operation step only when a metavariable at that call site names an Element. A match that names
none is dropped, so Semgrep never creates an operation on its own.

Linking, by Element kind:
- storage-key `storage:<type>.<key>`: the rule's `storage` metadata equals <type>, and `$K`
  (quotes removed) equals <key>.
- model-field `model:<Model>.<field>` and collection-field `collection:<name>.<field>`: a data
  metavariable (`$VAR` or `$FIELD`) reads <field> as a property (`x.field`, `field:`, `{field}`,
  `x['field']`). A receiver (`$M` or `$C`) named ...Model or ...Collection must name <Model> or
  <name>. Any other receiver needs <field> to belong to exactly one owner.

Metavariable text is raw code and feeds linking only. It is never copied into a Report; excerpts
are masked.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
import re
import shutil
import subprocess
import sys
from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path

import yaml

from auditor.masking import mask_for_report

_CHUNK_SIZE = 200
_DATA_METAVARS = ("$VAR", "$FIELD")
_MODEL_KINDS = frozenset({"model-field", "collection-field"})
_CLASS_SUFFIXES = ("Model", "Collection")
_QUOTES = "'\"`"


def run_semgrep(root: Path, files: Iterable[str | Path], config_dirs: Sequence[Path]) -> list[dict]:
    """Run the operation rules over exactly `files` and return one dict per match.

    `files` are relative to `root` or absolute under it; the caller chooses them, and exclusions
    come from iter_target_files. Each dict has rule_id, metadata, file (posix, relative to root),
    start_line, end_line, excerpt (masked) and metavars ({"$NAME": raw code text}).
    """
    root = root.resolve()
    rel_files = [(root / file).resolve().relative_to(root).as_posix() for file in files]
    if not rel_files:
        return []
    cache_path = _cache_path(root, rel_files, [Path(d).resolve() for d in config_dirs])
    try:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    matches = _run_semgrep_uncached(root, rel_files, config_dirs)
    _store(cache_path, matches)
    return matches


def _store(cache_path: Path, matches: list[dict]) -> None:
    tmp = None
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        cache_path.parent.chmod(0o700)
        fd, name = tempfile.mkstemp(prefix=".semgrep-", suffix=".tmp", dir=cache_path.parent)
        tmp = Path(name)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(matches, stream)
        tmp.replace(cache_path)
    except OSError:
        pass
    finally:
        if tmp is not None:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass


def _cache_path(root: Path, rel_files: list[str], config_dirs: Sequence[Path]) -> Path:
    """Result cache keyed by Semgrep version, the exact rule YAML bytes and every scanned file's bytes,
    so any Rule or Target change is a miss."""
    try:
        version = importlib.metadata.version("semgrep")
    except importlib.metadata.PackageNotFoundError:
        version = "unknown"
    digest = hashlib.sha256(f"semgrep-cache-v2-private-masking-v2\0semgrep {version}\0{_SEP}\0".encode())
    for directory in config_dirs:
        for path in sorted(directory.rglob("*.yaml")):
            digest.update(path.relative_to(directory).as_posix().encode() + b"\0" + path.read_bytes() + b"\0")
    for rel in sorted(rel_files):
        data = (root / rel).read_bytes()
        digest.update(rel.encode() + b"\0" + hashlib.sha256(data).digest())
    base = Path(os.environ.get("DPDP_SEMGREP_CACHE") or Path(__file__).resolve().parents[1] / ".dpdp-cache" / "semgrep")
    return base / f"{digest.hexdigest()}.json"


def _run_semgrep_uncached(root: Path, rel_files: list[str], config_dirs: Sequence[Path]) -> list[dict]:
    binary = _semgrep_binary()
    with tempfile.TemporaryDirectory(prefix="dpdp-semgrep-") as tmp:
        config, bound = _binding_config([Path(d).resolve() for d in config_dirs], Path(tmp))

        def scan(start: int) -> list[dict]:
            command = [binary, "scan", "--json", "--quiet", "--metrics=off", "--disable-version-check",
                       "--no-git-ignore", "--config", str(config), *rel_files[start:start + _CHUNK_SIZE]]
            proc = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
            if proc.returncode != 0:
                raise RuntimeError(f"semgrep exited {proc.returncode}: {proc.stderr.strip()[-2000:]}")
            report = json.loads(proc.stdout)
            # Warn-level entries (PartialParsing of one construct) leave the rest of the file scanned;
            # only error-level entries mean results are missing.
            fatal = [e for e in report["errors"] if e.get("level") != "warn"]
            if fatal:
                raise RuntimeError(f"semgrep reported {len(fatal)} error(s): {fatal[0]}")
            return [_match_dict(root, result, bound) for result in report["results"]]

        starts = list(range(0, len(rel_files), _CHUNK_SIZE))
        with ThreadPoolExecutor(max_workers=min(len(starts), os.cpu_count() or 4)) as pool:
            return [m for chunk in pool.map(scan, starts) for m in chunk]


def prewarm_semgrep(entries: Sequence[tuple[Path, Sequence[str | Path]]], config_dirs: Sequence[Path]) -> None:
    """Fill the result cache for many independent roots with a few large Semgrep runs.

    Each (root, files) entry is cached exactly as `run_semgrep(root, files, ...)` would store it, so a
    later per-root call is a cache hit. Rules are intra-file (ADR 0003), so a match depends only on its own
    file; matches are split back by path prefix and a root only ever receives matches from its own files.
    """
    dirs = [Path(d).resolve() for d in config_dirs]
    pending = []
    for root, files in entries:
        root = Path(root).resolve()
        rel = [(root / f).resolve().relative_to(root).as_posix() for f in files]
        if rel and not _cache_path(root, rel, dirs).is_file():
            pending.append((root, rel))
    if not pending:
        return
    # Paths are interpreted relative to the scan root, not the common batching root.
    if any("paths" in rule for directory in dirs for path in directory.rglob("*.yaml")
           for rule in (yaml.safe_load(path.read_text()) or {}).get("rules", [])):
        for root, rel in pending:
            _store(_cache_path(root, rel, dirs), _run_semgrep_uncached(root, rel, dirs))
        return
    common = Path(os.path.commonpath([str(r) for r, _ in pending]))
    if all(r == common for r, _ in pending):
        common = common.parent
    prefixes = [r.relative_to(common).as_posix() for r, _ in pending]
    combined = [f"{prefix}/{f}" for prefix, (_, rel) in zip(prefixes, pending) for f in rel]
    matches = _run_semgrep_uncached(common, combined, dirs)
    for prefix, (root, rel) in zip(prefixes, pending):
        mine = [{**m, "file": m["file"][len(prefix) + 1:]} for m in matches if m["file"].startswith(prefix + "/")]
        _store(_cache_path(root, rel, dirs), mine)


# Semgrep OSS JSON carries no metavariable bindings, but it does interpolate metavariables
# into `message`. The rules are copied with a message listing every metavariable they use,
# separated by _SEP, and the bindings are read back by position.
_SEP = "\u241e"
_METAVAR = re.compile(r"\$[A-Z_][A-Z0-9_]*")


def _binding_config(config_dirs: Sequence[Path], tmp: Path) -> tuple[Path, dict[str, list[str]]]:
    rules, bound = [], {}
    for directory in config_dirs:
        for path in sorted(directory.rglob("*.yaml")):
            for rule in (yaml.safe_load(path.read_text()) or {}).get("rules", []):
                body = {k: v for k, v in rule.items() if k not in {"message", "metadata", "id"}}
                names = sorted(set(_METAVAR.findall(yaml.safe_dump(body))))
                bound[rule["id"]] = names
                rules.append({**rule, "message": _SEP + _SEP.join(names)})
    config = tmp / "rules.yaml"
    config.write_text(yaml.safe_dump({"rules": rules}))
    return config, bound


def _metavars(message: str, names: list[str]) -> dict[str, str]:
    values = message.split(_SEP)[1:]
    return {name: value for name, value in zip(names, values) if value != name}


def operation_steps(matches: Sequence[dict], elements: Sequence[dict]) -> list[dict]:
    """Operation steps for the matches that link to an Element; unlinked matches are dropped."""
    model_owners = _model_field_owners(elements)
    steps: list[dict] = []
    seen: set[tuple] = set()
    for match in matches:
        metadata = match["metadata"]
        for element, note in _linked_elements(match, elements, model_owners):
            key = (element["id"], metadata["operation"], match["rule_id"], match["file"],
                   match["start_line"], match["end_line"])
            if key in seen:
                continue
            seen.add(key)
            steps.append({
                "element_id": element["id"],
                "operation": metadata["operation"],
                "stage": metadata["stage"],
                "source": {"file": match["file"], "start_line": match["start_line"],
                           "end_line": match["end_line"]},
                "origin": f"semgrep:{match['rule_id']}",
                "relation": "evidenced",
                "note": note,
            })
    return steps


def _semgrep_binary() -> str:
    """The Semgrep beside sys.executable (the project venv), else the one on PATH."""
    venv_bin = Path(sys.executable).parent / "semgrep"
    if venv_bin.is_file():
        return str(venv_bin)
    found = shutil.which("semgrep")
    if found is None:
        raise RuntimeError("semgrep not found beside sys.executable or on PATH")
    return found


def _match_dict(root: Path, result: dict, bound: dict[str, list[str]]) -> dict:
    extra = result["extra"]
    rule_id = result["check_id"].rsplit(".", 1)[-1]
    start, end = result["start"]["line"], result["end"]["line"]
    lines = (root / result["path"]).read_text(errors="replace").splitlines()[start - 1:end]
    return {
        "rule_id": rule_id,
        "metadata": extra["metadata"],
        "file": result["path"],
        "start_line": start,
        "end_line": end,
        "excerpt": mask_for_report("\n".join(lines)),
        "metavars": _metavars(extra["message"], bound[rule_id]),
    }


def _linked_elements(match: dict, elements: Sequence[dict],
                     model_owners: dict[str, set[str]]) -> Iterator[tuple[dict, str]]:
    metavars = match["metavars"]
    for element in elements:
        if element["kind"] == "storage-key":
            storage_type, key = _split_id(element["id"])
            if match["metadata"].get("storage") == storage_type and _unquote(metavars.get("$K")) == key:
                yield element, f"{storage_type} key {key}"
        elif element["kind"] in _MODEL_KINDS:
            owner, field = _split_id(element["id"])
            data = next((name for name in _DATA_METAVARS
                         if name in metavars and _references(metavars[name], field)), None)
            if data is None or not _owner_matches(metavars, owner, field, model_owners):
                continue
            yield element, f"{field} referenced in {data}"


def _owner_matches(metavars: dict[str, str], owner: str, field: str,
                   model_owners: dict[str, set[str]]) -> bool:
    receiver = metavars.get("$M") or metavars.get("$C")
    if receiver is not None and receiver.rsplit(".", 1)[-1].endswith(_CLASS_SUFFIXES):
        return _handle_name(receiver) == owner.lower()
    return model_owners.get(field) == {owner}


def _model_field_owners(elements: Sequence[dict]) -> dict[str, set[str]]:
    owners: dict[str, set[str]] = {}
    for element in elements:
        if element["kind"] in _MODEL_KINDS:
            owner, field = _split_id(element["id"])
            owners.setdefault(field, set()).add(owner)
    return owners


def _split_id(element_id: str) -> tuple[str, str]:
    """`model:User.email` -> ("User", "email"); `storage:localStorage.email` -> ("localStorage", "email")."""
    _, _, rest = element_id.partition(":")
    owner, _, leaf = rest.partition(".")
    return owner, leaf


def _handle_name(receiver: str) -> str:
    """`UserModel` -> "user"; `db.reviewsCollection` -> "reviews"."""
    name = receiver.rsplit(".", 1)[-1]
    for suffix in _CLASS_SUFFIXES:
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name.lower()


def _references(code: str, field: str) -> bool:
    """True when the code reads `field` as a property, object key, shorthand or string index."""
    name = re.escape(field)
    forms = (
        r"\." + name + r"(?![\w$])",
        r"(?<![\w$.'\"])" + name + r"\s*:",
        r"[{,]\s*" + name + r"\s*[,}]",
        r"\[\s*['\"]" + name + r"['\"]\s*\]",
    )
    return any(re.search(form, code) for form in forms)


def _unquote(text: str | None) -> str | None:
    if text is None:
        return None
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in _QUOTES:
        return text[1:-1]
    return text
