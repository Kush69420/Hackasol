"""Evidence-grounded Consent Assessment, independent of LLM verdicts."""
import json
from hashlib import sha256


_CRITERIA = (
    ('recorded', ('CON-06',), ('grant_paths', 'records')),
    ('specific', ('CON-02', 'CON-03'), ('purposes', 'controls')),
    ('enforced server-side', ('CON-01',), ('purposes', 'operations', 'enforcement_points')),
    ('withdrawable with comparable ease', ('CON-04',), ('grant_paths', 'withdrawal_paths')),
    ('propagated to Data Processors', ('CON-05',), ('processors', 'withdrawal_paths')),
    ('preceded by notice', ('CON-07',), ('controls', 'notices')),
    ('verifiable parental consent', ('CHI-01',), ()),
)


def assess_consent(graph, findings, llm):
    """Evaluate recorded facts; unresolved joins never become claims of compliance."""
    rows = []
    for criterion, issues, groups in _CRITERIA:
        items = [item for group in groups for item in graph.get(group, [])]
        relevant = [f for f in findings if f.get('issue_type') in issues]
        if criterion == 'verifiable parental consent' and graph['child_gate']['state'] != 'met':
            relevant = []
        evidence = []
        for item in items:
            for ev in item.get('evidence', []):
                if ev not in evidence:
                    evidence.append(ev)
        if criterion == 'verifiable parental consent':
            gate = graph['child_gate']
            evidence = gate['evidence']
            applicable = gate['state'] == 'met'
            reason = gate['reason']
        else:
            gate_group = {'recorded': 'grant_paths', 'specific': 'controls',
                          'enforced server-side': 'purposes',
                          'withdrawable with comparable ease': 'grant_paths',
                          'propagated to Data Processors': 'processors',
                          'preceded by notice': 'controls'}[criterion]
            applicable = bool(graph.get(gate_group))
            reason = (f'Inventory contains {gate_group.replace("_", " ")}.' if applicable else
                      f'No {gate_group.replace("_", " ")} established by the static inventory; applicability is not established.')
            if criterion == 'specific' and len(graph.get('purposes', [])) > 1:
                applicable = True
                reason = 'The inventory identifies more than one Purpose.'
        if relevant:
            applicable = True
            reason = 'The deterministic Rule Gate is met by the linked Finding Evidence.'
            for finding in relevant:
                for ev in finding.get('evidence', []):
                    if ev not in evidence:
                        evidence.append(ev)
        missing_fact = {
            'recorded': 'a consent grant and its linked Consent Record',
            'specific': 'a consent control or multiple Purposes',
            'enforced server-side': 'a Purpose linked to a Processing Operation and its lawful basis',
            'withdrawable with comparable ease': 'a grant and a comparable Withdrawal Path for the same Purpose',
            'propagated to Data Processors': 'a linked Data Processor transfer and withdrawal outcome',
            'preceded by notice': 'a consent request linked to notice contents and language options',
            'verifiable parental consent': 'the CHI-01 Gate and a linked parental verification mechanism',
        }[criterion]
        assessment = ('Finding identified; see linked Findings.' if relevant else
                      f'Not determinable: {missing_fact} not established by the static inventory.')
        if applicable and not relevant:
            if criterion == 'recorded':
                records = graph.get('records', [])
                if any(record.get('complete') for record in records):
                    assessment = 'A complete Consent Record is evidenced; verify its links to each grant and Purpose.'
                elif records:
                    assessment = 'The identified record is incomplete or its write is unresolved; a boolean alone is not a Consent Record.'
                else:
                    assessment = 'No complete Consent Record was established for the evidenced grant.'
            elif criterion == 'specific':
                selected = [control['id'] for control in graph.get('controls', []) if control.get('default_selected') is True]
                if selected:
                    assessment = 'Default-selected consent controls are evidenced: ' + ', '.join(selected)
                else:
                    assessment = 'Not assessed: control-to-Purpose specificity and affirmative consent remain unresolved.'
            elif criterion == 'enforced server-side':
                linked = [point for point in graph.get('enforcement_points', [])
                          if point.get('server_side') and point.get('purpose_ids') and point.get('operation_ids')]
                if linked:
                    assessment = 'Server-side Enforcement Points linked to Purposes and Processing Operations: ' + ', '.join(point['id'] for point in linked)
                else:
                    assessment = 'Not assessed: no server-side Enforcement Point is linked to both a Purpose and a Processing Operation.'
            elif criterion == 'propagated to Data Processors':
                facts = graph.get('processor_propagation', [])
                if facts:
                    assessment = '; '.join(f"{fact['processor_id']}: {fact['state']} — {fact['reason']}" for fact in facts)
                    for fact in facts:
                        for ev in fact.get('evidence', []):
                            if ev not in evidence:
                                evidence.append(ev)
            elif criterion == 'preceded by notice':
                notices = graph.get('notices', [])
                if notices:
                    assessment = '; '.join(
                        f"{notice['id']}: itemised={notice.get('itemised')}, language={notice.get('language')}, before grant={notice.get('before_grant')}"
                        for notice in notices
                    ) + '; unresolved values are not assessed.'
            elif criterion == 'verifiable parental consent':
                fact = graph.get('parental_verification')
                if fact:
                    assessment = f"{fact['state']}: {fact['reason']}"
                    for ev in fact.get('evidence', []):
                        if ev not in evidence:
                            evidence.append(ev)
        if criterion == 'enforced server-side' and not relevant:
            legitimate = [purpose for purpose in graph.get('purposes', []) if purpose.get('legitimate_use')]
            if legitimate:
                assessment += ' Evidenced legitimate use: ' + '; '.join(
                    f"{purpose['id']}: {purpose['legitimate_use']['basis']}" for purpose in legitimate)
                for purpose in legitimate:
                    for ev in purpose['legitimate_use'].get('evidence', []):
                        if ev not in evidence:
                            evidence.append(ev)
        counts = None
        if criterion == 'withdrawable with comparable ease':
            counts = {'grant': [p['step_count'] for p in graph.get('grant_paths', [])],
                      'withdrawal': [p['step_count'] for p in graph.get('withdrawal_paths', [])]}
            pairs = [(g, w) for g in graph.get('grant_paths', []) for w in graph.get('withdrawal_paths', [])
                     if g.get('start_template') and g.get('start_template') == w.get('start_template')
                     and set(g.get('purpose_ids', [])) & set(w.get('purpose_ids', []))
                     and g['step_count'] is not None and w['step_count'] is not None]
            if pairs and not relevant:
                assessment = '; '.join(
                    f"{g['id']} ({g['step_count']} steps) versus {w['id']} ({w['step_count']} steps): "
                    + ('withdrawal is harder' if w['step_count'] > g['step_count'] else 'withdrawal is no harder by static count')
                    for g, w in pairs)
        applicability = 'applicable' if applicable else 'not determinable'
        banner_only = (graph.get('banners') and not graph.get('grant_paths')
                       and not graph.get('controls') and not graph.get('purposes'))
        if banner_only and not relevant:
            for banner in graph['banners']:
                for ev in banner['evidence']:
                    if ev not in evidence:
                        evidence.append(ev)
            if criterion == 'recorded':
                assessment = ('Not met by the identified banner: no Consent Record was established. '
                              'A dismiss action is not a consent grant; no grant was established either.')
                reason = 'The static inventory identifies a banner but no consent grant or Consent Record.'
                applicability = 'not applicable'
            elif criterion in ('withdrawable with comparable ease', 'propagated to Data Processors',
                               'verifiable parental consent') and not applicable:
                applicability = 'not applicable'
                reason = ('The static inventory identifies no ' +
                          {'withdrawable with comparable ease': 'consent grant',
                           'propagated to Data Processors': 'Data Processor receiving Personal Data',
                           'verifiable parental consent': 'age/DOB collection or explicit Child audience'}[criterion]
                          + '; this is limited to the inspected inventory.')
                assessment = 'Not assessed; an inapplicable Gate is not a compliance conclusion.'
            elif not applicable:
                reason += ' The identified banner is not a grant.'
        rows.append({'criterion': criterion, 'applicability': applicability,
                     'reason': reason, 'assessment': assessment,
                     'linked_identifiers': [item['id'] for item in items] + [f['id'] for f in relevant],
                     'issue_types': list(issues), 'evidence': evidence, 'step_counts': counts})
    serialized = json.dumps(graph, ensure_ascii=False, sort_keys=True)
    if not any(value for key, value in graph.items() if isinstance(value, list) and key != 'limitations'):
        # No consent facts to reason across; spend no provider call.
        reasoning = {'status': 'not assessed', 'cache_key': sha256(serialized.encode()).hexdigest()}
    else:
        # The session masks both the serialized graph and its context before egress and caching.
        reasoning = llm.ask('consent', serialized,
                            {'instruction': 'Reason across the source-anchored graph; do not infer missing links or change Findings.'})
    return {'criteria': rows, 'graph': graph, 'llm_reasoning': reasoning}
