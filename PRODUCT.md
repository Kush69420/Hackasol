# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Confirmed (this session): the dashboard is shown to Hack-a-Sol judges, on a projector or a shared screen, by a presenter driving it live.
Inferred from AGENTS.md, PS.md and docs/plan.md (not separately confirmed): the product's real audience is the engineers and compliance reviewers of a Data Fiduciary, who need to know where a Target Application mishandles Personal Data and which Provision each Finding breaches.

## Product Purpose

DPDP Compliance Auditor scans a Target Application's code and configuration, finds where Personal Data is mishandled, and maps each Finding to India's DPDP Act 2023 and DPDP Rules 2025, with Evidence (file and line), Severity and a recommended fix. The dashboard is its front end: paste a repo, watch four streamed stages (Inventory, Elements, Data Flows, Findings), read Findings by Severity, open a Finding's Evidence, Data Flow and Provisions, browse the Personal Data Map, and download the Report. Success for this surface: a judge understands in the first minute what was found, why it matters legally, and that it came from code analysis, not keywords.

## Positioning

It checks what the code does with Personal Data (traced Data Flows from an Element to a Processing Operation), and each Finding carries a checked Provision, Penalty Ceiling and Enforceable From date. A privacy-policy or consent-banner checker cannot show a Finding's file, line and Data Flow.

## Operating Context

- Replay Mode plays back a recorded scan at its original pace, used when a live scan cannot run. Recordings exist in `dashboard/recordings/` for juice-shop, juice-shop-fork, ai-kyc-platform, singharya-e-kyc and trackmyrupee.
- Confirmed (this session): the demo must switch between recorded Targets; Juice Shop (Reference Target, 53 Findings: 32 high, 13 medium, 8 low) and ai-kyc-platform (7 Findings: 3 high, 1 medium, 3 low) lead.
- The service binds 127.0.0.1 only and is a local, trusted demo.

## Capabilities and Constraints

- Existing app: FastAPI backend (`dashboard/backend/`) and React + Vite front end (`dashboard/frontend/`), five Playwright specs in `dashboard/frontend/e2e/`. The API and the Report JSON schema (`auditor/schema/report.schema.json`, 1.3.0) are contracts; the redesign changes presentation, not the API.
- Existing features to keep: scan form, Replay, stage progress with provenance (Live, Cache-only, Replay Mode), Findings by band, Finding detail (Evidence with line numbers, Data Flow, Provisions with statute excerpt, Penalty Ceiling, Severity justification, recommended fix, LLM triage), Personal Data Map, Consent Assessment, Legal View (Penalty Ceiling rows and Enforceable From timeline), Live Probes, Fix Patches, Report downloads in JSON, MD, HTML and PDF.
- Replay Mode hides Live Probes and Fix Patches controls (they act on a running scan).
- Use CONTEXT.md terms exactly; never its `_Avoid_` words (no "vulnerability", "issue", "user", "PII", "demo mode").
- Evidence masks Authentication Secrets, keys and Government Identifiers; the UI must never undo that.
- Severity bands are critical, high, medium, low. Unrun states show "not assessed", never an invented value.
- Stack is the existing one (React 18, Vite, TypeScript); no new framework.

## Brand Commitments

None recorded. The product has no logo or brand identity beyond its name, "DPDP Compliance Auditor".

## Evidence on Hand

Real Reports and recordings in `reports/` and `dashboard/recordings/`. No customer, testimonial or benchmark claims exist; do not invent any. Accuracy figures live in `accuracy/` and may be cited only as published there.

## Product Principles

- Evidence before verdict: every Finding is one click from its file, line, excerpt and Data Flow.
- Law is checked, not asserted: Provisions, Penalty Ceilings and Enforceable From dates come from the registry and are shown with their source.
- Honest states: Replay Mode is labelled as a replay, missing assessments say "not assessed", and nothing recorded is presented as live.
- The story must survive a projector: the first screen shows the scale of what was found, and the next click shows why.

## Accessibility & Inclusion

No product-specific standard established. Treat WCAG AA contrast and keyboard operation as the floor; the presentation setting adds large-type legibility at a distance.
