"""Rules for framework configuration: nginx access logs and Kubernetes workloads serving a Personal Data store.

Every Rule needs a Personal Data link: a classified route Element for the nginx Rule, and a store link
(a mounted volume plus a Prisma datasource or Mongoose connection named by a container environment
variable) for the Kubernetes Rules. An isolated port, privileged flag or log directive is never enough.
"""
from __future__ import annotations

import re

from auditor.exposure import decide_exposure
from auditor.mapping import Match
from auditor.rules import RuleSpec, rule

VECTOR = 'CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N'
NGINX_LOG = RuleSpec('SEC-01-nginx-query-logging', 'SEC-01', 'Personal Data route parameters written to nginx access logs', 'config', 'technical', VECTOR, ('nginx',))
K8S_PRIVILEGED = RuleSpec('SEC-16-kubernetes-privileged-store', 'SEC-16', 'Privileged or root workload mounting a Personal Data store', 'config', 'technical', VECTOR, ('kubernetes',))
K8S_PUBLIC = RuleSpec('SEC-16-kubernetes-public-store', 'SEC-16', 'Public Service in front of a Personal Data store workload', 'config', 'technical', VECTOR, ('kubernetes',))

_REQUEST_VARIABLES = {'request', 'request_uri', 'uri', 'document_uri'}
_QUERY_VARIABLES = {'request', 'request_uri', 'args', 'query_string'}


def _match(ctx, spec, element, coords, operation, *, nexus=()):
    evidence = [ctx.evidence(c) for c in coords]
    return Match(spec.id, spec.issue_type, evidence, spec.classification, spec.base_vector,
                 ctx.schema_element(element['id']), element['data_category'], (element['data_category'],), operation,
                 ctx.flow_steps(element['id']), decide_exposure(authenticated=None, restricted=evidence[:1]),
                 nexus_elements=nexus)


def _location_matches(location, path):
    prefix, modifier = location['path'] or '', location['modifier']
    if modifier == '=':
        return path == prefix
    if modifier in ('~', '~*'):
        try:
            return bool(re.search(prefix, path, re.I if modifier == '~*' else 0))
        except re.error:
            return False
    return path.startswith(prefix)


def _log_variables(record, access):
    if not access or access['off']:
        return None
    if access['format'] == 'combined' and not any(f['name'] == 'combined' for f in record['log_formats']):
        return {'request', 'request_uri'}, None
    declared = next((f for f in record['log_formats'] if f['name'] == access['format']), None)
    return (set(declared['variables']), declared['source']) if declared else None


@rule(NGINX_LOG)
def nginx_query_logging(ctx):
    out = []
    for element in ctx.classified():
        if element['kind'] != 'route-param' or not element['id'].startswith('param:GET '):
            continue
        spec, _, name = element['id'][len('param:GET '):].rpartition('?' if '?' in element['id'] else '#')
        query = '?' in element['id']
        path = spec.split('?')[0]
        path = re.sub(r'\{[^}]*\}', 'x', path)
        route = next(iter(ctx.routes('GET', spec.split('?')[0])), None)
        for record in ctx.inventory.get('nginx', []):
            for server in record['servers']:
                for location in server['locations']:
                    logged = _log_variables(record, location['access_log']) if location['proxy'] else None
                    if not logged or not _location_matches(location, path):
                        continue
                    variables, format_source = logged
                    wanted = (_QUERY_VARIABLES if query else _REQUEST_VARIABLES)
                    if not (variables & wanted or (query and f'arg_{name}' in variables)):
                        continue
                    coords = [route['registration'] if route else element['source'], location['access_log']['source']]
                    if format_source:
                        coords.append(format_source)
                    out.append(_match(ctx, NGINX_LOG, element, coords, 'Log'))
    return out


def _store_elements(ctx):
    """Classified model Elements of ORM stores, keyed by the environment variable naming their connection."""
    by_env = {}
    for datasource in ctx.inventory.get('prisma_datasources', []):
        if not datasource.get('url_env'):
            continue
        models = {m['name'] for m in ctx.inventory.get('models', []) if m.get('kind') == 'prisma' and m['source']['file'].rsplit('/', 1)[0] == datasource['source']['file'].rsplit('/', 1)[0]}
        elements = [e for e in ctx.classified() if e['id'].startswith('model:') and e['id'][6:].split('.')[0] in models]
        if elements:
            by_env.setdefault(datasource['url_env'], []).append((datasource['source'], min(elements, key=lambda e: e['id'])))
    for connection in ctx.inventory.get('orm_connections', []):
        models = {m['name'] for m in ctx.inventory.get('models', []) if m.get('kind') == 'mongoose'}
        elements = [e for e in ctx.classified() if e['id'].startswith('model:') and e['id'][6:].split('.')[0] in models]
        if elements:
            by_env.setdefault(connection['env'], []).append((connection['source'], min(elements, key=lambda e: e['id'])))
    return by_env


def _store_workloads(ctx):
    """(resource, container, mount, env, datasource source, element) for workloads mounting a store volume."""
    stores = _store_elements(ctx)
    for resource in ctx.inventory.get('kubernetes', []):
        workload = resource.get('workload')
        if not workload:
            continue
        for container in workload['containers']:
            mount = next((m for m in container['mounts'] if m['persistent'] and m['volume_type'] == 'persistentVolumeClaim'), None)
            if not mount:
                continue
            for env in container['env']:
                for source, element in stores.get(env['name'], []):
                    yield resource, container, mount, env, source, element


def _risky(security):
    s = security['settings']
    return (s.get('privileged') is True or s.get('run_as_user') == 0
            or s.get('run_as_non_root') is False or s.get('allow_privilege_escalation') is True)


@rule(K8S_PRIVILEGED)
def kubernetes_privileged_store(ctx):
    out = []
    for resource, container, mount, env, source, element in _store_workloads(ctx):
        if _risky(container['security']):
            coords = [container['security']['sources'][-1], mount['source'], env['source'], source]
            out.append(_match(ctx, K8S_PRIVILEGED, element, coords, 'Store', nexus=(element['id'],)))
    return out


@rule(K8S_PUBLIC)
def kubernetes_public_store(ctx):
    out = []
    for resource, container, mount, env, source, element in _store_workloads(ctx):
        labels = resource['workload']['labels']
        for service in ctx.inventory['kubernetes']:
            detail = service.get('service')
            if (not detail or detail['exposure'] != 'public' or not detail['selector']
                    or service['namespace'] != resource['namespace']
                    or any(labels.get(k) != v for k, v in detail['selector'].items())):
                continue
            out.append(_match(ctx, K8S_PUBLIC, element, [service['source'], mount['source'], env['source'], source], 'Store', nexus=(element['id'],)))
    return out
