"""Response exposure and CORS Rules linked to evidenced Personal Data Elements."""
from __future__ import annotations

import ast
import re
from pathlib import PurePosixPath

from auditor.mapping import Match
from auditor.rules import RuleSpec, rule

VECTOR = 'CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N'
AUTH_VECTOR = 'CVSS:4.0/AV:N/AC:L/AT:N/PR:L/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N'


def _spec(id, issue, title, vector=VECTOR, semgrep=()):
    return RuleSpec(id, issue, title, 'semgrep' if semgrep else 'ts-ast', 'technical', vector,
                    ('typescript', 'javascript'), semgrep)


NESTED_AUTH = _spec('SEC-07-ts-unchecked-nested-records', 'SEC-07', 'Unauthenticated nested Personal Data records', semgrep=('exposure-model-query',))
NESTED_DATA = _spec('SEC-08-ts-nested-records', 'SEC-08', 'Nested Personal Data records in responses', semgrep=('exposure-model-query',))
ACCOUNT = _spec('SEC-08-ts-account-list', 'SEC-08', 'Account list serializes Personal Data', AUTH_VECTOR, ('exposure-model-query',))
REVIEW = _spec('SEC-08-ts-review-author', 'SEC-08', 'Review author Personal Data exposed')
CORS = _spec('SEC-11-ts-wildcard-cors', 'SEC-11', 'Wildcard CORS on Personal Data response routes')
FASTAPI_CORS = RuleSpec('SEC-11-fastapi-wildcard-cors', 'SEC-11', 'Wildcard CORS on FastAPI Personal Data routes', 'python-ast', 'technical', VECTOR, ('python',))


def _text(ctx, file):
    return (ctx.root / file).read_text(encoding='utf-8', errors='replace')


def _handler_file(ctx, route):
    handler = route.get('handler')
    if handler:
        return handler['file']
    # Resolve default imports used by wrapper calls when the inventory cannot resolve them.
    registration = route['registration']
    lines = _text(ctx, registration['file']).splitlines()
    line = '\n'.join(lines[registration['start_line'] - 1:registration['end_line']])
    source = '\n'.join(lines)
    for symbol, path in re.findall(r"import\s+([\w$]+)\s+from\s+['\"](\.[^'\"]+)['\"]", source):
        if re.search(r'\b' + re.escape(symbol) + r'\s*\(', line):
            import posixpath
            base = posixpath.normpath(posixpath.join(str(PurePosixPath(registration['file']).parent), path))
            for candidate in (base + '.ts', base + '.js', base + '/index.ts'):
                if candidate in ctx.rel_files:
                    return candidate
    return None


def _model_binding(ctx, file, symbol):
    source = _text(ctx, file)
    for model in ctx.inventory.get('models', []):
        model_file = model['source']['file']
        base = str(PurePosixPath(model_file).with_suffix(''))
        for clause, path in re.findall(r"import\s+([^\n]+?)\s+from\s+['\"](\.[^'\"]+)['\"]", source):
            import posixpath
            resolved = posixpath.normpath(posixpath.join(str(PurePosixPath(file).parent), path))
            if resolved == base and re.search(r'\b' + re.escape(symbol) + r'\b', clause):
                return model
        if file == model_file and symbol in (model['name'], model['name'] + 'Model'):
            return model
    return None


def _records(ctx):
    for query in ctx.semgrep_matches('exposure-model-query'):
        file = query['file']
        lines = _text(ctx, file).splitlines()
        for route in ctx.routes('GET'):
            if _handler_file(ctx, route) != file:
                continue
            handler = route.get('handler')
            if handler and not (handler['start_line'] <= query['start_line'] <= handler['end_line']):
                continue
            start = handler['start_line'] if handler else 1
            end = handler['end_line'] if handler else len(lines)
            body = '\n'.join(lines[start - 1:end])
            qtext = '\n'.join(lines[query['start_line'] - 1:query['end_line']])
            # A list query must feed a response, not merely occur in the same file.
            name_match = re.search(r'\b(?:const|let|var)\s+(\w+)\s*=\s*(?:await\s+)?[^\n]*?\.findAll\s*\(', qtext)
            if not name_match:
                continue
            variable = name_match.group(1)
            if not re.search(r'\bres(?:\.\w+\([^)]*\))*\.(?:json|send)\s*\([\s\S]*?\b' + re.escape(variable) + r'\b', body):
                continue
            # Explicit projections and ownership predicates change what is returned.
            if re.search(r'\b(?:attributes|where)\s*:', qtext):
                continue
            symbol = query['metavars'].get('$MODEL', '')
            model = _model_binding(ctx, file, symbol)
            if not model:
                continue
            include = re.search(r'\binclude\s*:\s*\[\s*(\w+)\s*\]', qtext)
            nested = _model_binding(ctx, file, include.group(1)) if include else None
            subject = nested or model
            elements = [e for e in ctx.classified() if e['id'].startswith('model:' + subject['name'] + '.')]
            if not elements:
                continue
            yield route, query, body, elements, bool(nested)


def _make(ctx, spec, route, anchor, elements, extra=(), flow=()):
    first = elements[0]
    return Match(spec.id, spec.issue_type, [ctx.evidence(anchor), *extra], 'technical', spec.base_vector,
                 ctx.schema_element(first['id']), first['data_category'],
                 tuple(dict.fromkeys(e['data_category'] for e in elements)), 'Expose', list(flow),
                 ctx.route_exposure(route), tuple(e['id'] for e in elements))


def _query_matches(ctx, spec, nested):
    matches = []
    for route, query, body, elements, is_nested in _records(ctx):
        if is_nested != nested or (spec is NESTED_AUTH and ctx.is_authenticated(route)):
            continue
        if not nested:
            if not ctx.is_authenticated(route) or not re.search(r'\.\.\.\s*\w+\.dataValues\b', body):
                continue
            # Explicitly masked properties do not remain exposed.
            elements = [e for e in elements if not re.search(r'\b' + re.escape(e['id'].rsplit('.', 1)[-1]) + r'\s*:\s*[^\n,}]*\.(?:replace|mask|slice|substring)\s*\(', body)]
            if not elements:
                continue
        anchor = {k: query[k] for k in ('file', 'start_line', 'end_line')}
        extra = [ctx.evidence(route['registration'])] + [ctx.evidence(e['source']) for e in elements]
        matches.append(_make(ctx, spec, route, anchor, elements, extra))
    return matches


@rule(NESTED_AUTH)
def detect_unchecked_nested(ctx):
    return _query_matches(ctx, NESTED_AUTH, True)


@rule(NESTED_DATA)
def detect_nested(ctx):
    return _query_matches(ctx, NESTED_DATA, True)


@rule(ACCOUNT)
def detect_account_list(ctx):
    return _query_matches(ctx, ACCOUNT, False)


@rule(REVIEW)
def detect_review_author(ctx):
    matches = []
    for flow in ctx.flows:
        if 'model:User.email' not in flow.get('derived_from', []):
            continue
        element = ctx.element(flow['element_id'])
        if not element or not element['data_category'] or not element['id'].startswith('collection:'):
            continue
        steps = flow['steps']
        stores = [s for s in steps if s['operation'] == 'Store']
        exposures = [s for s in steps if s['operation'] == 'Expose']
        collects = [s for s in steps if s['operation'] == 'Collect']
        if not stores or not exposures or not collects:
            continue
        for exposed in exposures:
            for route in ctx.routes('GET'):
                handler = route.get('handler')
                coord = exposed['source']
                if not handler or handler['file'] != coord['file'] or not handler['start_line'] <= coord['start_line'] <= handler['end_line']:
                    continue
                matches.append(_make(ctx, REVIEW, route, coord, [element],
                                     [ctx.evidence(route['registration']), *[ctx.evidence(s['source']) for s in stores]],
                                     ctx.flow_steps(element['id'])))
    return matches


@rule(CORS)
def detect_cors(ctx):
    # Only middleware actually applied to a Personal Data response establishes the nexus.
    by_middleware = {}
    routes = [(r, es) for r, _, _, es, _ in _records(ctx)]
    for m in detect_review_author(ctx):
        for r in ctx.routes('GET'):
            if ctx.evidence(r['registration']) in m.evidence:
                routes.append((r, [ctx.element(m.element['name'])]))
    for route, elements in routes:
        for middleware in route.get('middleware', []):
            if middleware['name'] != 'cors' or middleware['expression'].strip() not in ('cors()', "cors({ origin: '*' })", 'cors({ origin: "*" })'):
                continue
            source = middleware['source']
            key = (source['file'], source['start_line'], source['end_line'])
            group = by_middleware.setdefault(key, (source, route, [], []))
            for element in elements:
                if element not in group[2]:
                    group[2].append(element)
            ev = ctx.evidence(route['registration'])
            if ev not in group[3]:
                group[3].append(ev)
    return [_make(ctx, CORS, route, source, elements, route_evidence)
            for source, route, elements, route_evidence in by_middleware.values()]


@rule(FASTAPI_CORS)
def detect_fastapi_cors(ctx):
    out = []
    for file in ctx.files:
        if file.suffix != '.py':
            continue
        try:
            tree = ast.parse(file.read_text(encoding='utf-8'))
        except (OSError, UnicodeError, SyntaxError):
            continue
        rel = file.relative_to(ctx.root).as_posix()
        for call in ast.walk(tree):
            if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                    and call.func.attr == 'add_middleware' and call.args
                    and isinstance(call.args[0], ast.Name) and call.args[0].id == 'CORSMiddleware'):
                continue
            origins = next((k.value for k in call.keywords if k.arg == 'allow_origins'), None)
            if not isinstance(origins, (ast.List, ast.Tuple)) or not any(
                    isinstance(v, ast.Constant) and v.value == '*' for v in origins.elts):
                continue
            source = {'file': rel, 'start_line': call.lineno, 'end_line': call.end_lineno}
            for route in ctx.routes():
                if route.get('origin') != 'fastapi' or route['registration']['file'] != rel:
                    continue
                receiver = ast.unparse(call.func.value)
                if not re.search(r'@' + re.escape(receiver) + r'\.(?:get|post|put|patch|delete)\s*\(',
                                 _text(ctx, rel).splitlines()[route['registration']['start_line'] - 1], re.I):
                    continue
                prefix = f"param:{route['method']} {route['normalised_path']}#body."
                elements = [e for e in ctx.classified() if e['id'].startswith(prefix)
                            and e['data_category'] == 'Biometric']
                if not elements:
                    continue
                ev = [ctx.evidence(source), ctx.evidence(route['registration']),
                      *[ctx.evidence(e['source']) for e in elements]]
                first = elements[0]
                out.append(Match(FASTAPI_CORS.id, FASTAPI_CORS.issue_type, ev,
                    FASTAPI_CORS.classification, FASTAPI_CORS.base_vector,
                    ctx.schema_element(first['id']), first['data_category'], ('Biometric',),
                    'Collect', ctx.flow_steps(first['id']), ctx.route_exposure(route),
                    nexus_elements=tuple(e['id'] for e in elements)))
    return out
