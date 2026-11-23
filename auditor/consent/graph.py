"""Build an Evidence-backed consent graph without interpreting Target code at runtime."""
from __future__ import annotations

import re
from collections import deque

from auditor.analysers.django import analyse_consent
from auditor.masking import mask_for_report
from auditor.rules.data_monitoring import _child_gate


def _id(kind, source):
    return f"{kind}:{source['file']}:{source['start_line']}"


def _source(file, text, start, end=None):
    return {'file': file, 'start_line': text.count('\n', 0, start) + 1,
            'end_line': text.count('\n', 0, end if end is not None else start) + 1}


def _inside(inner, outer):
    return (inner['file'] == outer['file'] and outer['start_line'] <= inner['start_line']
            and inner['end_line'] <= outer['end_line'])


def _attributes(tag):
    return {m.group(1).lower(): (m.group(3) if m.group(2) else None)
            for m in re.finditer(r'''([\w:-]+)(?:\s*=\s*(["'])(.*?)\2)?''', tag)}


def build_graph(ctx):
    """Construct conservative links; an unresolved edge is never an absence Finding."""
    graph = {key: [] for key in ('purposes', 'records', 'enforcement_points', 'withdrawal_paths',
                                 'grant_paths', 'processors', 'operations', 'notices', 'controls', 'banners')}
    graph['limitations'] = [
        'Only statically resolved Purpose-specific links are represented; missing links are not proof of absence.',
        'Step counts require a common, statically resolved starting template; credentials and text entry are not counted.',
        'A dispatched deletion, browser choice, or Data Processor call does not establish actual deletion or a contract.',
    ]
    graph['processor_propagation'] = []
    graph['parental_verification'] = {'state': 'not determinable', 'evidence': [],
        'reason': 'No verifiable parental consent mechanism was resolved; age self-declaration alone is insufficient.'}
    gate, _ = _child_gate(ctx)
    graph['child_gate'] = {'state': 'met' if gate else 'not determinable',
                           'evidence': [gate] if gate else [],
                           'reason': ('The existing CHI-01 Gate found age/DOB collection or an explicit Child audience.'
                                      if gate else 'The existing CHI-01 Gate did not resolve age/DOB collection or an explicit Child audience.')}
    files = [p.relative_to(ctx.root).as_posix() for p in ctx.files]
    existing = ctx.inventory.get('django_consent', [])
    django = existing[0] if existing else (analyse_consent(ctx.root, files) if any(f.endswith('.py') for f in files) else {
        'models': [], 'event_writes': [], 'middleware': [], 'urls': [], 'template_actions': [],
        'conditions': [], 'calls': [], 'view_templates': []})
    templates = {}
    for path in ctx.files:
        if path.suffix.lower() not in ('.html', '.hbs'):
            continue
        try:
            templates[path.relative_to(ctx.root).as_posix()] = path.read_text(encoding='utf-8')
        except (OSError, UnicodeError):
            continue
    for file, text in templates.items():
        for match in re.finditer(r'<input\b[^>]*\bname\s*=\s*["\'](?:confirm_age|age|dob|date_of_birth)["\'][^>]*>', text, re.I):
            graph['parental_verification']['evidence'].append(ctx.evidence(_source(file, text, match.start(), match.end() - 1)))
    if gate:
        graph['parental_verification']['evidence'].append(gate)


    # A purpose is taken from a notice sentence, never from the mere existence of
    # a banner or a database flag. Each sentence stays anchored at its own line.
    for file, text in templates.items():
        for match in re.finditer(r'<p\b[^>]*>([\s\S]*?)</p\s*>', text, re.I):
            plain = re.sub(r'<[^>]+>|{%\s*\w+\s*|\s*%}', '', match.group(1)).strip(' \n\t"\'')
            if not re.search(r'\b(?:consent|privacy|data collection|analytics)\b', plain, re.I):
                continue
            source = _source(file, text, match.start(), match.end() - 1)
            containing_form = next((f for f in re.finditer(r'<form\b[^>]*>[\s\S]*?</form\s*>', text, re.I)
                                    if f.start() <= match.start() and match.end() <= f.end()), None)
            form_text = containing_form.group() if containing_form else ''
            language = re.search(r'<html\b[^>]*\blang\s*=\s*["\']([^"\']+)["\']', text, re.I)
            notice_evidence = [ctx.evidence(source)]
            if language:
                notice_evidence.append(ctx.evidence(_source(file, text, language.start(), language.end() - 1)))
            itemised = bool(re.search(r'<(?:ul|ol)\b[\s\S]*?<li\b', form_text, re.I)
                            or len(re.findall(r'<input\b[^>]*\bname\s*=\s*["\']consent', form_text, re.I)) > 1)
            graph['notices'].append({'id': _id('notice', source), 'purpose_ids': [],
                'text': mask_for_report(plain), 'language': language.group(1) if language else None,
                'itemised': itemised if containing_form else None, 'before_grant': None,
                'evidence': notice_evidence})
        # Purpose text in an itemised consent card immediately preceding its control.
        for control in re.finditer(r'<input\b[^>]*>', text, re.I):
            attrs = _attributes(control.group())
            name = attrs.get('name') or ''
            if 'consent' not in name.lower():
                continue
            source = _source(file, text, control.start(), control.end() - 1)
            graph['controls'].append({'id': _id('control', source), 'name': name,
                                      'default_selected': ('checked' in attrs) if (attrs.get('type') or '').lower() == 'checkbox' else None,
                                      'evidence': [ctx.evidence(source)]})
            prefix = text[max(0, control.start() - 1000):control.start()]
            statements = list(re.finditer(r'<p\b[^>]*>([\s\S]*?)</p\s*>', prefix, re.I))
            if statements:
                statement = statements[-1]
                plain = re.sub(r'<[^>]+>|{%\s*\w+\s*|\s*%}', '', statement.group(1)).strip(' \n\t"\'')
                if re.search(r'\b(?:to|used to|for)\s+\w+', plain, re.I):
                    start = max(0, control.start() - 1000) + statement.start()
                    ev = _source(file, text, start, start + len(statement.group()) - 1)
                    pid = _id('purpose', ev) + ':' + str(source['start_line'])
                    field_name = re.sub(r'^consent_', '', name, flags=re.I)
                    elements = [element['id'] for element in ctx.elements
                                if element.get('name', '').lower() == field_name.lower()]
                    basis = ({"basis": mask_for_report(plain), "evidence": [ctx.evidence(ev)]}
                             if re.search(r'(?:section|§)\s*7\b', plain, re.I)
                             and re.search(r'\blegitimate use\b', plain, re.I) else None)
                    graph['purposes'].append({'id': pid, 'name': mask_for_report(plain), 'element_names': elements,
                                              'legitimate_use': basis, 'evidence': [ctx.evidence(ev), ctx.evidence(source)]})
        for match in re.finditer(r'\b(?:window\.)?cookieconsent\.initialise\s*\(', text, re.I):
            source = _source(file, text, match.start())
            graph['banners'].append({'id': _id('banner', source), 'evidence': [ctx.evidence(source)]})
    for middleware in django['middleware']:
        implementation = middleware.get('implementation')
        if not implementation:
            continue
        for condition in django['conditions']:
            if not _inside(condition['source'], implementation):
                continue
            returns = [body for body in condition['body']
                       if ctx.evidence(body)['excerpt'].lstrip().startswith('return redirect(')]
            if returns:
                graph['enforcement_points'].append({'id': _id('enforcement', condition['source']),
                    'purpose_ids': [], 'operation_ids': [], 'server_side': True,
                    'evidence': [ctx.evidence(middleware['source']), ctx.evidence(condition['source']),
                                 ctx.evidence(returns[0])]})


    # A model with a consent boolean is not a Consent Record. Completeness also
    # requires a persisted event write and the full set of record fields.
    for model in django['models']:
        fields = {field['name'].lower() for field in model['fields']}
        writes = [w for w in django['event_writes'] if w['model'] == model['name']]
        if 'consent' not in model['name'].lower():
            continue
        required = (any(x in fields for x in ('user', 'principal', 'data_principal')),
                    'action' in fields, 'purpose' in fields,
                    any(x in fields for x in ('notice_version', 'consent_version', 'notice_reference')),
                    any(x in fields for x in ('timestamp', 'created_at', 'time')))
        for write in writes:
            write_fields = set(write['fields']) - set(write['null_fields'])
            times = {'timestamp', 'created_at', 'time'}
            has_time = bool(write_fields & times) or any(field['name'] in times and field['automatic_time']
                                                          for field in model['fields'])
            complete = (all(required) and has_time and bool(write_fields & {'user', 'principal', 'data_principal'})
                        and {'action', 'purpose'} <= write_fields
                        and bool(write_fields & {'notice_version', 'consent_version', 'notice_reference'}))
            source = write['source']
            purpose = write['values'].get('purpose')
            purpose_ids = [item['id'] for item in graph['purposes']
                           if isinstance(purpose, str) and purpose
                           and re.search(r'\b' + re.escape(purpose) + r'\b', item['name'], re.I)]
            graph['records'].append({'id': _id('record', source), 'model': model['name'], 'purpose_ids': purpose_ids,
                                     'fields': sorted(fields), 'complete': complete and bool(purpose_ids),
                                     'evidence': [ctx.evidence(model['source']), ctx.evidence(source)]})

    # Resolve direct imports of an SDK wrapper to its actual SDK invocation.
    for call in django['calls']:
        source = call['source']
        if not call['name'].endswith(('.capture', '.identify')):
            continue
        try:
            text = (ctx.root / source['file']).read_text(encoding='utf-8')
        except (OSError, UnicodeError):
            continue
        imported = re.findall(r'^\s*import\s+(posthog)\b', text, re.I | re.M)
        if not imported:
            continue
        wrapper_evidence = []
        module = source['file'].rsplit('/', 1)[-1].removesuffix('.py')
        for caller in django['calls']:
            if caller['name'] != call['function'] or caller['source']['file'] == source['file']:
                continue
            try:
                caller_text = (ctx.root / caller['source']['file']).read_text(encoding='utf-8')
            except (OSError, UnicodeError):
                continue
            imported_wrapper = re.search(r'^[ \t]*from\s+[\w.]*\b' + re.escape(module) +
                                         r'\s+import\s+' + re.escape(call['function']) + r'\b', caller_text, re.M)
            if imported_wrapper:
                wrapper_evidence.extend([ctx.evidence(_source(caller['source']['file'], caller_text, imported_wrapper.start(), imported_wrapper.end() - 1)),
                                         ctx.evidence(caller['source'])])
        operation_id = _id('operation', source)
        graph['operations'].append({'id': operation_id, 'name': call['name'], 'element_names': [],
                                    'evidence': [*wrapper_evidence, ctx.evidence(source)]})
        graph['processors'].append({'id': _id('processor', source), 'name': imported[0],
                                    'purpose_ids': [], 'operation_ids': [operation_id],
                                    'evidence': [*wrapper_evidence, ctx.evidence(source)]})
        gated = [condition for condition in django['conditions']
                 if _inside(condition['source'], call['function_source'])
                 and condition['source']['start_line'] < source['start_line']
                 and re.search(r'\bnot\b', condition['condition'])
                 and any(ctx.evidence(body)['excerpt'].lstrip().startswith('return') for body in condition['body'])]
        if gated:
            condition = gated[0]
            ev = [*wrapper_evidence, ctx.evidence(condition['source']), ctx.evidence(source)]
            graph['enforcement_points'].append({'id': _id('enforcement', condition['source']),
                'purpose_ids': [], 'operation_ids': [operation_id], 'server_side': True, 'evidence': ev})
        else:
            ev = [ctx.evidence(source)]
        graph['processor_propagation'].append({'processor_id': _id('processor', source),
            'state': 'gated' if gated else 'not determinable', 'evidence': ev,
            'reason': ('A server-side consent condition precedes this call; prior transfers and deletion remain unresolved.'
                       if gated else 'No linked consent condition or withdrawal notification was resolved for this call.')})

    _paths(ctx, django, templates, graph)
    for file, text in templates.items():
        for form in re.finditer(r'<form\b[^>]*>[\s\S]*?</form\s*>', text, re.I):
            form_source = _source(file, text, form.start(), form.end() - 1)
            grants = [path for path in graph['grant_paths']
                      if any(_inside(ev, form_source) for ev in path['evidence'])]
            for notice in graph['notices']:
                if grants and _inside(notice['evidence'][0], form_source):
                    notice['purpose_ids'] = sorted({pid for path in grants for pid in path['purpose_ids']})
                    notice['before_grant'] = notice['evidence'][0]['start_line'] <= grants[0]['evidence'][0]['start_line']
                    notice['evidence'].append(grants[0]['evidence'][0])
    return graph


def _paths(ctx, django, templates, graph):
    """Resolve template links and form submissions; compare only from a common entry."""
    urls = {url['name']: url for url in django['urls']}
    views = {item['view']: item for item in django['view_templates']}
    template_files = {name: next((f for f in templates if f == name or f.endswith('/' + name)), None)
                      for name in {item['template'] for item in django['view_templates']}}
    destinations = {name: template_files.get(views[url['view_name']]['template'])
                    for name, url in urls.items() if url.get('view') and url['view_name'] in views}
    edges = {}
    for file, text in templates.items():
        for match in re.finditer(r'''<a\b[^>]*href\s*=\s*["']\s*{%\s*url\s+["']([^"']+)["']\s*%}[^>]*>''', text, re.I):
            dest = destinations.get(match.group(1))
            if dest:
                source = _source(file, text, match.start(), match.end() - 1)
                edges.setdefault(file, []).append((dest, source))
    paths = []
    for file, text in templates.items():
        for form in re.finditer(r'<form\b[^>]*>[\s\S]*?</form\s*>', text, re.I):
            body = form.group()
            controls = list(re.finditer(r'<input\b[^>]*>', body, re.I))
            consent = any('consent' in (_attributes(c.group()).get('name') or '').lower() for c in controls)
            withdrawal = bool(re.search(r'withdraw', file, re.I) and re.search(r'type\s*=\s*["\']submit', body, re.I))
            if not consent and not withdrawal:
                continue
            actions = []
            for control in controls:
                attrs = _attributes(control.group())
                if (attrs.get('type') or '').lower() == 'checkbox' and 'required' in attrs and 'checked' not in attrs:
                    source = _source(file, text, form.start() + control.start(), form.start() + control.end() - 1)
                    actions.append({'description': 'Select required control ' + (attrs.get('name') or ''), 'evidence': [ctx.evidence(source)]})
            submit = re.search(r'<button\b[^>]*type\s*=\s*["\']submit["\'][^>]*>', body, re.I)
            if not submit:
                continue
            source = _source(file, text, form.start() + submit.start(), form.start() + submit.end() - 1)
            actions.append({'description': 'Submit form', 'evidence': [ctx.evidence(source)]})
            form_source = _source(file, text, form.start(), form.end() - 1)
            purpose_ids = [p['id'] for p in graph['purposes']
                           if any(_inside(ev, form_source) for ev in p['evidence'])]
            path_evidence = [ctx.evidence(source)]
            if withdrawal:
                binding = next((urls[name] for name, dest in destinations.items()
                                if dest == file and re.search(r'withdraw', name + urls[name]['view_name'], re.I)), None)
                if not binding:
                    continue
                view = binding['view']
                view_text = '\n'.join((ctx.root / view['file']).read_text(encoding='utf-8').splitlines()
                                      [view['start_line'] - 1:view['end_line']])
                if not re.search(r'withdraw[_a-z]*\s*\(|dispatch_account_deletion\s*\(|action\s*=\s*["\']WITHDRAWN["\']', view_text, re.I):
                    continue
                path_evidence.extend([ctx.evidence(binding['source']), ctx.evidence(view)])
                purpose_ids = []
                for write in django['event_writes']:
                    value = write['values'].get('purpose')
                    if isinstance(value, str) and value and re.search(r'\b' + re.escape(value) + r'\b', body, re.I):
                        purpose_ids.extend(p['id'] for p in graph['purposes']
                                           if re.search(r'\b' + re.escape(value) + r'\b', p['name'], re.I))
            else:
                action = next((a for a in django['template_actions'] if _inside(a['source'], form_source)), None)
                view = (action or {}).get('url', {}).get('view')
                signup = next((s for s in django.get('signup_forms', [])
                               if action and action['url_name'] == 'account_signup'
                               and any((_attributes(c.group()).get('name') or '') in s['fields'] for c in controls)), None)
                implementation = view or (signup['implementation'] if signup else None)
                grant = next((w for w in django['event_writes'] if implementation and _inside(w['source'], implementation)
                              and str(w['values'].get('action', '')).upper() in ('GRANTED', 'GRANT')), None)
                if not grant:
                    continue
                path_evidence.append(ctx.evidence(action['source']))
                if view:
                    path_evidence.extend([ctx.evidence(action['url']['source']), ctx.evidence(view)])
                else:
                    path_evidence.extend([ctx.evidence(signup['source']), ctx.evidence(implementation)])
                path_evidence.append(ctx.evidence(grant['source']))
            paths.append({'kind': 'withdrawal_paths' if withdrawal else 'grant_paths', 'file': file,
                          'source': source, 'actions': actions, 'purpose_ids': sorted(set(purpose_ids)),
                          'evidence': path_evidence})
    def route(start, end):
        queue = deque([(start, [])]); seen = {start}
        while queue:
            current, steps = queue.popleft()
            if current == end:
                return steps
            for dest, source in edges.get(current, []):
                if dest not in seen:
                    seen.add(dest); queue.append((dest, [*steps, source]))
        return None
    grants = [p for p in paths if p['kind'] == 'grant_paths']
    withdrawals = [p for p in paths if p['kind'] == 'withdrawal_paths']
    for path in paths:
        other = withdrawals if path['kind'] == 'grant_paths' else grants
        candidates = []
        for start in templates:
            steps = route(start, path['file'])
            if steps is None:
                continue
            for counterpart in other:
                if not set(path['purpose_ids']) & set(counterpart['purpose_ids']):
                    continue
                other_steps = route(start, counterpart['file'])
                if other_steps is not None:
                    candidates.append((len(steps) + len(other_steps), start, steps))
        selected = min(candidates, key=lambda x: (x[0], x[1])) if candidates else None
        navigation = ([{'description': 'Follow link', 'evidence': [ctx.evidence(s)]} for s in selected[2]] if selected else [])
        actions = navigation + path['actions']
        graph[path['kind']].append({'id': _id(path['kind'], path['source']), 'purpose_ids': path['purpose_ids'],
                                    'actions': actions, 'step_count': len(actions) if selected else None,
                                    'start_template': selected[1] if selected else None,
                                    'evidence': path['evidence']})
