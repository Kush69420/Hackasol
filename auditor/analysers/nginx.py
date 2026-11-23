"""nginx configuration analyser: servers, locations, proxying, TLS and access logging.

Source-only; configuration is tokenised, never executed. A file is nginx configuration only when it
contains a `server` block (or is named nginx.conf); other `.conf` files are ignored. Each file record
has a `network` list that separates `inbound` settings (`listen`) from `outbound` ones
(`proxy_pass`). Access logging is resolved per location: its own `access_log`, else the server's,
else the http block's; only an explicit directive counts (the compiled-in default is not assumed).
"""
from __future__ import annotations

import re
from pathlib import Path

_VAR = re.compile(r'\$(?:\{(\w+)\}|(\w+))')
_PRIVATE = re.compile(r'^(?:localhost|127\.|10\.|192\.168\.|172\.(?:1[6-9]|2\d|3[01])\.|\[::1\])')


def _tokenise(text: str):
    """Yield (token, line) where token is a word, quoted string content, ';', '{' or '}'."""
    i, line, n = 0, 1, len(text)
    while i < n:
        ch = text[i]
        if ch == '\n':
            line += 1; i += 1
        elif ch.isspace():
            i += 1
        elif ch == '#':
            while i < n and text[i] != '\n':
                i += 1
        elif ch in ';{}':
            yield ch, line; i += 1
        elif ch in '"\'':
            start, quote, begin = line, ch, i + 1
            i += 1
            while i < n and text[i] != quote:
                if text[i] == '\\':
                    i += 1
                if i < n and text[i] == '\n':
                    line += 1
                i += 1
            yield ('str', text[begin:i]), start
            i += 1
        else:
            begin = i
            while i < n and not text[i].isspace() and text[i] not in ';{}':
                i += 1
            yield text[begin:i], line


def _parse(text: str):
    """Return a list of directive dicts: {name, args, children|None, line, end_line}."""
    stack = [[]]
    pending, start = [], None
    for token, line in _tokenise(text):
        if token == ';':
            if pending:
                stack[-1].append({'name': pending[0], 'args': pending[1:], 'children': None, 'line': start, 'end_line': line})
            pending, start = [], None
        elif token == '{':
            node = {'name': pending[0] if pending else '', 'args': pending[1:], 'children': [], 'line': start or line, 'end_line': line}
            stack[-1].append(node); stack.append(node['children']); pending, start = [], None
        elif token == '}':
            if len(stack) > 1:
                stack.pop()
                # end_line of the closed block: the last block appended to the parent
                stack[-1][-1]['end_line'] = line
            pending, start = [], None
        else:
            if start is None:
                start = line
            pending.append(token[1] if isinstance(token, tuple) else token)
    return stack[0]


def _variables(fmt: str) -> list[str]:
    return list(dict.fromkeys(a or b for a, b in _VAR.findall(fmt)))


def _host_scope(target: str) -> str:
    host = re.sub(r'^\w+://', '', target).split('/')[0].split(':')[0]
    return 'internal' if _PRIVATE.match(host) or '.' not in host else 'external'


def _find(children, name):
    return [c for c in children or [] if c['name'] == name]


def analyse(root: Path, rel_files: list[str]) -> dict:
    records = []
    for file in rel_files:
        base = file.rsplit('/', 1)[-1]
        if not (base.endswith('.conf') or base == 'nginx.conf' or base.endswith(('.nginx', '.vhost'))):
            continue
        try:
            text = (root / file).read_text(encoding='utf-8')
        except (OSError, UnicodeError):
            continue
        if not re.search(r'\bserver\s*\{', text):
            continue
        tree = _parse(text)

        def coord(node):
            return {'file': file, 'start_line': node['line'], 'end_line': max(node['line'], node['end_line'])}

        scopes = [tree]
        http = [c for n in tree if n['name'] == 'http' for c in [n]]
        top = http[0]['children'] if http else tree
        log_formats = [{'name': n['args'][0] if n['args'] else None, 'format': ''.join(a for a in n['args'][1:] if not a.startswith('escape=')),
                        'variables': _variables(' '.join(n['args'][1:])), 'source': coord(n)} for n in _find(top, 'log_format')]

        def access(children, inherited):
            logs = _find(children, 'access_log')
            if not logs:
                return inherited
            first = logs[0]
            if first['args'] and first['args'][0] == 'off':
                return {'off': True, 'path': None, 'format': None, 'source': coord(first)}
            return {'off': False, 'path': first['args'][0] if first['args'] else None,
                    'format': first['args'][1] if len(first['args']) > 1 else 'combined', 'source': coord(first)}

        http_log = access(top, None)
        upstreams = [{'name': n['args'][0] if n['args'] else None, 'servers': [s['args'][0] for s in _find(n['children'], 'server') if s['args']],
                      'source': coord(n)} for n in _find(top, 'upstream')]
        servers, network = [], []
        for server in _find(top, 'server'):
            children = server['children']
            listens = []
            for directive in _find(children, 'listen'):
                args = directive['args']
                address = args[0] if args else ''
                port = re.search(r'(\d+)$', address)
                local = address.startswith(('127.', 'localhost', '[::1]', 'unix:'))
                listens.append({'address': address, 'port': int(port.group(1)) if port else None, 'ssl': 'ssl' in args or (port and port.group(1) == '443'),
                                'scope': 'loopback' if local else 'public', 'source': coord(directive)})
                network.append({'direction': 'inbound', 'scope': 'internal' if local else 'public', 'via': 'listen', 'target': address, 'source': coord(directive)})
            tls = None
            if _find(children, 'ssl_certificate') or any(l['ssl'] for l in listens):
                protocols = _find(children, 'ssl_protocols')
                tls = {'certificate': bool(_find(children, 'ssl_certificate')), 'protocols': protocols[0]['args'] if protocols else None,
                       'source': coord(_find(children, 'ssl_certificate')[0] if _find(children, 'ssl_certificate') else server)}
            server_log = access(children, http_log)
            locations = []
            for loc in _find(children, 'location'):
                args = loc['args']
                modifier = args[0] if len(args) > 1 else None
                proxy = _find(loc['children'], 'proxy_pass')
                target = None
                if proxy and proxy[0]['args']:
                    value = proxy[0]['args'][0]
                    name = re.sub(r'^\w+://', '', value).split('/')[0]
                    upstream = next((u for u in upstreams if u['name'] == name), None)
                    target = {'target': value, 'kind': 'upstream' if upstream else 'url', 'scope': 'internal' if upstream or _host_scope(value) == 'internal' else 'external', 'source': coord(proxy[0])}
                    network.append({'direction': 'outbound', 'scope': target['scope'], 'via': 'proxy_pass', 'target': value, 'source': target['source']})
                locations.append({'path': args[-1] if args else None, 'modifier': modifier, 'proxy': target,
                                  'access_log': access(loc['children'], server_log), 'headers': [{'name': h['args'][0], 'source': coord(h)} for h in _find(loc['children'], 'add_header') if h['args']],
                                  'source': coord(loc)})
            servers.append({'server_names': [a for d in _find(children, 'server_name') for a in d['args']], 'listen': listens, 'tls': tls,
                            'access_log': server_log, 'headers': [{'name': h['args'][0], 'source': coord(h)} for h in _find(children, 'add_header') if h['args']],
                            'locations': locations, 'source': coord(server)})
        records.append({'file': file, 'log_formats': log_formats, 'upstreams': upstreams, 'servers': servers, 'network': network})
    return {'nginx': records} if records else {}
