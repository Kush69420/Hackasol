"""Finding assembly and Evidence-derived Exposure contracts."""
import importlib.util
import sys
import types
from dataclasses import replace
from types import SimpleNamespace

import pytest

# Concurrent foundation modules may not have landed yet. Only substitute absent
# modules; the production assembler always imports the actual package APIs.
if importlib.util.find_spec('auditor.severity') is None:
    stub = types.ModuleType('auditor.severity')
    stub.highest_category = lambda categories: min(categories, key=lambda c: ['Financial', 'Authentication Secret', 'Contact', 'Profile'].index(c))
    def assess(classification, vector, category, exposure):
        matrix = {'tier': 'A' if category == 'Financial' else 'B' if category == 'Authentication Secret' else 'C', 'exposure': exposure, 'cell': 'high'}
        if classification == 'technical':
            return {'status': 'scored', 'vector': vector, 'score': 8.0}, matrix, 'high'
        return {'status': 'n/a', 'reason': 'No technical attack path'}, matrix, 'medium' if classification == 'disclosure' else 'high'
    stub.assess = assess
    stub.sort_key = lambda finding: finding['id']
    sys.modules['auditor.severity'] = stub
if importlib.util.find_spec('auditor.remediation') is None:
    stub = types.ModuleType('auditor.remediation')
    stub.load_catalogue = lambda: {}
    stub.guidance_for = lambda issue_type: 'Protect Personal Data.'
    sys.modules['auditor.remediation'] = stub

from auditor import mapping
from auditor.exposure import ExposureDecision, ExposureUnresolved, decide_exposure
from auditor.schema import validate_finding


VECTOR = 'CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N'


def ev(line=1, excerpt='process(account)'):
    return {'file': 'app.py', 'start_line': line, 'end_line': line, 'excerpt': excerpt}


@pytest.fixture(autouse=True)
def catalogue(monkeypatch):
    def issue(primary, related=(), gate=None, kind='security-personal-data'):
        return SimpleNamespace(primary=primary, related=list(related), gate=gate, kind_default=kind, title='Protect Personal Data')
    entries = {
        'SEC-01': issue('DPDP-Rule-6(1)(a)', ['CWE-532']),
        'SEC-05': issue('DPDP-Rule-6(1)(b)', ['CWE-798'], 'nexus', 'safeguard'),
        'SEC-13': issue('DPDP-Rule-6(1)(e)', ['DPDP-Rule-8(3)'], 'retention setting exists'),
        'RET-02': issue('DPDP-Act-8(7)', ['DPDP-Act-12(3)'], 'erasure route exists', 'dpdp-obligation'),
        'TRF-02': issue('DPDP-Act-16(1)', ['DPDP-Rule-15'], kind='dpdp-obligation'),
    }
    def provision(pid):
        known = {p for item in entries.values() for p in [item.primary, *item.related]} | {'DPDP-Act-11(1)(b)'}
        if pid not in known:
            raise ValueError(pid)
        security = pid.startswith('DPDP-Rule-6')
        return SimpleNamespace(citation=pid, penalty_parent='DPDP-Act-8(5)' if security else 'DPDP-Act-12(3)', penalty_ceiling_inr_crore=250 if security else 50, enforceable_from='2027-05-14')
    monkeypatch.setattr(mapping, 'load_catalogue', lambda: entries)
    monkeypatch.setattr(mapping, 'guidance_for', lambda issue_type: 'Protect Personal Data.')
    monkeypatch.setattr(mapping.registry, 'get', provision, raising=False)


def match(**changes):
    evidence = ev()
    base = mapping.Match(rule_id='R1', issue_type='SEC-01', evidence=[evidence], classification='technical',
                         base_vector=VECTOR, element={'name': 'account', 'data_category': 'Contact', 'evidence': evidence},
                         data_category='Contact', protected_categories=(), processing_operation='Log', data_flow=[],
                         exposure=ExposureDecision('Public', [evidence]))
    return replace(base, **changes)


def one(*matches, llm=None):
    result = mapping.assemble(matches, llm)
    assert len(result.findings) == 1
    validate_finding(result.findings[0])
    return result.findings[0]


def test_merge_and_group():
    first = match()
    other = match(rule_id='R2', issue_type='RET-02', gate_evidence=[ev(3)])
    finding = one(first, other)
    assert finding['issue_type'] == 'SEC-01'
    assert finding['rules_fired'] == ['R1', 'R2']
    assert 'DPDP-Act-12(3)' in finding['other_provisions']
    second = replace(first, evidence=[ev(2)])
    findings = mapping.assemble([first, second]).findings
    assert len(findings) == 2
    assert len(mapping.group_by_rule(findings)['R1']) == 2


def test_gates_and_nexus():
    result = mapping.assemble([match(issue_type='SEC-13'), match(rule_id='R2', issue_type='SEC-05')])
    assert not result.findings
    assert result.not_determinable[0]['issue_type'] == 'SEC-13'
    assert result.observations[0]['references'] == ['CWE-798']
    assert 'primary_provision' not in result.observations[0]


def test_primary_provisions_and_override():
    f = one(match(issue_type='SEC-13', gate_evidence=[ev(3)]))
    assert f['primary_provision'] == 'DPDP-Rule-6(1)(e)'
    assert f['penalty_ceiling'] == {'parent_section': 'DPDP-Act-8(5)', 'amount_inr_crore': 250}
    assert f['enforceable_from'] == '2027-05-14'
    f = one(match(issue_type='RET-02', primary_override='DPDP-Act-12(3)', gate_evidence=[ev(3)]))
    assert f['primary_provision'] == 'DPDP-Act-12(3)'
    with pytest.raises(ValueError):
        one(match(primary_override='DPDP-Act-12(3)'))


def test_disclosure_and_elementless():
    f = one(match(issue_type='TRF-02', classification='disclosure', base_vector=None))
    assert f['status'] == 'needs-legal-review'
    assert f['severity']['band'] in ('medium', 'low')
    f = one(match(issue_type='TRF-02', classification='disclosure', base_vector=None, destination_restricted=True))
    assert f['status'] == 'open'
    f = one(match(element=None, protected_categories=('Profile', 'Financial')))
    assert f['data_category'] == 'Financial'
    assert all(s in f['severity']['justification'] for s in ('Financial', 'Public', 'DPDP-Rule-6(1)(a)'))


def test_exposure_needs_evidence():
    registration = [ev(5)]
    result = decide_exposure(authenticated=True, open_registration_evidence=registration)
    assert (result.level, result.derived_from) == ('Public', registration)
    membership = [ev(7)]
    assert decide_exposure(authenticated=True, closed_membership=membership).level == 'Internal-Broad'
    with pytest.raises(ExposureUnresolved):
        decide_exposure(authenticated=False)
    assert decide_exposure(authenticated=False, route_evidence=[ev()]).level == 'Public'
    with pytest.raises(ExposureUnresolved):
        decide_exposure(authenticated=True)


def test_triage_does_not_drop_finding():
    class LLM:
        def ask(self, role, excerpt, context):
            return {'status': 'assessed', 'value': {'verdict': 'false-positive', 'reason': 'Review'}, 'cache_key': 'a' * 64, 'provider': 'omp', 'model': 'test', 'prompt_version': '1'} if role == 'triage' else {'status': 'not assessed', 'cache_key': 'b' * 64}
    assert one(match(), llm=LLM())['llm_triage']['value']['verdict'] == 'false-positive'
    assert one(match())['llm_triage']['status'] == 'not assessed'


def test_real_catalogue_and_registry_when_available(monkeypatch):
    monkeypatch.undo()
    if (getattr(mapping.severity, '__spec__', None) is None or
            getattr(sys.modules['auditor.remediation'], '__spec__', None) is None or
            not hasattr(mapping.registry, 'get')):
        pytest.skip('Concurrent Severity, Provision registry or remediation catalogue not available')
    finding = one(match(issue_type='SEC-13', gate_evidence=[ev(3)]))
    assert finding['primary_provision'] == 'DPDP-Rule-6(1)(e)'
    assert finding['penalty_ceiling'] == {'parent_section': 'DPDP-Act-8(5)', 'amount_inr_crore': 250}
    assert finding['enforceable_from'] == '2027-05-14'
