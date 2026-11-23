"""Route-level exposure Rules: missing ownership or authentication enforcement, whole-model
serialisation and Personal Data in query strings.

Every Rule is driven by structured inventory facts (routes, models, model queries, static mounts,
file writes, token payloads) and by classified Elements; nothing is keyed to a Target's file names.
"""
from __future__ import annotations

import posixpath
import re

from auditor.analysers.log_flows import _profile
from auditor.exposure import decide_exposure
from auditor.mapping import Match
from auditor.rules import RuleSpec, rule
from auditor.rules.exposure_rules import AUTH_VECTOR, VECTOR, _handler_file, _model_binding

OWNER_KEY = re.compile(r'^(user|owner|customer|account|member|principal)_?id$', re.I)
REQUEST_VALUE = re.compile(r'\b(?:req|request)\.(?:params|query|body)\b')
MASKED_KEY = re.compile(r'\b(?:const|let|var)\s+(\w+)\s*=\s*[\w$.?]+\.replace\(\s*/(?:\\/|[^/\n])+/[a-z]*\s*,\s*([\'"])[^\'"\n]*\2\s*\)')


def _spec(id, issue, title, vector=VECTOR, engine='ts-ast'):
    return RuleSpec(id, issue, title, engine, 'technical', vector, ('typescript', 'javascript'), ())


UNSCOPED = _spec('SEC-07-ts-unscoped-authenticated-read', 'SEC-07', 'Authenticated read returns every Data Principal record', AUTH_VECTOR)
PUBLIC_RECORD = _spec('SEC-07-ts-unauthenticated-record-read', 'SEC-07', 'Unauthenticated read of Personal Data records by request-supplied key')
LOSSY_KEY = _spec('SEC-07-ts-lossy-owner-key', 'SEC-07', 'Ownership filter keyed on a lossy-masked identifier', AUTH_VECTOR)
PUBLIC_DIR = _spec('SEC-07-ts-public-personal-data-directory', 'SEC-07', 'Personal Data stored in or logged to a publicly served directory')
WHOLE_MODEL = _spec('SEC-08-ts-whole-model-serialisation', 'SEC-08', 'Whole model rows serialised into responses or tokens')
QUERY_PD = _spec('SEC-09-ts-query-personal-data', 'SEC-09', 'Personal Data in GET query strings')


# ---- shared helpers --------------------------------------------------------------------------
def _model_name(symbol):
    return symbol[:-5] if symbol.endswith('Model') and len(symbol) > 5 else symbol


def _fields(ctx, name):
    return [e for e in ctx.classified() if e['id'].startswith(f'model:{name}.') and e['kind'] == 'model-field']


def _owner_fields(ctx, name):
    model = ctx.model(name)
    return [f for f in (model or {}).get('fields', []) if OWNER_KEY.match(f['name'])]


def _subject(ctx, name, exclude=()):
    """Classified Elements of a model, or its ownership-key fields when none are classified."""
    elements = [e for e in _fields(ctx, name) if e['id'].rsplit('.', 1)[-1] not in exclude]
    return elements, ([] if elements else _owner_fields(ctx, name))


def _has_secret(elements):
    return any(e['data_category'] == 'Authentication Secret' for e in elements)


def _coord(c):
    return {k: c[k] for k in ('file', 'start_line', 'end_line')}


def _routes_for(ctx, coord):
    found = []
    for route in ctx.inventory['routes']:
        if route['origin'] in ('finale', 'swagger-only') or _handler_file(ctx, route) != coord['file']:
            continue
        handler = route.get('handler')
        if handler and not (handler['start_line'] <= coord['start_line'] <= handler['end_line']):
            continue
        found.append(route)
    return found


def _exposure(ctx, route, anchor):
    if route:
        return ctx.route_exposure(route)
    return decide_exposure(authenticated=None, restricted=[ctx.evidence(anchor)])


def _match(spec, ctx, anchor, route, elements, owner_fields=(), extra=(), flow=(), operation='Expose'):
    evidence = [ctx.evidence(anchor), *extra]
    evidence += [ctx.evidence(e['source']) for e in elements] + [ctx.evidence(f['source']) for f in owner_fields]
    if elements:
        first = elements[0]
        element, category = ctx.schema_element(first['id']), first['data_category']
        protected = tuple(dict.fromkeys(e['data_category'] for e in elements))
    else:
        # A record keyed to a Data Principal's identifier is that Data Principal's Personal Data
        # even when no individual column is classified (same convention as secrets_logging).
        element, category, protected = None, 'Profile', ('Profile',)
    return Match(spec.id, spec.issue_type, evidence, 'technical', spec.base_vector, element, category, protected,
                 operation, list(flow), _exposure(ctx, route, anchor), tuple(e['id'] for e in elements))


def _bound_queries(ctx):
    for query in ctx.inventory.get('model_queries', []):
        model = _model_binding(ctx, query['source']['file'], query['receiver'])
        if model:
            yield query, model


# ---- SEC-07: authenticated but unscoped reads --------------------------------------------------
@rule(UNSCOPED)
def detect_unscoped_authenticated_read(ctx):
    matches, groups = [], {}
    # Auto-generated REST resources paired with an explicit authenticated registration that does not
    # scope the query to the requester (no identity middleware).
    for finale in ctx.routes('GET'):
        if finale['origin'] != 'finale' or not finale.get('model'):
            continue
        explicit = [r for r in ctx.routes('GET', finale['normalised_path'])
                    if r['origin'] not in ('finale', 'swagger-only') and not any(m['name'].endswith('denyAll') for m in r['middleware'])]
        if not explicit or any(m['role'] == 'identity' for r in explicit for m in r['middleware']):
            continue
        if not any(ctx.is_authenticated(r) for r in explicit):
            continue
        name = _model_name(finale['model'])
        elements, owner = _subject(ctx, name, (finale.get('finale') or {}).get('exclude_attributes', ()))
        if not elements and not owner:
            continue
        group = groups.setdefault(name, {'routes': [], 'elements': elements, 'owner': owner})
        group['routes'] += [r for r in explicit if r not in group['routes']]
    for group in groups.values():
        routes = sorted(group['routes'], key=lambda r: (r['registration']['file'], r['registration']['start_line']))
        extra = [ctx.evidence(r['registration']) for r in routes[1:]]
        matches.append(_match(UNSCOPED, ctx, routes[0]['registration'], routes[0], group['elements'], group['owner'], extra))
    # Handler queries that list every row of a Personal Data model for any authenticated caller.
    for query, model in _bound_queries(ctx):
        if query['filtered'] or query['projected'] or query['method'] != 'findAll' or not query['responses']:
            continue
        routes = [r for r in _routes_for(ctx, query['source']) if r['method'] == 'GET' and ctx.is_authenticated(r)
                  and not any(m['role'] == 'identity' for m in r['middleware'])]
        elements = _fields(ctx, model['name'])
        if routes and elements:
            matches.append(_match(UNSCOPED, ctx, _coord(query['source']), routes[0], elements, extra=[ctx.evidence(routes[0]['registration'])]))
    return matches


@rule(PUBLIC_RECORD)
def detect_unauthenticated_record_read(ctx):
    matches = []
    for query, model in _bound_queries(ctx):
        props = query['where_properties']
        if query['projected'] or not query['responses'] or not props:
            continue
        # An ownership predicate (e.g. UserId supplied by identity middleware) scopes the query.
        if any(OWNER_KEY.match(p['name'] or '') for p in props) or not all(REQUEST_VALUE.search(p['expression'] or '') for p in props):
            continue
        routes = [r for r in _routes_for(ctx, query['source']) if r['method'] == 'GET' and not ctx.is_authenticated(r)
                  and not any(m['role'] == 'identity' for m in r['middleware'])]
        elements, owner = _subject(ctx, model['name'])
        if routes and (elements or owner):
            matches.append(_match(PUBLIC_RECORD, ctx, _coord(query['source']), routes[0], elements, owner, [ctx.evidence(routes[0]['registration'])]))
    return matches


@rule(LOSSY_KEY)
def detect_lossy_owner_key(ctx):
    matches, seen = [], set()
    for query in ctx.inventory.get('model_queries', []):
        enclosing = query.get('enclosing')
        if not enclosing or not query['where_properties']:
            continue
        key = (enclosing['file'], enclosing['start_line'])
        if key in seen:
            continue
        text = (ctx.root / enclosing['file']).read_text(encoding='utf-8', errors='replace').splitlines()
        masked = {}
        for number in range(enclosing['start_line'], min(enclosing['end_line'], len(text)) + 1):
            for variable, _ in MASKED_KEY.findall(text[number - 1]):
                masked[variable] = number
        for prop in query['where_properties']:
            variable = (prop['expression'] or '').strip()
            if variable not in masked or (prop['name'] or '').strip("'\"") in query.get('disambiguated_owner_keys', ()):
                continue
            element = ctx.element(f"collection:{query['receiver']}.{prop['name']}")
            model = _model_binding(ctx, query['source']['file'], query['receiver'])
            elements = [element] if element and element['data_category'] else (_fields(ctx, model['name']) if model else [])
            if not elements:
                continue
            seen.add(key)
            line = {'file': enclosing['file'], 'start_line': masked[variable], 'end_line': masked[variable]}
            routes = _routes_for(ctx, query['source'])
            matches.append(_match(LOSSY_KEY, ctx, _coord(query['source']), routes[0] if routes else None, elements, extra=[ctx.evidence(line)]))
            break
    return matches


# ---- SEC-07: publicly served directories --------------------------------------------------------
def _directory(value):
    return posixpath.normpath(value or '.').strip('/')


def _function_elements(ctx, coord):
    lines = (ctx.root / coord['file']).read_text(encoding='utf-8', errors='replace').splitlines()
    body = '\n'.join(lines[coord['start_line'] - 1:coord['end_line']])
    return [e for e in ctx.classified() if e['kind'] == 'model-field'
            and re.search(r'\.' + re.escape(e['id'].rsplit('.', 1)[-1]) + r'\b', body)]


@rule(PUBLIC_DIR)
def detect_public_directory(ctx):
    matches = []
    mounts = [m for m in ctx.inventory.get('static_mounts', []) if not m['authenticated'] and m.get('directory')]
    for mount in mounts:
        directory = _directory(mount['directory'])
        # (a) application code writes Personal Data into the served directory
        for write in ctx.inventory.get('file_writes', []):
            targets = [p for p in write['path_literals'] if _directory(p).startswith(directory + '/') or _directory(p) == directory]
            if not targets or not write.get('enclosing'):
                continue
            elements = _function_elements(ctx, write['enclosing'])
            if not elements:
                continue
            routes = _routes_for(ctx, write['source'])
            matches.append(_match(PUBLIC_DIR, ctx, _coord(write['source']), routes[0] if routes else None, elements,
                                  extra=[ctx.evidence(mount['source'])], operation='Store'))
            flow = [{'operation': 'Store', 'evidence': ctx.evidence(write['source']), 'note': 'file write; served directory'}]
            matches.append(_match(PUBLIC_DIR, ctx, _coord(mount['source']), None, elements, flow=flow, operation='Expose'))
        # (b) the access log is written into the served directory
        for logger in (r for r in ctx.inventory.get('logging', []) if r.get('kind') == 'morgan'):
            profile = _profile(ctx.inventory, logger)
            pattern = profile['file_pattern']
            if not pattern or _directory(posixpath.dirname(pattern)) != directory:
                continue
            logged = [e for e in ctx.classified()
                      if any(s['operation'] == 'Log' and s['source'] == profile['source_morgan'] for s in ctx.steps(e['id']))]
            if logged:
                extra = [ctx.evidence(profile['source_rotation']), ctx.evidence(profile['source_morgan'])]
                matches.append(_match(PUBLIC_DIR, ctx, _coord(mount['source']), None, logged, extra=extra, operation='Log'))
    # one Finding per anchor
    unique = {}
    for m in matches:
        unique.setdefault((m.evidence[0]['file'], m.evidence[0]['start_line']), m)
    return list(unique.values())


# ---- SEC-08: whole-model serialisation -----------------------------------------------------------
def _field_vocabulary(ctx, body):
    best = None
    for model in ctx.inventory.get('models', []):
        elements = _fields(ctx, model['name'])
        hits = [e for e in elements if re.search(r'\b' + re.escape(e['id'].rsplit('.', 1)[-1]) + r'\b', body)]
        if len(hits) >= 2 and _has_secret(elements) and (best is None or len(hits) > len(best[1])):
            best = (model, elements)
    return best


@rule(WHOLE_MODEL)
def detect_whole_model(ctx):
    matches = []
    # Result rows (or a nested include of a model) sent as-is.
    for query, model in _bound_queries(ctx):
        if query['projected']:
            continue
        sent = [r for r in query['responses'] if r['how'] in ('direct', 'wrapped')]
        nested = next((m for m in (_model_binding(ctx, query['source']['file'], i) for i in query['include']) if m), None)
        subject = nested or model
        elements = _fields(ctx, subject['name'])
        if not sent or not _has_secret(elements):
            continue
        routes = _routes_for(ctx, query['source'])
        matches.append(_match(WHOLE_MODEL, ctx, _coord(sent[0]['source']), routes[0] if routes else None, elements,
                              extra=[ctx.evidence(query['source'])]))
    # Request-chosen field names copied from a model value without an allow-list.
    for read in ctx.inventory.get('dynamic_field_reads', []):
        enclosing = read.get('enclosing')
        if not enclosing:
            continue
        lines = (ctx.root / enclosing['file']).read_text(encoding='utf-8', errors='replace').splitlines()
        found = _field_vocabulary(ctx, '\n'.join(lines[enclosing['start_line'] - 1:enclosing['end_line']]))
        if found:
            routes = _routes_for(ctx, read['source'])
            matches.append(_match(WHOLE_MODEL, ctx, _coord(read['source']), routes[0] if routes else None, found[1],
                                  extra=[ctx.evidence(read['read'])]))
    # Model-typed values placed in a signed token payload.
    for payload in ctx.inventory.get('token_payloads', []):
        for member in payload['members']:
            model = ctx.model(member['type']) if member['type'] else None
            elements = _fields(ctx, model['name']) if model else []
            if _has_secret(elements):
                routes = _routes_for(ctx, payload['source'])
                matches.append(_match(WHOLE_MODEL, ctx, _coord(payload['source']), routes[0] if routes else None, elements))
                break
    # Auto-generated REST resources that exclude some fields yet still serialise other Personal Data.
    entries = {}
    for finale in ctx.routes('GET'):
        details = finale.get('finale') or {}
        if finale['origin'] == 'finale' and finale.get('model') and details.get('exclude_attributes'):
            entries.setdefault((details['model_entry']['file'], details['model_entry']['start_line']), (finale, details))
    for finale, details in entries.values():
        name = _model_name(finale['model'])
        remaining = [e for e in _fields(ctx, name) if e['id'].rsplit('.', 1)[-1] not in details['exclude_attributes']]
        if remaining and _has_secret(_fields(ctx, name)):
            matches.append(_match(WHOLE_MODEL, ctx, _coord(details['model_entry']), finale, remaining))
    unique = {}
    for m in matches:
        unique.setdefault((m.evidence[0]['file'], m.evidence[0]['start_line']), m)
    return list(unique.values())


# ---- SEC-09: Personal Data in query strings --------------------------------------------------------
@rule(QUERY_PD)
def detect_query_personal_data(ctx):
    groups = {}
    for element in ctx.classified():
        match = re.match(r'^param:GET\s+([^?]+)\?', element['id'])
        if element['kind'] == 'route-param' and match:
            groups.setdefault(match.group(1), []).append(element)
    matches = []
    for path, elements in groups.items():
        elements.sort(key=lambda e: (e['source']['file'], e['source']['start_line']))
        routes = ctx.routes('GET', path)
        anchor = _coord(elements[0]['source'])
        matches.append(_match(QUERY_PD, ctx, anchor, routes[0] if routes else None, elements,
                              flow=ctx.flow_steps(elements[0]['id']), operation='Collect'))
    return matches
