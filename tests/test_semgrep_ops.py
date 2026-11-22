"""Semgrep operation rules: corpus pairs, pinned-target matches and operation-step linking (issue #4)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from auditor.exclusions import iter_target_files
from auditor.semgrep import operation_steps, run_semgrep

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "targets/juice-shop"
OPERATIONS_DIR = ROOT / "rules/semgrep/operations"
CORPUS_DIR = ROOT / "corpus/operations"
OPERATIONS = {"Store", "Log", "Transfer", "Expose"}
LOGIN = "frontend/src/app/login/login.component.ts"
CHANGE_PASSWORD = "routes/changePassword.ts"


def _load_rules() -> dict[str, dict]:
    rules: dict[str, dict] = {}
    for path in sorted(OPERATIONS_DIR.glob("*.yaml")):
        for rule in yaml.safe_load(path.read_text())["rules"]:
            assert rule["id"] not in rules, f"duplicate rule id {rule['id']}"
            rules[rule["id"]] = rule
    return rules


RULES = _load_rules()
CORPUS = sorted(path.relative_to(ROOT).as_posix() for path in CORPUS_DIR.glob("*/*.ts"))


@pytest.fixture(scope="module")
def corpus_matches() -> list[dict]:
    return run_semgrep(ROOT, CORPUS, [OPERATIONS_DIR])


@pytest.fixture(scope="module")
def target_matches() -> list[dict]:
    files, _ = iter_target_files(TARGET, "juice-shop")
    return run_semgrep(TARGET, files, [OPERATIONS_DIR])


def _element(element_id: str, kind: str, model: str | None = None, field: str | None = None) -> dict:
    return {"id": element_id, "name": element_id.split(".")[-1], "kind": kind, "data_category": None,
            "status": "deterministic", "signals": [], "llm": None, "model": model, "field": field,
            "source": {"file": LOGIN, "start_line": 1, "end_line": 1}}


def _match(rule_id: str, metavars: dict[str, str]) -> dict:
    return {"rule_id": rule_id, "metadata": RULES[rule_id]["metadata"], "file": "routes/x.ts",
            "start_line": 10, "end_line": 12, "excerpt": "", "metavars": metavars}


@pytest.mark.parametrize("rule_id", sorted(RULES))
def test_rule_declares_operation_and_corpus_pair(rule_id: str) -> None:
    rule = RULES[rule_id]
    meta = rule["metadata"]
    assert meta["kind"] == "operation"
    assert meta["operation"] in OPERATIONS
    assert rule_id.startswith(f"op-{meta['operation'].lower()}-")
    assert meta["stage"]
    assert meta["corpus"] == {"positive": f"corpus/operations/{rule_id}/positive.ts",
                              "negative": f"corpus/operations/{rule_id}/negative.ts"}
    for path in meta["corpus"].values():
        assert (ROOT / path).is_file(), path
    patterns = json.dumps(rule["patterns"])
    assert "$VAR" in patterns or "$FIELD" in patterns, "rule must capture the data expression"


@pytest.mark.parametrize("rule_id", sorted(RULES))
def test_corpus_pair_matches_as_labelled(rule_id: str, corpus_matches: list[dict]) -> None:
    hit_files = {m["file"] for m in corpus_matches if m["rule_id"] == rule_id}
    assert f"corpus/operations/{rule_id}/positive.ts" in hit_files, f"{rule_id}: positive corpus not matched"
    assert f"corpus/operations/{rule_id}/negative.ts" not in hit_files, f"{rule_id}: negative corpus matched"


def test_pinned_target_localstorage_email_write(target_matches: list[dict]) -> None:
    hits = [m for m in target_matches if m["rule_id"] == "op-store-localstorage-set" and m["file"] == LOGIN]
    assert [(m["start_line"], m["metavars"]["$K"]) for m in hits] == [
        (106, "'email'"), (118, "'totp_tmp_token'"), (150, "'token'")]
    assert "localStorage.setItem" in hits[0]["excerpt"]


def test_pinned_target_user_model_write_is_found_and_masked(target_matches: list[dict]) -> None:
    hits = [m for m in target_matches
            if m["rule_id"] == "op-store-sequelize-update" and m["file"] == CHANGE_PASSWORD]
    assert [m["start_line"] for m in hits] == [51]
    assert "newPasswordInString" in hits[0]["metavars"]["$VAR"]
    assert "newPasswordInString" not in hits[0]["excerpt"]


def test_pinned_target_matches_stay_in_scope(target_matches: list[dict]) -> None:
    out_of_scope = [m["file"] for m in target_matches
                    if m["file"].startswith(("test/", "data/static/codefixes/", "node_modules/"))
                    or m["file"].endswith(".spec.ts")]
    assert out_of_scope == []


def test_localstorage_email_links_to_storage_element(target_matches: list[dict]) -> None:
    steps = operation_steps([m for m in target_matches if m["file"] == LOGIN],
                            [_element("storage:localStorage.email", "storage-key")])
    assert steps == [{
        "element_id": "storage:localStorage.email",
        "operation": "Store",
        "stage": "storage",
        "source": {"file": LOGIN, "start_line": 106, "end_line": 106},
        "origin": "semgrep:op-store-localstorage-set",
        "relation": "evidenced",
        "note": "localStorage key email",
    }]


def test_user_password_write_links_to_model_field_by_unique_name(target_matches: list[dict]) -> None:
    steps = operation_steps([m for m in target_matches if m["file"] == CHANGE_PASSWORD],
                            [_element("model:User.password", "model-field", "User", "password")])
    assert [(s["element_id"], s["stage"], s["source"]["start_line"]) for s in steps] == [
        ("model:User.password", "model", 51)]


def test_storage_link_needs_the_same_storage_type() -> None:
    match = _match("op-store-sessionstorage-set", {"$K": "'email'", "$VAR": "user.email"})
    assert operation_steps([match], [_element("storage:localStorage.email", "storage-key")]) == []


def test_receiver_naming_another_model_does_not_link() -> None:
    match = _match("op-store-sequelize-create", {"$M": "CardModel", "$VAR": "{ email: req.body.email }"})
    assert operation_steps([match], [_element("model:User.email", "model-field", "User", "email")]) == []


def test_instance_receiver_with_ambiguous_field_does_not_link() -> None:
    match = _match("op-store-sequelize-update", {"$M": "user", "$VAR": "{ email: req.body.email }"})
    elements = [_element("model:User.email", "model-field", "User", "email"),
                _element("model:Card.email", "model-field", "Card", "email")]
    assert operation_steps([match], elements) == []


def test_unreferenced_data_is_dropped() -> None:
    match = _match("op-expose-response-json", {"$VAR": "user"})
    assert operation_steps([match], [_element("model:User.email", "model-field", "User", "email")]) == []


def test_model_receiver_links_and_duplicates_collapse() -> None:
    match = _match("op-store-sequelize-create", {"$M": "UserModel", "$VAR": "{ email: req.body.email }"})
    steps = operation_steps([match, dict(match)], [_element("model:User.email", "model-field", "User", "email")])
    assert [(s["element_id"], s["note"]) for s in steps] == [("model:User.email", "email referenced in $VAR")]


def test_out_of_scope_files_are_never_matched(tmp_path: Path) -> None:
    body = "export function remember (user: any) {\n  localStorage.setItem('email', user.email)\n}\n"
    for rel in ("frontend/src/app/keep.ts", "test/api/skipped.ts",
                "data/static/codefixes/skipped.ts", "frontend/src/app/keep.spec.ts"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(body)
    files, _ = iter_target_files(tmp_path, "juice-shop")
    matches = run_semgrep(tmp_path, files, [OPERATIONS_DIR])
    assert {m["file"] for m in matches if m["rule_id"] == "op-store-localstorage-set"} == {
        "frontend/src/app/keep.ts"}
