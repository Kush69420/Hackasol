"""Source-only inventory of Django REST applications; never imports Target code."""
from __future__ import annotations

import ast
import re
from pathlib import Path


def _name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_name(node.value)}.{node.attr}"
    return ""


def _literal(node, default=None):
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError):
        return default


def _assignments(body):
    result = {}
    for node in body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    result[target.id] = node.value
    return result


def _dict(node):
    if not isinstance(node, ast.Dict):
        return {}
    return {_literal(k): v for k, v in zip(node.keys, node.values) if k is not None}


def _coord(file, node):
    return {"file": file, "start_line": node.lineno, "end_line": node.end_lineno}


def _names(node):
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return [_name(x).split('.')[-1] or str(_literal(x, '')).split('.')[-1] for x in node.elts]
    return []


def _path(path):
    path = re.sub(r'<(?:[^:>]+:)?([^>]+)>', r'{\1}', path)
    path = re.sub(r'\(\?P<([^>]+)>[^)]+\)', r'{\1}', path)
    return '/' + re.sub(r'/+', '/', path.strip('/^$')).rstrip('/')


def analyse(root: Path, rel_files: list[str]) -> dict:
    files = {}
    for file in rel_files:
        if not file.startswith('backend/') or not file.endswith('.py') or '/migrations/' in file:
            continue
        try:
            files[file] = ast.parse((root / file).read_text(encoding='utf-8'), filename=file)
        except (SyntaxError, UnicodeError, OSError):
            continue
    if not files:
        return {}
    modules = {f[:-3].replace('/', '.').removeprefix('backend.'): f for f in files}
    classes, functions, imports = {}, {}, {}
    models, serializers, logging = [], {}, []
    defaults, auth_defaults = [], []
    default_source = auth_default_source = None
    for file, tree in files.items():
        module = file[:-3].replace('/', '.').removeprefix('backend.')
        package = module.rpartition('.')[0]
        imports[file] = {}
        for node in tree.body:
            if isinstance(node, ast.ImportFrom):
                base = package.split('.') if package else []
                if node.level:
                    base = base[:len(base) - node.level + 1]
                else:
                    base = []
                mod = '.'.join([*base, *(node.module or '').split('.')]).strip('.')
                for alias in node.names:
                    imports[file][alias.asname or alias.name] = f'{mod}.{alias.name}'.strip('.')
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports[file][alias.asname or alias.name.split('.')[0]] = alias.name
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                classes[(module, node.name)] = (file, node)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions[(module, node.name)] = (file, node)
        if file.endswith('/settings.py'):
            assignments = _assignments(tree.body)
            rest = _dict(assignments.get('REST_FRAMEWORK'))
            if 'DEFAULT_PERMISSION_CLASSES' in rest:
                defaults = _names(rest['DEFAULT_PERMISSION_CLASSES'])
                default_source = _coord(file, rest['DEFAULT_PERMISSION_CLASSES'])
            auth_defaults = _names(rest.get('DEFAULT_AUTHENTICATION_CLASSES'))
            if 'DEFAULT_AUTHENTICATION_CLASSES' in rest:
                auth_default_source = _coord(file, rest['DEFAULT_AUTHENTICATION_CLASSES'])
            handlers = _dict(_dict(assignments.get('LOGGING')).get('handlers'))
            for name, handler in handlers.items():
                options = _dict(handler)
                filename = options.get('filename')
                if filename is not None:
                    value = _literal(filename)
                    if value is None and isinstance(filename, ast.Call):
                        value = '/'.join(str(x) for a in filename.args if isinstance((x := _literal(a)), str))
                    elif value is None:
                        value = ast.unparse(filename)
                else:
                    value = None
                logging.append({'kind': 'django-handler', 'name': name,
                                'class': _literal(options.get('class')), 'filename': value,
                                'source': _coord(file, handler)})
    def resolve(file, name):
        first, dot, rest = name.partition('.')
        return imports[file].get(first, first) + (dot + rest if dot else '')

    for (module, name), (file, node) in classes.items():
        bases = [_name(b).split('.')[-1] for b in node.bases]
        meta = next((n for n in node.body if isinstance(n, ast.ClassDef) and n.name == 'Meta'), None)
        options = _assignments(meta.body) if meta else {}
        if any(b in ('Model', 'AbstractUser', 'AbstractBaseUser') for b in bases):
            fields = []
            for field, value in _assignments(node.body).items():
                if isinstance(value, ast.Call) and (_name(value.func).split('.')[-1].endswith('Field') or _name(value.func).split('.')[-1] in ('ForeignKey', 'OneToOneField', 'ManyToManyField')):
                    item = {'name': field, 'type': _name(value.func).split('.')[-1], 'source': _coord(file, value)}
                    choice_node = next((k.value for k in value.keywords if k.arg == 'choices'), None)
                    if choice_node is not None:
                        choice_file = file
                        choices = []
                        ref = _name(choice_node)
                        if ref.endswith('.choices'):
                            qualified = resolve(file, ref[:-len('.choices')])
                            choice_module, _, choice_class = qualified.rpartition('.')
                            found = classes.get((choice_module or module, choice_class))
                            if found:
                                choice_file, choice_def = found
                                choices = list(_assignments(choice_def.body).values())
                        elif isinstance(choice_node, (ast.List, ast.Tuple)):
                            choices = choice_node.elts
                        elif isinstance(choice_node, ast.Name):
                            choices_value = _assignments(files[file].body).get(choice_node.id)
                            if isinstance(choices_value, (ast.List, ast.Tuple)):
                                choices = choices_value.elts
                        records = []
                        for choice in choices:
                            pair = _literal(choice)
                            if isinstance(pair, (list, tuple)) and pair:
                                records.append({'value': pair[0], 'label': pair[1] if len(pair) > 1 else None,
                                                'source': _coord(choice_file, choice)})
                        if records:
                            item['choices'] = records
                    fields.append(item)
            document_type = next((f for f in fields if f['name'] == 'document_type'), None)
            document_number = next((f for f in fields if f['name'] == 'document_number'), None)
            if document_type and document_number:
                evidence = [c for c in document_type.get('choices', [])
                            if isinstance(c['value'], str) and c['value'].lower() in ('aadhaar', 'aadhar', 'pan')]
                if evidence:
                    document_number['government_identifier_evidence'] = evidence
            app = module.split('.')[0]
            models.append({'name': name, 'table': _literal(options.get('db_table'), f'{app}_{name.lower()}'),
                           'app': app, 'fields': fields, 'source': _coord(file, node)})
        if any(b.endswith('Serializer') for b in bases):
            serializers[(module, name)] = {'name': name, 'model': _name(options.get('model')).split('.')[-1],
                'fields': _literal(options.get('fields')), 'exclude': _literal(options.get('exclude'), []),
                'read_only_fields': _literal(options.get('read_only_fields'), []), 'source': _coord(file, node)}
    model_map = {m['name']: m for m in models}
    for serializer in serializers.values():
        model = model_map.get(serializer['model'], {})
        fields = serializer['fields']
        if fields == '__all__' or fields is None:
            fields = [f['name'] for f in model.get('fields', []) if f['name'] not in serializer['exclude']]
        serializer['fields'] = list(fields or [])

    def lookup(file, ref, index):
        full = resolve(file, ref)
        module, _, name = full.rpartition('.')
        return index.get((module, name)) or index.get((file[:-3].replace('/', '.').removeprefix('backend.'), ref))

    # Build URLconf graph and router registrations from in-scope source only.
    urlconfs, included = {}, set()
    for file, tree in files.items():
        if not file.endswith('/urls.py'):
            continue
        module = file[:-3].replace('/', '.').removeprefix('backend.')
        patterns, routers = [], {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'register' and len(node.args) >= 2:
                prefix = _literal(node.args[0])
                if isinstance(prefix, str):
                    routers.setdefault(_name(node.func.value), []).append((prefix, _name(node.args[1]), node))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or _name(node.func).split('.')[-1] not in ('path', 're_path') or len(node.args) < 2:
                continue
            prefix = _literal(node.args[0])
            if not isinstance(prefix, str):
                continue
            view = node.args[1]
            if isinstance(view, ast.Call) and _name(view.func).split('.')[-1] == 'include' and view.args:
                arg = view.args[0]
                target = _literal(arg) if isinstance(arg, ast.Constant) else resolve(file, _name(arg))
                if isinstance(target, str) and target.endswith('.urls') and target in modules:
                    included.add(target)
                    patterns.append(('include', prefix, target, node))
                elif isinstance(arg, ast.Attribute) and arg.attr == 'urls':
                    patterns.extend(('router', prefix + p, v, n) for p, v, n in routers.get(_name(arg.value), []))
            else:
                ref = _name(view.func.value) if isinstance(view, ast.Call) and isinstance(view.func, ast.Attribute) and view.func.attr == 'as_view' else _name(view)
                patterns.append(('view', prefix, ref, node))
        urlconfs[module] = (file, patterns)
    routes, flows = [], []
    def add_step(model, field, operation, stage, file, node, note=''):
        if not model or not field:
            return
        eid = f'model:{model}.{field}'
        flow = next((f for f in flows if f['element_id'] == eid), None)
        if flow is None:
            flow = {'element_id': eid, 'steps': []}
            flows.append(flow)
        step = {'element_id': eid, 'operation': operation, 'stage': stage, 'source': _coord(file, node), 'origin': 'django', 'relation': 'evidenced', 'note': note}
        if step not in flow['steps']:
            flow['steps'].append(step)

    def handler(file, node, cls, method, path, registration):
        assigns = _assignments(cls.body) if cls else {}
        perms_node = assigns.get('permission_classes')
        auth_node = assigns.get('authentication_classes')
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and dec.args:
                if _name(dec.func).split('.')[-1] == 'permission_classes':
                    perms_node = dec.args[0]
                if _name(dec.func).split('.')[-1] == 'authentication_classes':
                    auth_node = dec.args[0]
        perms = _names(perms_node) if perms_node else defaults
        auth = _names(auth_node) if auth_node else auth_defaults
        perm_source = _coord(file, perms_node) if perms_node else default_source
        middleware = [{'name': p, 'role': 'authentication', 'source': perm_source} for p in perms if p == 'IsAuthenticated' and perm_source]
        ser_refs = {}
        if 'serializer_class' in assigns:
            ser = lookup(file, _name(assigns['serializer_class']), serializers)
            if ser:
                ser_refs['self'] = ser
        for sub in ast.walk(node):
            if isinstance(sub, ast.Assign) and isinstance(sub.value, ast.Call):
                ser = lookup(file, _name(sub.value.func), serializers)
                if ser:
                    for target in sub.targets:
                        if isinstance(target, ast.Name):
                            ser_refs[target.id] = ser
        used = list({(s['source']['file'], s['name']): s for s in ser_refs.values()}.values())
        model = used[0]['model'] if len(used) == 1 else None
        route = {'method': method, 'path': path, 'normalised_path': path, 'origin': 'explicit',
                 'source': registration, 'registration': registration, 'handler': {**_coord(file, node), 'name': f'{cls.name}.{node.name}' if cls else node.name},
                 'middleware': middleware, 'permission_classes': perms, 'authentication_classes': auth,
                 'permission_source': perm_source, 'authentication_source': _coord(file, auth_node) if auth_node else auth_default_source,
                 'model': model, 'request_models': used if method in ('POST', 'PUT', 'PATCH') else [],
                 'response_models': used, 'body_params': [], 'query_params': []}
        routes.append(route)
        for sub in ast.walk(node):
            if isinstance(sub, ast.Subscript) and _name(sub.value) == 'request.data':
                field = _literal(sub.slice)
                if isinstance(field, str):
                    route['body_params'].append({'name': field, 'source': _coord(file, sub)})
                    if model and any(f['name'] == field for f in model_map.get(model, {}).get('fields', [])):
                        add_step(model, field, 'Collect', 'handler', file, sub)
            if not isinstance(sub, ast.Call):
                continue
            call = _name(sub.func)
            if call.endswith('.save') and call[:-5] in ser_refs:
                ser = ser_refs[call[:-5]]
                for field in ser['fields']:
                    if field not in ser['read_only_fields'] and any(f['name'] == field for f in model_map.get(ser['model'], {}).get('fields', [])):
                        add_step(ser['model'], field, 'Store', 'handler', file, sub, 'Serializer save')
            if call.endswith('.objects.create'):
                target = call[:-len('.objects.create')].split('.')[-1]
                for kw in sub.keywords:
                    if kw.arg and any(f['name'] == kw.arg for f in model_map.get(target, {}).get('fields', [])):
                        add_step(target, kw.arg, 'Store', 'handler', file, kw.value)
            if call.split('.')[-1] in ('Response', 'JsonResponse'):
                for child in ast.walk(sub):
                    if isinstance(child, ast.Attribute) and child.attr == 'data':
                        ser = ser_refs.get(_name(child.value))
                        if ser is None and isinstance(child.value, ast.Call):
                            ser = lookup(file, _name(child.value.func), serializers)
                        if ser:
                            for field in ser['fields']:
                                if any(f['name'] == field for f in model_map.get(ser['model'], {}).get('fields', [])):
                                    add_step(ser['model'], field, 'Expose', 'response', file, child, 'Serializer response')
            if call.split('.')[0] in ('logger', 'logging') and call.split('.')[-1] in ('debug', 'info', 'warning', 'error', 'exception', 'critical', 'log'):
                for child in ast.walk(sub):
                    field = _literal(child.slice) if isinstance(child, ast.Subscript) else child.attr if isinstance(child, ast.Attribute) else None
                    if field and model and any(f['name'] == field for f in model_map.get(model, {}).get('fields', [])):
                        add_step(model, field, 'Log', 'log', file, sub)
        # A serializer constructed with request.data evidences collection of writable fields.
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call):
                ser = lookup(file, _name(sub.func), serializers)
                if ser and any(k.arg == 'data' and _name(k.value) == 'request.data' for k in sub.keywords):
                    for field in ser['fields']:
                        if field not in ser['read_only_fields'] and any(f['name'] == field for f in model_map.get(ser['model'], {}).get('fields', [])):
                            add_step(ser['model'], field, 'Collect', 'handler', file, sub, 'Serializer request data')

    def visit(module, prefix='', seen=frozenset()):
        if module in seen or module not in urlconfs:
            return
        file, patterns = urlconfs[module]
        for kind, part, ref, reg in patterns:
            part = part.removeprefix('^').removesuffix('$')
            path = _path(prefix + part)
            if kind == 'include':
                visit(ref, prefix + part, seen | {module})
                continue
            found = lookup(file, ref, classes) or lookup(file, ref, functions)
            if not found:
                continue
            view_file, view = found
            if isinstance(view, ast.ClassDef):
                methods = {n.name: n for n in view.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
                mapping = {'list': ('GET', ''), 'create': ('POST', ''), 'retrieve': ('GET', '/{id}'), 'update': ('PUT', '/{id}'), 'partial_update': ('PATCH', '/{id}'), 'destroy': ('DELETE', '/{id}')}
                for name, fn in methods.items():
                    if name.upper() in ('GET', 'POST', 'PUT', 'PATCH', 'DELETE'):
                        handler(view_file, fn, view, name.upper(), path, _coord(file, reg))
                    elif kind == 'router' and name in mapping:
                        method, suffix = mapping[name]
                        handler(view_file, fn, view, method, path + suffix, _coord(file, reg))
                if kind == 'router' and any(_name(b).split('.')[-1] == 'ModelViewSet' for b in view.bases):
                    assigns = _assignments(view.body)
                    ser = lookup(view_file, _name(assigns.get('serializer_class')), serializers)
                    perm_node = assigns.get('permission_classes')
                    auth_node = assigns.get('authentication_classes')
                    perms = _names(perm_node) if perm_node else defaults
                    perm_source = _coord(view_file, perm_node) if perm_node else default_source
                    middleware = [{'name': p, 'role': 'authentication', 'source': perm_source}
                                  for p in perms if p == 'IsAuthenticated' and perm_source]
                    for action, (method, suffix) in mapping.items():
                        if action in methods:
                            continue
                        action_path = path + suffix
                        routes.append({'method': method, 'path': action_path, 'normalised_path': action_path,
                            'origin': 'django-router', 'source': _coord(file, reg), 'registration': _coord(file, reg),
                            'handler': {**_coord(view_file, view), 'name': f'{view.name}.{action}'},
                            'middleware': middleware, 'permission_classes': perms, 'permission_source': perm_source,
                            'authentication_classes': _names(auth_node) if auth_node else auth_defaults,
                            'authentication_source': _coord(view_file, auth_node) if auth_node else auth_default_source,
                            'model': ser['model'] if ser else None,
                            'request_models': [ser] if ser and method in ('POST', 'PUT', 'PATCH') else [],
                            'response_models': [ser] if ser else [], 'body_params': [], 'query_params': []})
            else:
                for dec in view.decorator_list:
                    if isinstance(dec, ast.Call) and _name(dec.func).split('.')[-1] == 'api_view' and dec.args:
                        for method in _literal(dec.args[0], []):
                            handler(view_file, view, None, method.upper(), path, _coord(file, reg))
    for module in urlconfs:
        if module not in included:
            visit(module)
    return {'models': models, 'routes': routes, 'logging': logging, 'flows': flows}
