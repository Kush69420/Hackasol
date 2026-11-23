"""Fill the LLM cache concurrently before a scan.

A scan asks the provider one verdict at a time. Prewarming runs the scan cache-only, records every
cache miss, asks the live provider for those misses in parallel, and repeats: a classification verdict
can create Elements whose Findings need triage, so new misses can appear in a later round. A final
scan against the warmed cache then reproduces the Report with no provider call.

    python -m auditor.llm.prewarm targets/juice-shop --cache-dir accuracy/cache --provider omp --workers 8
"""
import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from auditor.llm import LLMSession, parse_role_models
from auditor.scan import run_scan


class _MissRecorder(LLMSession):
    """Cache-only session that records the arguments of every unanswered ask."""

    def __init__(self, cache_dir, provider, role_providers):
        super().__init__(cache_dir, provider, role_providers)
        self.misses = {}

    def probe(self):
        self.force_cache_only('prewarm capture')

    def ask(self, role, snippet, context=None):
        result = super().ask(role, snippet, context)
        if result['status'] != 'assessed':
            self.misses[result['cache_key']] = (role, snippet, context)
        return result


def prewarm(source, *, cache_dir, provider=None, model=None, role_models=None, commit=None, workers=8, max_rounds=4,
            targets_dir=Path('targets'), log=print):
    """Return per-round counts; the last round has zero misses unless the provider kept failing."""
    live = LLMSession.from_env(cache_dir=cache_dir, provider=provider, model=model, role_models=role_models)
    live.probe()
    if live.mode != 'live':
        raise RuntimeError(f'provider is not reachable: {live.reason}')
    rounds, failed = [], set()
    for number in range(1, max_rounds + 1):
        recorder = _MissRecorder(cache_dir, live.provider, live.role_providers)
        run_scan(source, commit=commit, cache_dir=cache_dir, targets_dir=targets_dir, session=recorder)
        pending = {key: args for key, args in recorder.misses.items() if key not in failed}
        if not pending:
            rounds.append({'round': number, 'misses': len(recorder.misses), 'asked': 0, 'assessed': 0})
            log(f'round {number}: no new misses ({len(recorder.misses)} unresolved after retries)')
            break
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(lambda args: live.ask(*args), pending.values()))
        assessed = sum(r['status'] == 'assessed' for r in results)
        failed |= {key for key, r in zip(pending, results) if r['status'] != 'assessed'}
        rounds.append({'round': number, 'misses': len(recorder.misses), 'asked': len(pending), 'assessed': assessed})
        log(f'round {number}: {len(pending)} asked, {assessed} assessed, {len(pending) - assessed} failed')
    return rounds


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('target')
    parser.add_argument('--cache-dir', type=Path, default=Path('.dpdp-cache'))
    parser.add_argument('--provider')
    parser.add_argument('--model')
    parser.add_argument('--role-model', action='append', metavar='ROLE=PROVIDER:MODEL')
    parser.add_argument('--commit')
    parser.add_argument('--workers', type=int, default=8)
    parser.add_argument('--max-rounds', type=int, default=4)
    args = parser.parse_args(argv)
    try:
        role_models = parse_role_models(args.role_model)
    except ValueError as exc:
        parser.error(str(exc))
    rounds = prewarm(args.target, cache_dir=args.cache_dir, provider=args.provider, model=args.model,
                     role_models=role_models, commit=args.commit, workers=args.workers, max_rounds=args.max_rounds)
    return 0 if rounds and rounds[-1]['asked'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
