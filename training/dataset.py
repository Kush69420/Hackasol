"""Label capture inputs with Opus and build the classification training splits."""
from argparse import ArgumentParser
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from math import ceil
import subprocess

import yaml

from auditor.accuracy import load_reference, score_findings
from auditor.llm import _mask_object
from auditor.llm.cache import Cache, cache_key
from auditor.llm.prompts import PROMPT_VERSION, valid_value
from auditor.llm.providers import Omp
from training.capture import CACHE, DATA, EVAL, ROOT, capture, read_jsonl, write_jsonl
from training.leakage import REPORT_TARGETS, report_path

ROLE = 'classification'
MODEL = 'anthropic/claude-opus-5-5'


def label(rows, *, role=ROLE):
    provider = Omp(MODEL)
    cache = Cache(CACHE / f'opus-{role}')
    version = PROMPT_VERSION[role]
    work = {}
    keys = []
    for row in rows:
        payload = json.loads(row['user'])
        key = cache_key(payload['evidence'], version, MODEL, payload['context'])
        work.setdefault(key, (row, payload))
        keys.append(key)

    def complete(item):
        key, (row, payload) = item
        context = payload['context']
        cached = cache.get(key)
        if (isinstance(cached, dict) and cached.get('model') == MODEL
                and cached.get('provider') == provider.name
                and cached.get('prompt_version') == version and valid_value(role, cached.get('value'), context)):
            return cached['value']
        try:
            value = _mask_object(json.loads(provider.complete(row['system'], row['user'])))
        except (OSError, ValueError, subprocess.SubprocessError):
            # Provider errors may contain request material. Log counts only.
            return None
        if not valid_value(role, value, context):
            return None
        cache.put(key, {'input': payload['evidence'], 'context': payload['context'], 'value': value,
                        'prompt_version': version, 'provider': provider.name, 'model': MODEL})
        return value

    with ThreadPoolExecutor(max_workers=8) as pool:
        values = dict(zip(work, pool.map(complete, work.items())))
    print(f'Opus: {sum(value is not None for value in values.values())}/{len(work)} distinct requests valid', flush=True)
    return [values[key] for key in keys]


def teacher_eval():
    rows = [row for target in sorted(REPORT_TARGETS) for row in read_jsonl(DATA / 'inputs' / f'{target}.jsonl')
            if row['role'] == ROLE]
    result = [dict(row, teacher_label=value['data_category'] if value is not None else None, teacher_value=value)
              for row, value in zip(rows, label(rows))]
    write_jsonl(DATA / 'eval/classification-teacher.jsonl', result)
    print(f'Teacher evaluation: {len(result)} rows; {sum(row["teacher_value"] is None for row in result)} invalid', flush=True)


def triage_gold():
    report = json.loads((ROOT / 'reports/juice-shop/report.json').read_text(encoding='utf-8'))
    reference_path = 'accuracy/juice-shop.json'
    reference = load_reference(ROOT / reference_path)
    if report['target']['commit'] != reference['target']['commit']:
        raise ValueError('Juice Shop Report and reference are not at the same revision')
    scored = score_findings(report['findings'], reference, reference_path=reference_path)
    labels = {item['finding_id']: 'true-positive' for item in scored['matches']}
    labels.update((item['finding_id'], 'false-positive') for item in scored['unmatched_predictions'])
    return {'target_commit': scored['commit'], 'reference': reference_path,
            'labels': dict(sorted(labels.items())),
            'counts': {'true-positive': scored['tp'], 'false-positive': scored['fp'],
                       'excluded-not-determinable': len(scored['excluded_predictions'])}}


def pinned_root(name, source):
    root = ROOT / 'targets/training' / name
    if report_path(root.relative_to(ROOT).as_posix()):
        raise ValueError(f'Report Target cannot be a training source: {name}')

    def git(*args):
        return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()

    if not root.exists():
        root.mkdir(parents=True)
        git('init', '--quiet')
        git('remote', 'add', 'origin', source['url'])
        git('fetch', '--quiet', '--depth', '1', 'origin', source['commit'])
        git('checkout', '--quiet', '--detach', source['commit'])

    if (git('remote', 'get-url', 'origin') != source['url']
            or git('rev-parse', 'HEAD') != source['commit'] or git('status', '--porcelain')):
        raise ValueError(f'Training source must be clean and match the pinned origin and revision: {name}')
    return root


def collect_sources(sources):
    def collect(item):
        name, source = item
        root = pinned_root(name, source)
        rows = capture(root, classification_only=True, deterministic=True)
        write_jsonl(DATA / 'inputs' / f'{name}.jsonl', rows)
        print(f'{name}: {len(rows)} captured classification inputs', flush=True)
        return name, rows

    # A few concurrent inventory runs overlap large TypeScript parser startup
    # without running a host-wide batch of memory-heavy ASTs at once.
    with ThreadPoolExecutor(max_workers=3) as pool:
        yield from pool.map(collect, sources.items())


def train_dataset(sources):
    held_out = list(read_jsonl(EVAL / 'classification.jsonl'))
    if not held_out:
        raise ValueError('Held-out classification data is required before distillation')
    hashes = {row['snippet_sha256'] for row in held_out}
    paths = {row['source'] for row in held_out}
    candidates = []
    stats = {name: Counter() for name in sources}
    for name, rows in collect_sources(sources):
        stats[name]['captured'] = len(rows)
        for row in rows:
            if row['snippet_sha256'] in hashes or row['source'] in paths or report_path(row['source']):
                stats[name]['held_out_overlap'] += 1
            else:
                candidates.append((name, row))
    teacher = iter(label([row for _, row in candidates if 'deterministic_value' not in row]))
    processed = defaultdict(list)
    for name, row in candidates:
        origin = 'deterministic' if 'deterministic_value' in row else 'teacher'
        value = row['deterministic_value'] if origin == 'deterministic' else next(teacher)
        if not valid_value(ROLE, value):
            stats[name]['invalid'] += 1
            continue
        messages = [{'role': 'system', 'content': row['system']}, {'role': 'user', 'content': row['user']},
                    {'role': 'assistant', 'content': json.dumps(value, ensure_ascii=False)}]
        processed[name].append(({'role': ROLE, 'source': row['source'], 'messages': messages}, value['data_category'], origin))
        stats[name][origin] += 1

    total = sum(map(len, processed.values()))
    if len(processed) < 2:
        raise ValueError('At least two repositories must yield valid rows for a repository-disjoint split')
    validation = min(processed, key=lambda name: (abs(len(processed[name]) - total / 10), name))
    splits = {'val': [], 'train': []}
    for name, rows in processed.items():
        splits['val' if name == validation else 'train'].extend(rows)
    summary = {'sources': stats, 'validation_repository': validation, 'splits': {}}
    for split, labeled in splits.items():
        path = DATA / split / 'classification.jsonl'
        write_jsonl(path, (row for row, _, _ in labeled))
        lengths = sorted(ceil(sum(len(m['content']) for m in row['messages']) / 3.5) for row, _, _ in labeled)
        summary['splits'][split] = {
            'rows': len(labeled), 'counts': Counter(category for _, category, _ in labeled),
            'label_origin': Counter(origin for _, _, origin in labeled),
            'tokens_approx': {'p50': lengths[ceil(len(lengths) * 0.50) - 1],
                              'p95': lengths[ceil(len(lengths) * 0.95) - 1], 'max': lengths[-1]},
            'sha256': sha256(path.read_bytes()).hexdigest(),
        }
    return summary


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('teacher-eval', 'triage-gold', 'train'))
    phase = parser.parse_args().phase
    if phase == 'teacher-eval':
        teacher_eval()
    elif phase == 'triage-gold':
        print(json.dumps(triage_gold(), indent=2))
    else:
        sources = yaml.safe_load((ROOT / 'training/sources.yaml').read_text(encoding='utf-8'))
        summary = train_dataset(sources)
        payload = json.dumps(summary, indent=2) + '\n'
        (DATA / 'classification-stats.json').write_text(payload, encoding='utf-8')
        print(payload, end='')


if __name__ == '__main__':
    main()
