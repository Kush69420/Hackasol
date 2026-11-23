"""Check classification training splits against the committed held-out set."""
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
    eval_hashes = {row['snippet_sha256'] for row in eval_rows}
    eval_sources = {row['source'] for row in eval_rows}
    counts = {}
    repo_splits = {}
    failures = []
    for split in ('train', 'val'):
        with (ROOT / f'training/data/{split}/classification.jsonl').open(encoding='utf-8') as stream:
            counts[split] = 0
            for number, line in enumerate(stream, 1):
                row = json.loads(line)
                source = row['source']
                path = PurePosixPath(source)
                location = f'{split}:{number}'
                if (path.parts[:2] != ('targets', 'training') or len(path.parts) < 4
                        or '..' in path.parts or source != path.as_posix() or '\\' in source):
                    failures.append(f'{location}: source is not a canonical training path')
                else:
                    repo = path.parts[2]
                    if repo_splits.setdefault(repo, split) != split:
                        failures.append(f'{location}: repository in both splits')
                if source in eval_sources or report_path(source):
                    failures.append(f'{location}: held-out source path')
                user = next(message['content'] for message in row['messages'] if message['role'] == 'user')
                digest = sha256(json.loads(user)['evidence'].encode()).hexdigest()
                if digest in eval_hashes:
                    failures.append(f'{location}: held-out Evidence hash {digest}')
                counts[split] += 1
        if not counts[split]:
            failures.append(f'{split}: no rows to check')
    if failures:
        print('LEAKAGE CHECK FAILED:\n' + '\n'.join(failures), file=sys.stderr)
        return 1
    print(f"Leakage check passed: {counts['train']} train + {counts['val']} val rows across "
          f'{len(repo_splits)} repositories; no overlap with {len(eval_rows)} held-out rows or Report Target paths.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
