"""Django consent Rules over source-anchored, resolved consent graph facts."""
from auditor.consent.graph import build_graph
from auditor.exposure import decide_exposure
from auditor.mapping import Match
from auditor.rules import RuleSpec, rule


def _graph(ctx):
    if not any(path.suffix == '.py' for path in ctx.files):
        return None
    if not hasattr(ctx, '_consent_graph'):
        ctx._consent_graph = build_graph(ctx)
    return ctx._consent_graph


def _match(spec, evidence, gate):
    if not evidence or not gate:
        return None
    return Match(spec.id, spec.issue_type, evidence, spec.classification, None,
                 None, 'Profile', (), None, [],
                 decide_exposure(authenticated=None, restricted=evidence[:1]), gate_evidence=gate)


DEFAULT = RuleSpec('CON-03-django-default-selected', 'CON-03',
                   'Django consent selected by default', 'config', 'compliance-gap', None, ('python', 'html'))
WITHDRAWAL = RuleSpec('CON-04-django-comparable-paths', 'CON-04',
                      'Django Withdrawal Path harder than grant', 'config', 'compliance-gap', None, ('python', 'html'))
RECORD = RuleSpec('CON-06-django-incomplete-record', 'CON-06',
                  'Django Consent Record missing required fields', 'config', 'compliance-gap', None, ('python', 'html'))
NOTICE = RuleSpec('CON-07-django-unitemised-notice', 'CON-07',
                  'Django consent notice not itemised', 'config', 'compliance-gap', None, ('python', 'html'))


@rule(DEFAULT)
def default_selected(ctx):
    graph = _graph(ctx)
    if graph is None:
        return []
    return [match for control in graph['controls'] if control['default_selected'] is True
            if (match := _match(DEFAULT, control['evidence'], control['evidence']))]


@rule(WITHDRAWAL)
def withdrawal_harder(ctx):
    graph = _graph(ctx)
    if graph is None:
        return []
    matches = []
    for grant in graph['grant_paths']:
        for withdrawal in graph['withdrawal_paths']:
            if (grant.get('start_template') and grant.get('start_template') == withdrawal.get('start_template')
                    and set(grant['purpose_ids']) & set(withdrawal['purpose_ids'])
                    and grant['step_count'] is not None and withdrawal['step_count'] is not None
                    and withdrawal['step_count'] > grant['step_count']):
                evidence = grant['evidence'] + withdrawal['evidence']
                for action in grant['actions'] + withdrawal['actions']:
                    evidence.extend(ev for ev in action['evidence'] if ev not in evidence)
                match = _match(WITHDRAWAL, evidence, grant['evidence'])
                if match:
                    matches.append(match)
    return matches


@rule(RECORD)
def incomplete_record(ctx):
    graph = _graph(ctx)
    if graph is None:
        return []
    matches = []
    for grant in graph['grant_paths']:
        for record in graph['records']:
            fields = set(record['fields'])
            missing = (not fields.intersection({'purpose'}) or
                       not fields.intersection({'notice_version', 'consent_version', 'notice_reference'}) or
                       not fields.intersection({'timestamp', 'created_at', 'time'}))
            if missing and set(grant['purpose_ids']) & set(record['purpose_ids']):
                match = _match(RECORD, record['evidence'] + grant['evidence'], grant['evidence'])
                if match:
                    matches.append(match)
    return matches


@rule(NOTICE)
def unitemised_notice(ctx):
    graph = _graph(ctx)
    if graph is None:
        return []
    matches = []
    for grant in graph['grant_paths']:
        for notice in graph['notices']:
            if notice.get('itemised') is False and set(grant['purpose_ids']) & set(notice['purpose_ids']):
                match = _match(NOTICE, notice['evidence'] + grant['evidence'], grant['evidence'])
                if match:
                    matches.append(match)
    return matches
