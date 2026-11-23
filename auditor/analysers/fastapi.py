"""Static FastAPI and Pydantic inventory for in-scope Python files."""
from __future__ import annotations

import ast
import re
from pathlib import Path


def _text(node):
    return ast.unparse(node) if node is not None else ''


def _name(node):
    return _text(node).split('.')[-1]


def _literal(node, default=None):
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError):
        return default


def _coord(file, node):
    return {'file': file, 'start_line': node.lineno, 'end_line': node.end_lineno}


def _keyword(call, name):
    return next ( (k.value for k in call.keywords if k.arg == name), None)


def _path(*parts):
    result = '/' + '/'.join(str(p).strip('/') for p in parts if p and p != '/')
    return re.sub(r'{(\w+):[^}]+}', r'{\1}', result) or '/'


def analyse(root: Path, rel_files: list[str]) -> dict:
    trees = {}
    for file in rel_files:
        if not file.endswith('.py'):
            continue
        try:
            trees[file] = ast.parse((root / file).read_text(encoding='utf8'), filename=file)
        except (SyntaxError, UnicodeError, OSError):
            continue
    models, routers, includes = [], {}, []
    for file, tree in trees.items():
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and any(_name(b) == 'BaseModel' for b in node.bases):
                fields = []
                for field in node.body:
                    if isinstance(field, ast.AnnAssign) and isinstance(field.target, ast.Name):
                        fields.append({'name': field.target.id, 'type': _text(field.annotation), 'allow_null': None, 'default': None, 'unique': None, 'validators': [], 'source': _coord(file, field)})
                models.append({'name': node.name, 'table': None, 'kind': 'pydantic', 'source': _coord(file, node), 'options': {}, 'fields': fields})
            if isinstance(node, (ast.Assign, ast.AnnAssign)) and isinstance(node.value, ast.Call) and _name(node.value.func) in ('FastAPI', 'APIRouter'):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target, ast.Name):
                        routers[(file, target.id)] = {'app': _name(node.value.func) == 'FastAPI', 'prefix': _literal(_keyword(node.value, 'prefix'), ''), 'dependencies': _keyword(node.value, 'dependencies'), 'node': node}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'include_router' and isinstance(node.func.value, ast.Name) and node.args:
                includes.append((file, node.func.value.id, node.args[0], node))
    def resolve(file, expr):
        if isinstance(expr, ast.Name):
            if (file, expr.id) in routers:
                return (file, expr.id)
            for imp in trees[file].body:
                if isinstance(imp, ast.ImportFrom):
                    for alias in imp.names:
                        if (alias.asname or alias.name) != expr.id:
                            continue
                        module = (imp.module or '').replace('.', '/')
                        candidates = [f for f in trees if f.endswith('/' + module + '.py') or f == module + '.py']
                        for candidate in candidates:
                            if (candidate, alias.name) in routers:
                                return (candidate, alias.name)
        if isinstance(expr, ast.Attribute) and isinstance(expr.value, ast.Name):
            for imp in trees[file].body:
                if isinstance(imp, ast.ImportFrom):
                    for alias in imp.names:
                        if (alias.asname or alias.name) == expr.value.id:
                            module = '/'.join(filter(None, [(imp.module or '').replace('.', '/'), alias.name]))
                            for candidate in trees:
                                if (candidate == module + '.py' or candidate.endswith('/' + module + '.py')) and (candidate, expr.attr) in routers:
                                    return (candidate, expr.attr)
        return None
    edges = []
    for file, parent, child, call in includes:
        target = resolve(file, child)
        if (file, parent) in routers and target:
            edges.append(((file, parent), target, _literal(_keyword(call, 'prefix'), ''), _keyword(call, 'dependencies'), file))
    def mounts(key, seen=frozenset()):
        if key in seen:
            return []
        router = routers[key]
        own = router['prefix']
        deps = [(key[0], router['dependencies'])] if router['dependencies'] else []
        parents = [(p, prefix, d, f) for p, c, prefix, d, f in edges if c == key]
        if not parents:
            return [(own, deps)] if router['app'] else []
        return [(_path(base, prefix, own), inherited + ([(f, d)] if d else []) + deps) for p, prefix, d, f in parents for base, inherited in mounts(p, seen | {key})]
    model_map = {m['name']: m for m in models}
    routes, steps, logging = [], [], []
    for file, tree in trees.items():
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in fn.decorator_list:
                if not isinstance(dec, ast.Call) or not isinstance(dec.func, ast.Attribute) or not isinstance(dec.func.value, ast.Name) or dec.func.attr.lower() not in ('get', 'post', 'put', 'patch', 'delete', 'head', 'options') or not dec.args:
                    continue
                key = (file, dec.func.value.id)
                if key not in routers or not isinstance(_literal(dec.args[0]), str):
                    continue
                for base, dependencies in mounts(key):
                    path = _path(base, _literal(dec.args[0])); method = dec.func.attr.upper()
                    middleware = []
                    extra = _keyword(dec, 'dependencies')
                    for dep_file, dep in dependencies + ([(file, extra)] if extra else []):
                        for call in ast.walk(dep):
                            if isinstance(call, ast.Call) and _name(call.func) in ('Depends', 'Security'):
                                middleware.append({'name': _text(call.args[0]) if call.args else _name(call.func), 'expression': _text(call), 'role': 'authentication' if re.search(r'auth|user|token|security|permission', _text(call), re.I) else 'other', 'scope': 'route', 'source': _coord(dep_file, call)})
                    body, query, request_models = [], [], []
                    args = fn.args.posonlyargs + fn.args.args + fn.args.kwonlyargs
                    defaults = [None] * (len(fn.args.posonlyargs + fn.args.args) - len(fn.args.defaults)) + fn.args.defaults + fn.args.kw_defaults
                    for arg, default in zip(args, defaults):
                        typ = _text(arg.annotation)
                        if isinstance(default, ast.Call) and _name(default.func) in ('Depends', 'Security'):
                            middleware.append({'name': _text(default.args[0]) if default.args else _name(default.func), 'expression': _text(default), 'role': 'authentication' if re.search(r'auth|user|token|security|permission', _text(default), re.I) else 'other', 'scope': 'route', 'source': _coord(file, default)})
                            continue
                        if typ in model_map:
                            request_models.append(typ)
                            body.extend({'name': f['name'], 'type': f['type'], 'source': f['source'], 'model_parameter': arg.arg} for f in model_map[typ]['fields'])
                        elif typ and typ not in ('Request', 'Response'):
                            param = {'name': arg.arg, 'type': typ, 'source': _coord(file, arg)}
                            if 'UploadFile' in typ or isinstance(default, ast.Call) and _name(default.func) in ('File', 'Body', 'Form'):
                                body.append(param)
                            else:
                                query.append(param)
                    response = _text(_keyword(dec, 'response_model')) or _text(fn.returns) or None
                    handler = {'name': fn.name, **_coord(file, fn)}
                    registration = _coord(file, dec)
                    route = {'method': method, 'path': path, 'normalised_path': path, 'origin': 'fastapi', 'registration': registration, 'source': registration, 'handler': handler, 'middleware': middleware, 'model': request_models[0] if request_models else None, 'request_models': request_models, 'response_model': response, 'response_fields': model_map.get(response, {}).get('fields', []), 'finale': None, 'swagger': None, 'body_params': body, 'query_params': query}
                    routes.append(route)
                    aliases = {arg.arg: {arg.arg} for arg in args}
                    for n in ast.walk(fn):
                        if isinstance(n, (ast.Assign, ast.AnnAssign)):
                            value = n.value
                            names = {x.id for x in ast.walk(value) if isinstance(x, ast.Name)} if value else set()
                            targets = n.targets if isinstance(n, ast.Assign) else [n.target]
                            for target in targets:
                                if isinstance(target, ast.Name):
                                    for origins in aliases.values():
                                        if origins & names:
                                            origins.add(target.id)
                    for param in body + query:
                        ident = f"param:{method} {path}" + (f"#body.{param['name']}" if param in body else f"?{param['name']}")
                        def add(op, source, note=''):
                            steps.append({'element_id': ident, 'operation': op, 'stage': 'backend', 'source': source, 'origin': 'fastapi', 'relation': 'evidenced', 'note': note})
                        add('Collect', param['source'])
                        origins = aliases.get(param.get('model_parameter', param['name']), {param['name']})
                        def references(node):
                            if 'model_parameter' in param:
                                return any(isinstance(x, ast.Attribute) and x.attr == param['name'] and isinstance(x.value, ast.Name) and x.value.id in origins for x in ast.walk(node)) or isinstance(node, ast.Name) and node.id in origins
                            return bool(origins & {x.id for x in ast.walk(node) if isinstance(x, ast.Name)})
                        for n in ast.walk(fn):
                            if isinstance(n, ast.Call):
                                name = _text(n.func)
                                if not any(references(a) for a in [*n.args, *(k.value for k in n.keywords)]):
                                    continue
                                if re.search(r'(^|\.)(requests|httpx)\.|^(client|session)\.(get|post|put|patch|delete)$', name):
                                    add('Transfer', _coord(file, n))
                                if re.match(r'^(print|logging\.|logger\.)', name):
                                    add('Log', _coord(file, n))
                                if 'UploadFile' in param.get('type', '') and re.search(r'(?:^|\.)(?:face_service|liveness_service|biometric_service|match_faces|detect_liveness)(?:\.|$)', name, re.I):
                                    param.setdefault('biometric_evidence', []).append(_coord(file, n))
                            elif isinstance(n, ast.Return) and n.value and references(n.value):
                                add('Expose', _coord(file, n))
    # Recover explicitly returned dictionary fields from service methods.  These
    # are not Pydantic declarations, but remain useful inventory Elements.
    collections = []
    for file, tree in trees.items():
        for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
            fields = []
            for fn in (n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))):
                returned = {n.value.id for n in ast.walk(fn) if isinstance(n, ast.Return) and isinstance(n.value, ast.Name)}
                for n in ast.walk(fn):
                    if not isinstance(n, (ast.Assign, ast.AnnAssign)):
                        continue
                    for target in n.targets if isinstance(n, ast.Assign) else [n.target]:
                        if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name) and target.value.id in returned:
                            key = _literal(target.slice)
                            if isinstance(key, str) and not any(f['name'] == key for f in fields):
                                fields.append({'name': key, 'source': _coord(file, target)})
            if fields:
                collections.append({'name': cls.name, 'kind': 'python-returned-dict', 'source': _coord(file, cls), 'fields': fields})
    # Join a returned service result only when the handler explicitly returns
    # its structured-data member and the service calls the field-producing method.
    classes = {n.name: (file, n) for file, tree in trees.items() for n in tree.body if isinstance(n, ast.ClassDef)}
    for route in routes:
        file = route['handler']['file']
        tree = trees[file]
        instances = {t.id: _name(n.value.func) for n in tree.body if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call) for t in n.targets if isinstance(t, ast.Name)}
        handler = next((n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == route['handler']['name'] and n.lineno == route['handler']['start_line']), None)
        if handler is None:
            continue
        for assignment in ast.walk(handler):
            if not isinstance(assignment, ast.Assign) or len(assignment.targets) != 1 or not isinstance(assignment.targets[0], ast.Name):
                continue
            call = assignment.value.value if isinstance(assignment.value, ast.Await) else assignment.value
            if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Attribute) or not isinstance(call.func.value, ast.Name):
                continue
            class_name = instances.get(call.func.value.id)
            if class_name not in classes:
                continue
            result = assignment.targets[0].id
            returned = [n for n in ast.walk(handler) if isinstance(n, ast.Return) and n.value and result in {x.id for x in ast.walk(n.value) if isinstance(x, ast.Name)} and 'structured_data' in _text(n.value)]
            if not returned:
                continue
            _, cls = classes[class_name]
            methods = {n.name: n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
            reachable, pending = set(), [call.func.attr]
            while pending:
                name = pending.pop()
                if name in reachable or name not in methods:
                    continue
                reachable.add(name)
                pending.extend(n.func.attr for n in ast.walk(methods[name]) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and n.func.value.id == 'self')
            collection = next((c for c in collections if c['name'] == class_name), None)
            if not collection:
                continue
            for field in collection['fields']:
                if any(methods[name].lineno <= field['source']['start_line'] <= methods[name].end_lineno for name in reachable):
                    ident = f"collection:{class_name}.{field['name']}"
                    steps.append({'element_id': ident, 'operation': 'Expose', 'stage': 'backend', 'source': _coord(file, returned[0]), 'origin': 'fastapi', 'relation': 'evidenced', 'note': 'Service structured data returned by handler'})
    flows = [{'element_id': ident, 'steps': [s for s in steps if s['element_id'] == ident]} for ident in dict.fromkeys(s['element_id'] for s in steps)]
    return {'routes': routes, 'models': models, 'collections': collections, 'logging': logging, 'flows': flows}
