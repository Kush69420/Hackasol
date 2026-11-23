"""Join React form bindings, client requests, backend routes and ORM write operations into Data Flows.

Inputs are inventory records only (`forms`, `react_requests`, `routes`, `models`, `orm_operations`).
A join needs all of: the same HTTP method and normalised path between a resolved client request and a
route, the ORM operation lexically inside that route's handler, the request key the operation reads
equal to the key the client sends, and the ORM model that actually declares the field. An unresolved
client request (dynamic URL or method) never joins a route.
"""
from __future__ import annotations

import re


def _within(inner: dict, outer: dict | None) -> bool:
    return bool(outer) and inner['file'] == outer['file'] and outer['start_line'] <= inner['start_line'] and inner['end_line'] <= outer['end_line']


def _path(value: str) -> str:
    return re.sub(r'\{[^}]*\}', '{}', value or '')


def _step(element_id, operation, stage, source, origin, note='', relation='evidenced'):
    return {'element_id': element_id, 'operation': operation, 'stage': stage, 'source': source,
            'origin': origin, 'relation': relation, 'note': note}


def resolve_model(inventory: dict, op: dict) -> dict | None:
    """The declared model an ORM operation acts on, by model identity (never by field name)."""
    if op['orm'] == 'prisma':
        found = [m for m in inventory.get('models', []) if m.get('kind') == 'prisma' and m['name'][:1].lower() + m['name'][1:] == op['delegate']]
    else:
        found = [m for m in inventory.get('models', []) if m.get('kind') == 'mongoose' and m['name'] == op['model'] and m['source']['file'] == op['model_file']]
    return found[0] if len(found) == 1 else None


def trace(inventory: dict) -> list[dict]:
    routes = [r for r in inventory.get('routes', []) if r.get('handler') and r.get('origin') != 'swagger-only']
    requests = [r for r in inventory.get('react_requests', []) if not r.get('unresolved')]
    forms = {}
    for form in inventory.get('forms', []):
        for item in form.get('inputs', []):
            if item.get('name') and item.get('source'):
                forms[(form['source']['file'], item['name'])] = item
    flows: dict[tuple, dict] = {}

    for op in inventory.get('orm_operations', []):
        if op['access'] != 'write':
            continue
        model = resolve_model(inventory, op)
        if not model:
            continue
        owners = [r for r in routes if _within(op['source'], r['handler'])]
        declared = {f['name']: f for f in model['fields']}
        label = f"{op['orm']} {op['operation']} on {model['name']}"
        for item in op['data_fields']:
            targets = []
            if item['field'] is not None:
                if item['field'] in declared:
                    targets.append((declared[item['field']], item['request_key']))
            else:
                # Whole request body: only keys the route is known to read can reach the model.
                for route in owners:
                    for param in route.get('body_params', []):
                        if param['name'] in declared:
                            targets.append((declared[param['name']], param['name']))
            for field, key in targets:
                eid = f"model:{model['name']}.{field['name']}"
                store = _step(eid, 'Store', 'model', field['source'], 'orm', f"ORM write ({label}) at {op['source']['file']}:{op['source']['start_line']}")
                joined = False
                for route in owners:
                    for request in requests:
                        if request['http_method'] != route['method'] or _path(request['normalised_path']) != _path(route['normalised_path']):
                            continue
                        for sent in request['payload']:
                            if key is None or sent['key'] != key or not sent['input']:
                                continue
                            item_input = forms.get((request['form']['file'], sent['input']))
                            if not item_input:
                                continue
                            steps = [_step(eid, 'Collect', 'form', item_input['source'], 'react-join'),
                                     _step(eid, 'Collect', 'component', sent['source'], 'react-join'),
                                     _step(eid, 'Collect', 'service', request['source'], 'react-join', f"{request['http_method']} {request['normalised_path']}"),
                                     _step(eid, 'Collect', 'route', route['registration'], 'react-join', f"{route['method']} {route['path']}")]
                            for middleware in route.get('middleware', []):
                                if middleware.get('scope') == 'route' or middleware.get('role') in ('authentication', 'identity'):
                                    steps.append(_step(eid, 'Collect', 'middleware', middleware['source'], 'react-join', f"{middleware.get('role')}: {middleware.get('name')}"))
                            steps += [_step(eid, 'Collect', 'handler', item['source'], 'orm', f"Reads request key {key}"), store]
                            flows[(eid, request['source']['file'], request['source']['start_line'], sent['input'])] = {'element_id': eid, 'steps': steps}
                            joined = True
                if joined:
                    continue
                steps = []
                if owners and key is not None:
                    steps.append(_step(eid, 'Collect', 'route', owners[0]['registration'], 'orm', f"{owners[0]['method']} {owners[0]['path']}"))
                if key is not None:
                    steps.append(_step(eid, 'Collect', 'handler', item['source'], 'orm', f"Reads request key {key}"))
                steps.append(store)
                flows.setdefault((eid, 'orm', op['source']['file'], op['source']['start_line'], item['source']['start_line']), {'element_id': eid, 'steps': steps})
    return list(flows.values())
