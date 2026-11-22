"""Retention and Data Principal rights Rules for Express applications and notices."""
from __future__ import annotations

import re

from auditor.exposure import decide_exposure
from auditor.mapping import Match
from auditor.rules import RuleSpec, rule

RETENTION = RuleSpec('RET-01-express-purpose-end', 'RET-01', 'No erasure at the end of a Purpose', 'ts-ast', 'compliance-gap', None, ('typescript',))
NOTICE = RuleSpec('RET-03-express-erasure-notice', 'RET-03', 'No 48-hour notice before erasure', 'ts-ast', 'compliance-gap', None, ('typescript',))
GRIEVANCE = RuleSpec('RIG-03-express-grievance', 'RIG-03', 'No grievance mechanism or contact', 'ts-ast', 'compliance-gap', None, ('typescript',))
NOMINATION = RuleSpec('RIG-04-rights-notice', 'RIG-04', 'DPDP rights notice omits nomination', 'config', 'compliance-gap', None, ('json', 'html', 'markdown'))


def _handler(ctx, route):
    coord = route.get('handler') or route.get('registration')
    if not coord or not coord.get('file'):
        return ''
    return '\n'.join((ctx.root / coord['file']).read_text(encoding='utf-8').splitlines()[coord['start_line'] - 1:coord['end_line']])

def _match(ctx, spec, anchor, gate=None, conditional=False):
    element = ctx.element('model:User.email')
    evidence = ctx.evidence(anchor)
    return Match(spec.id, spec.issue_type, [evidence], spec.classification, None,
                 ctx.schema_element(element['id']) if element else None,
                 element['data_category'] if element else 'Contact', (), None,
                 ctx.flow_steps(element['id']) if element else [],
                 decide_exposure(authenticated=None, restricted=[evidence]),
                 gate_evidence=gate, status_hint='conditional' if conditional else None,
                 severity_note='Applicable only if the Data Fiduciary is a Third Schedule class.' if conditional else None)


def _erasure_routes(ctx):
    return [r for r in ctx.routes() if r['method'] in ('POST', 'DELETE') and
            re.search(r'(?:eras|delet|clos)', r['normalised_path'], re.I)]


@rule(RETENTION)
def purpose_end(ctx):
    routes = _erasure_routes(ctx)
    closure_seen = False
    for route in routes:
        text = _handler(ctx, route)
        # A request to erase is not itself an account-closure event.
        closure = re.search(r'(?:account|purpose)[/_-]?(?:clos(?:e|ed|ure)|end(?:ed)?)|(?:clos(?:e|ed|ure)|end(?:ed)?)[/_-]?(?:account|purpose)', route['normalised_path'] + ' ' + text, re.I)
        closure = closure or re.search(r'\b(?:accountClosed|accountClosure|purposeEnded|purposeComplete)\b', text, re.I)
        if not closure:
            continue
        closure_seen = True
        if re.search(r'\b(?:User\w*|\w*Account\w*)\.(?:destroy|delete|erase)\s*\(', text, re.I):
            continue
        anchor = route.get('handler') or route['registration']
        return [_match(ctx, RETENTION, anchor, [ctx.evidence(route['registration'])])]
    if routes and not closure_seen:
        return [_match(ctx, RETENTION, routes[0]['registration'])]
    return []


@rule(NOTICE)
def erasure_notice(ctx):
    routes = _erasure_routes(ctx)
    if not routes:
        return []
    # A notice must be sent with an explicit 48-hour advance interval.
    for route in routes:
        text = _handler(ctx, route)
        if re.search(r'\b(?:send|notify|mail)\w*\s*\(', text, re.I) and re.search(r'\b48\s*(?:\*\s*60\s*\*\s*60|hours?|h\b)', text, re.I):
            return []
    anchor = routes[0]['registration']
    # Gate Evidence records the erasure workflow, not proof of Schedule membership.
    return [_match(ctx, NOTICE, anchor, [ctx.evidence(anchor)], conditional=True)]


@rule(GRIEVANCE)
def grievance(ctx):
    element = ctx.element('model:User.email')
    if not element:
        return []
    for route in ctx.routes():
        if route['method'] in ('POST', 'GET') and re.search(r'(?:complaint|grievance|privacy[-_]?contact)', route['normalised_path'], re.I):
            if ctx.is_authenticated(route) or route['method'] == 'POST':
                return []
    for file in ctx.files:
        if file.suffix.lower() not in ('.html', '.md', '.json', '.ts'):
            continue
        text = file.read_text(encoding='utf-8')
        if re.search(r'(?:privacy|personal data|data protection).{0,100}(?:contact|grievance|complaint)|(?:contact|grievance|complaint).{0,100}(?:privacy|personal data|data protection)', text, re.I):
            return []
    anchor = element['source']
    return [_match(ctx, GRIEVANCE, anchor, [ctx.evidence(anchor)])]


@rule(NOMINATION)
def nomination(ctx):
    fallback = None
    for file in ctx.files:
        if file.suffix.lower() not in ('.json', '.html', '.md', '.txt'):
            continue
        lines = file.read_text(encoding='utf-8').splitlines()
        text = '\n'.join(lines)
        rights = re.search(r'\b(?:right(?:s)?|eras(?:e|ure)|correct(?:ion)?|access)\b', text, re.I)
        dpdp = re.search(r'\b(?:DPDP|Digital Personal Data Protection)\b', text, re.I)
        if dpdp and rights:
            if re.search(r'\bnominat(?:e|ion|ed|or|ee)\b', text, re.I):
                continue
            line = text[:dpdp.start()].count('\n') + 1
            coord = {'file': file.relative_to(ctx.root).as_posix(), 'start_line': line, 'end_line': line}
            return [_match(ctx, NOMINATION, coord, [ctx.evidence(coord)])]
        if not fallback:
            for i, line in enumerate(lines, 1):
                if re.search(r'\b(?:GDPR|privacy|data protection)\b', line, re.I) and re.search(r'\b(?:right(?:s)?|eras(?:e|ure)|correct(?:ion)?|access)\b', line, re.I):
                    fallback = {'file': file.relative_to(ctx.root).as_posix(), 'start_line': i, 'end_line': i}
                    break
    return [_match(ctx, NOMINATION, fallback)] if fallback else []
