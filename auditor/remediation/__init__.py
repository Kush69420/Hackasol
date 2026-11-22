"""Issue Type catalogue: the written fix and provision mapping for each Issue Type.

Data lives in catalogue.yaml, one entry per Issue Type in docs/issue-types.md.
Lookups never touch the LLM layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from importlib import resources

import yaml


@dataclass(frozen=True)
class IssueType:
    id: str
    title: str
    group: str
    primary: str
    related: tuple[str, ...]
    ceiling_parent: str
    gate: str | None
    verify: tuple[str, ...]
    kind_default: str
    guidance: str


@cache
def load_catalogue() -> dict[str, IssueType]:
    """Return every Issue Type keyed by id, in catalogue order."""
    text = resources.files(__package__).joinpath("catalogue.yaml").read_text(encoding="utf-8")
    catalogue: dict[str, IssueType] = {}
    for entry in yaml.safe_load(text):
        fields = {**entry, "related": tuple(entry["related"]), "verify": tuple(entry["verify"])}
        issue = IssueType(**fields)
        if issue.id in catalogue:
            raise ValueError(f"duplicate Issue Type id {issue.id}")
        catalogue[issue.id] = issue
    return catalogue


def guidance_for(issue_type_id: str) -> str:
    """Return the written fix for an Issue Type. Raises KeyError for unknown ids."""
    return load_catalogue()[issue_type_id].guidance
