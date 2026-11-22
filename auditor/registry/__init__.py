"""Provision registry for the DPDP Act 2023, DPDP Rules 2025 and allied instruments.

Entries live in ``act.yaml``, ``rules.yaml`` and ``allied.yaml`` beside this module.
``load_registry`` validates every entry and every ``parent``/``penalty_parent`` link.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from typing import Any

import yaml

SOURCE_FILES = ("act.yaml", "rules.yaml", "allied.yaml")
DPDP_KINDS = frozenset({"dpdp-act", "dpdp-rule"})
KINDS = DPDP_KINDS | {"allied", "cwe", "owasp"}
INSTRUMENTS = frozenset(
    {
        "DPDP Act 2023",
        "DPDP Rules 2025",
        "Aadhaar Act 2016",
        "Aadhaar (Sharing of Information) Regulations 2016",
        "IT Act 2000",
        "CWE",
        "OWASP",
    }
)
PENALTY_CEILINGS_INR_CRORE = frozenset({250, 200, 150, 50})
# Units without a crore ceiling of their own: section 15 (Rs 10,000) and the Act's Schedule.
UNCAPPED_ID_PREFIXES = ("DPDP-Act-15", "DPDP-Act-Schedule")
FIELDS = (
    "id",
    "instrument",
    "kind",
    "citation",
    "title",
    "excerpt",
    "parent",
    "penalty_parent",
    "penalty_ceiling_inr_crore",
    "enforceable_from",
    "enforceable_basis",
    "source",
    "verified",
)


@dataclass(frozen=True)
class Source:
    document: str
    url: str


@dataclass(frozen=True)
class Provision:
    id: str
    instrument: str
    kind: str
    citation: str
    title: str
    excerpt: str
    parent: str | None
    penalty_parent: str | None
    penalty_ceiling_inr_crore: int | None
    enforceable_from: dt.date | None
    enforceable_basis: str | None
    source: Source
    verified: bool


def _as_date(value: Any, where: str) -> dt.date | None:
    if value is None:
        return None
    if isinstance(value, str):
        try:
            return dt.date.fromisoformat(value)
        except ValueError:
            raise ValueError(f"{where}: enforceable_from {value!r} is not an ISO date") from None
    if isinstance(value, dt.date) and not isinstance(value, dt.datetime):
        return value
    raise ValueError(f"{where}: enforceable_from must be an ISO date, got {value!r}")


def _parse_entry(raw: Any, origin: str) -> Provision:
    if not isinstance(raw, dict):
        raise ValueError(f"{origin}: every entry must be a mapping, got {raw!r}")
    missing = [name for name in FIELDS if name not in raw]
    if missing:
        raise ValueError(f"{origin}: {raw.get('id', '<no id>')}: missing fields {missing}")
    pid = raw["id"]
    if not isinstance(pid, str) or not pid:
        raise ValueError(f"{origin}: entry id must be a non-empty string")
    where = f"{origin}: {pid}"
    if raw["instrument"] not in INSTRUMENTS:
        raise ValueError(f"{where}: unknown instrument {raw['instrument']!r}")
    if raw["kind"] not in KINDS:
        raise ValueError(f"{where}: unknown kind {raw['kind']!r}")
    if not isinstance(raw["verified"], bool):
        raise ValueError(f"{where}: verified must be true or false")
    source = raw["source"]
    if not isinstance(source, dict) or set(source) != {"document", "url"}:
        raise ValueError(f"{where}: source must map exactly document and url")
    enforceable_from = _as_date(raw["enforceable_from"], where)
    ceiling = raw["penalty_ceiling_inr_crore"]
    if raw["kind"] in DPDP_KINDS:
        if enforceable_from is None:
            raise ValueError(f"{where}: DPDP entries need enforceable_from")
        if ceiling is None:
            if not pid.startswith(UNCAPPED_ID_PREFIXES):
                raise ValueError(f"{where}: penalty_ceiling_inr_crore is required")
        elif ceiling not in PENALTY_CEILINGS_INR_CRORE:
            raise ValueError(
                f"{where}: penalty_ceiling_inr_crore {ceiling!r} is not one of 250, 200, 150, 50"
            )
        elif raw["penalty_parent"] is None:
            raise ValueError(f"{where}: penalty_parent is required when a ceiling applies")
    else:
        for name in ("parent", "penalty_parent", "penalty_ceiling_inr_crore", "enforceable_basis"):
            if raw[name] is not None:
                raise ValueError(f"{where}: {name} must be null for non-DPDP entries")
        if enforceable_from is not None:
            raise ValueError(f"{where}: enforceable_from must be null for non-DPDP entries")
    return Provision(
        id=pid,
        instrument=raw["instrument"],
        kind=raw["kind"],
        citation=raw["citation"],
        title=raw["title"],
        excerpt=raw["excerpt"],
        parent=raw["parent"],
        penalty_parent=raw["penalty_parent"],
        penalty_ceiling_inr_crore=ceiling,
        enforceable_from=enforceable_from,
        enforceable_basis=raw["enforceable_basis"],
        source=Source(document=source["document"], url=source["url"]),
        verified=raw["verified"],
    )


def build_registry(documents: Mapping[str, str]) -> dict[str, Provision]:
    """Index YAML documents (origin name -> text) by id and validate their links."""
    registry: dict[str, Provision] = {}
    for origin, text in documents.items():
        entries = yaml.safe_load(text) or []
        if not isinstance(entries, list):
            raise ValueError(f"{origin}: top level must be a list of entries")
        for raw in entries:
            provision = _parse_entry(raw, origin)
            if provision.id in registry:
                raise ValueError(f"duplicate provision id {provision.id!r} in {origin}")
            registry[provision.id] = provision
    for provision in registry.values():
        links = (("parent", provision.parent), ("penalty_parent", provision.penalty_parent))
        for name, link in links:
            if link is not None and link not in registry:
                raise ValueError(
                    f"{provision.id}: {name} {link!r} does not resolve to a known provision"
                )
    return registry


@lru_cache(maxsize=1)
def load_registry() -> dict[str, Provision]:
    """Load and validate every registry file shipped beside this module."""
    package = resources.files(__package__)
    return build_registry(
        {name: package.joinpath(name).read_text(encoding="utf-8") for name in SOURCE_FILES}
    )


def get(provision_id: str) -> Provision:
    """Return one provision; raises KeyError for an unknown id."""
    try:
        return load_registry()[provision_id]
    except KeyError:
        raise KeyError(f"unknown provision id {provision_id!r}") from None
