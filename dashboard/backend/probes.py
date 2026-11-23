"""Run Live Probes against an explicitly selected dedicated instance."""
import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, StrictStr

from auditor.probes import run
from auditor.report import write_reports


class ProbeRequest(BaseModel):
    target: StrictStr
    authorized: bool = False


def router(get_run):
    api = APIRouter()

    @api.post('/api/scans/{run_id}/probes')
    def probe(run_id: str, body: ProbeRequest):
        if not body.authorized:
            raise HTTPException(422, 'Explicit authorization is required')
        scan = get_run(run_id)
        if scan.status != 'completed' or scan.report_dir is None or scan.mode == 'recorded':
            raise HTTPException(409, 'A completed live Report is required')
        path = scan.report_dir / 'report.json'
        try:
            report = json.loads(path.read_text(encoding='utf-8'))
            results = run(report, body.target)
            write_reports(report, path)
        except (OSError, ValueError) as exc:
            raise HTTPException(422, str(exc)) from exc
        return {'results': results, 'report': report}

    return api
