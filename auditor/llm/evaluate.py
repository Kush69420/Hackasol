"""Score the provider and model each LLM role is routed to on the held-out Report-Target set.

Inputs are the exact masked payloads production sends (classification from
accuracy/llm-eval/classification.jsonl; triage from the Juice Shop capture with gold labels in
accuracy/llm-eval/triage-labels.json). Each role answers through LLMSession, so shape and citation
validation are the production checks; an invalid answer counts as a miss, never as a skipped row.

    dpdp-audit llm-eval --role-model triage=ollama:qwen3.8:27b --default omp:anthropic/claude-opus-5-5
"""
import argparse
import json
import math
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

from auditor.llm import LLMSession, parse_role_models
from auditor.llm.providers import PROVIDERS, Ollama

ROOT = Path(__file__).resolve().parents[2]
EVAL = ROOT / 'accuracy/llm-eval'
TRIAGE_INPUTS = ROOT / 'training/data/eval/triage-inputs.jsonl'
DEFAULT_SPEC = 'omp:anthropic/claude-opus-5-5'
# Roles with a held-out gold set; consent and fix have none.
GOLD_ROLES = ('classification', 'triage')
# The field of each role's answer that carries the gold label.
LABEL_FIELD = {'classification': 'data_category', 'triage': 'verdict'}


def _rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]


def load_items():
    """Return (role, snippet, context, gold) tuples; gold None marks an out-of-taxonomy classification row."""
    items = []
    for row in _rows(EVAL / 'classification.jsonl'):
        payload = json.loads(row['user'])
        items.append(('classification', payload['evidence'], payload['context'], row['label']))
    labels = json.loads((EVAL / 'triage-labels.json').read_text(encoding='utf-8'))['labels']
    for row in _rows(TRIAGE_INPUTS):
        if row['element_or_finding_id'] in labels:
            payload = json.loads(row['user'])
            items.append(('triage', payload['evidence'], payload['context'], labels[row['element_or_finding_id']]))
    return items


def macro_f1(pairs):
    """Macro-F1 over the gold classes present; pairs are (gold, predicted-or-None)."""
    scores = []
    for cls in sorted({gold for gold, _ in pairs}):
        tp = sum(g == cls and p == cls for g, p in pairs)
        fp = sum(g != cls and p == cls for g, p in pairs)
        fn = sum(g == cls and p != cls for g, p in pairs)
        scores.append(0.0 if tp == 0 else 2 * tp / (2 * tp + fp + fn))
    return sum(scores) / len(scores) if scores else None


def accuracy(pairs):
    return sum(g == p for g, p in pairs) / len(pairs) if pairs else None


def _percentile(sorted_values, q):
    """Nearest-rank percentile: the value at rank ceil(q * n) of the ascending values."""
    return sorted_values[max(1, math.ceil(q * len(sorted_values))) - 1]


def bootstrap(pairs, metrics, replicates, seed):
    """95% percentile intervals for each metric ({name: fn(pairs)}) over resamples of pairs with replacement.

    Every metric is computed on the same resamples, and the result depends only on the seed.
    """
    if not pairs:
        return {name: None for name in metrics}
    rng = random.Random(seed)
    draws = {name: [] for name in metrics}
    for _ in range(replicates):
        sample = rng.choices(pairs, k=len(pairs))
        for name, metric in metrics.items():
            draws[name].append(metric(sample))
    intervals = {}
    for name, values in draws.items():
        values.sort()
        intervals[name] = [_percentile(values, 0.025), _percentile(values, 0.975)]
    return intervals


def score_role(role, rows, replicates, seed):
    """Score one role from (gold, answer) rows. Invalid answers and wrong labels both count as misses."""
    predicted = [(gold, (answer.get('value') or {}).get(LABEL_FIELD[role]) if answer['status'] == 'assessed' else None)
                 for gold, answer in rows]
    scored = [(gold, pred) for gold, pred in predicted if gold is not None]
    metrics = {'accuracy': accuracy}
    if role == 'classification':
        metrics['macro_f1'] = macro_f1
    intervals = bootstrap(scored, metrics, replicates, seed)
    valid = sum(answer['status'] == 'assessed' for _, answer in rows)
    result = {'items': len(rows), 'valid_json_and_citations': valid, 'validity': valid / len(rows) if rows else None,
              'scored': len(scored), 'accuracy': accuracy(scored), 'accuracy_ci95': intervals['accuracy']}
    if role == 'classification':
        nulls = [pred for gold, pred in predicted if gold is None]
        result.update(macro_f1=macro_f1(scored), macro_f1_ci95=intervals['macro_f1'],
                      out_of_taxonomy_items=len(nulls),
                      out_of_taxonomy_assigned_a_category=sum(pred is not None for pred in nulls))
    else:
        result.update(by_gold={gold: {'items': sum(g == gold for g, _ in scored),
                                      'correct': sum(g == gold and p == gold for g, p in scored)}
                               for gold in sorted({g for g, _ in scored})},
                      uncertain=sum(pred == 'uncertain' for _, pred in scored))
    return result


class _EvalOllama(Ollama):
    """The Auditor's Ollama request, with a longer timeout for large local models and an optional think flag."""

    def __init__(self, model, timeout, think):
        super().__init__(model, httpx.Client(timeout=timeout))
        self.think = think

    def complete(self, system, user):
        payload = {'model': self.model, 'stream': False, 'format': 'json', 'options': {'temperature': 0},
                   'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': user}]}
        if self.think is not None:
            payload['think'] = self.think
        return self.post(self.base + '/chat', payload)['message']['content']


def make_provider(provider_name, model, timeout, think):
    return _EvalOllama(model, timeout, think) if provider_name == 'ollama' else PROVIDERS[provider_name](model)


def evaluate_role(role, provider_name, model, items, args):
    """Answer one role's items with its own provider and model, then score them."""
    think = {'default': None, 'on': True, 'off': False}[args.think]
    started = time.monotonic()
    session = LLMSession(args.cache_root, make_provider(provider_name, model, args.timeout, think))
    session.probe()
    if session.mode != 'live':
        print(f'dpdp-audit: {role} on {provider_name}:{model} is cache-only ({session.reason}); '
              'uncached items count as not assessed', file=sys.stderr)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        answers = list(pool.map(lambda item: session.ask(role, item[1], item[2]), items))
    record = {'provider': provider_name, 'model': model, 'mode': session.mode, 'cache_hits': session.cache_hits,
              'wall_seconds': round(time.monotonic() - started, 1)}
    record.update(score_role(role, [(item[3], answer) for item, answer in zip(items, answers)], args.bootstrap, args.seed))
    return record


def role_assignments(role_models, default):
    """Map each gold-set role to its (provider, model): its --role-model, else --default."""
    given = parse_role_models(role_models)
    unscored = sorted(set(given) - set(GOLD_ROLES))
    if unscored:
        raise ValueError(f"no held-out gold set for {', '.join(unscored)}; llm-eval scores {', '.join(GOLD_ROLES)}")
    fallback = parse_role_models([f'{role}={default}' for role in GOLD_ROLES])  # validates --default the same way
    return {role: given.get(role, fallback[role]) for role in GOLD_ROLES}


def table(roles):
    def cell(value, interval):
        return 'n/a' if value is None else f'{100 * value:.1f}% ({100 * interval[0]:.1f}-{100 * interval[1]:.1f})'
    lines = ['| Role | Model | Accuracy, 95% CI | Macro-F1, 95% CI | Scored | Valid | Uncertain |',
             '|---|---|---:|---:|---:|---:|---:|']
    for role, r in roles.items():
        lines.append(f"| {role} | `{r['provider']}:{r['model']}` | {cell(r['accuracy'], r['accuracy_ci95'])} | "
                     f"{cell(r.get('macro_f1'), r.get('macro_f1_ci95'))} | {r['scored']} | "
                     f"{r['valid_json_and_citations']}/{r['items']} | {r.get('uncertain', 'n/a')} |")
    return '\n'.join(lines)


def run(args):
    try:
        assignments = role_assignments(args.role_model, args.default)
    except ValueError as exc:
        print(f'dpdp-audit: {exc}', file=sys.stderr)
        return 1
    items = load_items()
    roles = {role: evaluate_role(role, provider_name, model, [item for item in items if item[0] == role], args)
             for role, (provider_name, model) in assignments.items()}
    result = {'bootstrap': {'replicates': args.bootstrap, 'seed': args.seed, 'confidence': 0.95}, 'roles': roles}
    args.out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(table(roles))
    return 0


def _positive_int(text):
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError(f'must be at least 1, got {text}')
    return value


def add_arguments(parser):
    parser.add_argument('--role-model', action='append', metavar='ROLE=PROVIDER:MODEL',
                        help=f"route a role to its own provider and model; repeatable; roles: {', '.join(GOLD_ROLES)}")
    parser.add_argument('--default', default=DEFAULT_SPEC, metavar='PROVIDER:MODEL',
                        help='provider and model for each role without --role-model')
    parser.add_argument('--cache-root', type=Path, default=ROOT / '.dpdp-cache',
                        help='verdict cache shared with scans; entries are keyed by model and prompt version')
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--timeout', type=float, default=900, help='seconds per Ollama request')
    parser.add_argument('--think', choices=('default', 'on', 'off'), default='default',
                        help="Ollama 'think' flag; default omits it, as the Auditor does")
    parser.add_argument('--bootstrap', type=_positive_int, default=1000,
                        help='bootstrap resamples behind each 95%% interval')
    parser.add_argument('--seed', type=int, default=0, help='seed for the bootstrap resamples')
    parser.add_argument('--out', type=Path, default=EVAL / 'results.json', help='JSON results with intervals')
