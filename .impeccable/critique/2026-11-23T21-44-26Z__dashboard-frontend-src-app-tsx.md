---
target: dashboard (App.tsx)
total_score: 19
max_score: 32
na_heuristics: 5,9
p0_count: 0
p1_count: 3
target_identity: "file:/home/tankaizokuo/Code/projects/hack_a_sol_5/dashboard/frontend/src/App.tsx"
target_fingerprint: "sha256:1461d5120de4b8580684e4318ace44143751d42961eb2dcb6760b5613d777c6c"
target_path: /home/tankaizokuo/Code/projects/hack_a_sol_5/dashboard/frontend/src/App.tsx
timestamp: 2026-11-23T21-44-26Z
slug: dashboard-frontend-src-app-tsx
---
## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | Stepper is clear; Juice Shop replay kept "Status: running" for about 3 s after all four stages were done |
| 2 | Match System / Real World | 2 | Findings are titled by Rule id (`SEC-11`, `SEC-03`); "CVSS CVSS:4.0"; "No single Personal Data Element (configuration Finding)" |
| 3 | User Control and Freedom | 3 | One-click recorded-scan switching; no visible way to skip or pause a replay |
| 4 | Consistency and Standards | 2 | Nav "Legal view" vs heading "Statutory Penalty Ceilings and Enforcement Timeline"; Consent criteria headings in lowercase; "high: 17" vs "High" badges |
| 5 | Error Prevention | n/a | Live scan not exercised (it is not read-only) |
| 6 | Recognition Rather Than Recall | 3 | Theme and large-type toggles are icon-only ("T") |
| 7 | Flexibility and Efficiency | 2 | Search and filters exist; no shortcuts found |
| 8 | Aesthetic and Minimalist Design | 2 | Legal cells list 15 to 20 hash ids; Consent repeats boilerplate on every row; 130-row Personal Data Map table |
| 9 | Error Recovery | n/a | Error callout exists in source, not exercised |
| 10 | Help and Documentation | 2 | Penalty Ceiling is explained only in the Legal View intro |
| **Total** | | **19/32** | **Acceptable** |

## Design Specificity Verdict

**LLM assessment:** Mixed. The content is specific to this product: Penalty Ceiling copy, Rule 6(1)(a) statute text, a Collect → Log Data Flow, masked `«SECRET»` Evidence and honest Replay Mode labels. The chrome is the category default: left nav, topbar chips, white panels, indigo accent, Geist with Geist Mono. DESIGN.md chose that on purpose ("the category-standard security-ops console played straight"). So the risk is not that the chrome is generic. The risk is that the product's own story (₹ stake, traced flow) gets the weakest typography.

**Deterministic scan:** `impeccable detect` on `dashboard/frontend/src` found 0 issues and exited 0. Test files with planted anti-patterns confirmed it scans `.tsx` and `.css`. On the live page, the idle state scored 0. The completed Juice Shop replay scored 15: 14 `line-length` and 1 `em-dash-overuse`. The 14 line-length hits are real. Rendered prose runs about 88 to 111 characters per line against DESIGN.md's 62 to 76 ch cap. Hiding one section at a time traced them: Consent 9, Findings 3, Overview 1, Legal View 1. This agrees with the design review, which separately called Consent the weakest surface. The em-dash hit is a false positive: 77 `—` placeholders in the Personal Data Map (`PersonalDataMap.tsx:97`).

## Overall Impression

The Overview sentence and the one-click evidence chain carry the demo. Everything else is set for a laptop, not a projector. Default text is too small. Findings carry Rule ids instead of plain statements, and the scroll ends on the weakest screen (Consent's wall of "Not determinable"). The biggest opportunity: make the default the presentation scale, and give each Finding a plain title.

## What's Working

1. **The Overview sentence carries scale, stake and date** ("7 Findings across 5 of 30 Personal Data Elements", ₹250 crore, 13 May 2027), with severity numerals readable in seconds.
2. **Evidence is one click away.** The first Finding is pre-selected, with line-numbered Evidence, Data Flow, the Primary Provision with statute text, and the Penalty Ceiling at display size.
3. **Honest states throughout.** Replay Mode pill, "Evidence is masked before it is shown", "not a predicted or estimated fine", and "Not determinable" instead of invented verdicts.

## Priority Issues

**[P1] Projector legibility depends on a hidden toggle.**
- Why: At 1920×1080, 46% of text elements render below 14px. Nav is 12px; Evidence is 12 to 13px mono. The only fix is an unlabelled "T" at the bottom of the sidebar, and it scales text by just 1.19×.
- Fix: Make presentation scale the default (body ≥16px, Finding row titles ≥18px, Evidence ≥15px). Keep a labelled "Compact" option for laptop use.
- Command: $impeccable typeset

**[P1] Findings are named by Rule id, and the default Finding is the weakest story.**
- Why: On ai-kyc, the High band shows two rows both titled `SEC-03` (Expose and Store). The pre-selected `SEC-11` is a CORS configuration, not the Aadhaar exposure. Its "Why this Severity" cites `main.py:192`, but the first Evidence block shown is `main.py:36-42`.
- Raw artefacts: `Static step counts: {"grant":[],"withdrawal":[]}` in Consent; literal backticks in "Tailored fix"; "CVSS CVSS:4.0"; CWE-319/614/942 shown in the same card style as the Primary Provision. Report data includes "from a user's browser", which uses the banned word "user".
- Fix: Title each Finding with a plain statement built from the Element and Processing Operation (e.g. "Aadhaar number exposed by OCRService"), with the Rule id as a chip. Pre-select the highest-band Finding that has a Data Flow. Show first the Evidence block that the justification cites. Render inline code in the fix text, drop the duplicate CVSS prefix, and put CWEs in their own "Technical weakness" group.
- Command: $impeccable clarify

**[P1] The legal stake is the weakest type, and Legal View is a wall of ids.**
- Why: ₹250 crore sits as inline body text, while the 0/3/1/3 severity counts get display size. Legal View's Findings column lists 15 to 20 full hash ids per row, and a five-sentence disclosure sits at body size.
- Fix: Make the highest Penalty Ceiling a display figure, with its Provisions as a caption. Replace the id lists with "15 Findings ›" that expands. Fold the disclosure into a collapsible "How ceilings are read".
- Command: $impeccable distill, then $impeccable layout

**[P2] Consent Assessment has no verdict at a glance, and its lines are too long.**
- Why: Every criterion reads "Not determinable" in bold prose, with no status chip and no summary line. Each row repeats the same applicability boilerplate, and the headings are lowercase. Nine of the detector's 14 too-long lines are here.
- Fix: Add a summary line ("0 of 7 criteria met · 7 not determinable"), one status chip per row, the boilerplate stated once, and text capped at 70ch in two columns.
- Command: $impeccable distill

**[P2] Medium severity fails contrast in the light theme.**
- Why: `--sev-medium` `oklch(0.76 0.15 82)` measures 2.18:1 on white, below the 3:1 non-text minimum. `--sev-low` measures 3.11:1. Severity bar segments carry colour only. The dark theme passes.
- Fix: Darken `--sev-medium` to ≥3:1 while keeping it distinct from High, and label the bar segments.
- Command: $impeccable colorize

## Persona Red Flags

- **Judge at projector distance:** 12 to 13px nav, row titles and Evidence cannot be read from the back of the room. Only the Overview sentence and the numerals carry. The first Finding they see is labelled "No single Personal Data Element (configuration Finding)".
- **Presenter driving live:** must remember to press the unlabelled "T" before projecting. Each recorded-scan switch replays for 4 to 9 s with no skip. To reach the Aadhaar story, they must click past the CORS Finding. The scroll ends on Consent's "Not determinable" wall.
- **Sam (accessibility-dependent):** medium severity at 2.18:1; severity bars rely on colour alone; icon-only toggles are 34px.
- **Alex (power user):** the Juice Shop page is 9,798px of five stacked sections; no keyboard shortcuts found.

## Minor Observations

- "₹250 / crore" and "13 / May 2027" wrap across lines at 1920px; use non-breaking spaces.
- At 390px the stepper wraps "1127 / ms" and "Personal Data Elements" onto three lines; 40 of 51 controls are under 44px.
- An empty "Critical 0 · No Findings in this band." band opens every list.
- The Transfer and Erase columns in the Personal Data Map are empty with no "none found" note.
- "Replay Mode" appears twice (topbar chip and header pill).
- "Recommended fix" and "Tailored fix" repeat each other.
- Provision cells repeat themselves: "DPDP-Rule-6(1)(a) (Rule 6(1)(a))".
- About 208px is unused on the right at 1920px: content stops at 1680px while the topbar reaches 1888px.

## Questions to Consider

- If a judge reads one number, should it be ₹250 crore rather than the severity counts?
- Should the product pick the headline Finding (highest band with a traced Data Flow), rather than the list order?
- Projectors are this surface's only audience, so why is the default tuned for a laptop?
