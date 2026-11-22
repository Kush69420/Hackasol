"""Assemble deterministic, registry-backed Findings from Rule matches."""
from dataclasses import dataclass
from hashlib import sha256

from auditor import registry, severity
from auditor.exposure import ExposureDecision
from auditor.masking import mask_for_report
from auditor.remediation import guidance_for, load_catalogue
from auditor.schema import validate_finding


@dataclass(frozen=True)
class Match:
    rule_id: str
    issue_type: str
    evidence: list[dict]
    classification: str
    base_vector: str | None
    element: dict | None
    data_category: str | None
    protected_categories: tuple[str, ...]
    processing_operation: str | None
    data_flow: list[dict]
    exposure: ExposureDecision
    nexus_elements: tuple[str, ...] = ()
    gate_evidence: list[dict] | None = None
    primary_override: str | None = None
    legal_review: dict | None = None
    status_hint: str | None = None
    destination_restricted: bool = False
    # Evidence that changes residual risk (e.g. volume encryption under a plain field); the Rule
    # picks a base vector reflecting it and explains the choice here, quoted in the justification.
    severity_note: str | None = None


@dataclass(frozen=True)
class AssemblyResult:
    findings: list[dict]
    observations: list[dict]
    not_determinable: list[dict]


def _unique(items):
    result = []
    for item in items:
        if item not in result:
            result.append(item)
    return result


def _masked(value):
    if isinstance(value, dict):
        return {k: mask_for_report(v) if k == 'excerpt' else _masked(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_masked(v) for v in value]
    return value


def _anchor(match):
    if not match.evidence:
        raise ValueError(f"Rule {match.rule_id} has no primary Evidence")
    ev = match.evidence[0]
    return ev['file'], ev['start_line'], ev['end_line']


def _digest(*parts):
    return sha256('|'.join(map(str, parts)).encode()).hexdigest()[:12]


def _provision(provision_id):
    entry = registry.get(provision_id)
    if entry is None:
        raise ValueError(f"Unknown Provision: {provision_id}")
    return entry


def _primary(match, issue):
    permitted = [issue.primary, *issue.related]
    primary = match.primary_override or issue.primary
    if primary not in permitted:
        raise ValueError(f"Primary Provision {primary} is not owned by {match.issue_type}")
    for provision in permitted:
        _provision(provision)
    return primary


def _category(match):
    if match.element is not None:
        return match.element['data_category']
    if match.protected_categories:
        return severity.highest_category(match.protected_categories)
    if match.data_category:
        return match.data_category
    raise ValueError(f"Rule {match.rule_id} has no protected Data Category")


def _observation(match, issue):
    anchor = _anchor(match)
    return {
        'id': 'OBS-' + _digest(match.issue_type, *anchor),
        'title': issue.title,
        'rules_fired': [match.rule_id],
        'evidence': _masked(_unique(match.evidence)),
        'references': [p for p in issue.related if p.startswith(('CWE-', 'OWASP-'))],
        'recommended_fix': guidance_for(match.issue_type),
    }


def assemble(matches, llm=None) -> AssemblyResult:
    catalogue = load_catalogue()
    groups = {}
    observations = []
    not_determinable = []
    for match in matches:
        anchor = _anchor(match)
        issue = catalogue[match.issue_type]
        if issue.gate and issue.gate != 'nexus' and not match.gate_evidence:
            not_determinable.append({'issue_type': match.issue_type, 'rule_id': match.rule_id,
                                    'reason': f"Gate Evidence missing: {issue.gate}"})
            continue
        if (issue.gate == 'nexus' or issue.kind_default == 'safeguard') and not match.nexus_elements:
            observations.append(_observation(match, issue))
            continue
        primary = _primary(match, issue)
        groups.setdefault(anchor, []).append((match, issue, primary))

    findings = []
    for anchor, group in groups.items():
        group.sort(key=lambda row: row[0].rule_id)
        selected = min(group, key=lambda row: (-_provision(row[2]).penalty_ceiling_inr_crore,
                                                row[0].issue_type, row[0].rule_id))
        match, issue, primary = selected
        provision = _provision(primary)
        # Evaluate each technical Rule independently; preserve its vector when it wins.
        technical = [row for row in group if row[0].classification == 'technical']
        candidates = technical or [selected]
        assessments = []
        for row in candidates:
            candidate = row[0]
            cvss, matrix, band = severity.assess(candidate.classification, candidate.base_vector,
                                                  _category(candidate), candidate.exposure.level)
            assessments.append((cvss, matrix, band, candidate))
        cvss, matrix, band, rated = max(assessments, key=lambda a: a[0].get('score', -1))
        category = _category(rated)
        evidence = _masked(_unique([ev for m, _, _ in group for ev in
                                    [*m.evidence, *(m.gate_evidence or []), *m.exposure.derived_from]]))
        flow = _masked(_unique([step for m, _, _ in group for step in m.data_flow]))
        others = _unique([p for _, item, item_primary in group
                          for p in [item_primary, item.primary, *item.related] if p != primary])
        excerpt = evidence[0]['excerpt']
        missing = {'status': 'not assessed', 'cache_key': sha256(excerpt.encode()).hexdigest()}
        guidance = guidance_for(match.issue_type)
        triage = llm.ask('triage', excerpt, {'issue_type': match.issue_type, 'rule': match.rule_id}) if llm else dict(missing)
        tailored = llm.ask('fix', excerpt, {'issue_type': match.issue_type, 'guidance': guidance}) if llm else dict(missing)
        reviews = [m.legal_review for m, _, _ in group if m.legal_review]
        trf = next((m for m, _, _ in group if m.issue_type == 'TRF-02' and not m.destination_restricted), None)
        legal_review = reviews[0] if reviews else None
        if trf and not legal_review:
            for pid in ('DPDP-Act-16(1)', 'DPDP-Act-11(1)(b)'):
                _provision(pid)
            legal_review = {'readings': [
                {'provision': 'DPDP-Act-16(1)', 'reading': 'Transfer is lawful unless the destination is restricted by notification.'},
                {'provision': 'DPDP-Act-11(1)(b)', 'reading': 'Disclosure to the Data Principal may be required.'},
            ]}
        status = 'needs-legal-review' if legal_review else ('conditional' if any(m.status_hint == 'conditional' for m, _, _ in group) else 'open')
        exposure = {'level': rated.exposure.level, 'derived_from': _masked(rated.exposure.derived_from)}
        ev = exposure['derived_from'][0]
        subject = f"{rated.element['name']} ({category})" if rated.element else f"protected Data Category {category}"
        scoring = (f"CVSS {cvss['vector']} scores {cvss['score']}" if cvss['status'] == 'scored'
                   else f"Risk Matrix {matrix['tier']}/{matrix['exposure']} cell is {matrix['cell']}")
        if rated.classification == 'disclosure':
            scoring += ', capped at medium for disclosure'
        justification = (f"{subject} has {exposure['level']} Exposure based on Evidence at {ev['file']}:{ev['start_line']}; {scoring}. "
                         + (f"{rated.severity_note} " if rated.severity_note else '')
                         + f"Primary Provision {provision.citation} has Penalty Ceiling ₹{provision.penalty_ceiling_inr_crore} crore "
                         '(maximum under the Schedule; actual amount set by the Board under s.33).')
        finding = {
            'id': match.issue_type + '-' + _digest(match.issue_type, *anchor),
            'issue_type': match.issue_type, 'rules_fired': _unique([m.rule_id for m, _, _ in group]),
            'kind': issue.kind_default, 'classification': rated.classification,
            'evidence': evidence, 'data_flow': flow,
            'personal_data_element': None if issue.kind_default == 'safeguard' else _masked(rated.element), 'data_category': category,
            'processing_operation': rated.processing_operation, 'exposure': exposure,
            'primary_provision': primary, 'other_provisions': others,
            'penalty_ceiling': {'parent_section': provision.penalty_parent, 'amount_inr_crore': provision.penalty_ceiling_inr_crore},
            'enforceable_from': str(provision.enforceable_from), 'cvss': cvss, 'risk_matrix': matrix,
            'severity': {'band': band, 'justification': justification},
            'recommended_fix': {'guidance': guidance, 'tailored': tailored}, 'status': status,
            'legal_review': legal_review, 'llm_triage': triage, 'live_probe': None, 'fix_patch': None,
        }
        validate_finding(finding)
        findings.append(finding)
    findings.sort(key=severity.sort_key)
    return AssemblyResult(findings, observations, not_determinable)


def group_by_rule(findings):
    grouped = {}
    for finding in findings:
        for rule in finding['rules_fired']:
            grouped.setdefault(rule, []).append(finding['id'])
    return grouped
