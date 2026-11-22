"""Rules for Authentication Secrets, access logs and browser storage."""
from __future__ import annotations

import re

from auditor.analysers.log_flows import _profile
from auditor.exposure import decide_exposure
from auditor.mapping import Match
from auditor.rules import RuleSpec, rule

VECTOR = 'CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N'


def _spec(identifier, title, engine='ts-ast', classification='technical', semgrep_ids=()):
    return RuleSpec(identifier, identifier[:6], title, engine, classification,
                    VECTOR if classification == 'technical' else None, ('typescript',), semgrep_ids)


def _match(spec, ctx, element, evidence, operation, *, gate=None, nexus=(), flow=None):
    return Match(spec.id, spec.issue_type, evidence, spec.classification, spec.base_vector,
                 ctx.schema_element(element['id']) if element else None,
                 element['data_category'] if element else None,
                 (element['data_category'],) if element else ('Authentication Secret',), operation,
                 ctx.flow_steps(element['id']) if element and flow is None else (flow or []),
                 decide_exposure(authenticated=None, restricted=evidence),
                 nexus_elements=nexus, gate_evidence=gate)


def _query_flows(ctx):
    for element in ctx.classified():
        if element['kind'] != 'route-param' or not element['id'].startswith('param:GET ') or element['data_category'] != 'Authentication Secret':
            continue
        steps = ctx.steps(element['id'])
        collect = next((s for s in steps if s['operation'] == 'Collect' and s.get('stage') == 'service'), None)
        logs = [s for s in steps if s['operation'] == 'Log' and s.get('stage') == 'log']
        if collect and logs:
            yield element, collect, logs


URL = _spec('SEC-09-ts-query-authentication-secret', 'Authentication Secrets in query strings')
LOG = _spec('SEC-01-ts-morgan-query-secrets', 'Authentication Secrets in access logs')
RETENTION = _spec('SEC-13-ts-access-log-retention', 'Short Personal Data access-log retention', 'config', 'compliance-gap')
HASH = _spec('SEC-04-ts-md5-password-hash', 'MD5 password hashing', 'semgrep', semgrep_ids=('sec04-md5',))
KEY = _spec('SEC-05-ts-hardcoded-jwt-key', 'Hard-coded JWT signing material', 'ts-ast')
STORAGE = _spec('SEC-10-ts-storage-header', 'Personal Data stored and attached to intercepted requests', 'ts-ast')


@rule(URL)
def query_secrets(ctx):
    return [_match(URL, ctx, e, [ctx.evidence(c['source']), *(ctx.evidence(s['source']) for s in logs)], 'Collect')
            for e, c, logs in _query_flows(ctx)]


@rule(LOG)
def logged_secrets(ctx):
    return [_match(LOG, ctx, e, [ctx.evidence(c['source']), *(ctx.evidence(s['source']) for s in logs)], 'Log')
            for e, c, logs in _query_flows(ctx)]


@rule(RETENTION)
def short_retention(ctx):
    result = []
    for logger in ctx.inventory.get('logging', []):
        if logger.get('kind') != 'morgan':
            continue
        profile = _profile(ctx.inventory, logger)
        if profile['retention_days'] is None or profile['retention_days'] >= 365 or not profile['source_rotation']:
            continue
        for element, collect, logs in _query_flows(ctx):
            linked = [s for s in logs if s['source'] == profile['source_morgan']]
            if linked:
                gate = [ctx.evidence(collect['source']), *(ctx.evidence(s['source']) for s in linked)]
                result.append(_match(RETENTION, ctx, element, [ctx.evidence(profile['source_rotation'])], 'Log', gate=gate))
    return result


def _text(ctx, coord):
    lines = (ctx.root / coord['file']).read_text(errors='replace').splitlines()
    return '\n'.join(lines[coord['start_line'] - 1:coord['end_line']])


@rule(HASH)
def weak_password_hash(ctx):
    result = []
    for element in ctx.classified():
        if element['kind'] != 'model-field' or element['field'].lower() != 'password':
            continue
        setter = _text(ctx, element['source'])
        calls = re.findall(r"(?:\b([\w$]+)\.)?([\w$]+)\s*\(\s*\w+\s*\)", setter)
        model_path = ctx.root / element['source']['file']
        model_text = model_path.read_text(errors='replace')
        for hit in ctx.semgrep_matches('sec04-md5'):
            source = (ctx.root / hit['file']).read_text(errors='replace')
            line = source.splitlines()[hit['start_line'] - 1]
            declaration = re.search(r'\b(?:function\s+|(?:const|let|var)\s+)([\w$]+)', line)
            if not declaration:
                continue
            linked = False
            for receiver, name in calls:
                if name != declaration.group(1):
                    continue
                if not receiver and model_path == ctx.root / hit['file']:
                    linked = True
                elif receiver:
                    imported = re.search(r"\bimport\s+\*\s+as\s+" + re.escape(receiver) +
                                         r"\s+from\s+['\"]([^'\"]+)['\"]", model_text)
                    if imported:
                        target = (model_path.parent / imported.group(1)).resolve()
                        linked = target == (ctx.root / hit['file']).resolve().with_suffix('')
                if linked:
                    break
            if not linked:
                continue
            ev = [ctx.evidence(element['source']), ctx.evidence({'file': hit['file'], 'start_line': hit['start_line'], 'end_line': hit['end_line']})]
            result.append(_match(HASH, ctx, element, ev, 'Store'))
    return result


@rule(KEY)
def hardcoded_jwt(ctx):
    result = []
    protected = tuple(e['id'] for e in ctx.classified() if e['kind'] == 'model-field' and e['data_category'] == 'Authentication Secret')
    for path in ctx.files:
        if path.suffix not in ('.ts', '.js'):
            continue
        text = path.read_text(errors='replace')
        for signing in re.finditer(r'\b(?:jwt|jsonwebtoken)\.sign\s*\(\s*[^,\n]+,\s*([\w$]+)', text):
            name = signing.group(1)
            literal = re.search(r'\b(?:const|let|var)\s+' + re.escape(name) + r'\s*=\s*([\'"`])(?:(?!\1)[^\n])*?\1', text)
            if not literal:
                continue
            relative = path.relative_to(ctx.root).as_posix()
            line = text.count('\n', 0, literal.start()) + 1
            sign_line = text.count('\n', 0, signing.start()) + 1
            ev = [ctx.evidence({'file': relative, 'start_line': line, 'end_line': line}), ctx.evidence({'file': relative, 'start_line': sign_line, 'end_line': sign_line})]
            # Literal assignment names are not necessarily recognisable by the generic masker.
            ev[0] = {**ev[0], 'excerpt': '[hard-coded signing material masked]'}
            result.append(_match(KEY, ctx, None, ev, None, nexus=protected))
    return result


@rule(STORAGE)
def storage_header(ctx):
    stores = {}
    for stored in ctx.inventory.get('client_storage', []):
        if stored.get('op') == 'set' and stored.get('api') == 'localStorage':
            stores.setdefault(stored.get('key'), []).append(stored['source'])
    result = []
    for key, sources in stores.items():
        element = ctx.element(f'storage:localStorage.{key}')
        if not element or not element.get('data_category'):
            continue
        headers = []
        for header in ctx.inventory.get('outbound_headers', []):
            if not re.search(r'localStorage\.getItem\(\s*[\'\"]' + re.escape(key) + r'[\'\"]\s*\)', header.get('value_expression', '')):
                continue
            guarded = header.get('origin_guard')
            if 'origin_guard' not in header:
                text = (ctx.root / header['source']['file']).read_text(errors='replace')
                guarded = bool(re.search(r'\b(?:req|request)\.url(?:WithParams)?\s*\.\s*(?:startsWith|includes|match)\s*\(|\bnew\s+URL\s*\(\s*(?:req|request)\.url', text))
            # An Authentication Secret in browser storage remains in scope even
            # when the interceptor restricts the requests carrying its header.
            if guarded and element['data_category'] != 'Authentication Secret':
                continue
            headers.append(header['source'])
        if headers:
            order = lambda coord: (coord['file'], coord['start_line'], coord['end_line'])
            ordered = sorted(sources, key=order) + sorted(headers, key=order)
            evidence = [ctx.evidence(coord) for coord in ordered]
            result.append(_match(STORAGE, ctx, element, evidence, 'Store'))
    return result
