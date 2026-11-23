# Accuracy reference: juice-shop

This folder holds the hand-reviewed reference that measures the DPDP Compliance Auditor on the Target `juice-shop`.

- `juice-shop.json`: the reference list (`format_version` 1), pinned to commit `c9f99228d9d56afb5f5ca7925376292f7fa44b13`.
- `README.md`: this review procedure and its limitations.

## Scope

- Issue Types: the 36 catalogue IDs in `docs/issue-types.md`, listed in `scope_issue_types`. Items the catalogue marks as not checkable from code have no ID and are excluded.
- Exclusions (contract): `data/static/codefixes/**`, `test/**`, `frontend/**/*.spec.ts`.
- Each entry is one distinct mishandling at one anchor. Only `confirmed` entries count toward the denominator. `not-determinable` entries carry a reason and are excluded from scoring.
- Counts at this pin: 52 entries, 47 confirmed, 5 not-determinable.

## Independence

- Labels come from reading the pinned Target source and `docs/issue-types.md`. `CONTEXT.md` and `AGENTS.md` set the vocabulary.
- Not consulted: `reports/`, `auditor/rules/`, `rules/semgrep/`, `corpus/`, `RULES.md`, `tests/`, `.dpdp-cache`, any Findings, and no `dpdp-audit` run.
- `data/static/challenges.yml` was read after the code review and used only for `leads`. Each lead was checked in the code at its anchor. A lead never sets a label, status or denominator.

## Review procedure

1. Confirm the pin and a clean working tree.
2. Read the Issue Type rows and gates in `docs/issue-types.md`.
3. Review each surface and record candidate anchors with line numbers:
   - `server.ts` and `routes/`: route guards, query parameters, responses, logging.
   - `models/` and `lib/insecurity.ts`: storage, hashing, keys, tokens, cookies.
   - `frontend/src/app/`: browser storage, notice text, consent UI.
   - `terraform/` and `infrastructure/terraform/`: listeners, storage, backup, network rules, log retention.
   - `config/` and `monitoring/`: retention and alerting settings.
4. Check each gate. A gate that is not met produces no entry (see the gate table).
5. Choose the status. `confirmed`: the Issue Type condition holds at the anchor from code. `not-determinable`: a fact needs runtime data or a legal judgement.
6. Consult `challenges.yml` and add a lead only where the code at the anchor matches.
7. Mask all key material, hashes, TOTP values, card numbers and seeded personal data. Refer to them by location only.

## Anchor policy

- Anchor at the Processing Operation that handles or exposes a Personal Data Element (CONTEXT.md). For absences (no erasure, no correction route, no backup), anchor at the operation or route that should exist.
- The same Issue Type at two sites gives two entries. One root cause under two Issue Types gives one entry per Issue Type.
- Both Terraform trees are listed where the same fact appears in both. `networking.tf` is identical in both trees; `main.tf` and `variables.tf` carry the same facts at the same lines.

## Judgement calls to check first

| Entry | Call |
|---|---|
| REF-005 | HMAC with a constant key is treated as weak hashing (SEC-04). |
| REF-025 | Token readability is an [INFERENCE] from the JWT format; no token was decoded. |
| REF-037 | JSONP read is treated as cross-origin disclosure under SEC-11. |
| REF-038, REF-039 | Port 80 forward is treated as plaintext transport of Personal Data. |
| REF-044 | The Grafana dashboard counts as monitoring config that covers no access-log events (MON-01). |
| REF-048 | Email has no correction route while username is editable (RIG-02). |
| REF-051, REF-052 | Region eu-west-1 is confirmed on the code fact; docs/issue-types.md marks TRF-02 as Needs Legal Review. |
| REF-020 | Masked-email identifiability and order-id guessability are not determinable from code. |

## Gate table

| ID | Outcome | Basis |
|---|---|---|
| SEC-01 | applies | REF-001 |
| SEC-02 | applies | REF-002, REF-003 |
| SEC-03 | not applicable | No Aadhaar handling; repo-wide search returned no matches. |
| SEC-04 | applies | REF-004, REF-005, REF-006 |
| SEC-05 | applies | REF-007, REF-008 |
| SEC-06 | not determinable | REF-009 |
| SEC-07 | applies | REF-010 to REF-019; not determinable REF-020 |
| SEC-08 | applies | REF-021 to REF-027 |
| SEC-09 | applies | REF-028, REF-029 |
| SEC-10 | applies | REF-030 to REF-034 |
| SEC-11 | applies | REF-035 to REF-039 |
| SEC-12 | gate not met | A request logger is configured (server.ts L370). |
| SEC-13 | applies | REF-040 |
| SEC-14 | applies | REF-041, REF-042 (persistent store present, no backup) |
| SEC-15 | not applicable | Gate excludes seed and demo data; only seeded demo accounts exist (data/static/users.yml). |
| SEC-16 | not applicable | EFS port 2049 is open only to the ECS security group (networking.tf L228-233); container runs as non-root (Dockerfile L39, USER 65532); no aws_s3_bucket resource. |
| CON-01 | gate not met (judgement) | Account, order and chat processing are user-initiated and covered by the voluntary-provision legitimate use. |
| CON-02 | no finding | Several Purposes exist, but no consent request exists to bundle. |
| CON-03 | gate not met | No consent control; frontend/src/app/register/register.component.html has no checkbox or consent text. |
| CON-04 | gate not met | No consent grant. |
| CON-05 | not determinable | REF-043 |
| CON-06 | gate not met | No consent grant. |
| CON-07 | gate not met | No consent requested. |
| CON-08 | gate not met | The notice states no Purpose. |
| RET-01 | applies | REF-045 |
| RET-02 | applies | REF-046 |
| RET-03 | not applicable | Third Schedule class not established from code. |
| RIG-01 | applies | REF-047 |
| RIG-02 | applies | REF-048 |
| RIG-03 | no finding | A contact exists in the notice (privacy-policy component L167). |
| RIG-04 | not determinable | REF-049 |
| CHI-01 | gate not met | No age or DOB is collected (register form and user model); the notice excludes under-18s (L145-150). |
| CHI-02 | gate not met | Depends on CHI-01. |
| TRF-01 | not determinable | REF-050 |
| TRF-02 | applies | REF-051, REF-052 |
| MON-01 | applies | REF-044 (monitoring config present, no access-log coverage) |

## Out of catalogue (documented, not labelled)

- SQL injection in `routes/login.ts` L34, on the same line as REF-006.
- NoSQL `$where` injection in `routes/trackOrder.ts` L18 and `routes/showProductReviews.ts` L36.
- `routes/saveLoginIp.ts` L18-20 trusts a client-supplied `True-Client-IP` header for `lastLoginIp`. This affects data accuracy and has no catalogue ID.
- `totp_tmp_token` written to localStorage (`frontend/src/app/login/login.component.ts` L118) is omitted. Its payload carries only a user id and a type.
- Chat conversation storage in the browser was not reviewed in depth and is not labelled.
- Order ids include an MD5 prefix of the customer email (`routes/order.ts` L38-40). Not labelled; it supports the REF-020 judgement.
- A binary file in `ftp/` was not opened and is not labelled.
- Seeded accounts in `data/static/users.yml` are excluded under SEC-15. Their values are not reproduced.

## Secrets

`lib/insecurity.ts` L21 and L42 contain key material. The reference refers to them by location only; the values are not reproduced in the JSON, this README, or any output.

## Limitations

- Static review only. Nothing was built, run or queried. Runtime behaviour (errorhandler output at REF-009, token readability at REF-025) is inferred from code.
- Third-party dependencies in `node_modules` were not inspected. No label depends on them.
- Terraform was read, not planned or applied. Region, listener and backup facts come from the files at the pin.
- Legal characterisation (TRF-02, CON-01, CON-05, TRF-01 disclosure) is a judgement. Statuses record the code fact only.
- Single reviewer. A second, independent read is needed before this reference scores a release.
- Line numbers apply to the pinned commit only.

## Validation

Run from the repository root:

- `jq empty accuracy/juice-shop.json`
- `jq '[.entries[] | select(.status=="confirmed")] | length' accuracy/juice-shop.json` should print 47.
- `jq '[.entries[] | select(.status=="not-determinable")] | length' accuracy/juice-shop.json` should print 5.
- For each entry, check the anchor at the pin with `sed -n 'START,ENDp' targets/juice-shop/FILE`.

## Published figures and reproduction

Pinned run: Juice Shop `c9f99228`, LLM verdicts from `omp` / `anthropic/claude-opus-5-5` (prompt versions in `cache/manifest.json`), replayed cache-only from `accuracy/cache/`.

| Population | TP | FP | FN | Precision | Recall |
|---|---:|---:|---:|---|---|
| Reference Target, canonical Findings vs 47 confirmed entries (5 not determinable excluded) | 45 | 8 | 2 | 0.8491 (45/53) | 0.9574 (45/47) |
| Labelled Corpus, Rule emissions on designed fixtures (one pair per Rule) | 65 | 0 | 0 | 1.0000 (65/65) | 1.0000 (65/65) |

The two populations are not comparable: corpus pairs are designed cases, one per Rule, and show only that each Rule fires on its true positive and stays quiet on its near-miss.

Previous published run (commit `7fb1236`, before the recall Rules): 16 TP, 6 FP, 31 FN; precision 0.7273, recall 0.3404. Its mismatches are adjudicated against the pinned code in `adjudication.md`: 29 Auditor misses, 4 Auditor false positives, 4 anchor disagreements, 0 label changes.

**Not a held-out figure.** The recall Rules added after that run (SEC-07 route authorisation, SEC-08 whole-model serialisation, SEC-09 query parameters, SEC-04/05/10/11 sites, the second Terraform tree, RET-01) were written from the gaps in `adjudication.md` on this same Target and revision. The Juice Shop figure therefore measures fit to this reference, not generalisation. The other three Targets (ai-kyc-platform, TrackMyRupee, singharya-e-kyc) gained no Findings from these Rules.

The 8 unmatched predictions: the 4 false positives and 1 anchor disagreement already adjudicated (MON-01-8c5728dfea11, RET-03-41bffe4101f9, SEC-02-0a13729d5971, SEC-02-0f4631e6a05d, SEC-02-e0994a7481e3), and 3 new sites the reference does not list: `routes/changePassword.ts:56` and `routes/resetPassword.ts:46` return the whole updated User row (the REF-026 pattern), and `routes/updateUserProfile.ts:42` sets the session cookie with no flags (the REF-036 pattern). They count as false positives because the reference is not edited after scoring. Still missed: REF-021 (anchor disagreement at `routes/authenticatedUsers.ts`) and REF-044 (MON-01, anchor disagreement).

**Why the cache was regenerated.** Commit `69ac7bf` replaced the replay cache, the Juice Shop Report, `accuracy/results.md` and the manifest together. The previous manifest named `anthropic/claude-haiku-5-5` with `triage-v1` and `consent-v1`. The current manifest names `anthropic/claude-opus-5-5` with `triage-v2` and `consent-v2`; `classification-v1` and `fix-v1` are unchanged. A cache key covers the model, the prompt version and the masked context, so the model change re-keyed all four roles, not only triage and consent. The `-v2` prompts also changed the context: triage and consent now carry the retrieved Provisions (triage also the retrieved examples), and every citation must come from that retrieved set. The commit removed 178 cache entries and added 192: 79 classification-v1, 64 triage-v2, 1 consent-v2 and 48 fix-v1, all recorded as `omp` / `anthropic/claude-opus-5-5`. A cache-only replay of the regenerated cache gives 208 hits and 0 misses, and reproduces the precision and recall in the table above (0.8491 and 0.9574). All 159 Juice Shop citations resolve in the registry and appear in the retrieved set of their verdict.

Reproduce:

```sh
dpdp-audit accuracy targets/juice-shop --cache-only --cache-dir accuracy/cache
```

The run prints `reproduces published run: yes` only when the target commit, Rules digest, provider, model, prompt versions and the miss counts all match `cache/manifest.json`. The published run has no unassessed field (208 cached verdicts). After a Rule or prompt change, refill the cache with a live run (`dpdp-audit scan targets/juice-shop --provider omp --model anthropic/claude-opus-5-5 --cache-dir accuracy/cache`) and regenerate the manifest with `--write-manifest`.

Each run also writes a reproducible results summary (metrics, the command, the Rules digest) to `accuracy/results.md`. Use `--results PATH` to write it elsewhere, for example `--results /tmp/results.md` to leave the committed file untouched.

### Cache-only replay timings

The Labelled Corpus fixtures use one batched Semgrep run. Corpus evaluation now overlaps the Target scan, and fixtures whose inventory cannot produce TypeScript Data Flows skip the Node flow analyser. The Target still runs Semgrep in parallel chunks.

The table gives three wall-clock timings in seconds per condition, with the **one-minute load average at the start of each run** in parentheses. Both versions ran the cache-only Juice Shop command above with `--provider omp --model anthropic/claude-haiku-5-5` and temporary paths for `--results` and `--out`. Timings include generation of the JSON, Markdown, HTML and PDF Reports. No live provider was contacted.

The timings section was written at commit `0189aee`, when the manifest named `anthropic/claude-haiku-5-5` and the v1 prompts. The cache was regenerated in `69ac7bf` for `anthropic/claude-opus-5-5` (see above), so `--model anthropic/claude-haiku-5-5` in the timing command no longer matches any cached verdict.

Cold runs started without Semgrep results; each warm run immediately followed its cold run using the same cache. Semgrep results live in `.dpdp-cache/semgrep/` by default and are keyed on the Semgrep version, the Rule YAML bytes and the scanned files' bytes. Set `DPDP_SEMGREP_CACHE` to an empty directory for a cold run without altering the default cache.

| Machine | Semgrep cache | Before: seconds (load) | After: seconds (load) |
|---|---|---|---|
| A4000 host (Xeon Gold 6226R, 64 logical CPUs) | Cold | 99.24 (0.22), 35.68 (8.72), 37.35 (5.68) | 30.91 (3.32), 30.83 (5.05), 31.37 (8.12) |
| A4000 host | Warm | 27.13 (1.86), 25.74 (7.44), 24.35 (5.17) | 22.41 (5.75), 22.62 (4.84), 21.83 (7.92) |
| Local workstation (Core Ultra 9 285H, 16 logical CPUs) | Cold | 45.65 (8.66), 38.16 (14.19), 39.57 (13.69) | 28.06 (11.17), 29.12 (12.52), 29.54 (14.87) |
| Local workstation | Warm | 27.75 (14.45), 26.87 (13.59), 26.61 (12.98) | 19.10 (12.32), 22.78 (11.95), 19.03 (18.50) |

The A4000 cold replay now takes about **31 seconds**, just over the 30-second target. A separate instrumented cold replay took 29.66 seconds. All three local cold runs met the target. Load varied across both series, and the first A4000 baseline (99.24 seconds) was an unexplained outlier.

In the A4000 cold profile, Target Semgrep was the largest measured scan phase (10.20 s before, 9.44 s after). Rule evaluation was 6.51/6.00 s, the two Target TypeScript analyser calls totalled 2.87/3.03 s, and LLM cache replay took 0.07/0.07 s (208 hits). Corpus prewarm was 2.73/3.37 s, included in the full corpus time of 7.11/6.09 s. The corpus overlapped the Target scan only after the change; its TypeScript flow subprocess count dropped from 130 to 2.

Before and after, the Juice Shop Findings and Labelled Corpus results matched, and the accuracy Markdown was byte-identical. After excluding the scan timestamps, the full JSON Reports also matched for Juice Shop and the three Secondary Targets.
