# Eight-step demo script

Follows [docs/plan.md](../docs/plan.md#submission); terms follow [CONTEXT.md](../CONTEXT.md). Every Report, recording and pin used below is listed in [dashboard/recordings/manifest.json](../dashboard/recordings/manifest.json).

## Before you start

```sh
.venv/bin/python -m uvicorn dashboard.backend.app:app --host 127.0.0.1 --port 8000   # open http://127.0.0.1:8000/
```

Build the UI once with `npm --prefix dashboard/frontend ci && npm --prefix dashboard/frontend run build` if `dashboard/frontend/dist/` is absent. The header badge (`data-testid="provenance"`) shows the mode of the open run: `live`, `cache-only` (a live scan whose LLM provider was unreachable, so uncached LLM fields are "not assessed") or **Replay Mode**.

**Replay Mode** plays back a recorded scan: events arrive at their recorded offsets, and the run ends at the recorded Report. It never calls the scanner, an LLM provider or the Target Application. Run-level actions that write (Live Probes, Open PR) are not offered, and the service answers 409 if they are called. Replay Mode never publishes anything. Recorded times, provider verdicts, test outcomes and re-scan results are past results, not new measurements; say so aloud.

Recorded runs: click **Replay Mode (recorded Juice Shop scan)** or the button for another Target Application (`GET /api/replays` lists them). Choose one mode per step and keep to it.

| Path | Needs |
|---|---|
| Live | `targets/juice-shop` at `c9f99228d9d56afb5f5ca7925376292f7fa44b13`, `.venv`, Node; Docker for step 6; the fork checkout and GitHub authorization for step 7 |
| Recorded | the repository only |

## Step 1: Scan Juice Shop

**Live:** enter `targets/juice-shop` and start the scan (about 20 s cache-only; longer with a reachable provider). To see the cache-only disclosure without a provider, start the service with `DPDP_LLM_PROVIDER=ollama OLLAMA_HOST=http://127.0.0.1:1`.
**Recorded:** click **Replay Mode (recorded Juice Shop scan)**.
**Expected state:** the stages `inventory`, `elements`, `data_flows`, `findings` complete in that order, the run ends `completed`, Findings are listed by Severity band, and the Report downloads (json, md, html, pdf) are offered. The recorded run shows the **Replay Mode** badge. The scanned Findings count is 21; the recorded Report holds one more because of the Live Probe outcome in step 6.

## Step 2: Personal Data Map

**Live:** open the Personal Data Map table of the finished run.
**Recorded:** same view in the replayed run.
**Expected state:** rows for `email`, address-like Elements and the card number, each with Processing Operations and `file:line` Evidence. Values are masked; no Personal Data or Authentication Secret literal appears.

## Step 3: `/rest/memories` Finding detail

**Live:** open the SEC-07 Finding for `/rest/memories` (`SEC-07-2d4f025671b7`).
**Recorded:** same Finding in the replayed Report.
**Expected state:** highlighted Evidence lines, the Data Flow steps, the primary Provision with its statute excerpt and Penalty Ceiling, the Severity justification and the recommended fix. Severity is whatever the Report records (band `high` in this Report); do not override it in the narration. In Replay Mode the Finding also shows its past Live Probe Evidence (step 6).

## Step 4: Coverage Matrix

**Live:** download the Report as html or md and open the Coverage Matrix section.
**Recorded:** the same download from the replayed run.
**Expected state:** each Issue Type is marked static, live-testable, not code-checkable or not determinable. SEC-03 and CHI-* show "covered, not exercised on a real Target" where no real Target exercised them. The dashboard has no separate Coverage Matrix view; it is read from the Report.

## Step 5: Consent Assessment (TrackMyRupee)

**Live:** scan `targets/trackmyrupee` (pinned at `47990e4f19d7debea70c5d56bab77e3c3f051546`), then open the Consent Assessment section of its html or md Report.
**Recorded:** click **Replay Mode (recorded trackmyrupee scan)**, then open the same section.
**Expected state:** the seven criteria (recorded, specific, enforced server-side, withdrawable with comparable ease, propagated to Data Processors, preceded by notice, verifiable parental consent), each with Evidence or a "not determinable" reason, and the grant and withdrawal step counts the Report records.

## Step 6: Live Probe Confirm

**Live:** needs an authorized, dedicated, synthetic instance of the pinned image (commands in [docs/live-probes.md](../docs/live-probes.md)). With the live Juice Shop run open, enter `http://127.0.0.1:3000`, tick the authorization box and click **Run Live Probes**.
**Recorded:** open the recorded Juice Shop run and the `/rest/memories` Finding. The Live Probes panel is absent in Replay Mode.
**Expected state:** live, the Finding carries **Live Probe: Confirmed** with masked method, route and status only. Recorded, the same banner is a past outcome from the pinned image `dpdp/juice-shop:c9f99228`; the manifest records the image revision and digest. The recorded probe also confirmed SEC-11 (wildcard CORS), RET-02 (account still readable after the erasure request) and an additional SEC-08 Finding (`SEC-08-a0e14c48e6ad`); cookie, transport, consent-after-withdrawal and comparable-ease checks were inconclusive.

## Step 7: Open PR

**Live:** needs the authorized Juice Shop fork (see [docs/fix-patches.md](../docs/fix-patches.md)). Select the accepted Fix Patches, give the review branch, tick the authorization box and click **Open PR**.
**Recorded:** do not click anything that writes. Show the existing reviewed pull request <https://github.com/TanKaizokuO/juice-shop/pull/1> (head `2a66c603ea543aea6ab642c472431a27846b9e63`, base `c9f99228d9d56afb5f5ca7925376292f7fa44b13`) and its Code Scanning results.
**Expected state:** live, the Fix Patches and the new PR link appear. Recorded, only that existing reference is shown, and no PR, branch or file is created.

## Step 8: Re-scan

**Live:** scan the fork checkout (`targets/juice-shop-fork`, branch `dpdp-fix-patches`, head `2a66c603ea543aea6ab642c472431a27846b9e63`) and compare it with the base Report:

```sh
.venv/bin/python demo/compare_reports.py reports/juice-shop/report.json reports/juice-shop-fork/report.json
```

**Recorded:** click **Replay Mode (recorded juice-shop-fork scan)**, then run the same comparison command (it reads the committed Reports only).
**Expected state:** `gone` lists `RET-02-4696497b9137`, `SEC-01-d85a743d0415` and `SEC-13-394d3dbca514`; `new` is empty. The pinned Report has no SEC-09 Finding, so the password-query group verifies SEC-01 removal only. `RET-03` persists with a moved Evidence line range (a new id for the same Rule, Element and file); it is a Conditional Finding the patch does not address. This is the recorded re-scan, not a new measurement.

## Fallback when live scanning is unavailable

Live scanning can fail for a missing clone, Node, an unreachable provider or no network. Then:

1. Say "this is Replay Mode" and use only the **Replay Mode** buttons for steps 1, 2, 3, 5, 6 and 8.
2. Take steps 4 and 5 from the downloaded recorded Report.
3. Take step 7 from the existing pull request; do not open another.
4. Run `.venv/bin/python -m pytest -q tests/test_submission_package.py` to show that the recordings, pins and Reports still agree.

An unreachable LLM provider alone does not stop a live scan: it runs cache-only and discloses uncached fields as "not assessed".
