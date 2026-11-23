"""Publish a freshly re-scanned Fix Patch set to an authorized fork."""
from pathlib import Path
import subprocess
import tempfile

from auditor.fixpatch import verify
from auditor.masking import mask_for_egress


DESTINATION = 'TanKaizokuO/juice-shop'


def _provenance(patches):
    lines = [f"- {p.get('finding_id', p.get('finding_ids'))}: provenance {p.get('provenance', 'authored')}"
             + (f", provider {p['provider']}, model {p['model']}, prompt {p.get('prompt_version')}, cache key {p['cache_key']}"
                if p.get('cache_key') else '') for p in patches]
    return 'Provenance:\n' + '\n'.join(lines) + '\n\n'


def publish(target, baseline, patches, *, destination, base, branch, authorized=False,
            scan_options=None, test_commands=()):
    if not authorized:
        raise ValueError('Explicit authorization is required')
    if destination.lower() != DESTINATION.lower():
        raise ValueError('Destination must be the authorized fork, not upstream')
    if not patches or any(p.get('status') != 'accepted' for p in patches):
        raise ValueError('Only accepted Fix Patches may be published')
    if base != 'dpdp-pinned-base':
        raise ValueError('Base must be the pinned fork branch')
    subprocess.run(['git', 'check-ref-format', '--branch', branch], check=True, capture_output=True, text=True)
    if branch == base:
        raise ValueError('Review branch must differ from the base')
    remote = f'https://github.com/{DESTINATION}.git'
    base_sha = subprocess.run(['git', 'ls-remote', '--exit-code', remote, f'refs/heads/{base}'],
                              check=True, capture_output=True, text=True).stdout.split()[0]
    if base_sha != baseline['target']['commit']:
        raise ValueError('Fork base and Report revision do not match')
    result = verify(target, baseline, patches, scan_options=scan_options, test_commands=test_commands)
    if result['status'] != 'accepted':
        raise ValueError('Combined re-scan rejected the Fix Patches')
    issues = sorted({f['issue_type'] for f in baseline['findings'] if f['id'] in
                     {i for p in patches for i in p.get('finding_ids', [p.get('finding_id')])}})
    body = ('Fix Patches, reviewed by Issue Type: ' + ', '.join(issues) + '\n\n'
            + 'Combined re-scan: selected Findings absent, no new Finding. '
            + 'A re-scan is not a certification of compliance.\n\n'
            + _provenance(patches)
            + 'Re-scan delta: ' + str(result['before_findings']) + ' Findings before, '
            + str(result['after_findings']) + ' after; remaining selected: ' + str(result['remaining'])
            + '; new: ' + str(result['new']) + '.\n\n'
            + 'Target tests:\n' + (''.join(f"- `{' '.join(t['command'])}`: exit {t['exit_status']}\n```\n"
                                          f"{t['summary'].strip()[-1200:]}\n```\n" for t in result['target_tests'])
                                  or 'not run\n'))
    with tempfile.TemporaryDirectory(prefix='dpdp-publish-') as tmp:
        repo = Path(tmp) / 'checkout'
        subprocess.run(['git', 'clone', '--no-hardlinks', '--', str(Path(target).resolve()), str(repo)],
                       check=True, capture_output=True, text=True)
        def git(*args, **kwargs):
            return subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True, text=True, **kwargs)
        git('checkout', '-b', branch, base_sha)
        for patch in patches:
            git('apply', '-', input=patch['diff'])
        git('add', '-A')
        git('-c', 'user.name=DPDP Auditor', '-c', 'user.email=dpdp-auditor@users.noreply.github.com',
            'commit', '-m', 'Address Personal Data Findings')
        git('push', remote, f'HEAD:refs/heads/{branch}')
        pr = subprocess.run(['gh', 'pr', 'create', '--repo', DESTINATION, '--base', base, '--head', branch,
                             '--title', 'Address Personal Data Findings', '--body', mask_for_egress(body)],
                            check=True, capture_output=True, text=True)
        return {'url': pr.stdout.strip(), 'verification': result}
