"""Generate and evaluate Fix Patches without changing a Target Application."""
from collections import Counter
import json
import re
from pathlib import Path
import shutil
import subprocess
import tempfile

from auditor.llm import DEFAULT_MODELS, _mask_object
from auditor.llm.cache import Cache, cache_key
from auditor.llm.providers import PROVIDERS
from auditor.masking import contains_unmasked_material, mask_for_egress, mask_for_report
from auditor.scan import run_scan


def generate(finding, provider='omp', model=None, cache_dir=Path('.dpdp-cache')):
    """Request one unified diff; only masked Finding content leaves this machine."""
    client = PROVIDERS[provider](model or DEFAULT_MODELS[provider])
    payload = _mask_object({'issue_type': finding['issue_type'], 'evidence': finding['evidence'],
                            'recommended_fix': finding['recommended_fix']})
    prompt = 'Return a JSON object with a unified diff in the diff field. Use target-relative paths.'
    payload_text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    key = cache_key(payload_text, 'fix-patch-v1', client.model, {'provider': provider})
    cache = Cache(cache_dir)
    record = cache.get(key)
    if (isinstance(record, dict) and record.get('provider') == provider
            and record.get('model') == client.model and record.get('prompt_version') == 'fix-patch-v1'
            and isinstance(record.get('diff'), str) and record['diff'].strip()
            and not contains_unmasked_material(record['diff'])):
        return record['diff']
    diff = _parse_diff(client.complete(prompt, payload_text))
    cache.put(key, {'diff': diff, 'provider': provider, 'model': client.model, 'prompt_version': 'fix-patch-v1'})
    return diff


def _parse_diff(result):
    fenced_json = re.fullmatch(r"\s*```json\s*\n(.*?)```\s*", result, re.DOTALL | re.IGNORECASE)
    if fenced_json:
        result = fenced_json.group(1)
    try:
        diff = json.loads(result)['diff']
    except (ValueError, KeyError, TypeError):
        match = re.search(r"```(?:diff|patch)\s*\n(.*?)```", result, re.DOTALL | re.IGNORECASE)
        if not match:
            raise ValueError('Provider returned neither JSON nor a fenced unified diff') from None
        diff = match.group(1)
    if not isinstance(diff, str) or not diff.strip():
        raise ValueError('Provider did not return a unified diff')
    if contains_unmasked_material(diff):
        raise ValueError('Generated diff contains material requiring masking')
    return diff


def generate_review(finding, target, provider='omp', model=None, cache_dir=Path('.dpdp-cache')):
    """Generate, check applicability, and retry once with masked apply diagnostics."""
    client = PROVIDERS[provider](model or DEFAULT_MODELS[provider])
    diff = generate(finding, provider, model, cache_dir)
    def check(value):
        return subprocess.run(['git', '-C', str(target), 'apply', '--check', '-'], input=value,
                              text=True, capture_output=True, check=False)
    result = check(diff)
    if result.returncode:
        payload = _mask_object({'finding': finding, 'previous_diff': diff,
                                'apply_error': mask_for_egress(result.stderr)})
        prompt = 'Return a JSON object with a corrected target-relative unified diff in the diff field.'
        try:
            diff = _parse_diff(client.complete(prompt, json.dumps(payload, ensure_ascii=False)))
            result = check(diff)
        except (ValueError, KeyError, TypeError):
            return {'finding_id': finding['id'], 'diff': diff, 'status': 'rejected',
                    'reason': 'Provider retry returned no usable diff', 'provenance': 'generated'}
    return {'finding_id': finding['id'], 'diff': diff,
            'status': 'generated' if result.returncode == 0 else 'rejected',
            'reason': '' if result.returncode == 0 else mask_for_egress(result.stderr),
            'provenance': 'generated'}


def _identity(finding):
    # Conservatively treat any Finding from the same Rules at the same file as
    # persisting, even when its Evidence moves or its wording changes.
    return (finding['issue_type'], tuple(sorted(finding['rules_fired'])),
            finding['evidence'][0]['file'])


def _evidence_identity(finding):
    # The first Evidence line is the operation or handler anchor. Secondary
    # Evidence can legitimately change when a different Finding is fixed.
    anchor = finding['evidence'][0]['excerpt'].splitlines()
    return (_identity(finding), ' '.join(anchor[0].split()) if anchor else '')

def verify(target, baseline, patches, *, scan=run_scan, scan_options=None, test_commands=()):
    """Apply all diffs together, re-scan, and report Target tests independently."""
    target = Path(target).resolve()
    if not patches:
        raise ValueError('No Fix Patches selected')
    name = baseline['target']['name']
    if not name or Path(name).name != name or name in {'.', '..'}:
        raise ValueError('Invalid Target Application name')
    revision = subprocess.run(['git', '-C', str(target), 'rev-parse', '--verify', 'HEAD^{commit}'],
                              capture_output=True, text=True, check=True).stdout.strip()
    if baseline['target']['commit'] != revision:
        raise ValueError('Baseline revision differs from the Target Application')
    if subprocess.run(['git', '-C', str(target), 'status', '--porcelain', '--untracked-files=all'],
                      capture_output=True, text=True, check=True).stdout:
        raise ValueError('Target Application must be clean')
    with tempfile.TemporaryDirectory(prefix='dpdp-fix-') as temporary:
        scratch = Path(temporary) / baseline['target']['name']
        shutil.copytree(target, scratch, symlinks=True, ignore=shutil.ignore_patterns('.git'))
        for patch in patches:
            diff = patch['diff']
            if contains_unmasked_material(diff):
                raise ValueError('Fix Patch contains material requiring masking')
            subprocess.run(['git', 'apply', '--check', '-'], cwd=scratch, input=diff, text=True, check=True,
                           capture_output=True)
            subprocess.run(['git', 'apply', '-'], cwd=scratch, input=diff, text=True, check=True,
                           capture_output=True)
        after = scan(str(scratch), **(scan_options or {}))
        after_counts = Counter(map(_identity, after['findings']))
        if after['scan']['exclusions'] != baseline['scan']['exclusions']:
            raise ValueError('Baseline and re-scan exclusions differ')
        selected = {finding_id for p in patches for finding_id in
                    (p['finding_ids'] if 'finding_ids' in p else [p['finding_id']])}
        new = Counter(map(_evidence_identity, after['findings'])) - Counter(map(_evidence_identity, baseline['findings']))
        originals = [f for f in baseline['findings'] if f['id'] in selected]
        if len(originals) != len(selected):
            raise ValueError('Fix Patch references an unknown Finding')
        remaining = [f['id'] for f in originals if after_counts[_identity(f)]]
        tests = []
        for command in test_commands:
            result = subprocess.run(command, cwd=scratch, text=True, capture_output=True, check=False)
            tests.append({'command': command, 'exit_status': result.returncode,
                          'summary': mask_for_report((result.stdout + '\n' + result.stderr)[-4000:])})
        return {'status': 'accepted' if not remaining and not new else 'rejected',
                'remaining': remaining, 'new': [list(key) for key in new.elements()],
                'target_tests': tests, 'before_revision': baseline['target']['commit'],
                'after_revision': after['target']['commit']}
