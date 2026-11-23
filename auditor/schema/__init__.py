"""Finding / Report JSON contract and its validator.

The schema in ``report.schema.json`` is the contract between the engine and every
output. ``validate_report`` adds the cross-field checks JSON Schema cannot express.
"""

from __future__ import annotations

import json
from functools import cache
from importlib import resources
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

SCHEMA_VERSION = "1.4.0"


class ReportValidationError(ValueError):
    """Raised when a Report or Finding breaks the contract."""

    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


@cache
def report_schema() -> dict[str, Any]:
    return json.loads(resources.files(__package__).joinpath("report.schema.json").read_text())


@cache
def _validator() -> Draft202012Validator:
    return Draft202012Validator(report_schema(), format_checker=FormatChecker())


@cache
def _finding_validator() -> Draft202012Validator:
    schema = report_schema()
    sub = {"$schema": schema["$schema"], "$defs": schema["$defs"], "$ref": "#/$defs/finding"}
    return Draft202012Validator(sub, format_checker=FormatChecker())


def _evidence_items(finding: dict[str, Any]):
    yield from finding.get("evidence", [])
    for step in finding.get("data_flow", []):
        yield step["evidence"]
    if finding.get("personal_data_element"):
        yield finding["personal_data_element"]["evidence"]
    yield from finding.get("exposure", {}).get("derived_from", [])


def _line_errors(finding: dict[str, Any], where: str) -> list[str]:
    return [
        f"{where}: evidence {ev['file']} end_line {ev['end_line']} < start_line {ev['start_line']}"
        for ev in _evidence_items(finding)
        if ev["end_line"] < ev["start_line"]
    ]


def _schema_errors(validator: Draft202012Validator, instance: Any) -> list[str]:
    return [
        f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
        for e in sorted(validator.iter_errors(instance), key=lambda e: list(map(str, e.absolute_path)))
    ]


def validate_finding(finding: dict[str, Any]) -> None:
    errors = _schema_errors(_finding_validator(), finding)
    if not errors:
        errors = _line_errors(finding, finding["id"])
    if errors:
        raise ReportValidationError(errors)


def validate_report(report: dict[str, Any]) -> None:
    errors = _schema_errors(_validator(), report)
    if not errors:
        seen: set[str] = set()
        for f in report["findings"]:
            errors += _line_errors(f, f["id"])
            if f["id"] in seen:
                errors.append(f"duplicate finding id {f['id']}")
            seen.add(f["id"])
    if errors:
        raise ReportValidationError(errors)
