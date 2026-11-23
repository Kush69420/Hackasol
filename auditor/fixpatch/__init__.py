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


PROMPT_VERSION = 'fix-patch-v2'
MAX_RETRIES = 2
CONTEXT_RADIUS = 30
MAX_CONTEXT_FILES = 3
SYSTEM_PROMPT = (
    'You draft one Fix Patch for a Finding in a Target Application. Return only a JSON object whose '
    '"diff" field is a unified diff. Rules: (1) change only files listed under "files"; (2) use '
    'target-relative paths with "--- a/PATH" and "+++ b/PATH" headers; (3) every context and removed '
    'line must be copied verbatim from the numbered file content provided (the line-number prefix is '
    'not part of the line); (4) hunk headers must carry correct line numbers and counts; (5) make the '
    'smallest local change that removes the Finding and keeps the application working; (6) do not '
    'touch unrelated lines, and do not add files.')


def _context(finding, target, radius=CONTEXT_RADIUS):
    """Exact masked file content with line numbers around the Evidence of the Finding."""
    if target is None:
        return []
    root = Path(target).resolve()
    windows = {}
    for item in finding['evidence']:
        windows.setdefault(item['file'], []).append((item['start_line'], item['end_line']))
    files = []
    for name, spans in list(windows.items())[:MAX_CONTEXT_FILES]:
        path = (root / name).resolve()
        if root not in path.parents or not path.is_file():
            continue
        lines = path.read_text(encoding='utf-8', errors='replace').split('\n')
        if lines and lines[-1] == '':
            lines.pop()
        first, last = spans[0]
        low, high = max(1, first - radius), min(len(lines), last + radius)
        files.append({'path': name, 'total_lines': len(lines), 'first_line': low,
                      'content': '\n'.join(f'{number}: {mask_for_egress(lines[number - 1])}'
                                           for number in range(low, high + 1))})
    return files


def _payload(finding, target):
    return _mask_object({'issue_type': finding['issue_type'], 'evidence': finding['evidence'],
                         'recommended_fix': finding['recommended_fix'], 'files': _context(finding, target)})


def _key(payload_text, client, provider):
    return cache_key(payload_text, PROMPT_VERSION, client.model, {'provider': provider})


def _cached(cache, key, provider, client):
    record = cache.get(key)
    if (isinstance(record, dict) and record.get('provider') == provider
            and record.get('model') == client.model and record.get('prompt_version') == PROMPT_VERSION
            and isinstance(record.get('diff'), str) and record['diff'].strip()
            and not contains_unmasked_material(record['diff'])):
        return record['diff']
    return None


def generate(finding, provider='omp', model=None, cache_dir=Path('.dpdp-cache'), target=None):
    """Request one unified diff; only masked Finding content leaves this machine."""
    client = PROVIDERS[provider](model or DEFAULT_MODELS[provider])
    payload_text = json.dumps(_payload(finding, target), ensure_ascii=False, sort_keys=True)
    key = _key(payload_text, client, provider)
    cache = Cache(cache_dir)
    cached = _cached(cache, key, provider, client)
    if cached is not None:
        return cached
    diff = _parse_diff(client.complete(SYSTEM_PROMPT, payload_text))
    cache.put(key, {'diff': diff, 'provider': provider, 'model': client.model, 'prompt_version': PROMPT_VERSION})
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
    """Generate with numbered file context, `git apply --check`, and retry at most twice with the apply error."""
    client = PROVIDERS[provider](model or DEFAULT_MODELS[provider])
    payload = _payload(finding, target)
    payload_text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    key = _key(payload_text, client, provider)
    cache = Cache(cache_dir)
    def check(value):
        return subprocess.run(['git', '-C', str(target), 'apply', '--check', '-'], input=value,
                              text=True, capture_output=True, check=False)
    def record(diff, status, reason, attempts):
        return {'finding_id': finding['id'], 'diff': diff, 'status': status, 'reason': reason,
                'provenance': 'generated', 'provider': provider, 'model': client.model,
                'prompt_version': PROMPT_VERSION, 'cache_key': key, 'attempts': attempts}
    diff = _cached(cache, key, provider, client)
    attempts = 0
    if diff is None:
        attempts = 1
        try:
            diff = _parse_diff(client.complete(SYSTEM_PROMPT, payload_text))
        except ValueError:
            return record('', 'rejected', 'Provider returned no usable diff', attempts)
    result = check(diff)
    while result.returncode and attempts <= MAX_RETRIES:
        retry = dict(payload, previous_diff=mask_for_egress(diff), apply_error=mask_for_egress(result.stderr),
                     instruction='The previous diff failed `git apply --check`. Return a corrected diff '
                                 'copied against the exact numbered lines in "files".')
        attempts += 1
        try:
            diff = _parse_diff(client.complete(SYSTEM_PROMPT, json.dumps(retry, ensure_ascii=False, sort_keys=True)))
        except ValueError:
            return record(diff, 'rejected', 'Provider retry returned no usable diff', attempts)
        result = check(diff)
    if result.returncode:
        return record(diff, 'rejected', mask_for_egress(result.stderr), attempts)
    if attempts:
        cache.put(key, {'diff': diff, 'provider': provider, 'model': client.model, 'prompt_version': PROMPT_VERSION})
    return record(diff, 'generated', '', attempts)


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
                'before_findings': len(baseline['findings']), 'after_findings': len(after['findings']),
                'target_tests': tests, 'before_revision': baseline['target']['commit'],
                'after_revision': after['target']['commit']}
