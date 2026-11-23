"""Rules that close recall gaps found by hand review: weak or keyed credential verifiers, session
credential handling in the browser and cookies, cross-origin responses, plaintext listeners and
soft-deleted account rows.

Every Rule binds to inventory facts, Elements and source constructs, never to a Target's file names.
Each one only fires when the code itself settles the question; facts that depend on the running
deployment (for example the value of ``NODE_ENV``) are left to the Coverage Matrix.
"""
from __future__ import annotations

import re
from pathlib import Path, PurePosixPath

from auditor.exposure import decide_exposure
from auditor.mapping import Match
from auditor.rules import RuleSpec, rule

VECTOR = 'CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N'
TS = ('typescript', 'javascript')

KEYED = RuleSpec('SEC-04-ts-constant-key-verifier', 'SEC-04', 'Authentication Secret stored as a keyed hash under a constant key', 'ts-ast', 'technical', VECTOR, TS)
MD5_LOGIN = RuleSpec('SEC-04-ts-md5-credential-compare', 'SEC-04', 'Submitted password hashed with MD5 for comparison', 'ts-ast', 'technical', VECTOR, TS)
HMAC_KEY = RuleSpec('SEC-05-ts-hardcoded-hmac-key', 'SEC-05', 'Hard-coded HMAC key protecting an Authentication Secret verifier', 'ts-ast', 'technical', VECTOR, TS)
TOKEN_SITE = RuleSpec('SEC-10-ts-token-storage-site', 'SEC-10', 'Session token written to localStorage', 'ts-ast', 'technical', VECTOR, TS)
COOKIE = RuleSpec('SEC-11-ts-session-cookie-flags', 'SEC-11', 'Session cookie set without HttpOnly, Secure or SameSite', 'ts-ast', 'technical', VECTOR, TS)
JSONP = RuleSpec('SEC-11-ts-jsonp-response', 'SEC-11', 'JSONP response readable cross-origin carrying Personal Data', 'ts-ast', 'technical', VECTOR, TS)
LISTENER = RuleSpec('SEC-11-terraform-plaintext-listener', 'SEC-11', 'Plaintext HTTP listener forwarding without HTTPS redirect', 'config', 'technical', VECTOR, ('terraform',))
SOFT_DELETE = RuleSpec('RET-01-sequelize-soft-delete', 'RET-01', 'Soft-deleted account rows are never erased', 'ts-ast', 'compliance-gap', None, ('typescript', 'javascript'))

_CODE = ('.ts', '.js', '.mjs', '.cjs')
_IGNORED = re.compile(r'(?:\.spec\.|\.test\.|(?:^|/)(?:test|tests|__tests__)/)')


def _code_files(ctx):
    for path in ctx.files:
        rel = path.relative_to(ctx.root).as_posix()
        if path.suffix in _CODE and not _IGNORED.search(rel):
            yield path, rel, path.read_text(errors='replace')


def _line_of(text, offset):
    return text.count('\n', 0, offset) + 1


def _coord(rel, text, start, end=None):
    first = _line_of(text, start)
    last = _line_of(text, end if end is not None else start)
    return {'file': rel, 'start_line': first, 'end_line': last}


def _masked(evidence, label='[hard-coded key material masked]'):
    return {**evidence, 'excerpt': label}


def _match(ctx, spec, evidence, *, element=None, nexus=(), categories=(), operation=None, gate=None, exposure=None):
    categories = tuple(categories) or ((element['data_category'],) if element else ())
    return Match(spec.id, spec.issue_type, evidence, spec.classification, spec.base_vector,
                 ctx.schema_element(element['id']) if element else None,
                 element['data_category'] if element else (categories[0] if categories else None),
                 categories, operation,
                 ctx.flow_steps(element['id']) if element else [],
                 exposure or decide_exposure(authenticated=None, restricted=evidence[:1]),
                 nexus_elements=tuple(nexus), gate_evidence=gate)


def _secret_fields(ctx):
    return [e for e in ctx.classified() if e['kind'] == 'model-field' and e['data_category'] == 'Authentication Secret']


# Keyed and unkeyed digest helpers

# Only top-level declarations are importable helpers; an indented local of the same name is not.
_HELPER = re.compile(r'^(?:export\s+)?(?:const|let|var|function)\s+([\w$]+)\b[^\n]*', re.M)
_HMAC_CALL = re.compile(r'createHmac\(\s*[\'"][\w-]+[\'"]\s*,\s*(?:([\'"`])(?:(?!\1)[^\n$])+\1|([\w$]+))')
_MD5_CALL = re.compile(r'createHash\(\s*[\'"]md5[\'"]\s*\)')


def _constant_hmac_helpers(ctx):
    """Helpers whose body is an HMAC under a key that is a string literal (inline or a const in the file)."""
    found = []
    for path, rel, text in _code_files(ctx):
        for declaration in _HELPER.finditer(text):
            call = _HMAC_CALL.search(declaration.group(0))
            if not call:
                continue
            if call.group(2):
                literal = re.search(r'\b(?:const|let|var)\s+' + re.escape(call.group(2)) + r'\s*=\s*([\'"`])(?:(?!\1)[^\n$])+\1', text)
                if not literal:
                    continue
                key_coord = _coord(rel, text, literal.start())
            else:
                key_coord = _coord(rel, text, declaration.start())
            found.append({'name': declaration.group(1), 'path': path, 'key': key_coord})
    return found


def _md5_helpers(ctx):
    found = []
    for path, rel, text in _code_files(ctx):
        for declaration in _HELPER.finditer(text):
            if _MD5_CALL.search(declaration.group(0)):
                found.append({'name': declaration.group(1), 'path': path, 'coord': _coord(rel, text, declaration.start())})
    return found


def _resolves(caller: Path, receiver: str | None, name: str, declared: Path, text: str) -> bool:
    """True when ``receiver.name`` (or a bare ``name``) called in ``caller`` is the helper declared in ``declared``."""
    if caller == declared:
        return True
    if receiver:
        pattern = r'\bimport\s+(?:\*\s+as\s+|)' + re.escape(receiver) + r'\s+from\s+[\'"]([^\'"]+)[\'"]'
    else:
        pattern = r'\bimport\s*\{[^}]*\b' + re.escape(name) + r'\b[^}]*\}\s*from\s+[\'"]([^\'"]+)[\'"]'
    for spec in re.findall(pattern, text):
        if not spec.startswith('.'):
            continue
        target = (caller.parent / spec).resolve()
        if target in (declared.resolve(), declared.resolve().with_suffix('')):
            return True
    return False


def _setter_calls(ctx, element):
    """(receiver, name, coordinate) for each ``setDataValue(field, helper(...))`` inside the Element."""
    coord = element['source']
    lines = (ctx.root / coord['file']).read_text(errors='replace').splitlines()
    calls = []
    for number in range(coord['start_line'], coord['end_line'] + 1):
        for receiver, name in re.findall(r'\bsetDataValue\s*\(\s*[\'"][\w$]+[\'"]\s*,\s*(?:([\w$]+)\.)?([\w$]+)\s*\(', lines[number - 1]):
            calls.append((receiver, name, {'file': coord['file'], 'start_line': number, 'end_line': number}))
    return calls


def _linked_helpers(ctx, element, helpers):
    model = ctx.root / element['source']['file']
    text = model.read_text(errors='replace')
    for receiver, name, setter in _setter_calls(ctx, element):
        for helper in helpers:
            if helper['name'] == name and _resolves(model, receiver or None, name, helper['path'], text):
                yield {**helper, 'setter': setter}


@rule(KEYED)
def constant_key_verifier(ctx):
    out = []
    helpers = _constant_hmac_helpers(ctx)
    for element in _secret_fields(ctx):
        for helper in _linked_helpers(ctx, element, helpers):
            rel = helper['path'].relative_to(ctx.root).as_posix()
            call = {'file': rel, 'start_line': helper['key']['start_line'], 'end_line': helper['key']['end_line']}
            out.append(_match(ctx, KEYED, [ctx.evidence(helper['setter']), _masked(ctx.evidence(call), '[keyed hash helper; key masked]')],
                              element=element, operation='Store'))
    return out


@rule(HMAC_KEY)
def hardcoded_hmac_key(ctx):
    out = []
    helpers = _constant_hmac_helpers(ctx)
    for element in _secret_fields(ctx):
        for helper in _linked_helpers(ctx, element, helpers):
            key = ctx.evidence(helper['key'])
            out.append(_match(ctx, HMAC_KEY, [_masked(key), ctx.evidence(element['source'])],
                              element=element, nexus=(element['id'],), operation='Store'))
    return out


@rule(MD5_LOGIN)
def md5_credential_compare(ctx):
    out = []
    helpers = _md5_helpers(ctx)
    secrets = [e for e in _secret_fields(ctx) if re.search(r'pass(?:word|wd)?$|pwd$', e['field'], re.I)]
    if not helpers or not secrets:
        return out
    for path, rel, text in _code_files(ctx):
        for use in re.finditer(r'\b(?:([\w$]+)\.)?([\w$]+)\(\s*(?:req|request)\.(?:body|query)\.(?:password|passwd|pwd)\b', text):
            for helper in helpers:
                if helper['name'] != use.group(2) or not _resolves(path, use.group(1), helper['name'], helper['path'], text):
                    continue
                coords = [ctx.evidence(_coord(rel, text, use.start())), ctx.evidence(helper['coord'])]
                out.append(_match(ctx, MD5_LOGIN, coords, element=secrets[0], operation='Collect'))
    return out


# Browser storage and cookies


@rule(TOKEN_SITE)
def token_storage_site(ctx):
    sites = {}
    for stored in ctx.inventory.get('client_storage', []):
        if stored.get('op') != 'set' or stored.get('api') != 'localStorage' or _IGNORED.search(stored['source']['file']):
            continue
        sites.setdefault(stored['key'], []).append(stored['source'])
    out = []
    for key, coords in sites.items():
        element = ctx.element(f'storage:localStorage.{key}')
        if not element or element['data_category'] != 'Authentication Secret':
            continue
        headers = [h['source'] for h in ctx.inventory.get('outbound_headers', [])
                   if re.search(r'localStorage\.getItem\(\s*[\'"]' + re.escape(key) + r'[\'"]\s*\)', h.get('value_expression', ''))]
        if not headers:
            continue
        for coord in sorted({(c['file'], c['start_line'], c['end_line']) for c in coords}):
            site = {'file': coord[0], 'start_line': coord[1], 'end_line': coord[2]}
            out.append(_match(ctx, TOKEN_SITE, [ctx.evidence(site), *(ctx.evidence(h) for h in headers)], element=element, operation='Store'))
    return out


def _arguments(text, open_index):
    """Split the argument list opened at ``text[open_index] == '('``; returns (arguments, end_index) or None."""
    depth, args, start, quote = 0, [], open_index + 1, None
    for i in range(open_index, len(text)):
        ch = text[i]
        if quote:
            if ch == quote and text[i - 1] != '\\':
                quote = None
        elif ch in '\'"`':
            quote = ch
        elif ch in '([{':
            depth += 1
        elif ch in ')]}':
            depth -= 1
            if depth == 0:
                tail = text[start:i].strip()
                if tail:
                    args.append(tail)
                return args, i
        elif ch == ',' and depth == 1:
            args.append(text[start:i].strip())
            start = i + 1
    return None


def _cookie_flags(options, text, before, seen=frozenset(), initial=None):
    """Resolve object spreads in order; an opaque spread makes prior values unknown."""
    flags = dict(initial) if initial is not None else dict.fromkeys(('httpOnly', 'secure', 'sameSite'), False)
    if not (options.startswith('{') and options.endswith('}')):
        return dict.fromkeys(flags, None)
    parsed = _arguments('(' + options[1:-1] + ')', 0)
    for part in parsed[0] if parsed else ():
        spread = re.fullmatch(r'\.\.\.\s*([\w$]+)', part)
        if spread:
            name = spread.group(1)
            declarations = list(re.finditer(r'\bconst\s+' + re.escape(name) + r'\s*=\s*(\{[^{}]*\})', text[:before], re.S))
            if declarations and name not in seen:
                declaration = declarations[-1]
                values = _cookie_flags(declaration.group(1), text, declaration.start(), seen | {name}, flags)
            else:
                values = dict.fromkeys(flags, None)
            flags.update(values)
        elif part.startswith('...'):
            flags.update(dict.fromkeys(flags, None))
        else:
            match = re.fullmatch(r'\s*(httpOnly|secure|sameSite)\s*:\s*(.*?)\s*', part, re.S)
            if match:
                flag, value = match.groups()
                value = value.strip().strip('\'"').lower()
                flags[flag] = value not in ('false', 'undefined', 'null') and not (flag == 'sameSite' and value == 'none')
    return flags


@rule(COOKIE)
def session_cookie_flags(ctx):
    out = []
    secrets = _secret_fields(ctx)
    if not secrets:
        return out
    for path, rel, text in _code_files(ctx):
        for call in re.finditer(r'\bres\.cookie\s*\(', text):
            parsed = _arguments(text, call.end() - 1)
            if not parsed or len(parsed[0]) < 2:
                continue
            args, end = parsed
            if not re.fullmatch(r'[\'"`](?:[\w.-]*(?:token|session|sid|jwt|auth)[\w.-]*)[\'"`]', args[0], re.I):
                continue
            if len(args) > 2:
                options = args[2]
                if not options.startswith('{'):
                    continue  # options built elsewhere: the flags are not determinable from this call
            else:
                options = '{}'
            missing = [flag for flag, value in _cookie_flags(options, text, call.start()).items() if value is False]
            if not missing:
                continue
            evidence = ctx.evidence(_coord(rel, text, call.start(), end))
            out.append(_match(ctx, COOKIE, [evidence], nexus=tuple(e['id'] for e in secrets),
                              categories=('Authentication Secret',), operation='Store'))
    return out


@rule(JSONP)
def jsonp_response(ctx):
    out = []
    elements = [e for e in ctx.classified() if e['kind'] == 'model-field' and e['field'].lower() != 'id']
    for path, rel, text in _code_files(ctx):
        for call in re.finditer(r'\bres\.jsonp\s*\(', text):
            parsed = _arguments(text, call.end() - 1)
            if not parsed or not parsed[0]:
                continue
            tops = [m.start() for m in re.finditer(r'^(?:export\s+)?(?:async\s+)?(?:const|let|var|function)\b', text, re.M)]
            begin = max((t for t in tops if t <= call.start()), default=0)
            handler = text[begin:call.start()]
            expressions = [parsed[0][0]]
            seen = set()
            # Follow local values assigned into the response, not unrelated reads in the handler.
            for expression in expressions:
                for name in re.findall(r'\b[A-Za-z_$][\w$]*\b', expression):
                    if name in seen:
                        continue
                    seen.add(name)
                    pattern = r'\b' + re.escape(name) + r'(?:\s*:\s*[^=;\n]+)?\s*=\s*(\{[^{}]*\}|[^;\n]+)'
                    expressions.extend(m.group(1) for m in re.finditer(pattern, handler, re.S))
            reached = [e for e in elements if any(re.search(r'(?:\?\.|\.)' + re.escape(e['field']) + r'\b', expression) for expression in expressions)]
            if not reached:
                continue
            evidence = [ctx.evidence(_coord(rel, text, call.start(), call.end()))]
            out.append(_match(ctx, JSONP, evidence, nexus=tuple(e['id'] for e in reached),
                              categories=tuple(dict.fromkeys(e['data_category'] for e in reached)), operation='Expose'))
    return out


# Terraform


def _module(coord):
    return str(PurePosixPath(coord['file']).parent)


def _listener_actions(record):
    actions = record['attributes'].get('default_action', [])
    return [a for a in (actions if isinstance(actions, list) else [actions]) if isinstance(a, dict)]


@rule(LISTENER)
def plaintext_listener(ctx):
    elements = [e for e in ctx.classified() if e['id'].startswith('model:')]
    if not elements:
        return []
    terraform = ctx.inventory.get('terraform', [])
    listeners = [r for r in terraform if r['type'] in ('aws_lb_listener', 'aws_alb_listener') and r.get('sources')]
    out = []
    for listener in listeners:
        attrs = listener['attributes']
        if str(attrs.get('protocol', '')).upper() != 'HTTP':
            continue
        actions = _listener_actions(listener)
        if not actions or any(a.get('type') == 'redirect' for a in actions):
            continue
        for module in sorted({_module(s) for s in listener['sources']}):
            # A tree redirects port 80 to HTTPS when any listener of the same load balancer does.
            redirected = any(any(a.get('type') == 'redirect' for a in _listener_actions(other))
                             and other['attributes'].get('load_balancer_arn') == attrs.get('load_balancer_arn')
                             and any(_module(s) == module for s in other['sources'])
                             for other in listeners)
            serves = any(r['type'] in ('aws_lb_target_group', 'aws_alb_target_group') and any(_module(s) == module for s in r['sources'])
                         for r in terraform)
            if redirected or not serves:
                continue
            source = min((s for s in listener['sources'] if _module(s) == module), key=lambda s: (s['file'], s['start_line']))
            evidence = [ctx.evidence(source), ctx.evidence(elements[0]['source'])]
            out.append(_match(ctx, LISTENER, evidence, nexus=(elements[0]['id'],), categories=(elements[0]['data_category'],), operation='Expose'))
    return out


# Retention

_ERASURE_PATH = re.compile(r'(?:account|user|profile|data|member)\w*[/_-]?(?:eras|delet|clos|deactivat)|(?:eras|delet|clos|deactivat)\w*[/_-]?(?:account|user|profile|data|member)', re.I)


def _hard_deletes(ctx, name, table):
    patterns = [r'\b' + re.escape(name) + r'\w*\.destroy\s*\([^;]{0,400}?\bforce\s*:\s*true',
                r'\.destroy\s*\([^;]{0,400}?\btruncate\s*:\s*true',
                r'DELETE\s+FROM\s+[`"\'\[]?' + re.escape(table or name) + r'\b']
    for _, rel, text in _code_files(ctx):
        if any(re.search(p, text, re.I | re.S) for p in patterns):
            return rel
    return None


def _erasure_model_route(ctx, routes, model):
    name = re.escape(model['name'])
    reference = re.compile(r'(?:\bimport\b[^;\n]*\b' + name + r'(?:Model)?\b|\b' + name + r'(?:Model)?\.(?:find\w*|destroy|update|create)\s*\()', re.I)
    table = re.escape(model.get('table') or model['name'])
    auth_model = any(
        re.search(r'\b(?:login|authenticate|signin)\b', text, re.I)
        and re.search(r'\b(?:password|passwd|pwd)\b', text, re.I)
        and (re.search(r'\b' + name + r'(?:Model)?\.(?:findOne|findByPk|findAll)\s*\(', text)
             or re.search(r'\bSELECT\b[^;]*\bFROM\s+[`"\']?' + table + r'\b', text, re.I))
        for _, _, text in _code_files(ctx)
    )
    for route in routes:
        handler = route.get('handler') or route['registration']
        path = ctx.root / handler['file']
        if not path.is_file():
            continue
        text = path.read_text(errors='replace')
        if reference.search(text) or (auth_model and re.search(r'\b(?:authenticated|session|req\.user)\b', text, re.I)):
            return route
    return None


@rule(SOFT_DELETE)
def soft_delete_retention(ctx):
    routes = sorted((r for r in ctx.routes() if _ERASURE_PATH.search(r['normalised_path']) and r.get('registration')),
                    key=lambda r: (r['registration']['file'], r['registration']['start_line'], r['method']))
    if not routes:
        return []
    out = []
    for model in ctx.inventory.get('models', []):
        if not (model.get('options') or {}).get('paranoid'):
            continue
        elements = [e for e in ctx.classified() if e['id'].startswith('model:' + model['name'] + '.')]
        if not elements or _hard_deletes(ctx, model['name'], model.get('table')):
            continue
        route = _erasure_model_route(ctx, routes, model)
        if not route:
            continue
        source = model['source']
        lines = (ctx.root / source['file']).read_text(errors='replace').splitlines()
        hit = next((i for i in range(source['start_line'], source['end_line'] + 1) if re.search(r'\bparanoid\s*:\s*true\b', lines[i - 1])), None)
        if hit is None:
            continue
        anchor = {'file': source['file'], 'start_line': hit, 'end_line': hit}
        element = next((e for e in elements if e['field'].lower() == 'email'), elements[0])
        gate = [ctx.evidence(route['registration'])]
        out.append(_match(ctx, SOFT_DELETE, [ctx.evidence(anchor), ctx.evidence(element['source'])], element=element, operation='Store', gate=gate))
    return out
