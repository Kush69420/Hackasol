"""Static consent Rules over in-scope Angular forms, Sequelize models and Express routes.

The joins deliberately require local, concrete evidence; they do not infer a Purpose,
Data Processor, or legitimate use from the mere presence of an account.
"""
from __future__ import annotations

import json
from urllib.parse import urlparse
import re
from dataclasses import dataclass

from auditor.exposure import decide_exposure
from auditor.mapping import Match
from auditor.rules import RuleSpec, rule


def _spec(number, slug, title):
    return RuleSpec(f'CON-{number:02d}-{slug}', f'CON-{number:02d}', title,
                    'ts-ast', 'compliance-gap', None, ('typescript', 'html'))


ENFORCEMENT = _spec(1, 'express-enforcement', 'Processing without an Enforcement Point')
BUNDLED = _spec(2, 'angular-bundled-purposes', 'Consent bundled across Purposes')
DEFAULT = _spec(3, 'angular-default-true', 'Consent selected by default')
WITHDRAWAL = _spec(4, 'express-withdrawal-path', 'Missing or harder Withdrawal Path')
PROCESSOR = _spec(5, 'express-processor-withdrawal', 'Withdrawal not propagated to a Data Processor')
RECORD = _spec(6, 'sequelize-consent-record', 'Incomplete Consent Record')
NOTICE = _spec(7, 'angular-consent-notice', 'Incomplete consent notice')
EXCESS = _spec(8, 'angular-excess-elements', 'Personal Data Elements beyond the stated Purpose')


def _text(ctx, source):
    if not source or not source.get('file'):
        return ''
    return '\n'.join((ctx.root / source['file']).read_text(encoding='utf-8').splitlines()[source['start_line'] - 1:source['end_line']])


def _coord(file, text, start, end):
    return {'file': file, 'start_line': text.count('\n', 0, start) + 1,
            'end_line': text.count('\n', 0, end) + 1}


@dataclass
class ConsentModel:
    controls: list
    grants: list
    withdrawals: list
    records: list
    routes: list
    forms: list


def _model(ctx):
    cached = getattr(ctx, '_consent_model', None)
    if cached is not None:
        return cached
    controls = []
    forms = []
    translations = {}
    for path in ctx.files:
        if path.suffix != '.json':
            continue
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except (ValueError, UnicodeDecodeError):
            continue
        if isinstance(data, dict):
            translations.update({k: v for k, v in data.items() if isinstance(v, str)})
    # The inventory supplies the Angular component/template relationship and
    # input coordinates; inspect the containing form for its associated notice.
    for form in [*ctx.inventory.get('forms', []), *ctx.inventory.get('templates', [])]:
        source = form.get('source') or {}
        file = source.get('file') or form.get('file')
        if not file or not file.endswith(('.html', '.hbs')):
            continue
        text = (ctx.root / file).read_text(encoding='utf-8')
        for block in re.finditer(r'<form\b[^>]*>[\s\S]*?</form\s*>', text, re.I):
            body = block.group()
            inputs = [e for e in ctx.classified() if e['kind'] == 'form-input' and e['source']['file'] == file
                      and _coord(file, text, block.start(), block.start())['start_line'] <= e['source']['start_line'] <= _coord(file, text, block.end(), block.end())['start_line']]
            entry = {'text': body, 'source': _coord(file, text, block.start(), block.end() - 1), 'inputs': inputs}
            forms.append(entry)
            for control in re.finditer(r'<(?:input|mat-checkbox|mat-slide-toggle)\b[^>]*>', body, re.I):
                tag = control.group()
                if tag.lower().startswith('<input') and not re.search(r'\btype\s*=\s*["\']checkbox["\']', tag, re.I):
                    continue
                tail = body[control.end():]
                label = ''
                name = re.search(r'\b(?:id|name|formControlName)\s*=\s*["\']([^"\']+)', tag, re.I)
                if name:
                    linked = re.search(r'<label\b[^>]*\bfor\s*=\s*["\']' + re.escape(name.group(1)) + r'["\'][^>]*>([\s\S]*?)</label>', body, re.I)
                    label = linked.group(1) if linked else ''
                if not label:
                    enclosing = re.search(r'</(?:label|mat-checkbox|mat-slide-toggle)\s*>', tail, re.I)
                    label = tail[:enclosing.start()] if enclosing else ''
                for key in re.findall(r'["\']([^"\']+)["\']\s*\|\s*translate', label):
                    label += ' ' + translations.get(key, '')
                if not re.search(r'consent|agree|permission|accept', tag + ' ' + label, re.I):
                    continue
                source = _coord(file, text, block.start() + control.start(), block.start() + control.end() - 1)
                controls.append({**entry, 'tag': tag, 'label': label, 'control_source': source})
    routes = []
    for route in ctx.routes():
        if route.get('origin') != 'explicit' or not route.get('handler'):
            continue
        text = _text(ctx, route['handler'])
        routes.append({'route': route, 'text': text})
    grants = [r for r in routes if r['route']['method'] in ('POST', 'PUT', 'PATCH')
              and re.search(r'consent', r['route'].get('normalised_path', '') + ' ' + r['text'], re.I)
              and not re.search(r'withdraw|revoke', r['route'].get('normalised_path', ''), re.I)
              and re.search(r'(?:create|update|save)\s*\(', r['text'], re.I)
              and not re.search(r'\b(?:consent|granted)\s*:\s*false\b', r['text'], re.I)]
    withdrawals = [r for r in routes if re.search(r'consent', r['route'].get('normalised_path', '') + ' ' + r['text'], re.I)
                   and re.search(r'(?:\b(?:consent|granted)\s*:\s*false\b|\b(?:destroy|delete|revoke|withdraw)\s*\()', r['text'], re.I)]
    records = [m for m in ctx.inventory.get('models', []) if re.search(r'consent', m.get('name', ''), re.I)]
    ctx._consent_model = ConsentModel(controls, grants, withdrawals, records, routes, forms)
    return ctx._consent_model


def _match(ctx, spec, source, gate, element=None, extra=()):
    evidence = [ctx.evidence(source), *(ctx.evidence(s) for s in extra)]
    if element is None:
        element = next(iter(ctx.classified()), None)
    return Match(spec.id, spec.issue_type, evidence, spec.classification, None,
                 ctx.schema_element(element['id']) if element else None,
                 element['data_category'] if element else 'Profile', (),
                 'Collect' if element else None, ctx.flow_steps(element['id']) if element else [],
                 decide_exposure(authenticated=None, restricted=evidence[:1]),
                 gate_evidence=[ctx.evidence(g) for g in gate] if gate else None)


def _purposes(text):
    expressions = {
        'marketing': r'\bmarket(?:ing)?\b|\bpromot(?:ions?|ional)\b',
        'analytics': r'\banalytics\b|\btracking\b',
        'newsletter': r'\bnewsletters?\b',
        'sharing': r'\b(?:third[- ]party|data processors?)\b.{0,50}\b(?:shar\w*|disclos\w*)\b|\bshar\w*\b.{0,50}\b(?:third[- ]party|data processors?)\b',
        'terms': r'\b(?:terms(?: of (?:service|use))?|privacy (?:policy|notice))\b',
    }
    return {name for name, pattern in expressions.items() if re.search(pattern, text, re.I)}


def _within(source, container):
    return (source['file'] == container['file'] and source['start_line'] >= container['start_line']
            and source['end_line'] <= container['end_line'])


def _operations(ctx, route, kinds):
    handler = route.get('handler')
    if not handler:
        return []
    return [(element, step) for element in ctx.classified() for step in ctx.steps(element['id'])
            if step['operation'] in kinds and _within(step['source'], handler)]


def _frontend_gate(ctx, route):
    path = route.get('normalised_path', '')
    calls = [c for c in ctx.inventory.get('service_calls', [])
             if c.get('normalised_path') == path and c.get('http_method') == route['method']]
    for file in ctx.files:
        if not file.relative_to(ctx.root).as_posix().startswith('frontend/') or file.suffix not in ('.ts', '.html'):
            continue
        text = file.read_text(encoding='utf-8')
        for condition in re.finditer(r'(?:\bif\s*\([^)]*consent[^)]*\)|\*ngIf\s*=\s*["\'][^"\']*consent[^"\']*["\'])', text, re.I):
            nearby = text[condition.start():condition.start() + 1500]
            direct = bool(path and path in nearby)
            linked = any(re.search(r'\.\s*' + re.escape(c['function']) + r'\s*\(', nearby) for c in calls if c.get('function'))
            if direct or linked:
                return _coord(file.relative_to(ctx.root).as_posix(), text, condition.start(), condition.end() - 1)
    return None


@rule(ENFORCEMENT)
def enforcement(ctx):
    model = _model(ctx)
    out = []
    for item in model.routes:
        route, text = item['route'], item['text']
        if route['method'] not in ('POST', 'PUT', 'PATCH') or not _purposes(route['normalised_path'] + ' ' + text) - {'terms'}:
            continue
        if re.search(r'\b(?:order|checkout|purchase|register|registration|account)\b', route['normalised_path'], re.I):
            continue
        client = _frontend_gate(ctx, route)
        operations = _operations(ctx, route, {'Store', 'Transfer'})
        if not client or not operations:
            continue
        if re.search(r'\bif\s*\([^)]*consent', text, re.I) or any(re.search(r'consent', m['name'], re.I) for m in route['middleware']):
            continue
        element, operation = operations[0]
        out.append(_match(ctx, ENFORCEMENT, operation['source'], [client], element, [client, route['registration']]))
    return out


@rule(BUNDLED)
def bundled(ctx):
    model = _model(ctx)
    out = [_match(ctx, BUNDLED, c['control_source'], [c['control_source']], next(iter(c['inputs']), None))
           for c in model.controls if len(_purposes(c['label'])) > 1]
    by_field = {}
    for item in model.routes:
        condition = re.search(r'\bif\s*\([^)]*\b(\w*consent\w*)\b', item['text'], re.I)
        purposes = _purposes(item['route']['normalised_path'] + ' ' + item['text']) - {'terms'}
        if condition and len(purposes) == 1 and _operations(ctx, item['route'], {'Store', 'Transfer'}):
            by_field.setdefault(condition.group(1).lower(), []).append((item, next(iter(purposes))))
    for entries in by_field.values():
        if len({p for _, p in entries}) > 1:
            coords = [item['route']['handler'] for item, _ in entries]
            out.append(_match(ctx, BUNDLED, coords[0], coords, extra=coords[1:]))
    return out


@rule(DEFAULT)
def default_true(ctx):
    model = _model(ctx)
    out = []
    for c in model.controls:
        tag = c['tag']
        checked = re.search(r'(?:\[checked\]\s*=\s*["\']true["\']|(?<![\w\]-])checked(?:\s|=|/?>))', tag, re.I)
        if checked and not re.search(r'\bchecked\s*=\s*["\']false["\']', tag, re.I):
            out.append(_match(ctx, DEFAULT, c['control_source'], [c['control_source']], next(iter(c['inputs']), None)))
    for record in model.records:
        for field in record.get('fields', []):
            if re.search(r'consent|granted', field['name'], re.I) and re.search(r'defaultValue\s*:\s*true\b', _text(ctx, field['source']), re.I):
                out.append(_match(ctx, DEFAULT, field['source'], [field['source']]))
    # Angular reactive controls may initialise the value in their component,
    # rather than on the template element.
    for form in ctx.inventory.get('forms', []):
        names = {f.get('name') for f in form.get('inputs', []) if re.search(r'consent|agree|permission', f.get('name') or '', re.I)}
        if not names:
            continue
        component = form.get('component')
        for file in ctx.files:
            if file.suffix != '.ts':
                continue
            text = file.read_text(encoding='utf-8')
            if not component or not re.search(r'\bclass\s+' + re.escape(component) + r'\b', text):
                continue
            for name in names:
                pattern = r'\b' + re.escape(name) + r'\s*(?:=|:)\s*(?:new\s+(?:Untyped)?FormControl\s*\(\s*true\b|\[\s*true\b)'
                for found in re.finditer(pattern, text):
                    source = _coord(file.relative_to(ctx.root).as_posix(), text, found.start(), found.end() - 1)
                    out.append(_match(ctx, DEFAULT, source, [source]))
    return out


@rule(WITHDRAWAL)
def withdrawal(ctx):
    model = _model(ctx)
    grants = [(g['route']['registration'], g['route']) for g in model.grants]
    grants += [(c['control_source'], None) for c in model.controls
               if not re.search(r'withdraw|revoke', c['tag'] + c['label'], re.I)]
    for record in model.records:
        grants += [(f['source'], None) for f in record.get('fields', [])
                   if re.search(r'consent|granted', f['name'], re.I) and f.get('default') is True]
    controls = [c for c in model.controls if re.search(r'withdraw|revoke', c['tag'] + c['label'], re.I)]
    out = []
    for source, grant_route in grants:
        if controls:
            continue
        # A withdrawal endpoint with additional authentication steps is harder
        # than an unauthenticated grant or a grant directly on a form.
        grant_auth = sum(m.get('role') == 'authentication' for m in grant_route['middleware']) if grant_route else 0
        suitable = [w for w in model.withdrawals if sum(m.get('role') == 'authentication' for m in w['route']['middleware']) <= grant_auth]
        if suitable:
            continue
        extra = [model.withdrawals[0]['route']['registration']] if model.withdrawals else []
        out.append(_match(ctx, WITHDRAWAL, source, [source], extra=extra))
    return out


@rule(PROCESSOR)
def processor(ctx):
    model = _model(ctx)
    out = []
    if not model.withdrawals:
        return []
    for element in ctx.classified():
        for step in ctx.steps(element['id']):
            if step['operation'] != 'Transfer':
                continue
            source = step['source']
            call = _text(ctx, source)
            sdk = re.search(r'\b(sgMail|sesClient)\.send\s*\(', call)
            urls = re.findall(r'https?://[^\s\'\"`]+', call)
            # Resolve a local endpoint constant used directly by the operation.
            if not urls:
                full = (ctx.root / source['file']).read_text(encoding='utf-8')
                arg = re.search(r'\b(?:fetch|axios\.\w+|needle\.\w+)\s*\(\s*(\w+)', call)
                definition = re.search(r'\b(?:const|let)\s+' + re.escape(arg.group(1)) + r'\s*=\s*["\'](https?://[^"\']+)', full) if arg else None
                urls = [definition.group(1)] if definition else []
            host = urlparse(urls[0]).hostname if urls else None
            if not sdk and (not host or host in ('localhost', '127.0.0.1') or host.endswith(('.local', '.internal'))):
                continue
            destination = sdk.group(1) if sdk else host
            if any(destination.lower() in w['text'].lower() and re.search(r'\b(?:fetch|request|send|post|delete|erase|remove)\b', w['text'], re.I) for w in model.withdrawals):
                continue
            out.append(_match(ctx, PROCESSOR, model.withdrawals[0]['route']['handler'], [source], element, [source]))
    return out


@rule(RECORD)
def consent_record(ctx):
    model = _model(ctx)
    complete = any(all(any(re.search(pattern, f['name'], re.I) for f in record.get('fields', []))
                       for pattern in (r'purpose', r'notice(?:version|reference|id)', r'(?:time|date|at)$'))
                   for record in model.records)
    if complete:
        return []
    return [_match(ctx, RECORD, g['route']['handler'], [g['route']['registration']],
                   extra=[r['source'] for r in model.records if r.get('source')]) for g in model.grants]


@rule(NOTICE)
def notice(ctx):
    model = _model(ctx)
    out = []
    for c in model.controls:
        text = c['text']
        itemised = bool(re.search(r'<(?:ul|ol)\b[\s\S]*?<li\b', text, re.I)) and bool(re.search(r'purpose', text, re.I))
        languages = bool(re.search(r'\benglish\b', text, re.I)) and bool(re.search(r'\b(?:hindi|bengali|tamil|telugu|marathi|urdu|gujarati|kannada|malayalam|punjabi|odia|assamese|sanskrit|nepali|sindhi|konkani|manipuri|bodo|dogri|kashmiri|maithili|santali)\b', text, re.I))
        if not (itemised and languages):
            out.append(_match(ctx, NOTICE, c['control_source'], [c['control_source']], next(iter(c['inputs']), None)))
    return out


@rule(EXCESS)
def excess(ctx):
    model = _model(ctx)
    out = []
    for form in model.forms:
        # Require a stated Purpose and either an explicit list of necessary
        # Elements or a Data Flow which actually ends at Collect.
        declaration = re.search(r'(?:to|for)\s+(?:send|provide|deliver|enable)\s+(?:the\s+)?(?:newsletter|marketing|analytics)[^<.]*', form['text'], re.I)
        if not declaration:
            continue
        statement = declaration.group()
        names = {e['name'].lower() for e in form['inputs']
                 if re.search(r'\b' + re.escape(e['name']) + r'\b', statement, re.I)}
        explicit = bool(names and re.search(r'\b(?:only|need(?:ed)?|require[ds]?)\b', statement, re.I))
        for element in form['inputs']:
            steps = list(ctx.steps(element['id']))
            # Form Elements may be represented by a model Element's Data Flow.
            for candidate in ctx.classified():
                if candidate['id'] == element['id']:
                    continue
                candidate_steps = ctx.steps(candidate['id'])
                if any(s['operation'] == 'Collect' and s['source'] == element['source'] for s in candidate_steps):
                    steps.extend(candidate_steps)
            used = any(s['operation'] in ('Store', 'Transfer', 'Use') for s in steps)
            unused_collected = any(s['operation'] == 'Collect' for s in steps) and not used
            beyond_statement = explicit and element['name'].lower() not in names and not used
            if unused_collected or beyond_statement:
                out.append(_match(ctx, EXCESS, element['source'], [form['source']], element))
    return out
