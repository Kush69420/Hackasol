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

Pinned run: Juice Shop `c9f99228`, LLM verdicts from `omp` / `anthropic/claude-haiku-5-5` (prompt versions in `cache/manifest.json`), replayed cache-only from `accuracy/cache/`.

| Population | TP | FP | FN | Precision | Recall |
|---|---:|---:|---:|---|---|
| Primary Target, canonical Findings vs 47 confirmed entries (5 not determinable excluded) | 16 | 6 | 31 | 0.7273 (16/22) | 0.3404 (16/47) |
| Labelled Corpus, Rule emissions on designed fixtures (one pair per Rule) | 40 | 0 | 0 | 1.0000 (40/40) | 1.0000 (40/40) |

The two populations are not comparable: corpus pairs are designed cases, one per Rule, and show only that each Rule fires on its true positive and stays quiet on its near-miss.

Every mismatch is adjudicated against the pinned code in `adjudication.md`: 29 Auditor misses, 4 Auditor false positives, 4 anchor disagreements, 0 label changes. Most misses are per-site counting: the reference lists each code site separately, while the Auditor reports one Finding per Element. The others are the second Terraform tree under `infrastructure/terraform/` and authorisation gaps (SEC-07) that have no Rule yet.

Reproduce:

```sh
dpdp-audit accuracy targets/juice-shop --cache-only --cache-dir accuracy/cache
```

The run prints `reproduces published run: yes` only when the target commit, Rules digest, provider, model, prompt versions and the miss counts all match `cache/manifest.json`. The published run itself left one field unassessed. After a Rule or prompt change, refill the cache with a live run (`dpdp-audit scan targets/juice-shop --provider omp --cache-dir accuracy/cache`) and regenerate the manifest with `--write-manifest`.
