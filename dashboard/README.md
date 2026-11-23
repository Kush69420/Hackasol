# Dashboard and Replay Mode

A local, trusted-demo service that runs the Auditor on a Target Application, streams stage progress, and serves the Report. The flow follows P1.7 in [docs/plan.md](../docs/plan.md); terms follow [CONTEXT.md](../CONTEXT.md).

## Launch

```
.venv/bin/python -m uvicorn dashboard.backend.app:app --host 127.0.0.1 --port 8000
```

Bind to `127.0.0.1` only: the service accepts local paths, so it must not be exposed. The React app is served from `dashboard/frontend/dist/` at `http://127.0.0.1:8000/` once built.

## Accepted inputs

`POST /api/scans` with `{"target": "<input>"}`, where the input is an existing local directory (for example `targets/juice-shop`) or an `https://` Git URL. Anything else (empty, non-string, `-`-leading, containing whitespace or control characters, `http://`, a missing directory) is rejected with 422. Input is never passed to a shell.

## API

| Route | Result |
|---|---|
| `POST /api/scans` | 202 `{run_id, mode: "live"}` |
| `GET /api/replays` | `{recordings: [name, ...]}` for every bundle under `dashboard/recordings/` |
| `POST /api/replays/{name}` | 202 `{run_id, mode: "recorded"}`; 409 if the bundle format is incompatible; 404 if absent or the name is not `[a-z0-9][a-z0-9-]*` |
| `GET /api/scans/{run_id}` | `{run_id, mode, status: running\|completed\|failed, target}` |
| `GET /api/scans/{run_id}/events` | SSE; one `data: <json>` per event, from ordinal 0 for any client |
| `GET /api/scans/{run_id}/report/{json\|md\|html\|pdf}` | the artifact for that run; 404 unknown id/format; 409 while running or failed |
| `GET /api/provisions/{id}` | citation, title, statute excerpt, Penalty Ceiling, Enforceable From |

Event: `{run_id, ordinal, mode: live|cache-only|recorded, type: stage|completed|failed, stage?, elapsed_ms, message?, finding_count?}`. The four `stage` events (`inventory`, `elements`, `data_flows`, `findings`) are emitted by the Auditor as each stage finishes (`run_scan(..., on_stage=callback)`), followed by exactly one `completed` or `failed`. `completed` is sent only after all four Report files exist under `reports/dashboard/<run_id>/`. Events never carry Evidence excerpts; failure messages are masked.

## Replay Mode

`dashboard/recordings/<target>/` holds a versioned bundle: `recording.json` (`format_version`, Target Application commit, events with their recorded `elapsed_ms`) and the exact masked Report artifacts. Replay Mode emits each event at its recorded offset from replay start (mode `recorded`) and serves the bundle bytes unchanged. It calls neither the scanner nor the LLM and needs no `targets/` checkout. Cache-only scanning is different: it still scans, using the LLM cache. The Juice Shop bundle has 53 Findings; four carry forward Live Probe outcomes from the pinned image. TrackMyRupee carries forward outcomes on its Consent Assessment. See `live_probe_overlay` in the manifest.

Regenerate from the pinned Reference Target (`c9f99228d9d56afb5f5ca7925376292f7fa44b13`) with a warm `.dpdp-cache`:

```
DPDP_LLM_PROVIDER=omp DPDP_LLM_MODEL=anthropic/claude-opus-5-5 .venv/bin/python -m dashboard.backend.replay record targets/juice-shop   # likewise targets/<name>; the fork re-records from its PR head
```

The recorder checks the provider's availability. The published bundles were recorded with `omp` forced offline, so all verdicts came from the cache.

## Tests

```
.venv/bin/python -m pytest tests/test_dashboard.py -q            # -k live | replay | masking
```
