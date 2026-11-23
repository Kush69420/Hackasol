"""Prisma schema analyser: models, typed fields, defaults and datasources from `*.prisma` files.

Source-only: the schema is parsed as text and never executed. Models are emitted in the same
shape as the other analysers (`name`, `table`, `kind`, `source`, `options`, `fields`) so the
Element classifier and the Personal Data Map treat them like Sequelize or Django models.
Relation fields are not Personal Data declarations and are left out of `fields`.
"""
from __future__ import annotations

import re
from pathlib import Path

_BLOCK = re.compile(r'^\s*(model|enum|datasource|generator|type|view)\s+(\w+)\s*\{')
_FIELD = re.compile(r'^\s*(\w+)\s+(\w+)(\[\])?(\?)?(?:\s+(.*))?$')
_SCALARS = {'String', 'Boolean', 'Int', 'BigInt', 'Float', 'Decimal', 'DateTime', 'Json', 'Bytes'}


def _strip(line: str) -> str:
    """Remove a trailing `//` comment that is outside a string literal."""
    quote = False
    for i, ch in enumerate(line):
        if ch == '"':
            quote = not quote
        elif ch == '/' and not quote and line[i:i + 2] == '//':
            return line[:i]
    return line


def _default(attributes: str) -> str | None:
    match = re.search(r'@default\((.*?)\)(?=\s*(?:@|$))', attributes)
    if not match:
        return None
    # String defaults can be Authentication Secrets: emit presence, not the value.
    return re.sub(r'"(?:\\.|[^"\\])*"', lambda m: '""' if m.group(0) == '""' else '"<string>"', match.group(1))


def _blocks(text: str):
    """Yield (kind, name, first_line, last_line, [(line_no, content)]) for every top-level block."""
    current = None
    for number, raw in enumerate(text.splitlines(), 1):
        line = _strip(raw)
        if current is None:
            match = _BLOCK.match(line)
            if match:
                current = [match.group(1), match.group(2), number, number, []]
                if '}' in line[line.index('{'):]:
                    current[3] = number
                    yield tuple(current)
                    current = None
            continue
        if line.strip().startswith('}'):
            current[3] = number
            yield tuple(current)
            current = None
        else:
            current[4].append((number, line))


def analyse(root: Path, rel_files: list[str]) -> dict:
    parsed = []
    for file in rel_files:
        if not file.endswith('.prisma'):
            continue
        try:
            text = (root / file).read_text(encoding='utf-8')
        except (OSError, UnicodeError):
            continue
        parsed.append((file, list(_blocks(text))))
    if not parsed:
        return {}
    model_names = {name for _, blocks in parsed for kind, name, *_ in blocks if kind == 'model'}
    enum_names = {name for _, blocks in parsed for kind, name, *_ in blocks if kind == 'enum'}
    models, datasources = [], []
    for file, blocks in parsed:
        for kind, name, start, end, body in blocks:
            source = {'file': file, 'start_line': start, 'end_line': end}
            if kind == 'datasource':
                values = {}
                for number, line in body:
                    pair = re.match(r'\s*(\w+)\s*=\s*(.+?)\s*$', line)
                    if pair:
                        values[pair.group(1)] = (pair.group(2), number)
                url = values.get('url')
                env = re.fullmatch(r'env\("([^"]+)"\)', url[0]) if url else None
                literal = re.fullmatch(r'"file:([^"]+)"', url[0]) if url else None
                datasources.append({
                    'name': name,
                    'provider': (values.get('provider', ('', 0))[0]).strip('"') or None,
                    'url_env': env.group(1) if env else None,
                    # Only a sqlite file path is retained; a connection URL may embed credentials.
                    'file_path': literal.group(1) if literal else None,
                    'source': source,
                })
            if kind != 'model':
                continue
            fields, table = [], None
            for number, line in body:
                stripped = line.strip()
                if stripped.startswith('@@map'):
                    mapped = re.search(r'@@map\(\s*(?:name:\s*)?"([^"]+)"', stripped)
                    table = mapped.group(1) if mapped else table
                    continue
                if not stripped or stripped.startswith(('@@', '//', '/*', '*')):
                    continue
                match = _FIELD.match(line)
                if not match:
                    continue
                fname, ftype, is_list, optional, attributes = match.groups()
                if ftype in model_names or (ftype not in _SCALARS and ftype not in enum_names):
                    continue
                attributes = attributes or ''
                fields.append({
                    'name': fname, 'type': ftype + ('[]' if is_list else ''),
                    'allow_null': bool(optional), 'default': _default(attributes),
                    'unique': '@unique' in attributes or '@id' in attributes or None,
                    'validators': [], 'source': {'file': file, 'start_line': number, 'end_line': number},
                })
            models.append({'name': name, 'table': table, 'kind': 'prisma', 'source': source,
                           'options': {}, 'fields': fields})
    return {'models': models, 'prisma_datasources': datasources}
