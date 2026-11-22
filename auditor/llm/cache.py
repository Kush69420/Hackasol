"""On-disk cache containing only masked data and provenance."""
import hashlib
import json
from pathlib import Path


def cache_key(masked_snippet, prompt_version, model, context=None):
    material = masked_snippet + '\0' + prompt_version + '\0' + model
    if context is not None:
        material += '\0' + json.dumps(context, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    return hashlib.sha256(material.encode()).hexdigest()


class Cache:
    def __init__(self, directory: Path):
        self.directory = Path(directory)

    def get(self, key):
        try:
            return json.loads((self.directory / (key + '.json')).read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return None

    def put(self, key, record):
        self.directory.mkdir(parents=True, exist_ok=True)
        (self.directory / (key + '.json')).write_text(json.dumps(record, ensure_ascii=False), encoding='utf-8')
