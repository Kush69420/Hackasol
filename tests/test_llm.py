import json
import subprocess
from pathlib import Path

import httpx
import jsonschema
import pytest

from auditor.llm import LLMSession, _mask_object
from auditor.llm import prompts
from auditor.llm.providers import Anthropic, Gemini, Ollama, Omp, OpenAI
from auditor.llm.cache import cache_key
from auditor.masking import contains_unmasked_material, mask_for_egress, mask_for_report
from auditor.registry import load_registry


# Twelve digits with a valid Verhoeff check digit.
AADHAAR = '1234 5678 9010'
PAN = 'ABCDE1234F'
EMAIL = 'alice@example.com'
JWT = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjMifQ.signature'
PASSWORD = 'very-private-password'
EVIDENCE = f'{AADHAAR}\n{PAN}\n{EMAIL}\n{JWT}\npassword="{PASSWORD}"'
PROVISION = 'DPDP-Act-8(5)'
VALUE = {'verdict': 'true-positive', 'reason': 'Evidence supports the Finding.', 'citations': [PROVISION]}


@pytest.mark.parametrize('adapter', [Anthropic, OpenAI, Gemini, Ollama, Omp])
def test_provider_masking_and_cache_replay(adapter, tmp_path, monkeypatch):
    sent = []
    requests = []
    monkeypatch.setattr('auditor.llm.providers.shutil.which', lambda _: '/usr/bin/omp')
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'test-auth')
    monkeypatch.setenv('OPENAI_API_KEY', 'test-auth')
    monkeypatch.setenv('GEMINI_API_KEY', 'test-auth')
    def handler(request):
        if request.method == 'GET':
            return httpx.Response(200, json={})
        requests.append(request)
        sent.append(request.content.decode())
        content = json.dumps(VALUE)
        body = {'content': [{'type': 'text', 'text': content}], 'choices': [{'message': {'content': content}}], 'candidates': [{'content': {'parts': [{'text': content}]}}], 'message': {'content': content}}
        return httpx.Response(200, json=body)
    def runner(args, **kwargs):
        sent.append(' '.join(args) + '\n' + kwargs.get('input', ''))
        return subprocess.CompletedProcess(args, 0, json.dumps(VALUE), '')
    provider = adapter('example-model', runner=runner) if adapter is Omp else adapter('example-model', client=httpx.Client(transport=httpx.MockTransport(handler)))
    session = LLMSession(tmp_path, provider)
    session.probe()
    context = {'contact': EMAIL, 'password': PASSWORD, 'provisions': [{'id': PROVISION}]}
    result = session.ask('triage', EVIDENCE, context)
    assert result['status'] == 'assessed'
    assert result['value'] == VALUE
    if adapter is Omp:
        assert '--no-session' in sent[-1] and '--model example-model' in sent[-1]
    else:
        request = requests[-1]
        body = json.loads(request.content)
        assert request.method == 'POST'
        assert request.url.path.endswith({Anthropic: '/messages', OpenAI: '/chat/completions', Gemini: ':generateContent', Ollama: '/chat'}[adapter])
        if adapter is not Gemini:
            assert body['model'] == 'example-model'
    assert sent
    for data in sent + [p.read_text() for p in tmp_path.glob('*.json')]:
        for sensitive in (AADHAAR, PAN, EMAIL, JWT, PASSWORD):
            assert sensitive not in data
    session.mode = 'cache-only'
    session.reason = 'unreachable'
    assert session.ask('triage', EVIDENCE, dict(reversed(tuple(context.items())))) == result
    assert session.ask('triage', EVIDENCE + '\nchanged')['status'] == 'not assessed'
    monkeypatch.setitem(prompts.PROMPT_VERSION, 'triage', 'triage-v1')
    assert session.ask('triage', EVIDENCE, context)['status'] == 'not assessed'
    monkeypatch.setitem(prompts.PROMPT_VERSION, 'triage', 'triage-v2')
    provider.model = 'another-model'
    assert session.ask('triage', EVIDENCE, context)['status'] == 'not assessed'
    schema = json.loads(Path('auditor/schema/report.schema.json').read_text())
    jsonschema.validate(session.summary(), schema['properties']['llm'])


def test_masking_modes_and_line_anchors():
    text = EVIDENCE + '\n-----BEGIN PRIVATE KEY-----\nabc\ndef\n-----END PRIVATE KEY-----'
    report = mask_for_report(text)
    egress = mask_for_egress(text)
    assert text.count('\n') == report.count('\n') == egress.count('\n')
    assert EMAIL in report and EMAIL not in egress
    for value in (AADHAAR, PAN, JWT, PASSWORD, 'abc\ndef'):
        assert value not in report and value not in egress
    assert '«AADHAAR»' in report

def test_fix_patch_check_flags_secret_values_but_not_code_references():
    assert contains_unmasked_material('password = "hunter2xyz"')
    assert not contains_unmasked_material('const currentPassword = query.current')
    assert not contains_unmasked_material('password = readPassword()')
    # Masking itself stays conservative at the egress boundary.
    for mask in (mask_for_report, mask_for_egress):
        assert 'hunter2xyz' not in mask('password = "hunter2xyz"')
        assert 'query.current' not in mask('const currentPassword = query.current')

def test_biometric_masking_payloads_and_keyed_arrays(tmp_path):
    payload = 'A' * 240
    image = 'data:image/png;base64,' + payload
    for mask in (mask_for_report, mask_for_egress):
        assert payload not in mask(image)
        assert '«BIOMETRIC_PAYLOAD»' in mask(image)
        assert '«BINARY»' in mask(payload)
    sent = []
    class Provider:
        name = 'ollama'
        model = 'synthetic'
        def available(self): return True, None
        def complete(self, system, user):
            sent.append(user)
            return json.dumps(VALUE)
    session = LLMSession(tmp_path, Provider())
    session.probe()
    session.ask('triage', image, {'Face_Encoding': [0.123456, 0.987654], 'selfie': 'synthetic-face'})
    assert sent and payload not in sent[0] and 'synthetic-face' not in sent[0]
    assert '0.123456' not in sent[0] and '«BIOMETRIC»' in sent[0]

def test_url_credentials_are_masked_before_llm_egress(tmp_path):
    password = 'pw' + 'Synthetic9x'
    token = 'tok' + '_' + 'A1b2C3d4E5f6G7h8'
    urls = [f'postgres://admin:{password}@db.internal:5432/app',
            f'DATABASE_URL="mysql://root:{password}@localhost/app"',
            f'redis://:{password}@cache:6379/0',
            f'https://{token}@github.com/org/repo.git',
            'ssh://dep%2Floy@127.0.0.1/repo', 'ssh://x@host/repo']
    for mask in (mask_for_report, mask_for_egress):
        for url in urls:
            masked = mask(url)
            assert password not in masked and token not in masked and 'admin' not in masked, masked
            assert '«URL_CREDENTIALS»@' in masked
            assert 'dep%2Floy' not in masked and '://x@' not in masked
    # URLs without credentials are untouched.
    assert mask_for_egress('https://example.com:8443/path?q=1') == 'https://example.com:8443/path?q=1'
    sent = []
    class Provider:
        name = 'ollama'
        model = 'synthetic'
        def available(self): return True, None
        def complete(self, system, user):
            sent.append(user)
            return json.dumps(VALUE)
    session = LLMSession(tmp_path, Provider())
    session.probe()
    session.ask('triage', '\n'.join(urls), {'db': urls[1]})
    assert sent and password not in sent[0] and token not in sent[0] and 'dep%2Floy' not in sent[0]


def test_invalid_provider_response_is_not_assessed(tmp_path):
    class Invalid:
        name = 'openai'
        model = 'example'
        def available(self): return True, None
        def complete(self, system, user): return '{"verdict":"bad", "reason":"x"}'
    session = LLMSession(tmp_path, Invalid())
    session.probe()
    assert session.ask('triage', 'Evidence')['status'] == 'not assessed'
    assert not list(tmp_path.glob('*.json'))


def test_registry_context_preserves_every_provision():
    context = {'provisions': [dict(id=p.id, citation=p.citation, title=p.title, text=p.excerpt)
                              for p in load_registry().values()]}
    assert _mask_object(context) == context


@pytest.mark.parametrize('role, value', [
    ('triage', {**VALUE, 'citations': ['CWE-639']}),
    ('consent', {'assessment': 'Incomplete.', 'criteria': [], 'citations': ['CWE-639']}),
    ('consent', {'assessment': 'Incomplete.', 'criteria': [
        {'criterion': 'recorded', 'reading': 'not determinable', 'reason': 'No record shown.',
         'citations': ['CWE-639']},
    ], 'citations': [PROVISION]}),
])
def test_out_of_set_citation_is_not_assessed(tmp_path, role, value):
    provider = Omp('test', runner=lambda args, **_: subprocess.CompletedProcess(args, 0, json.dumps(value), ''))
    session = LLMSession(tmp_path, provider)
    session.mode = 'live'
    context = {'provisions': [{'id': PROVISION}]}
    result = session.ask(role, 'Evidence', context)
    assert result['status'] == 'not assessed'
    assert session.cache.get(result['cache_key']) is None

    session.cache.put(result['cache_key'], {
        'provider': 'omp', 'model': 'test', 'prompt_version': prompts.PROMPT_VERSION[role], 'value': value,
    })
    session.mode = 'cache-only'
    assert session.ask(role, 'Evidence', context)['status'] == 'not assessed'


def test_v1_triage_cache_value_is_not_accepted_for_v2(tmp_path):
    session = LLMSession(tmp_path, Omp('test'))
    context = {'provisions': [{'id': PROVISION}]}
    old_value = {'verdict': 'true-positive', 'reason': 'Evidence supports the Finding.'}
    assert prompts.PROMPT_VERSION['triage'] == 'triage-v2'
    for version in ('triage-v1', 'triage-v2'):
        key = cache_key('Evidence', version, 'test', context)
        session.cache.put(key, {'provider': 'omp', 'model': 'test', 'prompt_version': version, 'value': old_value})
        assert session.ask('triage', 'Evidence', context)['status'] == 'not assessed'


def test_changing_provisions_changes_cache_key(tmp_path):
    session = LLMSession(tmp_path, Omp('test'))
    first = session.ask('triage', 'Evidence', {'provisions': [{'id': PROVISION}]})
    second = session.ask('triage', 'Evidence', {'provisions': [{'id': 'CWE-639'}]})
    assert first['cache_key'] != second['cache_key']


def test_omp_json_inside_markdown_fence_is_assessed(tmp_path):
    value = {'data_category': 'Contact', 'reason': 'An email address column.'}
    fenced = '```json\n' + json.dumps(value) + '\n```\n'
    session = LLMSession(tmp_path, Omp('test', runner=lambda args, **_: subprocess.CompletedProcess(args, 0, fenced, '')))
    session.mode = 'live'
    result = session.ask('classification', 'column email')
    assert result['status'] == 'assessed'
    assert result['value'] == value
