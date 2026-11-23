"""LLM assessment session with masked egress and cache-only operation."""
import json
import os
import re

from auditor.masking import mask_for_egress
from .cache import Cache, cache_key
from .prompts import PROMPT_VERSION, system_prompt, valid_value
from .providers import PROVIDERS

DEFAULT_MODELS = {'anthropic': 'claude-haiku-5-5', 'openai': 'gpt-6.1-terra', 'gemini': 'gemini-2.5-flash', 'ollama': 'llama3.1', 'omp': 'anthropic/claude-opus-5-5'}


def _mask_object(value):
    if isinstance(value, str):
        return mask_for_egress(value)
    if isinstance(value, list):
        return [_mask_object(item) for item in value]
    if isinstance(value, dict):
        return {
            mask_for_egress(str(key)): (
                '«SECRET»' if re.search(r'password|passwd|secret|token|api[_-]?key|private[_ -]?key', str(key), re.I)
                else '«BIOMETRIC»' if re.search(r'face[_ -]?(?:encoding|template)|embedding|biometric|selfie|liveness[_ -]?frame|fingerprint|iris', str(key), re.I)
                else _mask_object(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        masked = mask_for_egress(str(value))
        return value if masked == str(value) else masked
    return value

class LLMSession:
    def __init__(self, cache_dir, provider):
        self.cache = Cache(cache_dir)
        self.provider = provider
        self.mode = 'cache-only'
        self.reason = 'Provider has not been probed'
        self.cache_hits = self.cache_misses = self.not_assessed = 0

    @classmethod
    def from_env(cls, cache_dir, provider=None, model=None):
        name = provider or os.environ.get('DPDP_LLM_PROVIDER') or 'omp'
        if name not in PROVIDERS:
            raise ValueError(f'Unknown LLM provider: {name}')
        selected_model = model or os.environ.get('DPDP_LLM_MODEL') or DEFAULT_MODELS[name]
        return cls(cache_dir, PROVIDERS[name](selected_model))

    def probe(self):
        available, reason = self.provider.available()
        self.mode = 'live' if available else 'cache-only'
        self.reason = None if available else (reason or 'Provider unavailable')

    def ask(self, role, snippet, context=None):
        version = PROMPT_VERSION[role]
        masked = mask_for_egress(snippet)
        masked_context = _mask_object(context)
        key = cache_key(masked, version, self.provider.model, masked_context)
        cached = self.cache.get(key)
        if (isinstance(cached, dict) and cached.get('model') == self.provider.model
                and cached.get('prompt_version') == version and cached.get('provider') in PROVIDERS
                and valid_value(role, cached.get('value'), masked_context)):
            self.cache_hits += 1
            return {'status': 'assessed', 'value': cached['value'], 'cache_key': key, 'provider': cached['provider'], 'model': cached['model'], 'prompt_version': version}
        self.cache_misses += 1
        if self.mode == 'live':
            try:
                payload = json.dumps({'evidence': masked, 'context': masked_context}, ensure_ascii=False)
                value = _mask_object(json.loads(self.provider.complete(system_prompt(role), payload)))
                if not valid_value(role, value, masked_context):
                    raise ValueError('Invalid response shape')
                record = {'input': masked, 'context': masked_context, 'value': value, 'provider': self.provider.name, 'model': self.provider.model, 'prompt_version': version}
                self.cache.put(key, record)
                return {'status': 'assessed', 'value': value, 'cache_key': key, 'provider': self.provider.name, 'model': self.provider.model, 'prompt_version': version}
            except Exception:
                # Provider errors can contain request data or Authentication Secrets; never retain them.
                pass
        self.not_assessed += 1
        return {'status': 'not assessed', 'cache_key': key}

    def summary(self):
        return {'mode': self.mode, 'provider': self.provider.name, 'model': self.provider.model, 'prompt_versions': dict(PROMPT_VERSION), 'cache_hits': self.cache_hits, 'cache_misses': self.cache_misses, 'not_assessed': self.not_assessed, 'reason': self.reason}
