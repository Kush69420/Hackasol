"""Security Rules for Personal Data storage, error responses and deployment configuration."""
from __future__ import annotations

import re
from pathlib import PurePosixPath

from auditor.exposure import decide_exposure
from auditor.mapping import Match
from auditor.rules import RuleSpec, rule

VECTOR = 'CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N'
AADHAAR = RuleSpec('SEC-03-sequelize-aadhaar-storage', 'SEC-03', 'Aadhaar stored outside a vault', 'ts-ast', 'technical', VECTOR, ('typescript', 'javascript'))
DJANGO_AADHAAR = RuleSpec('SEC-03-django-aadhaar-storage', 'SEC-03', 'Django Aadhaar number stored without field protection', 'python-ast', 'technical', VECTOR, ('python',))
FASTAPI_AADHAAR = RuleSpec('SEC-03-fastapi-aadhaar-response', 'SEC-03', 'FastAPI returns unmasked Aadhaar', 'python-ast', 'technical', VECTOR, ('python',))
ERROR = RuleSpec('SEC-06-express-error-disclosure', 'SEC-06', 'Verbose error response exposing Personal Data', 'ts-ast', 'technical', VECTOR, ('typescript', 'javascript'))
LOG = RuleSpec('SEC-12-express-access-logging', 'SEC-12', 'Personal Data reads without access logging', 'ts-ast', 'compliance-gap', None, ('typescript', 'javascript'))
BACKUP = RuleSpec('SEC-14-terraform-store-backup', 'SEC-14', 'Persistent Personal Data store without configured backup', 'config', 'compliance-gap', None, ('terraform',))
PUBLIC = RuleSpec('SEC-16-terraform-public-store', 'SEC-16', 'Public Personal Data store', 'config', 'technical', VECTOR, ('terraform',))
BUCKET = RuleSpec('SEC-16-terraform-public-storage', 'SEC-16', 'Public Personal Data object store', 'config', 'technical', VECTOR, ('terraform',))
ROOT = RuleSpec('SEC-16-docker-root-container', 'SEC-16', 'Root container serving a Personal Data store', 'config', 'technical', VECTOR, ('dockerfile', 'terraform'))


def _source(record):
    return min(record['sources'], key=lambda s: (len(PurePosixPath(s['file']).parts), s['file'], s['start_line']))


def _text(ctx, coord):
    lines = (ctx.root / coord['file']).read_text(encoding='utf-8', errors='replace').splitlines()
    return '\n'.join(lines[coord['start_line'] - 1:coord['end_line']])


def _match(ctx, spec, element, coords, *, gate=None, nexus=(), operation='Store'):
    evidence = [ctx.evidence(c) for c in coords]
    return Match(spec.id, spec.issue_type, evidence, spec.classification, spec.base_vector,
                 ctx.schema_element(element['id']) if element else None,
                 element['data_category'] if element else None,
                 (element['data_category'],) if element else (), operation,
                 ctx.flow_steps(element['id']) if element else [],
                 decide_exposure(authenticated=None, restricted=evidence[:1]),
                 nexus_elements=nexus, gate_evidence=[ctx.evidence(c) for c in gate] if gate else None)


def _model_elements(ctx):
    return [e for e in ctx.classified() if e['id'].startswith('model:')]


def _records(ctx, *types):
    return [r for r in ctx.inventory.get('terraform', []) if r['type'] in types and r.get('sources')]


@rule(AADHAAR)
def aadhaar_storage(ctx):
    result = []
    for element in _model_elements(ctx):
        if not re.search(r'aadhaar|aadhar', element['id'], re.I):
            continue
        text = _text(ctx, element['source'])
        if not re.search(r'\b(?:vault|tokeniz\w*|encrypt\w*)\s*\(', text, re.I):
            result.append(_match(ctx, AADHAAR, element, [element['source']]))
        field = element['id'].rsplit('.', 1)[-1]
        for route in ctx.routes():
            handler = route.get('handler')
            if not handler:
                continue
            body = _text(ctx, handler)
            display = re.search(r'\bres(?:ponse)?\.(?:send|json)\s*\(\s*[\w$]+\.' +
                                re.escape(field) + r'\s*\)', body, re.I)
            if display:
                line = handler['start_line'] + body[:display.start()].count('\n')
                coord = {'file': handler['file'], 'start_line': line, 'end_line': line}
                result.append(_match(ctx, AADHAAR, element, [coord, element['source']], operation='Expose'))
    return result

@rule(DJANGO_AADHAAR)
def django_aadhaar_storage(ctx):
    out = []
    for model in ctx.inventory.get('models', []):
        for field in model.get('fields', []):
            choices = [c['source'] for c in field.get('government_identifier_evidence', [])
                       if re.search(r'aadhaar|aadhar', str(c.get('value', '')), re.I)]
            if not choices:
                continue
            element = ctx.element(f"model:{model['name']}.{field['name']}")
            if not element or not field.get('type', '').endswith('Field'):
                continue
            if re.search(r'encrypt|vault|tokeniz', field['type'], re.I):
                continue
            out.append(_match(ctx, DJANGO_AADHAAR, element, [*choices, field['source']]))
    return out


@rule(FASTAPI_AADHAAR)
def fastapi_aadhaar_response(ctx):
    out = []
    for element in ctx.classified():
        if element['kind'] != 'collection-field' or not re.search(r'aadhaar|aadhar', element['name'], re.I):
            continue
        if re.search(r'\b(?:mask|redact|encrypt|tokeniz)\w*\s*\(', _text(ctx, element['source']), re.I):
            continue
        for step in ctx.steps(element['id']):
            if step['operation'] != 'Expose' or step.get('origin') != 'fastapi':
                continue
            # The analyser joins only an explicitly returned service result.
            if re.search(r'\b(?:mask|redact|encrypt|tokeniz)\w*\s*\(', _text(ctx, step['source']), re.I):
                continue
            out.append(_match(ctx, FASTAPI_AADHAAR, element, [step['source'], element['source']], operation='Expose'))
    return out


@rule(ERROR)
def error_disclosure(ctx):
    result = []
    for hit in ctx.semgrep_matches('op-expose-error-page'):
        coord = {k: hit[k] for k in ('file', 'start_line', 'end_line')}
        for route in ctx.routes():
            handler = route.get('handler')
            if not handler or handler['file'] != coord['file'] or not handler['start_line'] <= coord['start_line'] <= handler['end_line']:
                continue
            body = _text(ctx, handler)
            # A message built from an identified Element is a demonstrated nexus;
            # an arbitrary error message alone cannot establish Personal Data exposure.
            for element in ctx.classified():
                field = element.get('field') or element['id'].rsplit('.', 1)[-1]
                if not field or not re.search(r'new\s+Error\s*\([^\n]*(?:req\.body|req\.query|[\w$]+)\.' + re.escape(field) + r'\b', body, re.I):
                    continue
                result.append(_match(ctx, ERROR, element, [coord, handler, element['source']], nexus=(element['id'],), operation='Expose'))
    return result


@rule(LOG)
def access_logging(ctx):
    if any(entry.get('kind') == 'morgan' for entry in ctx.inventory.get('logging', [])):
        return []
    # Other request middleware is distinct from ordinary application event logging.
    for path in ctx.files:
        if path.suffix not in ('.js', '.ts'):
            continue
        source = path.read_text(encoding='utf-8', errors='replace')
        if re.search(r'\b(?:app|router)\.use\s*\(\s*(?:pinoHttp|expressWinston\.logger|accessLogger)\s*\(', source):
            return []
    elements = _model_elements(ctx)
    if not elements:
        return []
    for route in ctx.routes('GET'):
        model = route.get('model')
        matching = [e for e in elements if e['id'].startswith('model:' + str(model) + '.')]
        if not matching and route.get('handler'):
            body = _text(ctx, route['handler'])
            matching = [e for e in elements if re.search(
                r'\b' + re.escape(e['id'][6:].split('.')[0]) +
                r'(?:Model)?\.(?:findAll|findOne|findByPk)\s*\(', body)]
        if matching:
            coord = route['registration']
            return [_match(ctx, LOG, matching[0], [coord, matching[0]['source']], gate=[coord], operation='Expose')]
    return []


def _efs_stores(ctx):
    elements = _model_elements(ctx)
    if not elements:
        return
    # A task must mount the named EFS resource; an unrelated EFS declaration is not a store nexus.
    for store in _records(ctx, 'aws_efs_file_system'):
        ref = 'aws_efs_file_system.' + store['name']
        for task in _records(ctx, 'aws_ecs_task_definition'):
            text = _text(ctx, _source(task))
            if ref not in text or not re.search(r'\b(?:mountPoints|containerPath)\b', text):
                continue
            # SQLite or an explicitly database-labelled mount links the volume to the model store.
            if not re.search(r'\b(?:sqlite|database|postgres|mysql)\b', text, re.I):
                continue
            yield store, task, elements[0]


def _has_backup(ctx, store):
    ref = 'aws_efs_file_system.' + store['name']
    plans = {r['name'] for r in _records(ctx, 'aws_backup_plan')}
    store_dirs = {str(PurePosixPath(s['file']).parent) for s in store['sources']}
    for selection in _records(ctx, 'aws_backup_selection'):
        if not any(str(PurePosixPath(s['file']).parent) in store_dirs for s in selection['sources']):
            continue
        text = _text(ctx, _source(selection))
        plan = re.search(r'aws_backup_plan\.(\w+)', text)
        if ref in text and plan and plan.group(1) in plans:
            return True
    return False


@rule(BACKUP)
def missing_backup(ctx):
    out = []
    for store, task, element in _efs_stores(ctx):
        if _has_backup(ctx, store):
            continue
        coords = [_source(store), _source(task), element['source']]
        out.append(_match(ctx, BACKUP, element, coords, gate=coords[:2]))
    return out


@rule(PUBLIC)
def public_store(ctx):
    out = []
    elements = _model_elements(ctx)
    if not elements:
        return out
    for store in _records(ctx, 'aws_db_instance'):
        attrs = store['attributes']
        publicly_accessible = attrs.get('publicly_accessible') is True
        tasks = [task for task in _records(ctx, 'aws_ecs_task_definition')
                 if 'aws_db_instance.' + store['name'] in _text(ctx, _source(task))]
        if not tasks:
            continue
        if publicly_accessible:
            element = elements[0]
            out.append(_match(ctx, PUBLIC, element, [_source(store), _source(tasks[0]), element['source']], nexus=(element['id'],)))
            continue
        groups = str(attrs.get('vpc_security_group_ids', ''))
        for group in _records(ctx, 'aws_security_group'):
            if 'aws_security_group.' + group['name'] not in groups:
                continue
            port = attrs.get('port', {'postgres': 5432, 'mysql': 3306, 'mariadb': 3306}.get(attrs.get('engine')))
            for ingress in group.get('facts', {}).get('ingress', []):
                if not isinstance(port, int) or not isinstance(ingress.get('from_port'), int) or not isinstance(ingress.get('to_port'), int):
                    continue
                if not ingress['from_port'] <= port <= ingress['to_port'] or not set(ingress.get('cidr_blocks', [])) & {'0.0.0.0/0', '::/0'}:
                    continue
                element = elements[0]
                out.append(_match(ctx, PUBLIC, element, [_source(store), _source(group), _source(tasks[0]), element['source']], nexus=(element['id'],)))
    return out


@rule(BUCKET)
def public_storage(ctx):
    elements = _model_elements(ctx)
    if not elements:
        return []
    out = []
    for bucket in _records(ctx, 'aws_s3_bucket'):
        ref = 'aws_s3_bucket.' + bucket['name']
        tasks = [task for task in _records(ctx, 'aws_ecs_task_definition')
                 if ref in _text(ctx, _source(task))]
        if not tasks:
            continue
        configs = [bucket] + [r for r in _records(ctx, 'aws_s3_bucket_acl', 'aws_s3_bucket_policy',
                                                    'aws_s3_bucket_public_access_block')
                              if ref in _text(ctx, _source(r))]
        for config in configs:
            attrs = config['attributes']
            acl = attrs.get('acl') in ('public-read', 'public-read-write')
            block = config['type'] == 'aws_s3_bucket_public_access_block' and any(
                attrs.get(key) is False for key in ('block_public_acls', 'ignore_public_acls',
                                                     'block_public_policy', 'restrict_public_buckets'))
            text = _text(ctx, _source(config))
            policy = (config['type'] == 'aws_s3_bucket_policy'
                      and bool(re.search(r'(?is)["\']?principal["\']?\s*[:=]\s*(?:["\']\*["\']|\{[^}]*["\']\*["\'])', text))
                      and bool(re.search(r'(?i)\ballow\b', text)))
            if not (acl or block or policy):
                continue
            element = elements[0]
            out.append(_match(ctx, BUCKET, element,
                              [_source(config), _source(bucket), _source(tasks[0]), element['source']],
                              nexus=(element['id'],)))
    return out


@rule(ROOT)
def root_container(ctx):
    out = []
    # Only assess a Dockerfile selected by the deployment build and mounted store.
    for store, task, element in _efs_stores(ctx):
        for build in _records(ctx, 'null_resource'):
            build_text = _text(ctx, _source(build))
            for docker in ctx.inventory.get('docker', []):
                user = (docker.get('final_user') or '').split(':', 1)[0]
                if user not in ('', 'root', '0') or not docker.get('stages'):
                    continue
                module = PurePosixPath(_source(build)['file']).parent
                referenced = re.findall(r'\$\{path\.module\}/([^\"\'\s]+)', build_text)
                import posixpath
                if not any(posixpath.normpath(str(module / path)) == docker['file'] for path in referenced):
                    continue
                out.append(_match(ctx, ROOT, element,
                                  [docker['final_user_source'] or docker['stages'][-1]['source'],
                                   _source(build), _source(task), _source(store), element['source']],
                                  nexus=(element['id'],)))
    return out
