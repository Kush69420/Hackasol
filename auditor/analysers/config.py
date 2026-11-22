"""Configuration and infrastructure inventory: Dockerfiles, config/*.yml, app.json, .env and Terraform.

Each record carries source coordinates ``{"file", "start_line", "end_line"}`` (1-based, inclusive).
Only the in-scope files passed in are read. Values pass through ``mask_for_report``.
"""

import bisect
import json
import re
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import NamedTuple

import hcl2
import yaml

from auditor.masking import mask_for_report

_SECRET = mask_for_report('password="x"')  # the masker's label for a secret value
_HCL_OPTIONS = hcl2.utils.SerializationOptions(strip_string_quotes=True)
_BLOCK_LABELS = {"resource": 2, "provider": 1, "variable": 1}
_BLOCK_HEADER = re.compile(r'([A-Za-z_][\w-]*)((?:\s+"[^"\n]*")*)')
_HEREDOC = re.compile(r"<<-?([A-Za-z_]\w*)[ \t]*\n")
_VAR_REF = re.compile(r"var\.([A-Za-z_][\w-]*)")
_VAR_INTERPOLATION = re.compile(r"\$\{var\.([A-Za-z_][\w-]*)\}")
_WHITESPACE = re.compile(r"\s*")
_JSON_DECODE = json.JSONDecoder().raw_decode
_ENV_QUOTED = re.compile(r"([\"'])(.*?)\1")
_ENV_COMMENT = re.compile(r"\s+#")


def analyse_config(root: Path, files: list[str]) -> dict:
    """Inventory the in-scope configuration and infrastructure files under ``root``.

    ``files`` holds Target-relative POSIX paths (absolute paths are made relative). Callers apply
    exclusions first; nothing outside ``files`` is read.
    """
    rels = sorted({_relative(root, name) for name in files})
    return {
        "docker": [_dockerfile(rel, _read(root, rel)) for rel in rels if _is_dockerfile(rel)],
        "config_files": _config_files(root, rels),
        "app_json": _app_json(root, rels),
        "env_files": _env_files(root, rels),
        "terraform": _terraform(root, rels),
    }


def _relative(root: Path, name: str) -> str:
    if Path(name).is_absolute():
        return Path(name).relative_to(root).as_posix()
    return PurePosixPath(name).as_posix()


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8-sig", errors="replace")


def _coord(rel: str, start: int, end: int) -> dict:
    return {"file": rel, "start_line": start, "end_line": end}


def _line_count(text: str) -> int:
    return max(1, text.count("\n") + (0 if text.endswith("\n") else 1))


def _line(newlines: list[int], offset: int) -> int:
    """1-based line of a character offset, given the offsets of every newline."""
    return bisect.bisect_left(newlines, offset) + 1


def _mask_value(name: str, value: str) -> str:
    """Mask a value. Under a secret-named key the whole value is replaced, else value-level rules apply."""
    if value and _secret_name(name):
        return _SECRET
    return mask_for_report(value)


@lru_cache(maxsize=None)
def _secret_name(name: str) -> bool:
    """True when the masker's key-based rule treats values under this key as secrets."""
    probe = f'{name}="x"'
    return mask_for_report(probe) != probe


def _normalise(name: str, value):
    """Copy an HCL body: drop parser metadata, mask string values and unwrap ``${expr}`` references."""
    if isinstance(value, dict):
        return {key: _normalise(key, item) for key, item in value.items() if not key.startswith("__")}
    if isinstance(value, list):
        return [_normalise(name, item) for item in value]
    if isinstance(value, str):
        masked = _mask_value(name, value)
        whole = re.fullmatch(r"\$\{([^{}]*)\}", masked)
        return whole.group(1) if whole else masked
    return value


def _leaf_records(rel: str, leaves) -> list[dict]:
    records = []
    for path, value, start, end in leaves:
        name = next((part for part in reversed(path) if not part.isdigit()), "")
        records.append(
            {"file": rel, "key": ".".join(path), "value": _mask_value(name, value), "source": _coord(rel, start, end)}
        )
    return records


# Docker


def _is_dockerfile(rel: str) -> bool:
    name = PurePosixPath(rel).name
    return name == "Dockerfile" or name.startswith("Dockerfile.") or name.endswith(".Dockerfile")


def _dockerfile(rel: str, text: str) -> dict:
    stages: list[dict] = []
    final_user: str | None = None
    user_source: dict | None = None
    expose: list[str] = []
    expose_sources: list[dict] = []
    for joined, start, end in _instructions(text):
        words = joined.split(None, 1)
        if not words:
            continue
        keyword = words[0].upper()
        arguments = words[1].strip() if len(words) > 1 else ""
        source = _coord(rel, start, end)
        if keyword == "FROM":
            # USER and EXPOSE apply per stage, so only the final stage's values are kept.
            final_user, user_source, expose, expose_sources = None, None, [], []
            stages.append(_stage(len(stages), arguments, source))
        elif keyword == "USER" and arguments:
            final_user, user_source = arguments, source
        elif keyword == "EXPOSE":
            for port in arguments.split():
                expose.append(port)
                expose_sources.append(source)
    return {
        "file": rel,
        "stages": stages,
        "final_user": final_user,
        "final_user_source": user_source,
        "expose": expose,
        "expose_sources": expose_sources,
        "source": _coord(rel, 1, _line_count(text)),
    }


def _instructions(text: str):
    """Yield (joined_text, start_line, end_line) per instruction, joining backslash continuations.

    Blank and comment lines are skipped, also inside a continuation, as Docker does.
    """
    pending: list[str] = []
    start = number = 0
    for number, raw in enumerate(text.split("\n"), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if not pending:
            start = number
        continued = line.endswith("\\")
        pending.append(line[:-1].rstrip() if continued else line)
        if not continued:
            yield " ".join(pending), start, number
            pending = []
    if pending:
        yield " ".join(pending), start, number


def _stage(index: int, arguments: str, source: dict) -> dict:
    tokens = [token for token in arguments.split() if not token.startswith("--")]
    name = tokens[2] if len(tokens) == 3 and tokens[1].upper() == "AS" else str(index)
    return {"name": name, "base_image": tokens[0] if tokens else "", "source": source}


# config/*.yml


def _config_files(root: Path, rels: list[str]) -> list[dict]:
    records: list[dict] = []
    for rel in rels:
        path = PurePosixPath(rel)
        if path.parent.as_posix() == "config" and path.suffix in (".yml", ".yaml"):
            records.extend(_leaf_records(rel, _yaml_leaves(_read(root, rel))))
    return records


def _yaml_leaves(text: str):
    """Yield (path, value, start_line, end_line) for each scalar of each YAML document."""
    for document in yaml.compose_all(text, Loader=yaml.SafeLoader):
        if document is not None:
            yield from _yaml_walk(document, (), frozenset())


def _yaml_walk(node, path: tuple[str, ...], ancestors: frozenset):
    if isinstance(node, yaml.ScalarNode):
        yield path, node.value, node.start_mark.line + 1, _yaml_end_line(node)
    elif id(node) not in ancestors:  # an alias can make a node its own descendant
        inner = ancestors | {id(node)}
        if isinstance(node, yaml.MappingNode):
            for key, value in node.value:
                if not isinstance(key, yaml.ScalarNode):
                    continue
                child = path + (key.value,)
                if isinstance(value, yaml.ScalarNode):
                    yield child, value.value, key.start_mark.line + 1, _yaml_end_line(value)
                else:
                    yield from _yaml_walk(value, child, inner)
        elif isinstance(node, yaml.SequenceNode):
            for index, item in enumerate(node.value):
                yield from _yaml_walk(item, path + (str(index),), inner)


def _yaml_end_line(node) -> int:
    mark = node.end_mark
    # A block scalar can end at column 0 of the following line.
    return mark.line if mark.column == 0 and mark.line > node.start_mark.line else mark.line + 1


# app.json


def _app_json(root: Path, rels: list[str]) -> list[dict]:
    if "app.json" not in rels:
        return []
    return _leaf_records("app.json", _json_leaves(_read(root, "app.json")))


def _json_leaves(text: str):
    """Yield (path, value_text, start_line, end_line) for each scalar of a JSON document."""
    newlines = [i for i, ch in enumerate(text) if ch == "\n"]
    leaves: list[tuple] = []

    def skip(i: int) -> int:
        return _WHITESPACE.match(text, i).end()

    def walk(i: int, path: tuple[str, ...], start: int) -> int:
        i = skip(i)
        if text[i] == "{":
            i = skip(i + 1)
            while text[i] != "}":
                key_at = i
                key, i = _JSON_DECODE(text, i)
                i = walk(skip(i) + 1, path + (key,), key_at)
                i = skip(i)
                if text[i] == ",":
                    i = skip(i + 1)
            return i + 1
        if text[i] == "[":
            i = skip(i + 1)
            index = 0
            while text[i] != "]":
                i = walk(i, path + (str(index),), i)
                index += 1
                i = skip(i)
                if text[i] == ",":
                    i = skip(i + 1)
            return i + 1
        value, end = _JSON_DECODE(text, i)
        text_value = value if isinstance(value, str) else json.dumps(value)
        leaves.append((path, text_value, _line(newlines, start), _line(newlines, end - 1)))
        return end

    walk(0, (), 0)
    return leaves


# .env files


def _env_files(root: Path, rels: list[str]) -> list[dict]:
    records: list[dict] = []
    for rel in rels:
        if PurePosixPath(rel).name.startswith(".env"):
            records.extend(_env_entries(rel, _read(root, rel)))
    return records


def _env_entries(rel: str, text: str) -> list[dict]:
    records = []
    for number, raw in enumerate(text.split("\n"), 1):
        line = re.sub(r"^export\s+", "", raw.strip())
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        key = key.strip()
        if not sep or not key:
            continue
        value = _env_value(value.strip())
        records.append(
            {
                "file": rel,
                "key": key,
                "value_masked": _mask_value(key, value),
                "source": _coord(rel, number, number),
            }
        )
    return records


def _env_value(raw: str) -> str:
    quoted = _ENV_QUOTED.match(raw)
    if quoted:
        return quoted.group(2)
    return _ENV_COMMENT.split(raw, maxsplit=1)[0].rstrip()


# Terraform


class _Block(NamedTuple):
    kind: str
    labels: tuple[str, ...]
    body: dict
    source: dict


def _terraform(root: Path, rels: list[str]) -> list[dict]:
    """Inventory Terraform providers, the variables they read, and resources, grouped per module.

    Identical declarations (same type, name, attributes and facts) merge into one record whose
    ``sources`` lists every occurrence.
    """
    modules: dict[str, list[_Block]] = {}
    for rel in rels:
        if rel.endswith(".tf"):
            directory = PurePosixPath(rel).parent.as_posix()
            modules.setdefault(directory, []).extend(_terraform_blocks(rel, _read(root, rel)))
    records: dict[str, dict] = {}
    for directory in sorted(modules):
        _add_module(records, modules[directory])
    return list(records.values())


def _terraform_blocks(rel: str, text: str) -> list[_Block]:
    lines = text.split("\n")
    blocks: list[_Block] = []
    for header, start, end in _top_level_blocks(text):
        match = _BLOCK_HEADER.fullmatch(header.strip())
        if not match or match.group(1) not in _BLOCK_LABELS:
            continue
        kind = match.group(1)
        labels = tuple(re.findall(r'"([^"\n]*)"', match.group(2)))
        if len(labels) != _BLOCK_LABELS[kind]:
            continue
        parsed = hcl2.loads("\n".join(lines[start - 1 : end]), serialization_options=_HCL_OPTIONS)
        node = parsed[kind][0]
        for label in labels:
            node = node[label]
        blocks.append(_Block(kind, labels, _normalise("", node), _coord(rel, start, end)))
    return blocks


def _add_module(records: dict[str, dict], blocks: list[_Block]) -> None:
    variables = {
        block.labels[0]: block.body["default"]
        for block in blocks
        if block.kind == "variable" and "default" in block.body and _is_static(block.body["default"])
    }
    providers = [block for block in blocks if block.kind == "provider"]
    default = next((block for block in providers if "alias" not in block.body), None)
    region = _resolve(default.body["region"], variables) if default and "region" in default.body else None
    # Only variables that a provider reads for its region are inventoried.
    needed = {_variable_name(block.body.get("region")) for block in providers} - {None}
    for block in blocks:
        if block.kind == "provider":
            facts = {"region": _resolve(block.body["region"], variables)} if "region" in block.body else {}
            _add(records, "provider", block.labels[0], block.body, facts, block.source)
        elif block.kind == "variable" and block.labels[0] in needed:
            _add(records, "variable", block.labels[0], block.body, {}, block.source)
        elif block.kind == "resource":
            rtype, name = block.labels
            facts = _resource_facts(rtype, block.body, variables, region)
            _add(records, rtype, name, block.body, facts, block.source)


def _add(records: dict[str, dict], rtype: str, name: str, attributes: dict, facts: dict, source: dict) -> None:
    key = json.dumps([rtype, name, attributes, facts], sort_keys=True)
    if key not in records:
        records[key] = {"type": rtype, "name": name, "attributes": attributes, "facts": facts, "sources": []}
    records[key]["sources"].append(source)


def _resource_facts(rtype: str, body: dict, variables: dict, region) -> dict:
    facts = {} if region is None else {"region": region}

    def put(fact: str, key: str) -> None:
        if key in body:
            facts[fact] = _resolve(body[key], variables)

    if rtype == "aws_cloudwatch_log_group":
        put("log_group", "name")
        put("retention_in_days", "retention_in_days")
    elif rtype == "aws_efs_file_system":
        put("encrypted", "encrypted")
    elif rtype == "aws_subnet":
        put("map_public_ip_on_launch", "map_public_ip_on_launch")
    elif rtype == "aws_ecs_service":
        network = next(iter(_blocks(body, "network_configuration")), {})
        if "assign_public_ip" in network:
            facts["assign_public_ip"] = _resolve(network["assign_public_ip"], variables)
    elif rtype == "aws_security_group":
        facts["ingress"] = [_rule(rule, variables) for rule in _blocks(body, "ingress")]
        facts["egress"] = [_rule(rule, variables) for rule in _blocks(body, "egress")]
    return facts


def _rule(rule: dict, variables: dict) -> dict:
    facts = {
        key: _resolve(rule[key], variables)
        for key in ("from_port", "to_port", "protocol", "cidr_blocks")
        if key in rule
    }
    groups = _as_list(rule.get("security_groups", [])) + _as_list(rule.get("source_security_group_id", []))
    if groups:
        facts["source_security_group"] = _resolve(groups, variables)
    return facts


def _blocks(body: dict, key: str) -> list[dict]:
    items = _as_list(body.get(key, []))
    return [item for item in items if isinstance(item, dict)]


def _as_list(value) -> list:
    return value if isinstance(value, list) else [value]


def _variable_name(value) -> str | None:
    match = _VAR_REF.fullmatch(value) if isinstance(value, str) else None
    return match.group(1) if match else None


def _is_static(value) -> bool:
    if isinstance(value, list):
        return all(_is_static(item) for item in value)
    if isinstance(value, dict):
        return all(_is_static(item) for item in value.values())
    if isinstance(value, str):
        return "${" not in value and _VAR_REF.fullmatch(value) is None
    return True


def _resolve(value, variables: dict):
    """Replace ``var.X`` references whose default is static. Unknown references stay as written."""
    if isinstance(value, list):
        return [_resolve(item, variables) for item in value]
    if not isinstance(value, str):
        return value
    whole = _VAR_REF.fullmatch(value)
    if whole and whole.group(1) in variables:
        return variables[whole.group(1)]
    return _VAR_INTERPOLATION.sub(
        lambda match: _text(variables[match.group(1)]) if match.group(1) in variables else match.group(0),
        value,
    )


def _text(value) -> str:
    return str(value).lower() if isinstance(value, bool) else str(value)


def _top_level_blocks(text: str) -> list[tuple[str, int, int]]:
    """Return (header, start_line, end_line) per top-level block, matching braces outside comments and strings."""
    code = _code_view(text)
    newlines = [i for i, ch in enumerate(text) if ch == "\n"]
    blocks: list[tuple[str, int, int]] = []
    depth = 0
    opened = 0
    for index, char in enumerate(code):
        if char == "{":
            if depth == 0:
                opened = index
            depth += 1
        elif char == "}" and depth:
            depth -= 1
            if depth == 0:
                line_start = text.rfind("\n", 0, opened) + 1
                blocks.append((text[line_start:opened], _line(newlines, line_start), _line(newlines, index)))
    return blocks


def _code_view(text: str) -> str:
    """Return text with comments, template contents and heredoc bodies blanked.

    Offsets and newlines are preserved, so braces inside those regions cannot close a block.
    """
    chars = list(text)
    size = len(text)
    i = 0
    while i < size:
        if text.startswith(("#", "//"), i):
            stop = text.find("\n", i)
            stop = size if stop < 0 else stop
            _blank(chars, i, stop)
            i = stop
        elif text.startswith("/*", i):
            stop = text.find("*/", i + 2)
            stop = size if stop < 0 else stop + 2
            _blank(chars, i, stop)
            i = stop
        elif text[i] == '"':
            end = _template_end(text, i)
            _blank(chars, i + 1, end)
            i = end + 1 if end < size and text[end] == '"' else end
        elif text.startswith("<<", i) and (heredoc := _HEREDOC.match(text, i)):
            body = heredoc.end()
            stop = _heredoc_end(text, body, heredoc.group(1))
            _blank(chars, body, stop)
            i = stop
        else:
            i += 1
    return "".join(chars)


def _blank(chars: list[str], start: int, stop: int) -> None:
    for k in range(start, stop):
        if chars[k] != "\n":
            chars[k] = " "


def _template_end(text: str, start: int) -> int:
    """Index of the quote closing the template opened at ``start``, or of the newline or end where it stops."""
    i = start + 1
    while i < len(text):
        char = text[i]
        if char in '"\n':
            return i
        if char == "\\":
            i += 2
        elif char in "$%" and text.startswith("{", i + 1):
            i = _interpolation_end(text, i + 2)
        else:
            i += 1
    return len(text)


def _interpolation_end(text: str, start: int) -> int:
    """Index just past the brace closing an interpolation whose body starts at ``start``."""
    depth = 1
    i = start
    while i < len(text):
        char = text[i]
        if char == '"':
            i = _template_end(text, i) + 1
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return len(text)


def _heredoc_end(text: str, pos: int, marker: str) -> int:
    """Index of the end of the heredoc's terminator line, or the end of text if unterminated."""
    while pos < len(text):
        eol = text.find("\n", pos)
        eol = len(text) if eol < 0 else eol
        if text[pos:eol].strip() == marker:
            return eol
        pos = eol + 1
    return len(text)
