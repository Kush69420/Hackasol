"""Provider adapters. omp runs `omp -p --no-session --no-tools --model MODEL PROMPT`."""
import os
import shutil
import re
import subprocess
from typing import Protocol
from urllib.parse import quote

import httpx


class Provider(Protocol):
    name: str
    model: str
    def available(self) -> tuple[bool, str | None]: ...
    def complete(self, system: str, user: str) -> str: ...


class HTTPProvider:
    name = ''
    key_env = ''
    base = ''

    def __init__(self, model, client=None):
        self.model = model
        self.client = client or httpx.Client(timeout=30)

    def headers(self):
        return {}

    def available(self):
        if self.key_env and not os.environ.get(self.key_env):
            return False, f'{self.key_env} is not set'
        try:
            response = self.client.get(self.probe_url(), headers=self.headers())
            response.raise_for_status()
            return True, None
        except (httpx.HTTPError, ValueError):
            return False, f'{self.name} is unreachable or authentication failed'

    def probe_url(self):
        return self.base + '/models'

    def post(self, url, payload):
        response = self.client.post(url, headers=self.headers(), json=payload)
        response.raise_for_status()
        return response.json()


class Anthropic(HTTPProvider):
    name, key_env, base = 'anthropic', 'ANTHROPIC_API_KEY', 'https://api.anthropic.com/v1'
    def headers(self):
        return {'x-api-key': os.environ.get(self.key_env, ''), 'anthropic-version': '2023-06-01'}
    def complete(self, system, user):
        result = self.post(self.base + '/messages', {'model': self.model, 'max_tokens': 2048, 'system': system, 'messages': [{'role': 'user', 'content': user}]})
        return ''.join(part['text'] for part in result['content'] if part.get('type') == 'text')


class OpenAI(HTTPProvider):
    name, key_env, base = 'openai', 'OPENAI_API_KEY', 'https://api.openai.com/v1'
    def headers(self):
        return {'Authorization': 'Bearer ' + os.environ.get(self.key_env, '')}
    def complete(self, system, user):
        result = self.post(self.base + '/chat/completions', {'model': self.model, 'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': user}], 'response_format': {'type': 'json_object'}})
        return result['choices'][0]['message']['content']


class Gemini(HTTPProvider):
    name, key_env, base = 'gemini', 'GEMINI_API_KEY', 'https://generativelanguage.googleapis.com/v1beta'
    def headers(self):
        return {'x-goog-api-key': os.environ.get(self.key_env, '')}
    def complete(self, system, user):
        result = self.post(self.base + '/models/' + quote(self.model, safe='') + ':generateContent', {'systemInstruction': {'parts': [{'text': system}]}, 'contents': [{'role': 'user', 'parts': [{'text': user}]}], 'generationConfig': {'responseMimeType': 'application/json'}})
        return ''.join(part['text'] for part in result['candidates'][0]['content']['parts'] if 'text' in part)


class Ollama(HTTPProvider):
    name = 'ollama'
    def __init__(self, model, client=None):
        super().__init__(model, client)
        self.base = os.environ.get('OLLAMA_HOST', 'http://localhost:11434').rstrip('/') + '/api'
    def probe_url(self):
        return self.base + '/tags'
    def complete(self, system, user):
        result = self.post(self.base + '/chat', {'model': self.model, 'stream': False, 'format': 'json', 'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': user}]})
        return result['message']['content']


class Omp:
    name = 'omp'
    def __init__(self, model, runner=None):
        self.model = model
        self.runner = runner or subprocess.run
    def available(self):
        if not shutil.which('omp'):
            return False, 'omp is not installed'
        try:
            self.complete('Return only JSON.', '{"probe": true}')
            return True, None
        except (OSError, subprocess.SubprocessError, ValueError):
            return False, 'omp is unreachable or its model is unavailable'
    def complete(self, system, user):
        # The user payload goes on stdin: a consent graph can exceed the kernel's per-argument limit.
        result = self.runner(['omp', '-p', '--no-session', '--no-tools', '--no-extensions', '--no-skills', '--no-rules', '--no-context-files', '--model', self.model, '--system-prompt', system], input=user, capture_output=True, text=True, timeout=120, check=True)
        # omp prints Markdown; a model may wrap its JSON object in one fenced block.
        fenced = re.fullmatch(r'\s*```(?:json)?\s*\n(.*?)\n\s*```\s*', result.stdout, re.S)
        return fenced.group(1) if fenced else result.stdout


PROVIDERS = {cls.name: cls for cls in (Anthropic, OpenAI, Gemini, Ollama, Omp)}
