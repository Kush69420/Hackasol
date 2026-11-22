"""Resolve declared Terraform storage regions without linking log groups to Elements.

Variable defaults describe configuration, not necessarily deployed settings.
"""

from pathlib import PurePosixPath
import re


_STORAGE = {"aws_efs_file_system", "aws_db_instance", "aws_rds_cluster", "aws_s3_bucket", "aws_ebs_volume", "aws_fsx_lustre_file_system", "aws_fsx_windows_file_system"}
_VARIABLE = re.compile(r"^(?:\$\{)?var\.([\w-]+)(?:\})?$")


def _module(source):
    return str(PurePosixPath(source["file"]).parent)


def _add_unique(items, values):
    for value in values:
        if value not in items:
            items.append(value)


def storage_regions(inventory):
    records = inventory.get("terraform", [])
    providers = [r for r in records if r.get("type") == "provider"]
    variables = [r for r in records if r.get("type") == "variable"]
    regions = {}
    for provider in providers:
        attrs = provider.get("attributes", {})
        expression = attrs.get("region")
        match = _VARIABLE.fullmatch(expression) if isinstance(expression, str) else None
        for source in provider.get("sources", []):
            module = _module(source)
            resolved_from = [source]
            region = None
            if match:
                for variable in variables:
                    if variable.get("name") != match.group(1):
                        continue
                    sources = [s for s in variable.get("sources", []) if _module(s) == module]
                    default = variable.get("attributes", {}).get("default")
                    if sources and isinstance(default, str) and not re.search(r"\$\{|\bvar\.", default):
                        region = default
                        _add_unique(resolved_from, sources)
                        break
            elif isinstance(expression, str) and expression and not re.search(r"\$\{|\bvar\.|\(", expression):
                region = expression
            bucket = regions.setdefault(region, {"region": region, "resolved_from": [], "storage": [], "log_groups": []})
            _add_unique(bucket["resolved_from"], resolved_from)
            alias = attrs.get("alias")
            provider_ref = provider.get("name", "") + ("." + alias if alias else "")
            for record in records:
                kind = record.get("type", "")
                if kind not in _STORAGE and kind != "aws_cloudwatch_log_group":
                    continue
                if not kind.startswith(provider.get("name", "") + "_"):
                    continue
                reference = record.get("attributes", {}).get("provider")
                if (reference or provider.get("name")) != provider_ref:
                    continue
                sources = [s for s in record.get("sources", []) if _module(s) == module]
                if not sources:
                    continue
                if kind == "aws_cloudwatch_log_group":
                    item = {"name": record.get("name"), "retention_in_days": record.get("facts", {}).get("retention_in_days"), "sources": sources}
                    target = bucket["log_groups"]
                else:
                    item = {"type": kind, "name": record.get("name"), "sources": sources}
                    target = bucket["storage"]
                existing = next((x for x in target if all(x.get(k) == v for k, v in item.items() if k != "sources")), None)
                if existing:
                    _add_unique(existing["sources"], sources)
                else:
                    target.append(item)
    return list(regions.values())
