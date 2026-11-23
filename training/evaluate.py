"""Score models per LLM role on the held-out Report-Target set.

Inputs are the exact masked payloads production sends (classification from
accuracy/llm-eval/classification.jsonl; triage from the Juice Shop capture with gold labels in
accuracy/llm-eval/triage-labels.json). Each model answers through LLMSession, so shape and citation
validation are the production checks; an invalid answer counts as a miss, never as a skipped row.

    python training/evaluate.py --model opus=omp:anthropic/claude-opus-5-5 \
        --model base=ollama:qwen3:8b --model ft=ollama:dpdp-auditor:<run-id>
"""
import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from auditor.llm import LLMSession  # noqa: E402
from auditor.llm.providers import PROVIDERS  # noqa: E402

EVAL = ROOT / 'accuracy/llm-eval'
TRIAGE_INPUTS = ROOT / 'training/data/eval/triage-inputs.jsonl'
TRIAGE_VERDICTS = ('true-positive', 'false-positive', 'uncertain')


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


def evaluate(spec, items, cache_root, workers):
    name, target = spec.split('=', 1)
    provider_name, model = target.split(':', 1)
    session = LLMSession(cache_root / name, PROVIDERS[provider_name](model))
    session.probe()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        answers = list(pool.map(lambda item: session.ask(item[0], item[1], item[2]), items))
    result = {'name': name, 'provider': provider_name, 'model': model, 'mode': session.mode,
              'cache_hits': session.cache_hits, 'roles': {}}
    for role, key in (('classification', 'data_category'), ('triage', 'verdict')):
        rows = [(item[3], answer) for item, answer in zip(items, answers) if item[0] == role]
        predicted = [(gold, (a.get('value') or {}).get(key) if a['status'] == 'assessed' else None) for gold, a in rows]
        valid = sum(a['status'] == 'assessed' for _, a in rows)
        scored = [(g, p) for g, p in predicted if g is not None]
        entry = {'items': len(rows), 'valid_json_and_citations': valid, 'validity': valid / len(rows) if rows else None,
                 'accuracy': sum(g == p for g, p in scored) / len(scored) if scored else None}
        if role == 'classification':
            entry['macro_f1'] = macro_f1(scored)
            nulls = [p for g, p in predicted if g is None]
            entry['out_of_taxonomy_items'] = len(nulls)
            entry['out_of_taxonomy_assigned_a_category'] = sum(p is not None for p in nulls)
        else:
            entry['by_gold'] = {gold: {'items': sum(g == gold for g, _ in scored),
                                       'correct': sum(g == gold and p == gold for g, p in scored)}
                                for gold in sorted({g for g, _ in scored})}
            entry['uncertain'] = sum(p == 'uncertain' for _, p in scored)
        result['roles'][role] = entry
    return result


def table(results):
    def pct(value):
        return 'n/a' if value is None else f'{100 * value:.1f}%'
    lines = ['| Model | Classification macro-F1 | Classification accuracy | Classification valid | Triage accuracy | Triage valid | Triage uncertain |',
             '|---|---:|---:|---:|---:|---:|---:|']
    for r in results:
        c, t = r['roles']['classification'], r['roles']['triage']
        lines.append(f"| {r['name']} (`{r['provider']}:{r['model']}`) | {pct(c['macro_f1'])} | {pct(c['accuracy'])} | "
                     f"{c['valid_json_and_citations']}/{c['items']} | {pct(t['accuracy'])} | "
                     f"{t['valid_json_and_citations']}/{t['items']} | {t['uncertain']} |")
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--model', action='append', required=True, help='NAME=PROVIDER:MODEL')
    parser.add_argument('--cache-root', type=Path, default=ROOT / 'training/cache/eval',
                        help='per-model verdict caches; point a model at an existing cache dir by name to replay it')
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--out', type=Path, default=EVAL / 'results.json')
    args = parser.parse_args(argv)
    items = load_items()
    results = [evaluate(spec, items, args.cache_root, args.workers) for spec in args.model]
    args.out.write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    print(table(results))
    return 0


if __name__ == '__main__':
    sys.exit(main())
