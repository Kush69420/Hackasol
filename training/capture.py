"""Capture the Auditor's masked prompts without contacting an LLM.

Run from the repository root: python -m training.capture targets/<name>.
"""
from argparse import ArgumentParser
from hashlib import sha256
import json
from os.path import abspath
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from auditor import scan
from auditor.classify import classify, extract_elements
from auditor.llm import LLMSession, _mask_object
from auditor.llm.prompts import system_prompt
from auditor.masking import mask_for_egress
from auditor.rules import context as rules_context

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'training/data'
CACHE = ROOT / 'training/cache'
EVAL = ROOT / 'accuracy/llm-eval'


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows), encoding='utf-8')


def read_jsonl(path):
    with path.open(encoding='utf-8') as stream:
        for line in stream:
            yield json.loads(line)


class RecordingSession(LLMSession):
    def __init__(self, source):
        # The base session only needs provider identity for its scan summary.
        super().__init__(CACHE, SimpleNamespace(name='omp', model='capture-only'))
        self.reason = 'Provider-free training input capture'
        self.source = source
        self.rows = {}
        self.element = None

    def ask(self, role, snippet, context=None):
        masked = mask_for_egress(snippet)
        payload = json.dumps({'evidence': masked, 'context': _mask_object(context)}, ensure_ascii=False)
        key = sha256(f'capture only:{len(self.rows)}'.encode()).hexdigest()
        row = {'role': role, 'system': system_prompt(role), 'user': payload,
               'snippet_sha256': sha256(masked.encode()).hexdigest(),
               'element_or_finding_id': None, 'source': self.source}
        if self.element is not None:
            coordinate = self.element['source']
            row.update(element_or_finding_id=mask_for_egress(self.element['id']),
                       source=self.source + '/' + coordinate['file'], source_line=coordinate['start_line'])
            if self.element['data_category']:
                signals = ', '.join(self.element['signals'])
                row['deterministic_value'] = {
                    'data_category': self.element['data_category'],
                    'reason': mask_for_egress(f"The Auditor's deterministic classification uses: {signals}."),
                }
        self.rows[key] = row
        self.cache_misses += 1
        self.not_assessed += 1
        return {'status': 'not assessed', 'cache_key': key}

    def record_elements(self, elements, *, deterministic=False):
        results = []
        for element in elements:
            if element['data_category'] and not deterministic:
                results.append(element)
                continue
            self.element = element
            try:
                # Let the real classification code construct both unresolved and
                # deterministic prompts, but never remove a Data Category from the scan.
                recorded = classify([dict(element, data_category=None)], llm=self)[0]
            finally:
                self.element = None
            results.append(element if element['data_category'] else recorded)
        return results

    def attach_report_sources(self, report):
        for finding in report['findings']:
            evidence = finding['evidence'][0]
            for verdict in (finding['llm_triage'], finding['recommended_fix']['tailored']):
                row = self.rows[verdict['cache_key']]
                row.update(element_or_finding_id=finding['id'],
                           source=self.source + '/' + evidence['file'], source_line=evidence['start_line'])
        verdict = report['consent_assessment']['llm_reasoning']
        if verdict['cache_key'] in self.rows:
            self.rows[verdict['cache_key']]['element_or_finding_id'] = 'consent-assessment'
        if any(row['element_or_finding_id'] is None for row in self.rows.values()):
            raise RuntimeError('An LLM prompt could not be joined to its Report or Personal Data Element')


def capture(source, *, classification_only=False, deterministic=False):
    path = Path(source)
    # abspath, not resolve(): the worktree's targets/ is intentionally a symlink.
    canonical = Path(abspath(path)).relative_to(ROOT)
    if len(canonical.parts) < 2 or canonical.parts[0] != 'targets':
        raise ValueError('Capture paths must be relative to the repository targets/ directory')
    session = RecordingSession(canonical.as_posix())
    if classification_only:
        inventory = scan.run_inventory(str(path))['inventory']
        session.record_elements(extract_elements(inventory), deterministic=deterministic)
    else:
        def record(elements, llm=None):
            return session.record_elements(elements, deterministic=deterministic)

        with patch.object(rules_context, 'classify', record):
            report = scan.run_scan(str(path), session=session, cache_dir=CACHE)
        session.attach_report_sources(report)
    return list(session.rows.values())


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('targets', nargs='+')
    parser.add_argument('--classification-only', action='store_true')
    parser.add_argument('--include-deterministic', action='store_true')
    args = parser.parse_args()
    for target in args.targets:
        rows = capture(target, classification_only=args.classification_only,
                       deterministic=args.include_deterministic)
        destination = DATA / 'inputs' / (Path(target).name + '.jsonl')
        write_jsonl(destination, rows)
        print(f'{destination.relative_to(ROOT)}: {len(rows)} prompts', flush=True)


if __name__ == '__main__':
    main()
