# Build plan

Goal: win CS-01. One builder orchestrating coding agents, no time limit.
- **P1 delivers every must-have feature as a real solution to the problem statement**, ending with the Juice Shop Report and all three deliverables.
- **P2 adds the three bonus features.**
- Nothing is cut: work for other frameworks and Targets is sequenced after the Juice Shop exit, not dropped.

Vocabulary follows CONTEXT.md; Issue Types, Gates and Provisions follow docs/issue-types.md; decisions follow docs/adr/.

## What a real solution means here

PS.md asks for a tool that checks "what the code actually does with personal data", including back-end services, APIs, databases, third-party integrations and cloud configuration. A keyword scanner that flags `email` or `password` does not meet that bar. Every P1 Finding must therefore come from:

1. a **Personal Data Element** found in a schema, form, route or config, with its Data Category;
2. a **Processing Operation** (Collect / Store / Log / Transfer / Expose) traced across files, or a missing one anchored at an Anchor Point and allowed by its Gate;
3. **Evidence**: file, line range and excerpt, with secrets and Government Identifiers masked;
4. a **Primary Provision** (the most specific obligation) from the Provision registry, never cited from memory;
5. a **Severity** with a generated justification, per ADR 0002;
6. a **recommended fix** in words.

Each Finding is labelled as one of three kinds: DPDP obligation, security check that depends on personal data, or Safeguard. A security weakness with no shown link to Personal Data is reported as an observation without a DPDP Provision.

## Targets

- **Reference: OWASP Juice Shop, as-is, pinned to `c9f99228`.**
  - Excluded from the scan: `data/static/codefixes/` (deliberately vulnerable challenge variants, including `.tf` files), `test/` (includes `test/cypress/`), `frontend/**/*.spec.ts`.
  - The two Terraform trees (`terraform/`, `infrastructure/terraform/`) differ: scan both, merging identical resources.
- **ai-kyc-platform**: the first Target after the P1 exit, before P2, so Government Identifier and Biometric Findings appear in the demo.
- **TrackMyRupee**: P2.1, for its real consent code.
- **singharya E-KYC**: after P2.
- **No India overlay** on Juice Shop.

---

# P1: Must-have features

## P1.0 Foundation

- Layout:
  - Python package `auditor/` (CLI `dpdp-audit scan <path|git-url>`);
  - `rules/semgrep/` (one directory per Issue Type);
  - `auditor/analysers/` (Python config/IaC analysers) and `auditor/ts/` (TypeScript AST analyser, Node);
  - `corpus/` (Labelled Corpus), `dashboard/` (FastAPI + React), `targets/` (git-ignored, pinned clones), `reports/`.
- **Finding schema** (JSON; the contract every later step codes against):
  - id, Issue Type, Rules fired, kind;
  - Evidence (file, line range, masked excerpt), Data Flow steps;
  - Personal Data Element, Data Category (or the protected category for Elementless Findings), Processing Operation, Exposure + the Evidence it was derived from;
  - Primary Provision, other Provisions, Penalty Ceiling (parent section), Enforceable From;
  - CVSS 4.0 vector + score or N/A, Risk Matrix cell, Severity + justification;
  - recommended fix, status (open / Needs Legal Review / conditional), LLM triage verdict + reason + cache key;
  - reserved for P2: Live Probe outcome, Fix Patch.
- **Provision registry**: every Act section and sub-section and every Rule, with a text excerpt, parent section, Penalty Ceiling and Enforceable From (13 Nov 2026 for Rule 4; 13 May 2027 for Rules 3, 5–16, 22–23). Each entry is checked against the official Act, Rules (G.S.R. 846(E)) and commencement notice (G.S.R. 843(E)). Allied law and CWE/OWASP entries sit alongside.
- **Remediation catalogue**: written fix guidance per Issue Type, tailored to the Evidence by the LLM.
- **LLM layer** (ADR 0003): Anthropic, OpenAI, Gemini, Ollama and headless `omp` behind one interface. Outbound snippets are masked; verdicts are cached by snippet hash, prompt version and model.
- **Masking**: one function shared by LLM egress and Report Evidence (Authentication Secrets, keys, tokens, Government Identifiers).

Acceptance: `dpdp-audit scan targets/juice-shop` runs with an empty Rule set, applies the exclusions, and writes a schema-valid empty Report.

## P1.1 Application inventory (Juice Shop stack)

What exists in the Target, before any judgement is made.

- **API routes**: method, path, handler file:line, middleware chain (`security.isAuthorized()`, `appendUserId()` and others).
  - Explicit `app.get/post/put/delete/use` calls in `server.ts`, resolved to `routes/*.ts` handler factories.
  - **finale-rest generated routes**: read `finale.resource` registrations and the model list (`server.ts:520-545`), and emit the generated list and item endpoints per model (Users, Addresss, Cards and others).
  - `swagger.yml` merged where present; code is the source of truth.
- **DB schemas**: Sequelize `Model.init` fields with types and options (`paranoid`, defaults, validators) from `models/*.ts`, plus the MongoDB-style collections (`db.reviewsCollection`, `db.ordersCollection`).
- **Front end**: Angular templates, including Signal Forms, `UntypedFormControl` and `ngModel` bindings; their labels and i18n strings; server-rendered `views/*.hbs`; `index.html` scripts (cookie consent); client storage and outbound headers (`request.interceptor.ts`); Angular service URLs (`this.host + '/…'`).
- **Infrastructure and config**: Dockerfile (user, ports), `config/*.yml`, `app.json`, Terraform (region, log groups and retention, public IPs, security groups with ingress/egress direction and source, storage encryption), morgan and file-rotation settings, `.env*`.

Acceptance: the Juice Shop inventory lists every explicit route, every finale-generated endpoint, every model and collection, every Angular form and service URL, and every Terraform resource, each with file:line.

## P1.2 Personal data detection and Data Flows

- **Elements**: classify inventory fields, form inputs, route parameters and config values into Data Categories.
  - Signals: name dictionary (Juice Shop's `email`, `password`, `totpSecret`, `deluxeToken`, `lastLoginIp`, `profileImage`, `address` fields, `cardNum`, `wallet`, plus Indian identifiers with Hinglish variants); value validators (email, card + Luhn, phone, IP, Aadhaar + Verhoeff, PAN, IFSC, VPA); schema types; UI labels; LLM classification of anything unresolved.
- **Processing Operations within a function** (Semgrep OSS):
  - Store: ORM writes, files, client storage;
  - Log: loggers, `console.*`;
  - Transfer: HTTP clients, SDKs;
  - Expose: `res.json`/`res.send` of model instances, error pages.
- **Cross-file Data Flows** (TypeScript analyser, ADR 0003): Angular form → service URL → route → middleware → handler factory → model read/write → response serialiser.
  - Joins on method plus normalised path, and on model identity.
  - Records whether auth middleware is on the path, which feeds Exposure.
- **Configuration-driven operations** (Python analysers):
  - morgan format + stream → which request parts (URL, query, headers) are logged and for how long;
  - Terraform region → where stored data sits;
  - log retention settings.
- **Personal Data Map**: Elements × Processing Operations with Evidence, as its own Report section.

Acceptance:
- The Juice Shop Personal Data Map traces **email, address and card number** from the Angular form → route → Sequelize model → API response, with file:line at every step.
- It shows passwords reaching the access log through `GET /rest/user/change-password?current=&new=` (`routes/changePassword.ts:14-15` → `server.ts:370` morgan `combined`).

## P1.3 Checks

Every Rule ships with a Labelled Corpus pair (a true positive and a near-miss negative). Absence checks fire only when their Gate is met; otherwise the Coverage Matrix marks them "not determinable".

**Slice 1: Juice Shop, Evidence confirmed at `c9f99228`** (demo-ready first):

| Issue Type | Evidence | Kind |
|---|---|---|
| SEC-07 + SEC-08: user records exposed without login | `GET /rest/memories` (`server.ts:670`, no auth) → `routes/memory.ts:24` `findAll({ include: [UserModel] })` returns email, password hash, totpSecret | depends on personal data |
| SEC-09 + SEC-01: passwords in the URL, written to the access log | `server.ts:636`, `routes/changePassword.ts:14-15`; morgan `combined` at `server.ts:370` | depends on personal data |
| SEC-13: access log of Personal Data kept 2 days | `server.ts:368` `max_logs: '2d'` vs Rule 6(1)(e) and Rule 8(3) | DPDP obligation |
| SEC-08: every user's record shown to any logged-in user | `server.ts:430,640` → `routes/authenticatedUsers.ts:12-28` (email, lastLoginIp, everything but password/totpSecret) | depends on personal data |
| SEC-08: review authors' emails public | the Angular product-details page sends the signed-in user's email as `author` (`frontend/src/app/product-details/product-details.component.ts:80,91`); `routes/createProductReviews.ts:26` stores `req.body.author`; product reviews route returns it | depends on personal data |
| SEC-02: no field-level protection for TOTP secrets and card numbers | `models/user.ts:109` `totpSecret`, `models/card.ts:38` `cardNum` in plain columns. The disk itself is encrypted (EFS `encrypted = var.efs_encrypted` at `terraform/networking.tf:251`, default true at `terraform/variables.tf:70`; `transit_encryption = "ENABLED"` at `terraform/main.tf:84`), so severity reflects that residual risk only. Card numbers are masked in API responses (`routes/payment.ts:32`) | depends on personal data |
| SEC-04: weak password hashing | `lib/insecurity.ts:41` MD5 | depends on personal data |
| SEC-05: hard-coded JWT signing key protecting every session | `lib/insecurity.ts:21` | Safeguard (nexus: Authentication Secrets) |
| SEC-10: email stored in localStorage and attached to every outgoing request with no origin check | `frontend/src/app/login/login.component.ts:105-106` (stored when "remember me" is ticked); `frontend/src/app/Services/request.interceptor.ts:23` `X-User-Email`. Delivery to another site is unproven and left for a Live Probe | depends on personal data |
| RET-02: erasure request that only records a flag | `routes/dataErasure.ts:83-85` creates a request with `deletionRequested: true`; `models/user.ts:120` `paranoid: true` | DPDP obligation |
| RIG-01: data export omits most of the user's Personal Data | `routes/dataExport.ts:19-45` retrieves and `:68-108` returns username, email, memories, orders and reviews only; addresses, cards, wallet, security answer, `lastLoginIp` and TOTP are missing, vs §11(1)(a) | DPDP obligation |
| RIG-02: email cannot be corrected | `routes/updateUserProfile.ts:38` updates only the username, and no other route changes the email (addresses and password are editable, e.g. `server.ts:482`; cards can only be added or deleted), vs §12(2) | DPDP obligation |
| TRF-02: storage outside India | `terraform/variables.tf` `aws_region` default `eu-west-1` | Needs Legal Review |
| SEC-11: CORS wildcard on Personal Data routes | `server.ts:184-185` | Safeguard (nexus: routes above) |

- **Dropped from the slice:** SEC-16. The internet-facing ingress in `terraform/networking.tf:72,79` is the load balancer on 80/443, `:82-87` is egress, ECS tasks accept only the load balancer (`:101-106`), and `Dockerfile:39` runs as `USER 65532`.
- **Secondary SEC-13 evidence:** CloudWatch `retention_in_days = 30` (`terraform/main.tf:128`), reported only once the log group is shown to carry Personal Data.

**Slice 2: breadth on the Juice Shop stack.** All remaining Issue Types in docs/issue-types.md for TypeScript/Express/Sequelize/Angular and config, each with its Gate. Expected outcomes on Juice Shop:
- SEC-14 fires: SQLite sits on EFS (`terraform/networking.tf:249`) with no `aws_backup` plan or backup policy anywhere in Terraform;
- SEC-15 does not fire on `data/static/users.yml`: seeded fictional accounts are not real Personal Data (see its Gate);
- RIG-03 not raised: a complaint route (`server.ts:413-414`) and a contact page exist;
- RIG-04 not determinable: the erasure notice cites GDPR Art. 17, and no in-repo notice lists DPDP rights;
- MON-01 fires: `monitoring/grafana-dashboard.json` has business, challenge and runtime panels (HTTP Requests, User Signups) but none for access-log review or authentication events;
- CHI-01 not determinable (no age or DOB collection);
- RET-03 conditional (not a Third Schedule class);
- SEC-12 not raised (morgan access logging exists).

**Legal framing to apply:**
- Applicability Assumptions (§3; not a Significant Data Fiduciary; not Third Schedule; consent unless §7) are printed on every Report; Findings that depend on them say so.
- TRF-02 is a disclosure (§16 restricts only notified destinations). TRF-01 is a §11(1)(b) disclosure gap, not a §8(2) breach.
- §8(3) accuracy, §8(6)/Rule 7 breach intimation and §8(2) contracts appear in the Coverage Matrix as not code-checkable.

Acceptance:
- Every slice-1 Finding fires on Juice Shop with the Evidence above.
- No Finding comes from excluded paths.
- Every Issue Type has at least one Juice Shop-stack Rule whose Labelled Corpus pair passes.

## P1.4 DPDP mapping and risk classification

- Merging: several Rules on the same file:line become one Finding with Provisions unioned; one Rule on many lines becomes one Finding per line, grouped with a count.
- Primary Provision = the most specific obligation (e.g. Rule 6(1)(e), §12(3)). Penalty Ceiling comes from its parent section and breaks ties only.
- Severity per ADR 0002:
  - each Rule carries a base CVSS 4.0 vector;
  - CR comes from the Data Category (Financial is tier A / CR:H);
  - Elementless Findings use the category the weakened resource protects;
  - Exposure is derived from Evidence (no auth middleware on the path, or auth that anyone can obtain through open self-registration → Public; region outside India → Cross-Border; outbound to another organisation → Third-Party; authenticated users of a closed user base → Internal-Broad). Juice Shop's `POST /api/Users` (`server.ts:440`) is open, so `/rest/user/authentication-details` counts as Public;
  - disclosure Findings (TRF-01, TRF-02) are capped at Medium and labelled "disclosure";
  - the Risk Matrix orders Findings within a band and sets the band for Compliance Gaps.
- **Justification** generated from those inputs in one or two sentences, e.g. "Critical: password hashes and TOTP secrets (Authentication Secret, tier B) returned on an unauthenticated route (Public); CVSS 4.0 <score> (<vector>); Rule 6(1)(b) under §8(5), ceiling ₹250 cr."
- LLM false-positive triage: verdict and reason shown; a Finding is never dropped silently.

Acceptance: every Juice Shop Finding has a Primary Provision, Penalty Ceiling, Enforceable From, Severity and a justification naming its Data Category and Exposure.

## P1.5 Compliance report and Rules List

- JSON is the source of truth; Markdown and HTML are rendered from it; PDF is printed from the HTML.
- Report sections:
  1. Applicability Assumptions;
  2. executive summary: counts by Severity and kind, top penalty exposure, what to fix before 13 May 2027;
  3. Personal Data Map;
  4. Findings: file, line, Evidence, Data Flow, Provisions, Severity + justification, recommended fix;
  5. Coverage Matrix: every Act section and Rule marked static / live-testable / not code-checkable / not determinable, with covering Rules; Child Data marked "covered, not exercised on a real Target";
  6. method, accuracy and limitations (LLM provider, model, prompt version, cache).
- **Rules List** (deliverable 3), generated from the Rule files: Issue Types with nested Rules, languages, Gates, Provisions, CWE and a Labelled Corpus example.

Acceptance: `reports/juice-shop/` contains JSON, Markdown, HTML and PDF with no unmasked secret; the Rules List is committed.

Commands: `dpdp-audit scan targets/juice-shop` writes `reports/juice-shop/report.{json,md,html,pdf}` from one scan (PDF via WeasyPrint, which needs the system Pango libraries); `dpdp-audit rules list > RULES.md` regenerates the Rules List, and `dpdp-audit rules list | diff -u RULES.md -` checks it is current.

## P1.6 Accuracy

- **Ground truth**: hand-checked list of Juice Shop's Personal Data mishandling at `c9f99228`, built from the code. `data/static/challenges.yml` (118 challenges, about 42 involving personal data) is used only as hints.
- Report precision and recall against that list, plus Labelled Corpus precision and recall per Rule in CI. LLM verdicts are replayed from the cache so the figures reproduce.
- **Commands**: `dpdp-audit accuracy targets/juice-shop --cache-only [--reference accuracy/juice-shop.json] [--cache-dir accuracy/cache]` runs a cache-only scan, refuses a Target revision that differs from the reference pin, scores canonical Findings, evaluates the Labelled Corpus, attaches `report["accuracy"]` and writes all four Report formats. `dpdp-audit accuracy --corpus-only` evaluates only the Labelled Corpus (used by `.github/workflows/accuracy.yml`) and exits non-zero when a Rule's pair is missing.
- **Comparison**: one canonical Finding is one prediction; it matches one confirmed reference entry when the Issue Type and file are equal and Evidence overlaps the reviewed anchor range. Matching is one-to-one in Finding id order; a second prediction for a matched entry is a false positive; not-determinable entries are excluded and listed with their reason. Precision = TP/(TP+FP), recall = TP/(TP+FN), N/A for a zero denominator, counts always shown.
- **Two populations**: Reference Target rows count canonical Findings; Labelled Corpus rows name the Rule and count fixture emissions (positive: TP or FN; negative: FP or TN). They are never combined.
- **Cache replay**: `accuracy/cache/manifest.json` records the Target revision, a Rules digest (sha256 over `auditor/rules/*.py` and `rules/semgrep/**/*.y*ml`), provider, model, prompt version and the cache identity (masked snippet, prompt version, model). A cache miss is "not assessed", is counted in the Report, and means the run does not reproduce the published figures. A Rule or prompt change invalidates the manifest; regenerate it with `--write-manifest` and document why.
- **Limits**: one Target at one revision; hand-checked list; Labelled Corpus fixtures are designed cases, not a sample of real code.

Acceptance: precision and recall published in the Report for Juice Shop and the Labelled Corpus.

## P1.7 Dashboard and demo safety

- Dashboard flow:
  - paste a repo URL or path;
  - streamed progress (inventory → Elements → Data Flows → Findings);
  - Findings by Severity;
  - Finding detail: Evidence with highlighted lines, Data Flow graph, Provisions with statute excerpt, Penalty Ceiling, justification, recommended fix;
  - Personal Data Map;
  - Report download.
- Replay Mode recording of the Juice Shop scan.

Acceptance: a full Juice Shop demo runs live and in Replay Mode.

## P1.8 ai-kyc-platform (after the P1 exit, before P2)

- Scan the pinned Secondary Target using the supported Next.js, Django and FastAPI idioms; see [Target layout, scan commands and limits](targets/ai-kyc-platform.md), the generated [Rules List](../RULES.md), and `reports/ai-kyc-platform/` for the four Report formats.

Acceptance: `reports/ai-kyc-platform/` exists with Government Identifier Findings masked in Evidence.

**P1 exit (all must-haves and deliverables; P1.0–P1.7 only, P1.8 not required):**
- scanner and source pushed;
- Juice Shop Report;
- Rules List published;
- accuracy figures shown.

---

# P2: Bonus features

## P2.1 Consent Assessment

- Model Purposes, Consent Records, Enforcement Points and Withdrawal Paths from code; the LLM reasons across files, grounded in the deterministic inventory.
- Evaluate the seven criteria (recorded, specific, enforced server-side, withdrawable with comparable ease, propagated to Data Processors, noticed, verifiable parental consent) with Issue Types CON-01…07 and their Gates.
- **Juice Shop**: has only a cookie banner (`frontend/src/index.html:19`) and no analytics, so most criteria come out "not applicable". The Report says so with Evidence, rather than inventing Findings.
- **TrackMyRupee** carries the depth: Django support added here (models, views, middleware, templates); `ConsentEvent`, `consent_granted` middleware gate, `WithdrawConsentView`, PostHog gating.
- Static step count, grant vs withdraw.

Acceptance:
- a TrackMyRupee Consent Assessment covering all seven criteria with Evidence;
- the Juice Shop Report's Consent Assessment states applicability per criterion.

## P2.2 Fix Patches and pull requests

- LLM-generated Fix Patch per Finding, built on the recommended fix.
- Validation:
  - apply the patch to a scratch copy and re-scan: the Finding must be gone and no new Finding may appear;
  - run the Target's unit tests and report results. Juice Shop's challenge-verification tests may intentionally fail once a vulnerability is fixed (unverified), so failures are shown, not treated as blocking.
- "Open PR" groups accepted patches by Issue Type onto a branch of our Juice Shop fork.
- SARIF 2.1.0 output added here and uploaded so Code Scanning annotates the fork.

Acceptance: a PR on our Juice Shop fork fixing SEC-09/SEC-01 (change-password via POST body), SEC-13 and RET-02, with a re-scan showing those Findings gone.

## P2.3 Live Probes

- Allowed targets: localhost and an explicit allowlist only.
- Juice Shop's official Docker image at the pinned version, locally; endpoints from the P1.1 route inventory, including finale-generated ones.
- Probes:
  - unauthenticated and cross-user access;
  - over-exposure in responses;
  - transport, cookie and CORS headers;
  - consent enforcement after withdrawal;
  - erasure verification (account still readable after `/dataerasure`);
  - Playwright click counts for withdrawal ease.
- Destructive probes run only on accounts the Auditor signs up itself.
- Results Confirm or Refute static Findings, with captured request/response added as masked Evidence; unmatched results become new Findings.

Acceptance: SEC-07/08 (`/rest/memories`), RET-02 and SEC-11 Confirmed live on local Juice Shop with captured traffic, shown in the dashboard.

---

# P3: Retrieval grounding and a fine-tuned local model

Decision: [ADR 0004](adr/0004-retrieval-grounding-and-fine-tuned-local-model.md). ADR 0003 still holds: the LLM never creates or drops a Finding.

## P3.1 Retrieval-grounded prompts

Status: done.

- **Index.** At scan time the Auditor builds an offline, in-memory index on first use in a process. It has one BM25 over Provision registry excerpts and one BM25 per Issue Type over its Labelled Corpus fixtures, with one document per Rule and label. The remediation catalogue supplies the seed Provisions and Issue Type titles; it is not indexed. No statute PDF text is extracted or indexed, no index file is written, and Target Application code is not indexed. Returned fixture examples are truncated to 60 lines.
- **Retrieval.** `retrieve_provisions` takes the Issue Type's primary and related Provisions, then their parents. If the seeds number fewer than k, it fills to k with BM25 over the masked query and the Issue Type titles. Triage uses k=8, and `retrieve_examples` returns the nearest positive and negative fixture when available. Consent seeds CON-01 through CON-07 (20 seed Provisions, parents included), then fills to k=24 with BM25 over the masked serialised consent graph.
- **Prompts v2.** `triage-v2` and `consent-v2` carry the retrieved Provisions in their context (triage also the retrieved examples). A citation outside that request's retrieved set makes the response invalid, so the verdict is `not assessed`. Consent also returns a reading per criterion. The retrieved set is part of the cache key. Classification and fix remain on v1.
- **Regenerate.** Done in `69ac7bf`. Triage and consent moved to v2 and the model moved to `anthropic/claude-opus-5-5`, so every cache key changed. The cache, the Juice Shop Report, `accuracy/results.md` and the manifest were regenerated together; the reason is in `accuracy/README.md`.

Acceptance:
- Retrieval recall@8 of each Issue Type's catalogue Provisions is 100%.
- Every cited id in the Juice Shop Report resolves in the registry.
- `dpdp-audit accuracy --cache-only` reproduces the published figures.

## P3.2 Per-role routing and the held-out evaluation

- **Routing.** A provider and model per role, set by `--role-model ROLE=PROVIDER:MODEL` or `DPDP_LLM_ROLES`. The report schema's `llm` block, the accuracy manifest and the dashboard record each role separately.
- **Held-out set.** Built only from the Report Targets:
  - classification: hand-checked Data Categories for unresolved Elements;
  - triage: verdicts derived from `accuracy/juice-shop.json` matches;
  - consent: per-criterion labels for TrackMyRupee and the consent fixtures.
- **Evaluation command.** `dpdp-audit llm-eval` (proposed) reports the following per role and model:
  - the primary metric (classification macro-F1, triage accuracy, consent per-criterion agreement);
  - JSON validity;
  - citation validity;
  - latency.
- **Baselines.** Measure the hosted default and the zero-shot base-model candidates. Candidates run on Ollama on the A4000.

Acceptance: one evaluation table covers the hosted default and every base candidate, and names the chosen base model.

## P3.3 Distilled training set

- **Sources.** Pinned public repositories that are not Report Targets, listed in `training/sources.yaml` (proposed) and cloned under the git-ignored `targets/`. Add synthetic consent graphs made by perturbing facts programmatically.
- **Inputs.** Build them with the Auditor's own pipeline and masking, so the training text matches the v2 prompts exactly.
- **Labels.** Two teacher models label each item. Keep an item only when the teachers agree, or when a teacher agrees with a deterministic label.
- **Split.** Split by repository; Report Targets never appear in training.
- **Records.** Write a dataset card with counts, agreement rate, token-length percentiles and a digest. The data itself stays git-ignored.

Acceptance:
- A filtered training set exists with recorded counts per role.
- A leakage check proves no Report Target file or snippet hash appears in it.

## P3.4 Fine-tune, serve and adopt

- **Training.** QLoRA on the A4000 with the chosen base model and one multi-task adapter. The sequence length comes from the dataset card's p95. Peak VRAM is measured in a smoke run before the full run.
- **Serving.** Merge the adapter, export GGUF, and `ollama create dpdp-auditor:<run-id>`.
- **Adoption.** Evaluate with `dpdp-audit llm-eval`. A role adopts the model only if it meets ADR 0004's bar: beats its base, comes within 5 points of the hosted default, and has 100% JSON and citation validity. Otherwise the role stays on the hosted default.
- **After adoption.** Re-record the cache, the accuracy manifest and the Replay Mode recordings. The Report's method section names the model for each role.

Acceptance:
- The `llm-eval` table shows base, fine-tuned and hosted results for each role, with the adoption decision.
- The Juice Shop scan runs live with adopted roles on the fine-tuned model and replays offline in cache-only mode.

---

# After P2

- Framework coverage through the same analyser split: Django (P2.1), plus Prisma and Mongoose (schema and ORM Processing Operations), React form-to-route-to-Element joins, Kubernetes and nginx configuration. Cross-file joins live in `auditor/analysers/framework_flows.py`; new Rules in `auditor/rules/framework_config.py`.
- singharya E-KYC scan and Report: pin `e6e78d53edd30fd5be88dcd82d5afc1a2010d025`, see `docs/targets/singharya-e-kyc.md`.
  - Scan: `OLLAMA_HOST=http://127.0.0.1:1 .venv/bin/dpdp-audit scan targets/singharya-e-kyc --provider ollama --out reports/singharya-e-kyc/report.json`.
  - Actual coverage: Python (FastAPI) and Kubernetes (including nginx-class Ingress) are exercised by the Target; the Report has no Findings. Prisma, Mongoose, React, Django and `nginx.conf` are covered by fixtures only (`tests/fixtures/frameworks/**`, `tests/fixtures/django`).
  - Gap: committed ID-document images are not assessed by `SEC-15`, which reads text formats only.

## Submission

- Replay recordings for every scanned Target.
- Demo script:
  1. Indian Targets: Consent Assessment (TrackMyRupee), ai-kyc-platform Government Identifier Findings, and singharya E-KYC (no Findings, stated as the Rules' result);
  2. scan Juice Shop;
  3. Personal Data Map;
  4. `/rest/memories` Critical Finding detail with its Data Flow;
  5. Coverage Matrix;
  6. Live Probe Confirm;
  7. Open PR;
  8. re-scan.
- Repo README: install, run, and links to the three deliverables.
