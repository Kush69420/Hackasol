# Build plan

Solo builder orchestrating coding agents. Order: a demo-ready vertical slice first, then breadth. Nothing in docs/issue-types.md or the ADRs is dropped; phases only set the sequence. Vocabulary follows CONTEXT.md.

## Phase 0: Scaffold and contract

- Python package `auditor/` (CLI `dpdp-audit`), `rules/semgrep/` (YAML Rules, one directory per Issue Type), `auditor/analysers/` (schema and config), `corpus/` (Labelled Corpus), `dashboard/` (FastAPI backend + React front end), `targets/` (git-ignored clones), `reports/` (generated Reports).
- Fix the **Finding schema** (JSON) first; every later phase codes against it: id, Issue Type, Rules fired, Evidence (file, line range, raw excerpt), Personal Data Element + Data Category, Processing Operation, Exposure, Provisions (Primary flagged), Penalty Ceiling, Enforceable From, CVSS 4.0 vector + score (or N/A for Compliance Gaps), Risk Matrix cell, Severity + generated justification, status (open / Needs Legal Review), Live Probe outcome (Confirmed / Refuted), LLM triage verdict + reason, Fix Patch.
- Provision registry: data file of every Act section/sub-section and Rule with text excerpt, Penalty Ceiling and Enforceable From; allied-law and CWE entries alongside.
- LLM provider interface: Anthropic, OpenAI, Gemini (env var), Ollama, and headless `omp -p --mode json --no-tools --no-session --no-context-files --no-skills`. A masking pass runs on every outbound snippet.

Acceptance: `dpdp-audit scan <path>` runs on an empty Rule set and writes a schema-valid empty Report.

## Phase 1: Vertical slice on TrackMyRupee (demo-ready)

- Personal Data Element detection: name dictionary, value validators (Aadhaar + Verhoeff, PAN, IFSC, VPA, Indian mobile, email, card + Luhn), Django model types, LLM classification of unresolved names.
- Six Issue Types end to end: SEC-01 (logs), SEC-05 (hard-coded secret / .env), SEC-08 (over-exposure), SEC-15 (committed Personal Data), CON-05 (withdrawal not propagated), TRF-02 (cross-border). Whether CON-05 and TRF-02 actually fire on TrackMyRupee is unverified; pick replacements from the catalogue if they don't.
- Severity per ADR 0002; LLM triage verdicts.
- Dashboard: paste a GitHub URL → streamed progress → Findings list by Severity → Finding detail (Evidence, Data Flow, Provisions, Penalty Ceiling, justification).
- HTML Report; record the run for Replay Mode.

Acceptance: a full demo run on TrackMyRupee, live and in Replay Mode, producing an HTML Report whose every Finding has Evidence, Provisions and a Severity justification.

## Phase 2: Detection breadth

- Remaining Issue Types in docs/issue-types.md, with Rules for Python (Django, FastAPI, Streamlit) and JS/TS (Express, Next.js, Angular, Sequelize, Mongoose, Prisma).
- Analysers: Django models, SQL DDL, Sequelize/Mongoose/Prisma schemas; Dockerfile, compose, Kubernetes, nginx, .env, settings files; committed binaries (ID document images, logs, dumps).
- Cross-file Data Flow stitching; Finding merging on the same Evidence; Anchor Points for absences and app-wide gaps; Safeguard Findings.
- Vendored-code exclusion (venv, node_modules, generated, minified).

Acceptance: every Issue Type has at least one Rule and its Labelled Corpus pair passes.

## Phase 3: Consent Assessment

- Model Purposes, Consent Records, Enforcement Points and Withdrawal Paths from code, with LLM reasoning across files.
- Evaluate all seven criteria (recorded, specific, enforced, withdrawable with comparable ease, propagated, noticed, verifiable parental consent).
- Needs Legal Review Findings for tensions (deletion on withdrawal vs Rule 8(3)).
- Static step count for grant vs withdrawal.

Acceptance: TrackMyRupee Report contains a Consent Assessment section covering all seven criteria with Evidence.

## Phase 4: Live Probes

- Any URL allowed. Destructive probes (erasure, withdrawal) only on accounts the Auditor signs up itself.
- Probes: unauthenticated/cross-user access, over-exposure, transport and session, consent enforcement (outbound Data Processor calls after withdrawal), erasure verification, Playwright click counts for withdrawal ease.
- Results Confirm or Refute matching static Findings; captured request/response added as Evidence; unmatched results become new Findings.
- Local docker-compose instances of TrackMyRupee and Juice Shop for the demo.

Acceptance: against a local TrackMyRupee instance, at least one static Finding is Confirmed with captured traffic.

## Phase 5: Fix Patches and PRs

- LLM-generated Fix Patch per Finding; re-scan proves the Finding is gone and no new Finding appears.
- "Open PR" groups accepted patches by Issue Type onto a branch of our fork of the Target.

Acceptance: one PR opened on our TrackMyRupee fork; the re-scan shows the fixed Findings gone.

## Phase 6: Report formats and Coverage Matrix

- JSON (source of truth) → HTML, PDF, SARIF 2.1.0, Markdown.
- Coverage Matrix of every Act section and Rule: static / live-testable / not code-checkable, with covering Rules; Child Data marked "covered, not exercised on a real Target".
- Rules List (deliverable 3): Issue Types with Rules nested, generated from the Rule files.
- "Fix before 13 May 2027" view grouped by Enforceable From.

Acceptance: all five formats generated for TrackMyRupee; SARIF shows as Code Scanning annotations on our fork.

## Phase 7: Accuracy

- Labelled Corpus precision and recall per Rule in CI.
- Juice Shop: map its published challenges to Issue Types; report recall on the Personal-Data-relevant ones.
- TrackMyRupee: hand-label a random sample of Findings for precision.
- Record the LLM provider and model with every figure (ADR 0003).

Acceptance: the dashboard shows all three accuracy figures.

## Phase 8: Secondary Targets and demo

- Full scans and Reports for Juice Shop, ai-kyc-platform and singharya E-KYC.
- Replay Mode recordings of every Target; demo script: scan → Finding detail → Consent Assessment → Live Probe Confirm → Open PR → re-scan.

Acceptance: four Reports in `reports/`, four Replay recordings, and a rehearsed demo script.
