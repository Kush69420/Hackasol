"""Pinned TrackMyRupee consent paths, exercised in a fresh isolated browser."""
import json
from pathlib import Path
import subprocess

from auditor.probes.assessments import comparable_ease, consent_enforcement

PIN = '47990e4f19d7debea70c5d56bab77e3c3f051546'


def run_browser(origin: str) -> list[dict]:
    script = Path(__file__).with_suffix('.mjs')
    try:
        process = subprocess.run(['node', str(script)], input=json.dumps({'origin': origin}),
                                 capture_output=True, text=True, timeout=90, check=True)
        data = json.loads(process.stdout)
        before = data.get('before') is True and data.get('withdrawn') is True
        after = data.get('after') if isinstance(data.get('after'), bool) else None
        grant = data.get('grant') if type(data.get('grant')) is int else None
        withdrawal = data.get('withdrawal') if type(data.get('withdrawal')) is int else None
    except (OSError, subprocess.SubprocessError, ValueError, TypeError):
        before, after, grant, withdrawal = False, None, None, None
    enforcement = consent_enforcement(before, after)
    if grant is not None and withdrawal is not None:
        ease = ('inconclusive', f'Grant recorded {grant} interactions and withdrawal {withdrawal}; the Report does not establish a common starting point or Purpose link')
    else:
        ease = comparable_ease(None, None)
    return [
        {'assertion': 'consent-after-withdrawal', 'finding_id': None, 'result': enforcement[0],
         'method': 'POST', 'route': '/settings/consent/withdraw/', 'reason': enforcement[1],
         'request': 'Auditor-created account; values: [masked]',
         'response': 'Account profile availability compared before and after withdrawal; values: [masked]'},
        {'assertion': 'comparable-ease', 'finding_id': None, 'result': ease[0],
         'method': 'BROWSER', 'route': '/accounts/signup/ → /settings/consent/withdraw/',
         'reason': ease[1], 'request': 'Signup and withdrawal interactions; values: [masked]',
         'response': 'Counts include clicks and checkbox changes, excluding text entry'},
    ]
