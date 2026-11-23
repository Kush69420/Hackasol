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


ROLES = tuple(PROMPT_VERSION)


def parse_role_models(specs: list[str] | None) -> dict[str, tuple[str, str]]:
    """['classification=ollama:qwen3.8:27b'] -> {'classification': ('ollama', 'qwen3.8:27b')}.

    Split role at the first '=', provider at the first ':'; model may contain ':'.
    ValueError on unknown role, unknown provider (not in PROVIDERS), empty model, or a role given twice.
    """
    routes = {}
    for spec in specs or []:
        role, equals, target = spec.partition('=')
        provider, colon, model = target.partition(':')
        if not equals or not colon:
            raise ValueError(f'Role model must be ROLE=PROVIDER:MODEL: {spec!r}')
        if role not in ROLES:
            raise ValueError(f'Unknown LLM role: {role}')
        if provider not in PROVIDERS:
            raise ValueError(f'Unknown LLM provider: {provider}')
        if not model.strip():
            raise ValueError(f'Empty model for LLM role {role}')
        if role in routes:
            raise ValueError(f'LLM role given twice: {role}')
        routes[role] = (provider, model)
    return routes


def role_overrides(llm):
    """Roles whose provider or model differs from the top-level route; empty when one route serves every role."""
    return {role: route for role, route in llm['roles'].items()
            if (route['provider'], route['model']) != (llm['provider'], llm['model'])}


class LLMSession:
    def __init__(self, cache_dir, provider, role_providers=None):
        """`provider` answers every role unless `role_providers` routes that role to another provider."""
        self.cache = Cache(cache_dir)
        self.provider = provider
        self.role_providers = {role: (role_providers or {}).get(role, provider) for role in ROLES}
        self.role_modes = {role: 'cache-only' for role in ROLES}
        self.role_reasons = {role: 'Provider has not been probed' for role in ROLES}
        self._settle()
        self.cache_hits = self.cache_misses = self.not_assessed = 0

    @classmethod
    def from_env(cls, cache_dir, provider=None, model=None, role_models=None):
        name = provider or os.environ.get('DPDP_LLM_PROVIDER') or 'omp'
        if name not in PROVIDERS:
            raise ValueError(f'Unknown LLM provider: {name}')
        selected_model = model or os.environ.get('DPDP_LLM_MODEL') or DEFAULT_MODELS[name]
        instances = {}

        def instance(provider_name, provider_model):
            # Routes naming the same provider and model share one instance, so each provider is probed once.
            if provider_name not in PROVIDERS:
                raise ValueError(f'Unknown LLM provider: {provider_name}')
            if (provider_name, provider_model) not in instances:
                instances[(provider_name, provider_model)] = PROVIDERS[provider_name](provider_model)
            return instances[(provider_name, provider_model)]

        default = instance(name, selected_model)
        routes = {role: instance(*route) for role, route in (role_models or {}).items()}
        return cls(cache_dir, default, routes)

    def probe(self):
        """Probe each distinct provider once; a role is live only when the provider serving it is available."""
        outcomes = {}
        for role in ROLES:
            provider = self.role_providers[role]
            if id(provider) not in outcomes:
                outcomes[id(provider)] = provider.available()
            available, reason = outcomes[id(provider)]
            self.role_modes[role] = 'live' if available else 'cache-only'
            self.role_reasons[role] = None if available else (reason or 'Provider unavailable')
        self._settle()

    def force_cache_only(self, reason):
        """Serve every role from the cache; no provider is probed or called."""
        self.role_modes = {role: 'cache-only' for role in ROLES}
        self.role_reasons = {role: reason for role in ROLES}
        self._settle()

    def _settle(self):
        """Live only when every role is live. The reason is the shared cause, or each cause prefixed by the roles it covers."""
        causes = {}
        for role in ROLES:
            if self.role_modes[role] != 'live':
                causes.setdefault(self.role_reasons[role], []).append(role)
        self.mode = 'cache-only' if causes else 'live'
        if not causes:
            self.reason = None
        elif len(causes) == 1 and len(next(iter(causes.values()))) == len(ROLES):
            self.reason = next(iter(causes))
        else:
            self.reason = '; '.join(f"{', '.join(roles)}: {reason}" for reason, roles in causes.items())

    def ask(self, role, snippet, context=None):
        provider = self.role_providers[role]
        version = PROMPT_VERSION[role]
        masked = mask_for_egress(snippet)
        masked_context = _mask_object(context)
        key = cache_key(masked, version, provider.model, masked_context)
        cached = self.cache.get(key)
        if (isinstance(cached, dict) and cached.get('model') == provider.model
                and cached.get('prompt_version') == version and cached.get('provider') in PROVIDERS
                and valid_value(role, cached.get('value'), masked_context)):
            self.cache_hits += 1
            return {'status': 'assessed', 'value': cached['value'], 'cache_key': key, 'provider': cached['provider'], 'model': cached['model'], 'prompt_version': version}
        self.cache_misses += 1
        if self.role_modes[role] == 'live':
            try:
                payload = json.dumps({'evidence': masked, 'context': masked_context}, ensure_ascii=False)
                value = _mask_object(json.loads(provider.complete(system_prompt(role), payload)))
                if not valid_value(role, value, masked_context):
                    raise ValueError('Invalid response shape')
                record = {'input': masked, 'context': masked_context, 'value': value, 'provider': provider.name, 'model': provider.model, 'prompt_version': version}
                self.cache.put(key, record)
                return {'status': 'assessed', 'value': value, 'cache_key': key, 'provider': provider.name, 'model': provider.model, 'prompt_version': version}
            except Exception:
                # Provider errors can contain request data or Authentication Secrets; never retain them.
                pass
        self.not_assessed += 1
        return {'status': 'not assessed', 'cache_key': key}

    def summary(self):
        return {'mode': self.mode, 'provider': self.provider.name, 'model': self.provider.model, 'prompt_versions': dict(PROMPT_VERSION), 'cache_hits': self.cache_hits, 'cache_misses': self.cache_misses, 'not_assessed': self.not_assessed, 'reason': self.reason,
                'roles': {role: {'provider': provider.name, 'model': provider.model, 'mode': self.role_modes[role], 'reason': self.role_reasons[role]}
                          for role, provider in self.role_providers.items()}}
