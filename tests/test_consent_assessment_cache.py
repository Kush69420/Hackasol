import json

from auditor.consent.criteria import assess_consent
from auditor.llm import LLMSession
from test_consent_assessment_criteria import empty_graph


class Provider:
    name = 'ollama'
    model = 'fake'

    def __init__(self):
        self.payloads = []

    def available(self):
        return True, None

    def complete(self, system, payload):
        self.payloads.append(payload)
        context = json.loads(payload)['context']
        citation = 'DPDP-Act-6(1)'
        return json.dumps({
            'assessment': 'Evidence is incomplete.',
            'criteria': [
                {'criterion': criterion, 'reading': 'not determinable',
                 'reason': 'Incomplete Evidence.', 'citations': [citation]}
                for criterion in context['criteria']
            ],
            'citations': [citation],
        })


def test_cache_masked_and_replayed(tmp_path):
    graph = empty_graph()
    graph['banners'] = [{'id': 'b', 'evidence': [{'file': 'index.html', 'start_line': 1, 'end_line': 1,
                                                 'excerpt': 'person@example.com'}]}]
    provider = Provider()
    live = LLMSession(tmp_path, provider)
    live.probe()
    findings = [{'id': 'CON-03-1', 'issue_type': 'CON-03', 'evidence': []}]
    first = assess_consent(graph, findings, live)
    assert provider.payloads and 'person@example.com' not in provider.payloads[0]
    verdict = first['llm_reasoning']
    assert verdict['status'] == 'assessed' and verdict['prompt_version'] == 'consent-v2'
    context = json.loads(provider.payloads[0])['context']
    assert len(context['provisions']) == 24
    assert {'DPDP-Act-4(1)', 'DPDP-Act-6(6)', 'DPDP-Rule-3(a)'} <= {p['id'] for p in context['provisions']}
    assert [item['criterion'] for item in verdict['value']['criteria']] == [row['criterion'] for row in first['criteria']]
    replay = LLMSession(tmp_path, provider)
    second = assess_consent(graph, findings, replay)
    assert second['criteria'] == first['criteria']
    assert second['llm_reasoning'] == first['llm_reasoning']
    assert findings == [{'id': 'CON-03-1', 'issue_type': 'CON-03', 'evidence': []}]
    graph['limitations'].append('different input')
    missed = assess_consent(graph, [], replay)
    assert missed['llm_reasoning']['status'] == 'not assessed'
