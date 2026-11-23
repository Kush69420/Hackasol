from auditor.consent.criteria import assess_consent


class NoLLM:
    def ask(self, *args):
        return {'status': 'not assessed', 'cache_key': '0' * 64}


def empty_graph():
    return {'purposes': [], 'records': [], 'enforcement_points': [], 'withdrawal_paths': [],
            'grant_paths': [], 'processors': [], 'operations': [], 'notices': [], 'controls': [],
            'banners': [], 'child_gate': {'state': 'not determinable', 'evidence': [],
                                         'reason': 'No age or DOB Gate established.'}, 'limitations': []}


def test_criteria_banner_is_not_grant():
    graph = empty_graph()
    graph['banners'] = [{'id': 'banner', 'evidence': [{'file': 'index.html', 'start_line': 19,
                                                     'end_line': 19, 'excerpt': 'cookieconsent'}]}]
    result = assess_consent(graph, [], NoLLM())
    assert len(result['criteria']) == 7
    rows = {row['criterion']: row for row in result['criteria']}
    assert rows['recorded']['applicability'] == 'not applicable'
    assert 'dismiss action is not a consent grant' in rows['recorded']['assessment']
    assert rows['verifiable parental consent']['applicability'] == 'not applicable'
    assert not result['graph']['grant_paths']


def test_criteria_compares_linked_paths():
    graph = empty_graph()
    graph['grant_paths'] = [{'id': 'g', 'purpose_ids': ['p'], 'start_template': 'home', 'step_count': 1, 'evidence': []}]
    graph['withdrawal_paths'] = [{'id': 'w', 'purpose_ids': ['p'], 'start_template': 'home', 'step_count': 3, 'evidence': []}]
    result = assess_consent(graph, [], NoLLM())
    row = next(row for row in result['criteria'] if row['criterion'].startswith('withdrawable'))
    assert row['step_counts'] == {'grant': [1], 'withdrawal': [3]}
    assert '3 steps' in row['assessment']
    graph['withdrawal_paths'][0]['start_template'] = 'other'
    row = next(row for row in assess_consent(graph, [], NoLLM())['criteria']
               if row['criterion'].startswith('withdrawable'))
    assert 'withdrawal is harder' not in row['assessment']



def test_criteria_preserves_evidenced_facts_and_unresolved_states():
    graph = empty_graph()
    ev = {'file': 'consent.py', 'start_line': 1, 'end_line': 1, 'excerpt': 'consent'}
    graph['controls'] = [{'id': 'control', 'name': 'consent', 'default_selected': False, 'evidence': [ev]}]
    graph['notices'] = [{'id': 'notice', 'purpose_ids': [], 'evidence': [ev], 'itemised': None,
                         'language': None, 'before_grant': None}]
    graph['processors'] = [{'id': 'processor', 'name': 'service', 'purpose_ids': [],
                            'operation_ids': [], 'evidence': [ev]}]
    graph['processor_propagation'] = [{'processor_id': 'processor', 'state': 'not determinable',
                                       'reason': 'No linked withdrawal.', 'evidence': [ev]}]
    graph['child_gate'] = {'state': 'met', 'evidence': [ev], 'reason': 'Age collected.'}
    graph['parental_verification'] = {'state': 'not determinable', 'evidence': [ev], 'reason': 'No linked verification.'}
    rows = {row['criterion']: row for row in assess_consent(graph, [], NoLLM())['criteria']}
    assert 'not determinable' in rows['propagated to Data Processors']['assessment']
    assert 'unresolved' in rows['preceded by notice']['assessment']
    assert 'No linked verification' in rows['verifiable parental consent']['assessment']


def test_criteria_links_deterministic_findings_without_llm_override():
    graph = empty_graph()
    graph['child_gate'] = {'state': 'met', 'evidence': [], 'reason': 'Age collected.'}
    issue_types = ['CON-01', 'CON-02', 'CON-03', 'CON-04', 'CON-05', 'CON-06', 'CON-07', 'CHI-01']
    findings = [{'id': issue + '-test', 'issue_type': issue, 'evidence': []} for issue in issue_types]
    rows = assess_consent(graph, findings, NoLLM())['criteria']
    linked = {identifier for row in rows for identifier in row['linked_identifiers']}
    assert linked == {finding['id'] for finding in findings}
    assert all(row['applicability'] == 'applicable' for row in rows)


def test_criteria_django_rule_corpus():
    from pathlib import Path
    from auditor.rules.consent_django import default_selected, withdrawal_harder, incomplete_record, unitemised_notice
    from auditor.rules.context import build_context

    for rule_id, detect in [('CON-03-django-default-selected', default_selected),
                            ('CON-04-django-comparable-paths', withdrawal_harder),
                            ('CON-06-django-incomplete-record', incomplete_record),
                            ('CON-07-django-unitemised-notice', unitemised_notice)]:
        for label, expected in [('positive', True), ('negative', False)]:
            ctx = build_context(Path('corpus') / rule_id / label, 'corpus')
            assert bool(detect(ctx)) is expected, (rule_id, label)