"""Derive request logging operations from the structured inventory.

Morgan's predefined formats are documented at
https://github.com/expressjs/morgan#predefined-formats. Its :url token logs
req.originalUrl (including the query string), not just the route path.
"""

from __future__ import annotations

import re


_FORMATS = {
    "combined": ["remote-addr", "remote-user", "date", "method", "url", "http-version", "status", "res[content-length]", "referrer", "user-agent"],
    "common": ["remote-addr", "remote-user", "date", "method", "url", "http-version", "status", "res[content-length]"],
    "dev": ["method", "url", "status", "response-time", "res[content-length]"],
    "short": ["remote-addr", "remote-user", "method", "url", "http-version", "status", "res[content-length]", "response-time"],
    "tiny": ["method", "url", "status", "res[content-length]", "response-time"],
}
_TOKEN = re.compile(r":([\w-]+(?:\[[^\]]+\])?)")
_PARAM = re.compile(r"^param:GET\s+([^?]+)\?([^&?]+)$")


def _fields(fmt):
    if not isinstance(fmt, str):
        return []
    return list(_FORMATS[fmt]) if fmt in _FORMATS else list(dict.fromkeys(_TOKEN.findall(fmt)))


def _retention(max_logs, frequency):
    value = str(max_logs or "").strip().lower()
    match = re.fullmatch(r"(\d+)d", value)
    if match:
        return int(match.group(1))
    if not value.isdigit():
        return None
    units = {"daily": 1, "weekly": 7, "hourly": 1 / 24, "monthly": None}
    interval = units.get(str(frequency).lower())
    if interval is None:
        freq = re.fullmatch(r"(\d+)([dhm])", str(frequency).lower())
        if freq:
            interval = int(freq.group(1)) * {"d": 1, "h": 1 / 24, "m": 1 / 1440}[freq.group(2)]
    return int(value) * interval if interval is not None else None


def _profile(inventory, logger):
    stream = logger.get("stream")
    rotations = [r for r in inventory.get("logging", []) if r.get("kind") == "rotation"]
    rotation = next((r for r in rotations if stream and stream == r.get("binding")
                     and r.get("source", {}).get("file") == logger.get("source", {}).get("file")), None)
    return {
        "format": logger.get("format"),
        "fields_logged": _fields(logger.get("format")),
        "file_pattern": rotation.get("filename") if rotation else None,
        "frequency": rotation.get("frequency") if rotation else None,
        "retention_days": _retention(rotation.get("max_logs"), rotation.get("frequency")) if rotation else None,
        "source_morgan": logger.get("source"),
        "source_rotation": rotation.get("source") if rotation else None,
    }


def access_log_profile(inventory):
    """Return the first Morgan profile, or None when no Morgan call is inventoried."""
    logger = next((r for r in inventory.get("logging", []) if r.get("kind") == "morgan"), None)
    return _profile(inventory, logger) if logger else None


def _path(value):
    return value.split("?", 1)[0].rstrip("/") or "/"


def _covered(route, source):
    if route.get("origin") == "swagger-only":
        return False
    return any(m.get("name") == "morgan" and m.get("source") == source
               for m in route.get("middleware", []))


def log_operations(inventory, elements):
    """Find evidenced service collection and Morgan logging for query Elements."""
    steps = []
    loggers = [r for r in inventory.get("logging", []) if r.get("kind") == "morgan"]
    for element in elements:
        match = _PARAM.fullmatch(element.get("id", "")) if element.get("kind") == "route-param" else None
        if not match:
            continue
        path, key = match.groups()
        routes = [r for r in inventory.get("routes", []) if r.get("method") == "GET" and _path(r.get("normalised_path") or r.get("path") or "") == _path(path) and r.get("origin") != "swagger-only"]
        for call in inventory.get("service_calls", []):
            expression = call.get("url_expression") or ""
            if (routes and call.get("http_method") == "GET"
                    and _path(call.get("normalised_path") or "") == _path(path)
                    and re.search(r"[?&]" + re.escape(key) + r"=", expression)):
                steps.append({"element_id": element["id"], "operation": "Collect", "stage": "service", "source": call["source"], "origin": "ts-join", "relation": "evidenced", "note": "Query parameter appended to the request URL."})
        for logger in loggers:
            profile = _profile(inventory, logger)
            if "url" not in profile["fields_logged"] or not any(_covered(r, logger.get("source")) for r in routes):
                continue
            note = (f"Morgan {profile['format']} logs the request URL including its query; "
                    f"file pattern: {profile['file_pattern'] or 'unresolved'}; "
                    f"retention: {str(profile['retention_days']) + ' days' if profile['retention_days'] is not None else 'unresolved'}.")
            steps.append({"element_id": element["id"], "operation": "Log", "stage": "log", "source": logger["source"], "origin": "config", "relation": "evidenced", "note": note})
    return steps
