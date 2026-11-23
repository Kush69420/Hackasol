"""Legal view of a completed run: Penalty Ceilings per Provision and the Enforceable From timeline."""
import datetime as dt
import json

from fastapi import APIRouter, HTTPException

from auditor import legal_view
from auditor.registry import load_registry


def router(get_run):
    api = APIRouter()

    @api.get('/api/scans/{run_id}/legal')
    def legal(run_id: str, as_of: str | None = None):
        run = get_run(run_id)
        if run.status != 'completed' or run.report_dir is None:
            raise HTTPException(409, f'Report not available: run is {run.status}')
        try:
            reference = dt.date.fromisoformat(as_of) if as_of else None
        except ValueError:
            raise HTTPException(422, 'as_of must be an ISO date')
        report = json.loads((run.report_dir / 'report.json').read_text(encoding='utf-8'))
        return legal_view.legal_view(report, load_registry(), as_of=reference)
    return api
