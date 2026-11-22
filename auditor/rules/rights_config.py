"""Rules for field protection, Data Principal rights and storage region defaults."""
from __future__ import annotations

import re

from auditor.analysers.region import storage_regions
from auditor.exposure import decide_exposure
from auditor.mapping import Match
from auditor.rules import RuleSpec, rule
from auditor.severity import TIER_BY_CATEGORY

SEC = RuleSpec('SEC-02-sequelize-plain-fields', 'SEC-02', 'Personal Data Elements without field-level protection', 'ts-ast', 'technical', 'CVSS:4.0/AV:L/AC:L/AT:N/PR:H/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N', ('typescript',))
RET = RuleSpec('RET-02-express-erasure-request', 'RET-02', 'Erasure request records a flag without erasure', 'ts-ast', 'compliance-gap', None, ('typescript',))
ACCESS = RuleSpec('RIG-01-express-incomplete-export', 'RIG-01', 'Access summary omits Personal Data Elements', 'ts-ast', 'compliance-gap', None, ('typescript',))
CORRECT = RuleSpec('RIG-02-express-email-correction', 'RIG-02', 'No evidenced email correction path', 'ts-ast', 'compliance-gap', None, ('typescript',))
REGION = RuleSpec('TRF-02-terraform-storage-region', 'TRF-02', 'Storage configured outside India', 'config', 'disclosure', None, ('terraform',))


def _text(ctx, coord):
    p = ctx.root / coord['file']
    return '\n'.join(p.read_text(encoding='utf-8').splitlines()[coord['start_line'] - 1:coord['end_line']])


def _ev(ctx, coord):
    return ctx.evidence(coord)


def _match(ctx, spec, element, evidence, *, gate=None, exposure=None, legal=None, vector=None, severity_note=None):
    ev = list(dict.fromkeys((e['file'], e['start_line'], e['end_line']) for e in evidence))
    evidence = [next(e for e in evidence if (e['file'], e['start_line'], e['end_line']) == key) for key in ev]
    return Match(spec.id, spec.issue_type, evidence, spec.classification, vector or spec.base_vector,
                 ctx.schema_element(element['id']), element['data_category'], (), 'Store',
                 ctx.flow_steps(element['id']), exposure or decide_exposure(authenticated=None, restricted=evidence[:1]),
                 gate_evidence=gate, legal_review=legal, status_hint='needs-legal-review' if legal else None,
                 severity_note=severity_note)


def _principal(ctx):
    return ctx.element('model:User.email')


def _handler(ctx, route):
    h = route.get('handler')
    return _text(ctx, h) if h and h.get('file') else ''


@rule(SEC)
def plain_fields(ctx):
    out = []
    infra = []
    for record in ctx.inventory.get('terraform', []):
        if record.get('type') == 'aws_efs_file_system' and record.get('facts', {}).get('encrypted') is True:
            sources = record.get('sources', [])
            if sources:
                infra.append(_ev(ctx, min(sources, key=lambda s: (len(s['file'].split('/')), s['file']))))
                expr = record.get('attributes', {}).get('encrypted', '')
                if isinstance(expr, str) and expr.startswith('var.'):
                    for variable in ctx.inventory.get('terraform', []):
                        if variable.get('type') == 'variable' and variable.get('name') == expr[4:] and variable.get('sources'):
                            infra.append(_ev(ctx, min(variable['sources'], key=lambda s: (len(s['file'].split('/')), s['file']))))
    # A volume declaration alone does not establish that the database is mounted there.
    storage_paths = []
    for file in ctx.files:
        if file.suffix not in ('.ts', '.js'):
            continue
        for index, line in enumerate(file.read_text(encoding='utf-8').splitlines(), 1):
            match = re.search(r"storage\s*:.*?['\"]([^'\"]+\.sqlite(?:3)?)['\"]", line)
            if match:
                storage_paths.append((match.group(1), {'file': file.relative_to(ctx.root).as_posix(), 'start_line': index, 'end_line': index}))
    note = None
    if infra and storage_paths:
        for record in ctx.inventory.get('terraform', []):
            if record.get('type') != 'aws_ecs_task_definition' or not record.get('sources'):
                continue
            definitions = record.get('attributes', {}).get('container_definitions', '')
            mounts = re.findall(r'containerPath\s*=\s*\"([^\"]+)\"', str(definitions))
            if mounts and not any('/' + path.lstrip('./') in mount + '/' or mount.rstrip('/') in path for path, _ in storage_paths for mount in mounts):
                source = min(record['sources'], key=lambda s: (len(s['file'].split('/')), s['file']))
                task_text = _text(ctx, source)
                mount_line = next((i for i, line in enumerate(task_text.splitlines()) if 'containerPath' in line), 0)
                mount_source = {'file': source['file'], 'start_line': source['start_line'] + mount_line,
                                'end_line': source['start_line'] + mount_line}
                infra.extend([_ev(ctx, mount_source), _ev(ctx, storage_paths[0][1])])
                note = (f"The configured volume mount in {mount_source['file']}:{mount_source['start_line']} does not match SQLite storage at "
                        f"{storage_paths[0][1]['file']}:{storage_paths[0][1]['start_line']}; volume encryption is not credited. "
                        "The Personal Data Element remains without field-level protection.")
                break
    for model in ctx.inventory.get('models', []):
        if model.get('kind') != 'sequelize':
            continue
        for field in model.get('fields', []):
            element = ctx.element(f"model:{model['name']}.{field['name']}")
            if not element or TIER_BY_CATEGORY.get(element['data_category']) not in ('A', 'B'):
                continue
            # This Slice's financial case is an account identifier, not an amount
            # or card expiry component. SEC-02's catalogue scope is broader.
            if element['data_category'] == 'Financial' and not re.search(
                    r'(?:card(?:num|number)|account(?:num|number|no)|ifsc|upi|vpa)',
                    field['name'].replace('_', ''), re.I):
                continue
            text = _text(ctx, field['source'])
            # A getter or a sanitising setter alone does not protect data at rest.
            if re.search(r'\bset\s*\(', text) and re.search(r'\b(?:encrypt|encryptSync|hash|hashSync|scrypt|bcrypt|argon2)\s*\(', text, re.I):
                continue
            evidence = [_ev(ctx, field['source']), *infra]
            out.append(_match(ctx, SEC, element, evidence, severity_note=note))
    return out


@rule(RET)
def erasure_request(ctx):
    element = _principal(ctx)
    if not element:
        return []
    out = []
    for route in ctx.routes('POST'):
        text = _handler(ctx, route)
        flag = re.search(r'\bdeletionRequested\s*:\s*true\b', text)
        if not flag or not re.search(r'\b\w*(?:PrivacyRequest|ErasureRequest)\w*\.create\s*\(', text, re.I):
            continue
        if re.search(r'\b(?:User\w*|\w*[Aa]ccount\w*)\.(?:destroy|update)\s*\(', text):
            continue
        h = route['handler']
        line = h['start_line'] + text[:flag.start()].count('\n')
        anchor = _ev(ctx, {'file': h['file'], 'start_line': line, 'end_line': line})
        gate = [_ev(ctx, route['registration'])]
        out.append(_match(ctx, RET, element, [anchor, *gate], gate=gate))
    return out


@rule(ACCESS)
def incomplete_export(ctx):
    principal = _principal(ctx)
    if not principal:
        return []
    out = []
    # The inventory can contain one entry per handler in an Express chain. Assess
    # only the final response-producing handler for each method and endpoint.
    endpoints = {}
    for route in ctx.routes():
        if re.search(r'(?:export|access)', route['normalised_path'], re.I):
            text = _handler(ctx, route)
            if text and re.search(r'\b(?:send|json)\s*\(', text):
                endpoints[(route['method'], route['normalised_path'])] = (route, text)
    for route, text in endpoints.values():
        omitted = []
        for e in ctx.classified():
            if not e['id'].startswith('model:') or e['id'] == principal['id']:
                continue
            model, field = e['id'][6:].split('.', 1)
            schema_model = ctx.model(model)
            if model != 'User' and not (schema_model and any(
                    f['name'].lower() in ('userid', 'user_id') for f in schema_model['fields'])):
                continue
            if model == 'User':
                missing = not re.search(r'\b' + re.escape(field) + r'\b', text, re.I)
            else:
                missing = model.lower() not in text.lower() and field.lower() not in text.lower()
            if missing:
                omitted.append(e)
        if omitted:
            gate = [_ev(ctx, principal['source'])]
            evidence = [_ev(ctx, route['handler']), _ev(ctx, route['registration']), *[_ev(ctx, e['source']) for e in omitted]]
            out.append(_match(ctx, ACCESS, principal, evidence, gate=gate))
    return out


@rule(CORRECT)
def email_correction(ctx):
    element = _principal(ctx)
    if not element:
        return []
    account = ctx.model('User')
    editable = {f['name'] for f in account['fields']
                if ctx.element(f"model:User.{f['name']}")
                and ctx.element(f"model:User.{f['name']}")['data_category'] in ('Contact', 'Profile')} if account else set()
    owned = [model for model in ctx.inventory['models'] if model.get('table') and
             any(f['name'].lower() in ('userid', 'user_id') for f in model['fields']) and
             any(ctx.element(f"model:{model['name']}.{f['name']}") and
                 ctx.element(f"model:{model['name']}.{f['name']}")['data_category']
                 for f in model['fields'])]
    profile = []
    writes = []
    generated = {(r['method'], r['normalised_path']): r.get('model')
                 for r in ctx.routes() if r['origin'] == 'finale'}
    for route in ctx.routes():
        text = _handler(ctx, route)
        updates = re.findall(r'\b(?:User\w*|user)\.update\s*\(\s*\{([^}]*)\}', text, re.S)
        if any(re.search(r'\bemail\s*:', update) for update in updates):
            return []
        if updates and any(re.search(r'\b' + re.escape(field) + r'\s*:', update)
                           for update in updates for field in editable):
            if any(re.search(r'\b' + re.escape(field) + r'\s*:\s*req\.body\.' + re.escape(field) + r'\b', update)
                   for update in updates for field in editable):
                profile.append(route)
        user_write = any(re.search(r'\b' + re.escape(field['name']) + r'\s*:', update)
                         for update in updates for field in (account['fields'] if account else [])
                         if field['name'] in editable or field['name'].lower() == 'password')
        model_name = generated.get((route['method'], route['normalised_path'])) or route.get('model')
        owned_route = (route['method'] in ('POST', 'PUT', 'PATCH') and
                       not any('deny' in m['name'].lower() for m in route['middleware']) and
                       any(model_name in (model['name'], model['name'] + 'Model') for model in owned))
        if user_write or owned_route:
            writes.append(route)
    if not profile:
        return []
    account_put = [r for r in ctx.routes('PUT') if re.search(r'/api/users/\{', r['normalised_path'], re.I)]
    denied = [r for r in account_put if any('deny' in m['name'].lower() for m in r['middleware'])]
    if account_put and not denied:
        return []
    # Prefer explicitly mounted write paths over duplicate generated routes.
    blocked = {(r['method'], r['normalised_path']) for r in ctx.routes()
               if any('deny' in m['name'].lower() for m in r['middleware'])}
    writes = [r for r in writes if r['origin'] != 'finale' and
              (r['method'], r['normalised_path']) not in blocked]
    gate = [_ev(ctx, r['registration']) for r in writes]
    if not gate:
        return []
    evidence = [_ev(ctx, profile[0]['handler']), _ev(ctx, profile[0]['registration']),
                _ev(ctx, element['source']), *[_ev(ctx, r['registration']) for r in denied], *gate]
    return [_match(ctx, CORRECT, element, evidence, gate=gate)]


@rule(REGION)
def outside_storage(ctx):
    element = _principal(ctx)
    if not element:
        return []
    out = []
    for region in storage_regions(ctx.inventory):
        name = region.get('region')
        if not name or name.startswith('ap-south-') or not region['storage']:
            continue
        def canonical(sources):
            return min(sources, key=lambda s: (len(s['file'].split('/')), s['file']))
        coords = [canonical(region['resolved_from'])]
        # Keep the variable default as an anchor, and one source per logical resource.
        defaults = [s for record in ctx.inventory.get('terraform', []) if record.get('type') == 'variable'
                    for s in record.get('sources', []) if s in region['resolved_from']]
        if defaults:
            coords.insert(0, canonical(defaults))
        coords += [canonical(item['sources']) for item in region['storage'] if item['sources']]
        evidence = [_ev(ctx, c) for c in coords]
        legal = {'readings': [
            {'provision': 'DPDP-Act-16(1)', 'reading': 'Transfer is lawful unless the destination is restricted by notification; this region is a deployment default, not evidence of deployed geography.'},
            {'provision': 'DPDP-Act-11(1)(b)', 'reading': 'The Data Principal may be owed a summary of evidenced sharing; configured storage alone does not establish sharing.'},
        ]}
        out.append(_match(ctx, REGION, element, evidence, exposure=decide_exposure(authenticated=None, outside_india=evidence), legal=legal))
    return out
