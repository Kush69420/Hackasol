"""Check training splits against held-out Report Target inputs."""
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import sys

ROOT = Path(__file__).resolve().parents[1]
REPORT_TARGETS = frozenset({'juice-shop', 'ai-kyc-platform', 'trackmyrupee', 'singharya-e-kyc'})


def report_path(source):
    path = PurePosixPath(source.replace('\\', '/'))
    if 'targets' not in path.parts:
        return False
    parts = path.parts[path.parts.index('targets') + 1:]
    if parts[:1] == ('training',):
        parts = parts[1:]
    return bool(parts and parts[0].casefold() in REPORT_TARGETS | {'juice-shop-fork'})


def main():
    eval_file = ROOT / 'accuracy/llm-eval/classification.jsonl'
    with eval_file.open(encoding='utf-8') as stream:
        eval_rows = [json.loads(line) for line in stream]
    if not eval_rows:
        print('LEAKAGE CHECK FAILED: no held-out classification rows', file=sys.stderr)
        return 1
    roles = ['classification']
    data = ROOT / 'training/data'
    if any((data / split / 'triage.jsonl').exists() for split in ('train', 'val')):
        roles.append('triage')
        eval_capture = []
        for path in (data / 'eval/triage-inputs.jsonl', data / 'eval/triage-cache-only-inputs.jsonl'):
            if not path.is_file():
                print(f'LEAKAGE CHECK FAILED: missing {path.relative_to(ROOT)}', file=sys.stderr)
                return 1
            with path.open(encoding='utf-8') as stream:
                eval_capture.extend(json.loads(line) for line in stream)
        if not eval_capture:
            print('LEAKAGE CHECK FAILED: no held-out triage captures', file=sys.stderr)
            return 1
        eval_rows.extend(eval_capture)
    eval_hashes = {row['snippet_sha256'] for row in eval_rows}
    eval_sources = {row['source'] for row in eval_rows}
    counts = {}
    repo_splits = {}
    failures = []
    for role in roles:
        hashes = {}
        for split in ('train', 'val'):
            counts[role, split] = 0
            path = data / split / f'{role}.jsonl'
            if not path.is_file():
                failures.append(f'{role}/{split}: missing split')
                continue
            with path.open(encoding='utf-8') as stream:
                for number, line in enumerate(stream, 1):
                    row = json.loads(line)
                    source = row['source']
                    parts = PurePosixPath(source).parts
                    location = f'{role}/{split}:{number}'
                    valid_source = (len(parts) >= 4 and '..' not in parts and '\\' not in source
                                    and source == PurePosixPath(source).as_posix())
                    if valid_source and parts[:2] == ('targets', 'training'):
                        if repo_splits.setdefault(parts[2], split) != split:
                            failures.append(f'{location}: repository in both splits')
                    elif not (valid_source and role == 'triage' and split == 'train'
                              and parts[0] == 'corpus' and parts[2] in ('positive', 'negative')):
                        failures.append(f'{location}: source is not a canonical training path')
                    if source in eval_sources or report_path(source):
                        failures.append(f'{location}: held-out source path')
                    user = next(message['content'] for message in row['messages'] if message['role'] == 'user')
                    digest = sha256(json.loads(user)['evidence'].encode()).hexdigest()
                    if digest in eval_hashes:
                        failures.append(f'{location}: held-out Evidence hash {digest}')
                    if role == 'triage' and hashes.setdefault(digest, split) != split:
                        failures.append(f'{location}: triage Evidence hash in both splits')
                    counts[role, split] += 1
            if not counts[role, split]:
                failures.append(f'{role}/{split}: no rows to check')
    if failures:
        print('LEAKAGE CHECK FAILED:\n' + '\n'.join(failures), file=sys.stderr)
        return 1
    if roles == ['classification']:
        print(f"Leakage check passed: {counts['classification', 'train']} train + {counts['classification', 'val']} val rows "
              f'across {len(repo_splits)} repositories; no overlap with {len(eval_rows)} held-out rows or Report Target paths.')
    else:
        sizes = ', '.join(f"{role} {counts[role, 'train']} train + {counts[role, 'val']} val" for role in roles)
        print(f'Leakage check passed: {sizes} across {len(repo_splits)} repositories and training-only fixtures; '
              f'no overlap with {len(eval_rows)} held-out captures or Report Target paths.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
