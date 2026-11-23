# Fix Patches

`dpdp-audit fix generate --report REPORT.json --finding FINDING-ID --out PATCH.json` asks the configured LLM provider for a unified diff. Evidence and guidance are masked before egress and cached. Review the diff; generation alone does not establish that it works.

`dpdp-audit fix verify TARGET --report REPORT.json --patch PATCH.json` applies the selected diffs together in a temporary copy and re-scans. Pass `--patch` repeatedly for a combined evaluation. The Target Application must be clean and at the Report revision. The original Finding must not persist at the same Rule and Evidence file, even after line movement; any new Evidence is rejected conservatively. Re-scan exclusions must match. `--test-command` records a Target test command's exit status separately from the acceptance decision. Test dependencies must be available for meaningful Target test results. Disappearing Findings do not establish compliance.

`dpdp-audit scan TARGET --format sarif` writes SARIF 2.1.0 derived from the Report. Evidence paths are target-relative and messages are masked.

## CLI workflow

```
dpdp-audit fix generate TARGET --report REPORT.json --finding FINDING-ID --out PATCH.json [--provider P] [--model M]
dpdp-audit fix verify   TARGET --report REPORT.json --patch PATCH.json [--patch ...] [--test-command CMD ...]
dpdp-audit fix publish  TARGET --report REPORT.json --patch PATCH.json [--patch ...] \
    --destination TanKaizokuO/juice-shop --branch BRANCH [--base dpdp-pinned-base] --authorize
```

`generate` writes the patch and records it on the Finding's `fix_patch` in the Report (exit 1 if rejected). `verify` re-scans the combined diffs and sets each patch's status to `accepted` or `rejected` (exit 0 only when accepted), with the remaining and new Findings and Target test result in `reason`.

## Authorized publish

Opening a PR is a GitHub write and is refused unless every condition holds (`auditor/fixpatch/publish.py`):

- `--authorize` (CLI) or the explicit authorization checkbox (dashboard) is given; a scan or a verify alone never creates a branch or PR.
- The destination is exactly `TanKaizokuO/juice-shop`; upstream `juice-shop/juice-shop` and any other destination are refused. The dashboard backend rejects a wrong destination before reading the Report, and the dashboard disables Open PR.
- Every patch is `accepted`, the base is `dpdp-pinned-base`, the review branch is valid and differs from the base, and the fork base commit equals the Report revision.
- A fresh combined re-scan accepts the patches (selected Findings absent, no new Finding). The PR body states that a re-scan is not a certification of compliance.

The dashboard's Fix Patch review (live Reports only) shows the destination fork, review branch and base, the diffs grouped by Issue Type with each re-scan status, and then calls `POST /api/scans/{run_id}/fix-patches/publish`. Playwright coverage is `dashboard/frontend/e2e/fix-patches.spec.ts`; it uses a route-intercepted fake publisher, so no GitHub write occurs in tests.

## Results at the pinned Juice Shop revision

| Item | Result |
|---|---|
| Review PR | https://github.com/TanKaizokuO/juice-shop/pull/1 (Fix Patches for SEC-01 password change, SEC-13 log configuration, RET-02 erasure) |
| Code Scanning (SARIF upload) | https://github.com/TanKaizokuO/juice-shop/security/code-scanning |
| Combined re-scan of the PR revision | baseline 21 Findings → 18; the three targeted Findings are gone; none new |
| Target tests, frontend | 1 failed / 1,457 passed (the failing test expects the previous GET contract) |
| Target tests, server | timed out: 395 passed / 1 failed / 1 cancelled / 2 skipped |

Disappearing Findings do not establish compliance; the Target test failures are recorded, not hidden.

## SEC-09

The pinned Juice Shop Report identifies password-change logging as `SEC-01-d85a743d0415` at `frontend/src/app/Services/user.service.ts:54–55` and `server.ts:370`. It emits no SEC-09 Finding; a password-change group can therefore verify SEC-01 removal only, not SEC-09 removal.
