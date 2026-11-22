"""Rules for committed Personal Data, monitoring, sharing and Child Data."""
from __future__ import annotations

from contextlib import closing
import json
import csv
import ipaddress
import sqlite3
import re
from urllib.parse import urlparse

from auditor import validators
from auditor.exposure import decide_exposure
from auditor.mapping import Match
from auditor.rules import RuleSpec, rule

SEC = RuleSpec('SEC-15-committed-personal-data', 'SEC-15', 'Validated committed Personal Data', 'config', 'technical', 'CVSS:4.0/AV:L/AC:L/AT:N/PR:L/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N', ('yaml', 'json', 'csv', 'sql', 'sqlite', 'log'))
MON = RuleSpec('MON-01-monitoring-coverage', 'MON-01', 'Monitoring omits access and authentication events', 'config', 'compliance-gap', None, ('json', 'yaml'))
TRF = RuleSpec('TRF-01-undisclosed-processor-transfer', 'TRF-01', 'Undisclosed Personal Data Transfer to a Data Processor', 'ts-ast', 'disclosure', None, ('typescript', 'javascript'))
CHI = RuleSpec('CHI-01-age-parental-consent', 'CHI-01', 'Age gate or verifiable parental consent not evidenced', 'ts-ast', 'compliance-gap', None, ('typescript', 'html'))
TRACK = RuleSpec('CHI-02-child-tracking', 'CHI-02', 'Tracking without excluding Child Data', 'ts-ast', 'compliance-gap', None, ('typescript', 'javascript', 'html'))


def _coord(ctx, file, line):
    return {'file': file.relative_to(ctx.root).as_posix(), 'start_line': line, 'end_line': line}


def _match(ctx, spec, evidence, element=None, gate=None, operation=None, third_party=False):
    schema = ctx.schema_element(element['id']) if element else None
    category = element['data_category'] if element else 'Child Data'
    exposure = decide_exposure(authenticated=None, **({'outbound_third_party': evidence[:1]} if third_party else {'restricted': evidence[:1]}))
    return Match(spec.id, spec.issue_type, evidence, spec.classification, spec.base_vector,
                 schema, category, (), operation, ctx.flow_steps(element['id']) if element else [], exposure,
                 nexus_elements=(element['id'],) if element else (), gate_evidence=gate)


def _texts(ctx, suffixes):
    for file in ctx.files:
        if file.suffix.lower() in suffixes:
            try:
                yield file, file.read_text(encoding='utf-8')
            except (UnicodeError, OSError):
                continue


def _seed_files(ctx):
    # Resolve the common static-data loader -> named loader -> creator chain.
    scripts = list(_texts(ctx, {'.ts', '.js'}))
    seeded = set()
    for loader, text in scripts:
        for match in re.finditer(r"(?:path\.resolve|path\.join)\(\s*['\"]([^'\"]*/)['\"]\s*\+\s*(\w+)\s*\+\s*['\"](\.[\w]+)['\"]", text):
            directory, _, extension = match.groups()
            for call in re.finditer(r"(?:function\s+(\w+)|const\s+(\w+)\s*=)(?:(?!\bfunction\s+\w+)[\s\S]){0,180}?loadStaticData\(\s*['\"]([^'\"]+)['\"]\s*\)", text):
                function = call.group(1) or call.group(2)
                if any(re.search(r'\b' + re.escape(function) + r'\s*\(', source) and re.search(r'\b(?:create|bulkCreate|seed)\s*\(', source, re.I) for other, source in scripts if other != loader):
                    seeded.add((directory.lstrip('./') + call.group(3) + extension).replace('//', '/'))
    return seeded


def _validated(key, value):
    key = re.sub(r'[^a-z]', '', key.lower())
    value = str(value).strip()
    if key in ('email', 'emailaddress') and validators.is_email(value):
        local, domain = (part.lower() for part in value.rsplit('@', 1))
        role_mailbox = re.fullmatch(r'(?:no-?reply|do-?not-?reply|postmaster|abuse|privacy|support|info|admin|webmaster)', local) or domain == 'users.noreply.github.com'
        if not role_mailbox and domain not in {'example.com', 'example.org', 'example.net', 'localhost'} and not domain.endswith(('.example.com', '.example.org', '.example.net', '.test', '.example', '.invalid', '.localhost')):
            return 'Contact'
    if key in ('phone', 'phonenumber', 'mobile', 'mobilenum', 'mobilenumber') and validators.is_indian_phone(value):
        return 'Contact'
    if key in ('ip', 'ipaddress', 'clientip') and validators.is_ip(value) and ipaddress.ip_address(value).is_global:
        return 'Profile'
    if key in ('cardnum', 'cardnumber') and validators.is_card(value):
        return 'Financial'
    if key in ('aadhaar', 'aadhaarnumber') and validators.is_aadhaar(value):
        return 'Government Identifier'
    if key in ('pan', 'pannumber') and validators.is_pan(value):
        return 'Government Identifier'
    return None


def _committed_match(ev, key, category):
    element = {'name': f'committed:{ev["file"]}#{key}', 'data_category': category, 'evidence': ev}
    return Match(SEC.id, SEC.issue_type, [ev], SEC.classification, SEC.base_vector, element, category, (), 'Store', [],
                 decide_exposure(authenticated=None, restricted=[ev]), gate_evidence=[ev])


def _sqlite_matches(ctx, seeded):
    matches = []
    for file in ctx.files:
        try:
            with file.open('rb') as stream:
                if stream.read(16) != b'SQLite format 3\x00':
                    continue
            with closing(sqlite3.connect(file.resolve().as_uri() + '?mode=ro&immutable=1', uri=True)) as db:
                db.execute('PRAGMA query_only = ON')
                tables = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
                for (table,) in tables:
                    quoted = '"' + table.replace('"', '""') + '"'
                    columns = [row[1] for row in db.execute(f'PRAGMA table_info({quoted})')]
                    relevant = [column for column in columns if re.sub(r'[^a-z]', '', column.lower()) in {
                        'email', 'emailaddress', 'phone', 'phonenumber', 'mobile', 'mobilenum', 'mobilenumber',
                        'ip', 'ipaddress', 'clientip', 'cardnum', 'cardnumber', 'aadhaar', 'aadhaarnumber', 'pan', 'pannumber'}]
                    if not relevant:
                        continue
                    for row in db.execute(f'SELECT * FROM {quoted}'):
                        if (file.relative_to(ctx.root).as_posix() in seeded and
                                any(re.search(r'\b(?:demo|dummy|placeholder|test(?:er)?|fictional|example)\b', str(v), re.I) for v in row)):
                            continue
                        for column in relevant:
                            category = _validated(column, row[columns.index(column)])
                            if not category:
                                continue
                            ev = {'file': file.relative_to(ctx.root).as_posix(), 'start_line': 1, 'end_line': 1,
                                  'excerpt': f'SQLite table {table}, column {column}: validated {category} value (masked)'}
                            matches.append(_committed_match(ev, column, category))
                            break
        except (OSError, sqlite3.Error, ValueError):
            continue
    return matches


def _dump_values(text):
    insert = re.compile(r'\bINSERT\s+INTO\s+[\w.\"`]+\s*\(([^)]+)\)\s*VALUES\s*(.*?);', re.I | re.S)
    for statement in insert.finditer(text):
        columns = [c.strip(' `\"') for c in statement.group(1).split(',')]
        for row in re.finditer(r'\(([^()]*)\)', statement.group(2)):
            try:
                values = next(csv.reader([row.group(1)], quotechar="'", skipinitialspace=True))
            except csv.Error:
                continue
            if len(values) != len(columns):
                continue
            line = text.count('\n', 0, statement.start(2) + row.start()) + 1
            for column, value in zip(columns, values):
                category = _validated(column, value)
                if category:
                    yield line, column, category


def _log_values(line):
    patterns = (
        ('email', r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+"),
        ('ip', r'(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])'),
        ('phone', r'(?<!\d)(?:\+91[ -]?)?[6-9]\d{9}(?!\d)'),
    )
    for key, pattern in patterns:
        for match in re.finditer(pattern, line):
            category = _validated(key, match.group())
            if category:
                yield key, category


@rule(SEC)
def committed_data(ctx):
    seeded = _seed_files(ctx)
    out = _sqlite_matches(ctx, seeded)
    value_re = re.compile(r'''(?<![\w-])["']?(email|phone|mobile(?:Num)?|card(?:Num|Number)|aadhaar|pan)["']?\s*[:=,]\s*["']?([^\s,"'\]}#]+)''', re.I)
    for file, text in _texts(ctx, {'.yml', '.yaml', '.json', '.csv', '.sql', '.log'}):
        if (file.relative_to(ctx.root).as_posix() in seeded and
                re.search(r'\b(?:demo|dummy|placeholder|test(?:er)?|fictional|example)\b', text, re.I)):
            continue
        if file.suffix.lower() == '.sql':
            for line_no, key, category in _dump_values(text):
                ev = ctx.evidence(_coord(ctx, file, line_no))
                out.append(_committed_match(ev, key, category))
            continue
        if file.suffix.lower() == '.log':
            for line_no, line in enumerate(text.splitlines(), 1):
                for key, category in _log_values(line):
                    ev = ctx.evidence(_coord(ctx, file, line_no))
                    out.append(_committed_match(ev, key, category))
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            for found in value_re.finditer(line):
                key, value = found.groups()
                key = key.lower()
                category = _validated(key, value)
                if not category:
                    continue
                ev = ctx.evidence(_coord(ctx, file, line_no))
                out.append(_committed_match(ev, key, category))
    return out


def _panels(node):
    if isinstance(node, dict):
        if 'targets' in node and ('title' in node or 'type' in node):
            yield node
        for value in node.values():
            yield from _panels(value)
    elif isinstance(node, list):
        for value in node:
            yield from _panels(value)


@rule(MON)
def monitoring(ctx):
    out = []
    for file, text in _texts(ctx, {'.json'}):
        try:
            panels = list(_panels(json.loads(text)))
        except ValueError:
            continue
        if not panels:
            continue
        coverage = re.compile(r'access[_ -]?log|auth(?:entication)?[_ -]?(?:event|failure|success|log)|(?:login|logon|sign[_ -]?in)[_ -]?(?:failure|success|event|attempt)', re.I)
        if any(coverage.search(json.dumps(panel)) for panel in panels):
            continue
        target = next((p for p in panels if p.get('targets')), panels[0])
        title = target.get('title', '')
        lines = text.splitlines()
        line = next((i for i, value in enumerate(lines, 1) if title and json.dumps(title) in value), 1)
        ev = ctx.evidence(_coord(ctx, file, line))
        element = next(iter(ctx.classified()), None)
        out.append(_match(ctx, MON, [ev], element, [ev]))
    return out


@rule(TRF)
def undisclosed_transfer(ctx):
    out = []
    for element in ctx.classified():
        for step in ctx.steps(element['id']):
            if step['operation'] != 'Transfer':
                continue
            ev = ctx.evidence(step['source'])
            line = ev['excerpt']
            urls = re.findall(r'https?://[^\s\'"`]+', line)
            host = urlparse(urls[0]).hostname if urls else None
            sdk = re.search(r'\b(?:sgMail|sesClient)\.send\s*\(', line)
            if not sdk and (not host or host in ('localhost', '127.0.0.1') or host.endswith(('.local', '.internal'))):
                continue
            processor = host or ('sendgrid' if 'sgMail' in line else 'amazon ses')
            disclosed = any(processor.lower() in notice.lower() and re.search(r'\b(?:share|sharing|processor|recipient|disclos)', notice, re.I)
                            for file, notice in _texts(ctx, {'.html', '.md', '.txt'}) if file != ctx.root / step['source']['file'])
            if not disclosed:
                out.append(_match(ctx, TRF, [ev], element, [ev], 'Transfer', True))
    return out


def _child_gate(ctx):
    for form in [*ctx.inventory.get('forms', []), *ctx.inventory.get('templates', [])]:
        for field in form.get('inputs', []):
            if re.search(r'^(?:age|dob|date[_-]?of[_-]?birth|birthdate)$', field.get('name') or '', re.I):
                source = field.get('source') or form.get('source')
                if source:
                    return ctx.evidence(source), None
    for element in ctx.elements:
        if element['kind'] in ('form-input', 'route-param') and re.search(r'^(?:age|dob|date[_-]?of[_-]?birth|birthdate)$', element['name'], re.I):
            return ctx.evidence(element['source']), element if element.get('data_category') else None
    # Explicit audience statements, not incidental mentions of games or children.
    for file, text in _texts(ctx, {'.html', '.md', '.json'}):
        for i, line in enumerate(text.splitlines(), 1):
            if re.search(r'\b(?:designed|intended|made)\s+for\s+(?:children|kids|school students)\b', line, re.I):
                return ctx.evidence(_coord(ctx, file, i)), None
    return None, None


def _registration(ctx):
    for form in ctx.inventory.get('forms', []):
        if re.search(r'register|registration|signup', str((form.get('source') or {}).get('file', '')), re.I) and form.get('source'):
            return ctx.evidence(form['source'])
    for route in ctx.routes('POST'):
        if re.search(r'register|signup|/api/users', route.get('normalised_path', ''), re.I):
            return ctx.evidence(route['registration'])
    return None


def _handling(ctx, pattern):
    return any(re.search(pattern, text, re.I) for _, text in _texts(ctx, {'.ts', '.js', '.html'}))


@rule(CHI)
def child_consent(ctx):
    gate, element = _child_gate(ctx)
    if gate:
        if _handling(ctx, r'\b(?:verify(?:Age|ParentalConsent)|verifiableParentalConsent|ageGate)\s*\('):
            return []
        return [_match(ctx, CHI, [gate], element, [gate], 'Collect')]
    anchor = _registration(ctx)
    return [_match(ctx, CHI, [anchor])] if anchor else []


@rule(TRACK)
def child_tracking(ctx):
    gate, element = _child_gate(ctx)
    if not gate:
        return []
    for file, text in _texts(ctx, {'.ts', '.js', '.html'}):
        for i, line in enumerate(text.splitlines(), 1):
            if re.search(r'\b(?:analytics\.track|gtag|fbq|trackBehaviour|targetedAds)\s*\(', line, re.I):
                if re.search(r'\b(?:excludeChildren|isAdult|ageVerified)\b', text, re.I):
                    continue
                ev = ctx.evidence(_coord(ctx, file, i))
                return [_match(ctx, TRACK, [ev, gate], element, [gate, ev], 'Collect')]
    return []
