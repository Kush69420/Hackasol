"""Publish reviewed Fix Patches only after a fresh re-scan and authorization."""
import json
import subprocess

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, StrictStr

from auditor.fixpatch.publish import DESTINATION, publish


class PublishRequest(BaseModel):
    destination: StrictStr
    branch: StrictStr
    finding_ids: list[StrictStr]
    authorized: bool = False


def router(get_run):
    api = APIRouter()

    @api.post('/api/scans/{run_id}/fix-patches/publish')
    def open_pr(run_id: str, body: PublishRequest):
        # Replay Mode never publishes, whatever the request says; check the run first.
        scan = get_run(run_id)
        if scan.status != 'completed' or scan.report_dir is None or scan.mode == 'recorded':
            raise HTTPException(409, 'A completed live Report is required')
        if not body.authorized:
            raise HTTPException(422, 'Explicit authorization is required')
        if body.destination.lower() != DESTINATION.lower():
            raise HTTPException(422, 'Destination must be the authorized fork, not upstream')
        try:
            report = json.loads((scan.report_dir / 'report.json').read_text(encoding='utf-8'))
            selected = set(body.finding_ids)
            findings = [f for f in report['findings'] if f['id'] in selected]
            if not selected or len(findings) != len(selected):
                raise ValueError('Select Findings from this Report')
            groups = {}
            for finding in findings:
                patch = finding.get('fix_patch')
                if not patch or patch['status'] != 'accepted':
                    raise ValueError('Every selected Fix Patch must be accepted')
                group = groups.setdefault(patch['diff'], {'diff': patch['diff'], 'status': 'accepted', 'finding_ids': []})
                group['finding_ids'].append(finding['id'])
            result = publish(scan.target, report, list(groups.values()), destination=body.destination,
                             base='dpdp-pinned-base', branch=body.branch, authorized=True)
            return {'url': result['url']}
        except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
            raise HTTPException(422, type(exc).__name__) from exc
    return api
