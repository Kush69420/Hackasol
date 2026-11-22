"""Derive Exposure only from positive Evidence."""
from dataclasses import dataclass


class ExposureUnresolved(ValueError):
    """No Evidence supports an Exposure level."""


@dataclass(frozen=True)
class ExposureDecision:
    level: str
    derived_from: list[dict]


def decide_exposure(*, authenticated: bool | None, open_registration_evidence: list | None = None,
                    outbound_third_party: list | None = None, outside_india: list | None = None,
                    closed_membership: list | None = None, restricted: list | None = None,
                    route_evidence: list | None = None) -> ExposureDecision:
    if authenticated is False and not route_evidence:
        raise ExposureUnresolved("An unauthenticated route requires route Evidence")
    if outside_india:
        return ExposureDecision("Cross-Border", list(outside_india))
    if authenticated is False:
        return ExposureDecision("Public", list(route_evidence))
    if authenticated is True and open_registration_evidence:
        return ExposureDecision("Public", list(open_registration_evidence))
    if outbound_third_party:
        return ExposureDecision("Third-Party", list(outbound_third_party))
    if closed_membership:
        return ExposureDecision("Internal-Broad", list(closed_membership))
    if restricted:
        return ExposureDecision("Internal-Restricted", list(restricted))
    raise ExposureUnresolved("No Evidence supports an Exposure level")
