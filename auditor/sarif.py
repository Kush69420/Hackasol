"""Derive SARIF 2.1.0 from a canonical Report."""
from pathlib import PurePosixPath
from urllib.parse import quote

from auditor.masking import mask_for_egress


def to_sarif(report: dict) -> dict:
    rules = {}
    results = []
    levels = {'critical': 'error', 'high': 'error', 'medium': 'warning', 'low': 'note'}
    for finding in report['findings']:
        rule_id = finding['rules_fired'][0]
        issue = finding['issue_type']
        rules.setdefault(rule_id, {'id': rule_id, 'name': rule_id,
                                   'shortDescription': {'text': issue},
                                   'properties': {'issueType': issue}})
        locations = []
        for evidence in finding['evidence']:
            path = PurePosixPath(evidence['file'])
            if path.is_absolute() or '..' in path.parts:
                raise ValueError('SARIF Evidence must have a target-relative path')
            locations.append({'physicalLocation': {'artifactLocation': {'uri': quote(path.as_posix(), safe='/')},
                'region': {'startLine': evidence['start_line'], 'endLine': evidence['end_line']}}})
        message = mask_for_egress(f"{issue}: {finding['severity']['justification']}")
        results.append({'ruleId': rule_id, 'level': levels[finding['severity']['band']],
                        'message': {'text': message}, 'locations': locations,
                        'properties': {'issueType': issue, 'findingId': finding['id']}})
    return {'$schema': 'https://json.schemastore.org/sarif-2.1.0.json', 'version': '2.1.0',
            'runs': [{'tool': {'driver': {'name': 'dpdp-audit', 'rules': list(rules.values())}},
                      'results': results}]}
