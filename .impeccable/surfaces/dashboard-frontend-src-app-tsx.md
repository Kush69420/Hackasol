---
version: 1
slug: "dashboard-frontend-src-app-tsx"
primary_target: "dashboard/frontend/src/App.tsx"
related_targets: []
---

# Surface: dashboard (dashboard/frontend)

Mode: Operate. Redesign of the existing React dashboard; keep every feature, the API and the Report schema.
Audience: Hack-a-Sol judges on a projector or shared screen, presenter driving. Task: understand what was found, why it matters legally, and that it comes from traced code, in under a minute. Frequency: one demo, several recorded Targets switched live (Juice Shop and ai-kyc-platform lead).
Benchmarks (user-chosen craft bar): Vercel dashboard, Snyk, Sentry. User chose the category standard played straight.
Constraints: Replay Mode honest labelling, CONTEXT.md terms, masked Evidence stays masked, e2e testids and accessible names stay.
Unresolved: none.

## Direction contract

THESIS: A calm, precise security-ops console: the category standard executed at Vercel/Sentry finish, where the evidence for every Finding is one click from the list. Refuses the stacked-card admin template and the hero-metric strip.
OWN-WORLD: Cool near-white surfaces (dark theme selectable), one indigo accent for selection and primary actions, a four-step severity ramp used only on severity, Geist sans with Geist Mono for ids, code and tabular numbers, 1px hairlines, 6px radii, no shadows beyond one popover shadow.
STORY: A judge sees the Target, how many Findings, how severe, and the highest applicable Penalty Ceiling; clicks a Finding and sees file, line, Data Flow and the statute; the presenter switches Targets in one click.
FIRST VIEWPORT: Fixed sidebar left (brand, recorded scans list, section nav, theme and large-type toggles); main shows run header with Target, provenance and download actions, then the overview: severity distribution bar and Findings by Data Category, with a one-sentence legal summary; Findings master-detail begins immediately below. Idle state is a start panel listing recorded scans and the scan input.
FORM: Category standard, sidebar console with master-detail list. Seed key a8a167c9 (canon).
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
