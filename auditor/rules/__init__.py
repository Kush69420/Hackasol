"""Rules: one concrete detector per Issue Type and language/framework/file kind.

Every Rule is a Python ``detect(ctx) -> list[Match]`` registered with ``@rule``. Rules that
need intra-function matching declare Semgrep YAML in ``rules/semgrep/<issue-type>/`` and read
their matches from ``ctx.semgrep_matches(<yaml rule id>)``; cross-file Rules read the inventory,
Elements and Data Flows from the context. Every Rule ships a Labelled Corpus pair:
``corpus/<rule-id>/positive/`` (must fire) and ``corpus/<rule-id>/negative/`` (near miss, must not).
Rule modules live in ``auditor/rules/`` and are imported by ``load_rules``.
"""

from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass
from typing import Callable

from auditor.mapping import Match

REPO_ROOT_RULES = "rules/semgrep"


@dataclass(frozen=True)
class RuleSpec:
    id: str                       # e.g. "SEC-01-ts-morgan-query-secrets"
    issue_type: str               # owning Issue Type, e.g. "SEC-01"
    title: str                    # one line, for the Rules List
    engine: str                   # "semgrep" | "ts-ast" | "config"
    classification: str           # technical | compliance-gap | disclosure
    base_vector: str | None       # CVSS 4.0 base vector (technical only)
    languages: tuple[str, ...]    # e.g. ("typescript",) or ("terraform",)
    semgrep_ids: tuple[str, ...] = ()  # YAML rule ids this Rule consumes


Detector = Callable[["ScanContext"], list[Match]]  # noqa: F821 - defined in auditor.rules.context

_RULES: dict[str, tuple[RuleSpec, Detector]] = {}


def rule(spec: RuleSpec) -> Callable[[Detector], Detector]:
    def register(fn: Detector) -> Detector:
        if spec.id in _RULES:
            raise ValueError(f"duplicate Rule id {spec.id}")
        if not spec.id.startswith(spec.issue_type + "-"):
            raise ValueError(f"Rule id {spec.id} must start with its Issue Type {spec.issue_type}")
        if (spec.classification == "technical") != (spec.base_vector is not None):
            raise ValueError(f"{spec.id}: technical Rules need a base vector; others must not have one")
        _RULES[spec.id] = (spec, fn)
        return fn
    return register


def load_rules() -> dict[str, tuple[RuleSpec, Detector]]:
    """Import every Rule module in this package and return the registry."""
    for info in pkgutil.iter_modules(__path__):
        if info.name not in {"context"}:
            importlib.import_module(f"{__name__}.{info.name}")
    return dict(_RULES)
