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

- **Primary: OWASP Juice Shop, as-is, pinned to `c9f99228`.**
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
- **Provision registry**: every Act section and sub-section and every Rule, with a text excerpt, parent section, Penalty Ceiling and Enforceable From (14 Nov 2026 for Rule 4; 14 May 2027 for Rules 3, 5–16, 22–23). Each entry is checked against the official Act, Rules (G.S.R. 846(E)) and commencement notice (G.S.R. 843(E)). Allied law and CWE/OWASP entries sit alongside.
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
  2. executive summary: counts by Severity and kind, top penalty exposure, what to fix before 14 May 2027;
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

- Extend the analysers to Next.js and FastAPI, then scan it and produce its Report (Government Identifier and Biometric Findings, SEC-03).

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

# After P2

- Remaining frameworks through the same analyser split: Django (already in P2.1), Prisma, Mongoose, React, Kubernetes, nginx.
- singharya E-KYC scan and Report.

## Submission

- Replay recordings for every scanned Target.
- Demo script:
  1. scan Juice Shop;
  2. Personal Data Map;
  3. `/rest/memories` Critical Finding detail with its Data Flow;
  4. Coverage Matrix;
  5. Consent Assessment (TrackMyRupee);
  6. Live Probe Confirm;
  7. Open PR;
  8. re-scan.
- Repo README: install, run, and links to the three deliverables.
