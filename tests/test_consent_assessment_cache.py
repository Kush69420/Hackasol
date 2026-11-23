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
        return '{"assessment": "Evidence is incomplete."}'


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
    replay = LLMSession(tmp_path, provider)
    second = assess_consent(graph, findings, replay)
    assert second['criteria'] == first['criteria']
    assert second['llm_reasoning'] == first['llm_reasoning']
    assert findings == [{'id': 'CON-03-1', 'issue_type': 'CON-03', 'evidence': []}]
    graph['limitations'].append('different input')
    missed = assess_consent(graph, [], replay)
    assert missed['llm_reasoning']['status'] == 'not assessed'
