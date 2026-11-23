"""Kubernetes manifest analyser: workloads, security contexts, services, ingress, storage, logging.

Source-only. Documents are read with `yaml.compose_all` so every record carries file:line. Secret
resources are never read and literal environment values are kept only when they are filesystem paths
(a storage location), so credentials in a manifest cannot reach the inventory. A document is a
manifest only if it has both `apiVersion` and `kind`; other YAML (Helm templates, compose files) is
ignored.

Each resource record has a `network` list whose entries say whether the setting is `inbound` or
`outbound` and its `scope` (`public`, `internal`, `restricted`, `external`).
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

_WORKLOADS = {'Deployment', 'StatefulSet', 'DaemonSet', 'ReplicaSet', 'Job', 'CronJob', 'Pod'}
_VOLUME_TYPES = ('persistentVolumeClaim', 'emptyDir', 'hostPath', 'configMap', 'secret', 'projected', 'nfs', 'csi', 'downwardAPI')
_PATH_ENV = re.compile(r'(?:PATH|DIR|FILE|FOLDER)$', re.I)
_constructor = yaml.constructor.SafeConstructor()


class _N:
    """A YAML node with its source position."""

    def __init__(self, node, file):
        self.node, self.file = node, file

    @property
    def coord(self):
        return {'file': self.file, 'start_line': self.node.start_mark.line + 1,
                'end_line': max(self.node.start_mark.line + 1, self.node.end_mark.line + (1 if self.node.end_mark.column else 0))}

    def get(self, key):
        if not isinstance(self.node, yaml.MappingNode):
            return None
        for k, v in self.node.value:
            if isinstance(k, yaml.ScalarNode) and k.value == key:
                return _N(v, self.file)
        return None

    def path(self, *keys):
        cur = self
        for key in keys:
            cur = cur.get(key) if cur else None
        return cur

    def pairs(self):
        if isinstance(self.node, yaml.MappingNode):
            return [(k.value, _N(v, self.file)) for k, v in self.node.value if isinstance(k, yaml.ScalarNode)]
        return []

    def seq(self):
        return [_N(v, self.file) for v in self.node.value] if isinstance(self.node, yaml.SequenceNode) else []

    def value(self):
        try:
            return _constructor.construct_object(self.node, deep=True)
        except yaml.YAMLError:
            return None

    def scalar(self, key=None):
        node = self.get(key) if key else self
        value = node.value() if node else None
        return value if isinstance(value, (str, int, float, bool)) else None


def _security(pod, container):
    merged, sources = {}, []
    for scope in (pod.path('securityContext') if pod else None, container.path('securityContext')):
        if not scope:
            continue
        sources.append(scope.coord)
        for key, name in (('privileged', 'privileged'), ('runAsUser', 'run_as_user'), ('runAsNonRoot', 'run_as_non_root'),
                          ('allowPrivilegeEscalation', 'allow_privilege_escalation'), ('readOnlyRootFilesystem', 'read_only_root_filesystem')):
            value = scope.scalar(key)
            if value is not None:
                merged[name] = value
        drop = scope.path('capabilities', 'drop')
        if drop:
            merged['capabilities_drop'] = [d.scalar() for d in drop.seq()]
    return {'settings': merged, 'sources': sources}


def _workload(resource, spec_path, file):
    pod = resource.path(*spec_path)
    if not pod:
        return None
    labels_node = resource.path(*spec_path[:-1], 'metadata', 'labels') or resource.path('metadata', 'labels')
    volumes = []
    for volume in (pod.path('volumes').seq() if pod.path('volumes') else []):
        kind = next((t for t in _VOLUME_TYPES if volume.get(t)), None)
        detail = volume.get(kind) if kind else None
        volumes.append({'name': volume.scalar('name'), 'type': kind,
                        'claim': detail.scalar('claimName') if kind == 'persistentVolumeClaim' and detail else None,
                        'host_path': detail.scalar('path') if kind == 'hostPath' and detail else None, 'source': volume.coord})
    by_name = {v['name']: v for v in volumes}
    containers = []
    for section in ('containers', 'initContainers'):
        for container in (pod.path(section).seq() if pod.path(section) else []):
            env = []
            for item in (container.path('env').seq() if container.path('env') else []):
                name = item.scalar('name')
                entry = {'name': name, 'source': item.coord, 'value_kind': 'literal'}
                if item.path('valueFrom', 'secretKeyRef'):
                    entry['value_kind'] = 'secret'
                elif item.path('valueFrom', 'configMapKeyRef'):
                    entry.update(value_kind='configMap', config_map=item.path('valueFrom', 'configMapKeyRef').scalar('name'),
                                 config_key=item.path('valueFrom', 'configMapKeyRef').scalar('key'))
                elif item.path('valueFrom'):
                    entry['value_kind'] = 'field'
                else:
                    value = item.scalar('value')
                    entry['value'] = value if isinstance(value, str) and value.startswith('/') and _PATH_ENV.search(name or '') else None
                env.append(entry)
            for ref in (container.path('envFrom').seq() if container.path('envFrom') else []):
                cm = ref.path('configMapRef')
                if cm:
                    env.append({'name': None, 'value_kind': 'configMap-all', 'config_map': cm.scalar('name'), 'source': ref.coord})
            mounts = []
            for mount in (container.path('volumeMounts').seq() if container.path('volumeMounts') else []):
                volume = by_name.get(mount.scalar('name'))
                mounts.append({'volume': mount.scalar('name'), 'path': mount.scalar('mountPath'), 'read_only': bool(mount.scalar('readOnly')),
                               'volume_type': volume['type'] if volume else None, 'claim': volume['claim'] if volume else None,
                               'persistent': bool(volume and volume['type'] in ('persistentVolumeClaim', 'hostPath', 'nfs', 'csi')), 'source': mount.coord})
            ports = [{'container_port': p.scalar('containerPort'), 'name': p.scalar('name')} for p in (container.path('ports').seq() if container.path('ports') else [])]
            containers.append({'name': container.scalar('name'), 'image': container.scalar('image'), 'init': section == 'initContainers',
                               'ports': ports, 'env': env, 'mounts': mounts, 'security': _security(pod, container), 'source': container.coord})
    labels = {k: n.scalar() for k, n in labels_node.pairs()} if labels_node else {}
    return {'labels': labels, 'volumes': volumes, 'containers': containers, 'host_network': bool(pod.scalar('hostNetwork')), 'source': pod.coord}


def _service(resource):
    spec = resource.get('spec')
    kind = (spec.scalar('type') if spec else None) or 'ClusterIP'
    annotations = {k: n.scalar() for k, n in (resource.path('metadata', 'annotations').pairs() if resource.path('metadata', 'annotations') else [])}
    internal_lb = any(re.search(r'internal', k) and str(v).lower() in ('true', '0.0.0.0/0', 'internal') for k, v in annotations.items() if 'load-balancer' in k or 'lb' in k)
    ports = [{'port': p.scalar('port'), 'target_port': p.scalar('targetPort'), 'name': p.scalar('name')} for p in (spec.path('ports').seq() if spec and spec.path('ports') else [])]
    selector = {k: n.scalar() for k, n in (spec.path('selector').pairs() if spec and spec.path('selector') else [])}
    return {'type': kind, 'selector': selector, 'ports': ports, 'external_name': spec.scalar('externalName') if spec else None,
            'exposure': 'outbound' if kind == 'ExternalName' else 'internal' if kind == 'ClusterIP' or internal_lb else 'public'}


def _ingress(resource):
    spec = resource.get('spec')
    annotations = {k: n.scalar() for k, n in (resource.path('metadata', 'annotations').pairs() if resource.path('metadata', 'annotations') else [])}
    rules = []
    for rule in (spec.path('rules').seq() if spec and spec.path('rules') else []):
        for entry in (rule.path('http', 'paths').seq() if rule.path('http', 'paths') else []):
            backend = entry.path('backend', 'service')
            rules.append({'host': rule.scalar('host'), 'path': entry.scalar('path'), 'path_type': entry.scalar('pathType'),
                          'service': backend.scalar('name') if backend else None,
                          'port': (backend.path('port').scalar('number') or backend.path('port').scalar('name')) if backend and backend.path('port') else None,
                          'source': entry.coord})
    tls = spec.path('tls').seq() if spec and spec.path('tls') else []
    return {'class': (spec.scalar('ingressClassName') if spec else None) or annotations.get('kubernetes.io/ingress.class'),
            'tls': bool(tls), 'tls_hosts': [h.scalar() for t in tls for h in (t.path('hosts').seq() if t.path('hosts') else [])],
            'rules': rules, 'annotations': {k: v for k, v in annotations.items() if isinstance(v, (str, int, bool))}}


def _policy(resource):
    spec = resource.get('spec')
    def peers(section):
        out = []
        for rule in (spec.path(section).seq() if spec and spec.path(section) else []):
            out.append({'ports': [p.scalar('port') for p in (rule.path('ports').seq() if rule.path('ports') else [])],
                        'cidrs': [b.scalar('cidr') for b in [p.path('ipBlock') for p in (rule.path('from').seq() if rule.path('from') else []) + (rule.path('to').seq() if rule.path('to') else [])] if b],
                        'source': rule.coord})
        return out
    return {'types': [t.scalar() for t in (spec.path('policyTypes').seq() if spec and spec.path('policyTypes') else [])],
            'pod_selector': {k: n.scalar() for k, n in (spec.path('podSelector', 'matchLabels').pairs() if spec and spec.path('podSelector', 'matchLabels') else [])},
            'ingress': peers('ingress'), 'egress': peers('egress')}


def analyse(root: Path, rel_files: list[str]) -> dict:
    records = []
    for file in rel_files:
        if not file.endswith(('.yaml', '.yml')):
            continue
        try:
            text = (root / file).read_text(encoding='utf-8')
            nodes = [n for n in yaml.compose_all(text) if n is not None]
        except (OSError, UnicodeError, yaml.YAMLError):
            continue
        for node in nodes:
            doc = _N(node, file)
            kind, version = doc.scalar('kind'), doc.scalar('apiVersion')
            if not isinstance(kind, str) or not isinstance(version, str) or kind == 'Secret':
                continue
            record = {'kind': kind, 'name': doc.path('metadata').scalar('name') if doc.path('metadata') else None,
                      'namespace': doc.path('metadata').scalar('namespace') if doc.path('metadata') else None,
                      'source': doc.coord, 'network': [], 'workload': None, 'service': None, 'ingress': None, 'policy': None, 'storage': None, 'config_data': None}
            if kind in _WORKLOADS:
                path = {'Pod': ('spec',), 'CronJob': ('spec', 'jobTemplate', 'spec', 'template', 'spec')}.get(kind, ('spec', 'template', 'spec'))
                record['workload'] = _workload(doc, path, file)
                if record['workload']:
                    for c in record['workload']['containers']:
                        for port in c['ports']:
                            record['network'].append({'direction': 'inbound', 'scope': 'internal', 'via': 'container-port', 'target': port['container_port'], 'source': c['source']})
            elif kind == 'Service':
                record['service'] = _service(doc)
                s = record['service']
                record['network'].append({'direction': 'outbound' if s['exposure'] == 'outbound' else 'inbound', 'scope': 'external' if s['exposure'] == 'outbound' else s['exposure'],
                                          'via': f"service/{s['type']}", 'target': s['external_name'] or [p['port'] for p in s['ports']], 'source': doc.coord})
            elif kind == 'Ingress':
                record['ingress'] = _ingress(doc)
                for rule in record['ingress']['rules']:
                    record['network'].append({'direction': 'inbound', 'scope': 'public', 'via': 'ingress', 'target': f"{rule['host'] or '*'}{rule['path'] or ''} -> {rule['service']}", 'source': rule['source']})
            elif kind == 'NetworkPolicy':
                record['policy'] = _policy(doc)
                for rule in record['policy']['ingress']:
                    record['network'].append({'direction': 'inbound', 'scope': 'restricted', 'via': 'network-policy', 'target': rule['ports'], 'source': rule['source']})
                for rule in record['policy']['egress']:
                    record['network'].append({'direction': 'outbound', 'scope': 'restricted' if rule['cidrs'] or rule['ports'] else 'external', 'via': 'network-policy', 'target': rule['ports'], 'source': rule['source']})
            elif kind == 'PersistentVolumeClaim':
                spec = doc.get('spec')
                record['storage'] = {'storage_class': spec.scalar('storageClassName') if spec else None,
                                     'size': spec.path('resources', 'requests').scalar('storage') if spec and spec.path('resources', 'requests') else None,
                                     'access_modes': [m.scalar() for m in (spec.path('accessModes').seq() if spec and spec.path('accessModes') else [])]}
            elif kind == 'ConfigMap':
                record['config_data'] = {k: (n.scalar() if isinstance(n.scalar(), str) and n.scalar().startswith('/') else None) for k, n in (doc.get('data').pairs() if doc.get('data') else [])}
            else:
                continue
            records.append(record)
    return {'kubernetes': records} if records else {}
