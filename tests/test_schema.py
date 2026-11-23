"""Contract tests for the Finding / Report schema and its cross-field validator."""

import pytest

from auditor.schema import SCHEMA_VERSION, ReportValidationError, validate_finding, validate_report

CACHE_KEY = "a" * 64
CVSS_VECTOR = "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N"
NOT_SCORED_CVSS = {"status": "n/a", "reason": "No attack path; Risk Matrix band applies."}


def evidence(file="src/server.ts", start=10, end=12):
    return {"file": file, "start_line": start, "end_line": end, "excerpt": "logger.info(user.email)"}


def element(name="email", data_category="Contact"):
    return {"name": name, "data_category": data_category, "evidence": evidence()}


def assessed(value):
    return {
        "status": "assessed",
        "value": value,
        "cache_key": CACHE_KEY,
        "provider": "anthropic",
        "model": "claude-test",
        "prompt_version": "fix-v1",
    }


def not_assessed():
    return {"status": "not assessed", "cache_key": CACHE_KEY}


def finding(**overrides):
    base = {
        "id": "SEC-01-0123456789ab",
        "issue_type": "SEC-01",
        "rules_fired": ["logging.personal-data"],
        "kind": "security-personal-data",
        "classification": "technical",
        "evidence": [evidence()],
        "data_flow": [],
        "personal_data_element": element(),
        "data_category": "Contact",
        "processing_operation": "Log",
        "exposure": {"level": "Internal-Broad", "derived_from": [evidence()]},
        "primary_provision": "DPDP-Rule-6(1)(a)",
        "other_provisions": ["CWE-532"],
        "penalty_ceiling": {"parent_section": "DPDP-Act-8(5)", "amount_inr_crore": 250},
        "enforceable_from": "2027-05-14",
        "cvss": {"status": "scored", "vector": CVSS_VECTOR, "score": 6.9},
        "risk_matrix": {"tier": "A", "exposure": "Internal-Broad", "cell": "high"},
        "severity": {"band": "high", "justification": "Contact data reaches a shared log."},
        "recommended_fix": {
            "guidance": "Mask the identifier before it reaches the log sink.",
            "tailored": not_assessed(),
        },
        "status": "open",
        "legal_review": None,
        "llm_triage": not_assessed(),
        "live_probe": None,
        "fix_patch": None,
    }
    base.update(overrides)
    return base


def make_report(findings=(), mode="live", reason=None, **overrides):
    report = {
        "schema_version": SCHEMA_VERSION,
        "tool": {"name": "dpdp-audit", "version": "0.1.0"},
        "target": {"name": "fixture-app", "source": "targets/fixture-app", "kind": "path", "commit": None},
        "scan": {
            "started_at": "2026-11-22T10:00:00Z",
            "finished_at": "2026-11-22T10:01:00Z",
            "exclusions": ["node_modules/"],
            "files_scanned": 12,
            "files_excluded": 3,
            "rule_count": 40,
        },
        "llm": {
            "mode": mode,
            "provider": "anthropic",
            "model": "claude-test",
            "prompt_versions": {"triage": "triage-v1"},
            "cache_hits": 0,
            "cache_misses": 0,
            "not_assessed": 0,
            "reason": reason,
        },
        "applicability_assumptions": [
            {
                "id": "AA-1",
                "text": "The Target Application processes Personal Data of Data Principals in India.",
                "provisions": ["DPDP-Act-4(1)"],
            }
        ],
        "personal_data_map": [],
        "findings": list(findings),
        "observations": [],
        "coverage_matrix": [],
        "consent_assessment": None,
    }
    report.update(overrides)
    return report


def test_empty_live_report_is_valid():
    validate_report(make_report())


def test_measured_accuracy_is_optional_but_shaped():
    from tests.test_accuracy import accuracy_report

    validate_report(make_report())
    validate_report(make_report(accuracy=accuracy_report()["accuracy"]))
    with pytest.raises(ReportValidationError):
        validate_report(make_report(accuracy={"precision": 0.9, "recall": 0.8}))


def test_empty_cache_only_report_is_valid():
    validate_report(make_report(mode="cache-only", reason="No provider reachable; replaying cached verdicts."))


def test_technical_finding_is_valid():
    validate_finding(finding())
    validate_report(make_report([finding()]))


def test_compliance_gap_without_attack_path_is_valid():
    validate_finding(
        finding(
            id="CON-01-0123456789ab",
            issue_type="CON-01",
            kind="dpdp-obligation",
            classification="compliance-gap",
            cvss=NOT_SCORED_CVSS,
            primary_provision="DPDP-Act-4(1)",
            severity={"band": "medium", "justification": "Processing runs without a legitimate use check."},
        )
    )


def test_safeguard_without_personal_data_element_is_valid():
    validate_finding(
        finding(
            id="SEC-16-0123456789ab",
            issue_type="SEC-16",
            kind="safeguard",
            personal_data_element=None,
            data_category="Authentication Secret",
            processing_operation=None,
        )
    )


def test_disclosure_at_medium_with_legal_review_is_valid():
    validate_finding(
        finding(
            id="TRF-02-0123456789ab",
            issue_type="TRF-02",
            kind="dpdp-obligation",
            classification="disclosure",
            cvss=NOT_SCORED_CVSS,
            severity={"band": "medium", "justification": "Personal Data stored outside India."},
            status="needs-legal-review",
            legal_review={
                "readings": [
                    {"provision": "DPDP-Act-16(1)", "reading": "Destination is not restricted, so the transfer is lawful."},
                    {"provision": "DPDP-Rule-15", "reading": "Foreign-State access rules may apply."},
                ]
            },
            primary_provision="DPDP-Act-16(1)",
            processing_operation="Transfer",
            exposure={"level": "Cross-Border", "derived_from": [evidence()]},
            risk_matrix={"tier": "B", "exposure": "Cross-Border", "cell": "medium"},
            penalty_ceiling={"parent_section": "DPDP-Act-Schedule-7", "amount_inr_crore": 50},
        )
    )


def test_full_report_with_every_section_is_valid():
    full = finding(
        data_flow=[{"operation": "Log", "evidence": evidence(start=20, end=24), "note": "request logger"}],
        other_provisions=["CWE-532", "DPDP-Rule-8(3)"],
        llm_triage=assessed({"verdict": "true-positive", "reason": "The email is written to the request log."}),
        recommended_fix={
            "guidance": "Mask the identifier before it reaches the log sink.",
            "tailored": assessed("Replace the email with a salted hash in the logger call."),
        },
    )
    observation = {
        "id": "OBS-0123456789ab",
        "title": "Debug banner in production configuration",
        "rules_fired": ["config.debug-mode"],
        "evidence": [evidence(file="config/prod.json", start=3, end=3)],
        "references": ["CWE-489"],
        "recommended_fix": "Disable debug mode in production configuration.",
    }
    report = make_report(
        [full],
        personal_data_map=[
            {
                "element": element(),
                "operations": [{"operation": "Log", "evidence": evidence(), "note": "request logger"}],
            }
        ],
        observations=[observation],
    )

    validate_report(report)


REJECTED_FINDINGS = {
    "absolute evidence path": {"evidence": [evidence(file="/etc/passwd")]},
    "parent-relative evidence path": {"evidence": [evidence(file="../outside.ts")]},
    "start_line below 1": {"evidence": [evidence(start=0, end=1)]},
    "end_line before start_line": {"evidence": [evidence(start=12, end=10)]},
    "unknown status": {"status": "closed"},
    "technical finding without a scored CVSS": {"cvss": NOT_SCORED_CVSS},
    "compliance gap with a scored CVSS": {
        "classification": "compliance-gap",
        "cvss": {"status": "scored", "vector": CVSS_VECTOR, "score": 6.9},
    },
    "scored CVSS without a vector": {"cvss": {"status": "scored", "score": 6.9}},
    "disclosure above medium": {
        "classification": "disclosure",
        "cvss": NOT_SCORED_CVSS,
        "severity": {"band": "high", "justification": "Cross-border flow."},
    },
    "needs-legal-review without legal_review": {"status": "needs-legal-review", "legal_review": None},
    "safeguard with a personal data element": {"kind": "safeguard"},
    "live probe populated": {"live_probe": {"verdict": "Confirmed"}},
}


@pytest.mark.parametrize("overrides", list(REJECTED_FINDINGS.values()), ids=list(REJECTED_FINDINGS))
def test_invalid_finding_is_rejected(overrides):
    with pytest.raises(ReportValidationError):
        validate_finding(finding(**overrides))


def test_cache_only_report_without_reason_is_rejected():
    with pytest.raises(ReportValidationError):
        validate_report(make_report(mode="cache-only", reason=None))


def test_duplicate_finding_ids_are_rejected():
    with pytest.raises(ReportValidationError, match="duplicate finding id SEC-01-0123456789ab"):
        validate_report(make_report([finding(), finding()]))
