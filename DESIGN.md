---
name: DPDP Compliance Auditor Dashboard
description: A calm, precise security-ops console where every Finding sits one click from its file, line, Data Flow and statute.
colors:
  cool-paper: "oklch(0.982 0.004 262)"
  white-sheet: "oklch(1 0 0)"
  sunken-sheet: "oklch(0.968 0.006 262)"
  pressed-sheet: "oklch(0.945 0.008 262)"
  hairline: "oklch(0.912 0.007 262)"
  hairline-strong: "oklch(0.84 0.012 262)"
  ink: "oklch(0.2 0.025 262)"
  ink-muted: "oklch(0.41 0.02 262)"
  ink-subtle: "oklch(0.5 0.02 262)"
  signal-indigo: "oklch(0.5 0.21 266)"
  signal-indigo-deep: "oklch(0.44 0.21 266)"
  indigo-wash: "oklch(0.955 0.03 266)"
  indigo-ink: "oklch(0.4 0.2 266)"
  on-accent: "oklch(0.99 0 0)"
  sev-critical: "oklch(0.42 0.19 18)"
  sev-critical-wash: "oklch(0.95 0.035 18)"
  sev-critical-ink: "oklch(0.38 0.17 18)"
  sev-high: "oklch(0.58 0.21 30)"
  sev-high-wash: "oklch(0.955 0.04 35)"
  sev-high-ink: "oklch(0.42 0.16 32)"
  sev-medium: "oklch(0.76 0.15 82)"
  sev-medium-wash: "oklch(0.96 0.06 90)"
  sev-medium-ink: "oklch(0.42 0.1 72)"
  sev-low: "oklch(0.66 0.05 255)"
  sev-low-wash: "oklch(0.955 0.012 255)"
  sev-low-ink: "oklch(0.42 0.04 255)"
  good: "oklch(0.45 0.13 150)"
  good-wash: "oklch(0.955 0.04 150)"
  warn: "oklch(0.45 0.1 75)"
  warn-wash: "oklch(0.96 0.06 90)"
  bad: "oklch(0.42 0.17 22)"
  bad-wash: "oklch(0.95 0.035 18)"
  code-sheet: "oklch(0.975 0.006 262)"
  code-highlight: "oklch(0.955 0.04 266)"
typography:
  headline:
    fontFamily: "Geist Variable, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 650
    lineHeight: 1.2
    letterSpacing: "-0.02em"
  title:
    fontFamily: "Geist Variable, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 620
    lineHeight: 1.3
    letterSpacing: "-0.01em"
  lede:
    fontFamily: "Geist Variable, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 400
    lineHeight: 1.5
  body:
    fontFamily: "Geist Variable, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Geist Variable, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 600
    lineHeight: 1.3
  caption:
    fontFamily: "Geist Variable, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 500
    lineHeight: 1.4
  stat:
    fontFamily: "Geist Variable, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 620
    lineHeight: 1.15
    letterSpacing: "-0.02em"
    fontFeature: "tnum"
  code:
    fontFamily: "Geist Mono Variable, ui-monospace, SF Mono, Menlo, monospace"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.6
    fontFeature: "tnum"
rounded:
  xs: "4px"
  sm: "5px"
  md: "8px"
  pill: "999px"
spacing:
  xs: "0.25rem"
  sm: "0.5rem"
  md: "1rem"
  lg: "1.5rem"
  xl: "2rem"
components:
  button-primary:
    backgroundColor: "{colors.signal-indigo}"
    textColor: "{colors.on-accent}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    padding: "0.35rem 0.8rem"
    height: "2.1rem"
  button-primary-hover:
    backgroundColor: "{colors.signal-indigo-deep}"
  button-secondary:
    backgroundColor: "{colors.white-sheet}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    padding: "0.35rem 0.8rem"
    height: "2.1rem"
  button-secondary-hover:
    backgroundColor: "{colors.pressed-sheet}"
  input:
    backgroundColor: "{colors.white-sheet}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    padding: "0.3rem 0.65rem"
    height: "2.1rem"
  nav-item:
    backgroundColor: "{colors.sunken-sheet}"
    textColor: "{colors.ink-muted}"
    rounded: "{rounded.sm}"
    padding: "0.42rem 0.55rem"
  nav-item-active:
    backgroundColor: "{colors.indigo-wash}"
    textColor: "{colors.indigo-ink}"
  panel:
    backgroundColor: "{colors.white-sheet}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "1.25rem"
  badge-severity-high:
    backgroundColor: "{colors.sev-high-wash}"
    textColor: "{colors.sev-high-ink}"
    typography: "{typography.caption}"
    rounded: "{rounded.pill}"
    padding: "0.12rem 0.55rem"
  chip:
    backgroundColor: "{colors.pressed-sheet}"
    textColor: "{colors.ink-muted}"
    typography: "{typography.caption}"
    rounded: "{rounded.xs}"
    padding: "0.05rem 0.45rem"
  finding-row-selected:
    backgroundColor: "{colors.indigo-wash}"
    textColor: "{colors.ink}"
    padding: "0.6rem 0.9rem"
---

# Design System: DPDP Compliance Auditor Dashboard

## Overview

**Creative North Star: "The Evidence Desk"**

The dashboard is a desk where a judge or a compliance reviewer reads the case file: what was found, how severe it is, and the statute it breaches, with the file and line one click away. It is the category-standard security-ops console played straight, finished to the level of Vercel, Snyk and Sentry: a fixed sidebar, a quiet top bar, hairline panels on a cool near-white page, and a master-detail Findings list where selection is the only thing that moves.

Everything is in service of one claim: the result came from traced code, not keywords. Colour therefore carries meaning and nothing else. Severity has its own four-step ramp and is used only on severity; indigo marks selection, focus and the single primary action; everything else is a tonal step of one cool neutral. Numbers are tabular, ids and code are monospaced, and statute text is quoted, never paraphrased into decoration. The interface is built to survive a projector: a large-type mode raises the root size, light and dark themes are both complete, and contrast clears WCAG AA.

**Key Characteristics:**
- Cool near-white page, white panels, 1px hairlines; no card stacks inside cards.
- One indigo accent, rationed to selection, focus and the primary action.
- A four-step severity ramp (critical, high, medium, low) used only on severity.
- Geist for reading, Geist Mono for ids, code and Evidence; tabular figures everywhere numbers are compared.
- Depth from tone and hairline; one popover shadow, nothing else.
- Honest provenance: Live, Cache-only and Replay Mode each carry their own badge.

## Colors

A cool-neutral field (hue 262) with a single indigo voice and a separate severity ramp. Every surface, border and ink is a step of the same neutral, so the only saturated colour on screen means something.

### Primary
- **Signal Indigo** (`oklch(0.5 0.21 266)`): the one accent. The primary button, focus ring, selected tab and selected Finding row outline, the brand mark, and the matrix's selected cell. Hover deepens to Signal Indigo Deep (`oklch(0.44 0.21 266)`).
- **Indigo Wash** (`oklch(0.955 0.03 266)`): the tint behind a selected or current item (active nav link, selected Finding row, active stage, Replay Mode badge, information callout).
- **Indigo Ink** (`oklch(0.4 0.2 266)`): text and icons on Indigo Wash, and the colour of text links.

### Neutral
- **Cool Paper** (`oklch(0.982 0.004 262)`): the page background.
- **White Sheet** (`oklch(1 0 0)`): panels, inputs and secondary buttons.
- **Sunken Sheet** (`oklch(0.968 0.006 262)`): the sidebar, table headers, band headers, quoted Provision blocks and idle matrix cells.
- **Pressed Sheet** (`oklch(0.945 0.008 262)`): hover on rows and buttons, chips, and the track behind tabs.
- **Hairline** (`oklch(0.912 0.007 262)`) and **Hairline Strong** (`oklch(0.84 0.012 262)`): panel borders and dividers, and control borders respectively.
- **Ink** (`oklch(0.2 0.025 262)`), **Ink Muted** (`oklch(0.41 0.02 262)`), **Ink Subtle** (`oklch(0.5 0.02 262)`): primary, secondary and tertiary text. Ink Subtle is the floor; nothing carries text lighter than it.
- **Code Sheet** (`oklch(0.975 0.006 262)`) and **Code Highlight** (`oklch(0.955 0.04 266)`): the Evidence block background and the highlighted Finding lines.

### Severity ramp
Each band has a solid (bars, dots), a wash (badge background) and an ink (badge text).
- **Critical:** deep crimson (`oklch(0.42 0.19 18)`).
- **High:** vermilion (`oklch(0.58 0.21 30)`).
- **Medium:** amber (`oklch(0.76 0.15 82)`), with a dark amber ink for text.
- **Low:** desaturated slate-blue (`oklch(0.66 0.05 255)`).

### Status
**Good** green (`oklch(0.45 0.13 150)`) marks Live and completed stages; **Warn** amber-brown (`oklch(0.45 0.1 75)`) marks Cache-only and legal Provision chips; **Bad** red (`oklch(0.42 0.17 22)`) marks failures and Enforceable-now dates. Each has a wash for its background.

### Dark theme
`[data-theme="dark"]` redefines every token: page `oklch(0.155 0.012 262)`, panel `oklch(0.2 0.013 262)`, ink `oklch(0.96 0.006 262)`, and a lighter indigo (`oklch(0.72 0.15 266)`) with dark `on-accent` text. Severity solids lift in lightness and washes become dark tints. Both themes are complete; the toggle persists in localStorage.

### Named Rules
**The Severity-Only Rule.** The severity ramp appears only where a Severity is being shown. Never use crimson, vermilion, amber or slate for decoration, emphasis or status that is not a Severity.
**The One Voice Rule.** Indigo marks selection, focus and the single primary action. If two indigo things compete on one screen, one of them is not selection.
**The Wash-and-Ink Rule.** A coloured badge or callout is a wash background with its matching ink text, never a solid fill with white text; solids are reserved for bars, dots and the primary button.

## Typography

**Body and Display Font:** Geist Variable (system-ui fallback), bundled so it works offline.
**Mono Font:** Geist Mono Variable (ui-monospace fallback) for ids, Finding Issue Type names, file paths, and Evidence.

**Character:** One family at moderate weight contrast, so hierarchy comes from size, weight and ink step rather than from a second typeface. Mono marks anything a reviewer might copy.

### Hierarchy
- **Headline** (650, 1.5rem, 1.2, -0.02em): the Target name in the run header; one per screen.
- **Title** (620, 1.0625rem, 1.3, -0.01em): panel headings and section titles.
- **Lede** (400, 1.0625rem, 1.5, Ink Muted, max 70ch): the one-sentence summary that opens the Overview, with its key numbers in Ink at weight 620.
- **Body** (400, 0.9375rem, 1.5): running text, form controls, table cells at 0.875rem.
- **Label** (600, 0.8125rem, Ink Muted): sub-headings inside a Finding, chart titles and table headers (0.75rem). Sentence case, never uppercase.
- **Caption** (500, 0.75rem): badges, chips, counts, stage timings.
- **Stat** (620, 1.5rem, tabular): the four severity counts and the Penalty Ceiling amount (640, 1.375rem).
- **Code** (400, 0.8125rem, 1.6, tabular): Evidence with line numbers, anchors and ids.

Reading text is capped at 62 to 76ch. Large-type mode raises the root from 16px to 19px so every rem-based size scales together.

### Named Rules
**The Tabular Rule.** Any figure that is compared, summed or sorted uses tabular numerals.
**The No-Eyebrow Rule.** Headings stand alone; no small uppercase kicker above a title.

## Layout

A two-column shell: a 15rem sticky sidebar (brand, recorded-scan list, section nav with scroll-spy, theme and large-type toggles) beside a fluid main column. The main column has a sticky, blurred top bar (recorded-scan tab switcher and scan form) over a content stack capped at 92rem, padded 1.75rem by 2rem, with 1.5rem between sections.

The first screen reads top to bottom: run header (Target, provenance badge, Report downloads, four-stage stepper), then the Overview panel (a one-sentence legal summary above a two-column pair, severity distribution and Findings by Data Category), then the Findings master-detail. Findings uses a container query: at 60rem and wider the list (20 to 26rem, sticky) sits beside the detail; narrower, it stacks with the list height-capped at 28rem.

Spacing runs on a small rem scale (0.25, 0.5, 1, 1.5, 2) with panel padding at 1.25rem. Density is moderate: rows are 2.1rem controls and 0.55rem table padding, comfortable at projector distance without wasting the screen.

Responsive: at 62rem the Overview collapses to one column; at 52rem the sidebar becomes a top strip (nav hidden, toggles kept), the top bar loses stickiness, and the scan form goes full width. Wide tables and the Personal Data matrix scroll inside their own wrapper; the page itself never scrolls horizontally.

### Named Rules
**The Evidence-First Rule.** From the first screen, a Finding's file, line and Data Flow are reachable in one click; the first Finding is pre-selected so the detail is never empty.
**The Own-Scroll Rule.** Anything wider than its column (matrix, tables, Evidence, CVSS vectors) scrolls or wraps inside itself.

## Elevation & Depth

Flat, tonal and hairline. Depth is conveyed by stepped surface tones (page, white panel, sunken sheet, pressed sheet) and 1px borders; nothing floats at rest. The sticky top bar uses a 92% page tint with a 10px backdrop blur so content passes beneath it, which is the only translucent surface.

### Shadow Vocabulary
- **Popover** (`box-shadow: 0 8px 24px oklch(0.2 0.03 262 / 0.12), 0 1px 3px oklch(0.2 0.03 262 / 0.1)`): reserved for floating layers. Darker in the dark theme.
- **Focus ring** (`box-shadow: 0 0 0 3px {indigo-wash}` on inputs, `outline: 2px solid {signal-indigo}; outline-offset: 2px` elsewhere): focus is always visible.

### Named Rules
**The Hairline-Not-Shadow Rule.** Separate with a 1px line or a tone step. A shadow on a panel, row or button at rest is a defect.

## Shapes

Gently squared. Panels use an 8px radius, controls 5px, chips 4px, the brand mark 7px, and badges are full pills. Selected rows are marked by an inset 1px indigo ring, never a coloured side stripe. Severity bars are 14px tall with 2px gaps and slightly rounded ends. Matrix cells are 4px squares on a 2px grid. Flow steps in a Data Flow are small bordered boxes joined by a 1px connector with a chevron.

## Components

### Buttons
- **Shape:** 5px radius, 2.1rem minimum height, 1px border (`Hairline Strong`).
- **Primary:** Signal Indigo fill, on-accent text, 0.35rem by 0.8rem padding; one per context (Audit on the Home form, Replay on a Target card, Scan in the dashboard). Hover deepens the fill. Disabled drops to Sunken Sheet with Ink Muted text and a dashed Hairline Strong border, never opacity, so it stays legible as a button.
- **Secondary:** White Sheet with ink text; hover to Pressed Sheet. Report downloads and Scan live on a Target card use this.
- **Icon button:** 2.1rem square; `aria-pressed` fills Indigo Wash with an indigo border (theme and large-type toggles).
- **Press:** 1px downward translate on `:active`; transitions 150ms on `cubic-bezier(0.2, 0.7, 0.2, 1)`.

### Tabs (recorded-scan switcher)
- **Style:** a Pressed Sheet track with 7px radius holding 5px-radius segments; the pressed segment becomes White Sheet with a 1px Hairline Strong ring.
- **State:** disabled segments dim and show a progress cursor while a scan runs.

### Badges and chips
- **Badge:** pill, 0.75rem, wash plus ink. Severity badges are capitalised; provenance badges are Live (good), Cache-only (warn) and Replay Mode (indigo).
- **Chip:** 4px radius on Pressed Sheet; Provision chips use the warn wash, assessment chips use good or bad.

### Panels
- **Corner style:** 8px, White Sheet, 1px Hairline border, no shadow.
- **Header:** title left, one-line description right or below, divided from the body by a hairline.
- **Never nested.** A panel does not contain another bordered panel; sub-areas use dividers or the Sunken Sheet.

### Inputs
- **Style:** White Sheet, 1px Hairline Strong, 5px radius, 2.1rem height; placeholder in Ink Subtle.
- **Focus:** border turns Signal Indigo with a 3px Indigo Wash halo. Hover darkens the border to Ink Subtle.

### Navigation (sidebar)
- **Style:** 0.875rem, weight 500, Ink Muted, 5px-radius rows with an icon, a label and a tabular count.
- **States:** hover on Pressed Sheet; the current section (scroll-spy, `aria-current`) on Indigo Wash with Indigo Ink. On narrow screens the list is hidden.

### Findings list and detail (signature)
- **List:** grouped into sticky severity bands (band header on Sunken Sheet with a count). Each row is a button: the Issue Type in mono weight 600, the Processing Operation at the right, then one line of file and Provision. Selected: Indigo Wash plus an inset indigo ring.
- **Detail:** Issue Type headline in mono with its Severity badge; a facts line; then Evidence (file caption bar, line numbers, highlighted lines on Code Highlight), Data Flow (numbered steps in a chain), Provisions (quoted statute clamped to three lines with a show-more link, Penalty Ceiling and Enforceable From), Severity justification and the recommended fix. Evidence stays masked exactly as the Report supplies it.

### Severity distribution and category bars
- **Severity bar:** one segmented bar plus four count keys that act as filters (`aria-pressed` fills Indigo Wash). Counts use Stat.
- **Category rows:** a label, a stacked severity bar (10px tall), and a tabular total.

### Personal Data Map matrix
- A grid of Data Category by Processing Operation. Idle cells sit on Sunken Sheet, populated cells on Indigo Wash, cells with Findings on the High wash; the pressed cell takes an indigo border. Empty cells are disabled.

### Stage stepper
- Four connected cells (Inventory, Elements, Data Flows, Findings). Done: a green check. Active: Indigo Wash with a spinning ring. Pending: an empty ring in Ink Subtle. Stage timing is tabular at the right.

## Do's and Don'ts

### Do:
- **Do** use Signal Indigo only for selection, focus and the single primary action.
- **Do** show Severity with the four-step ramp, always as a wash badge or a bar segment, and always with a text label as well as colour.
- **Do** set ids, Issue Types, file paths and Evidence in Geist Mono, and every compared number in tabular figures.
- **Do** separate with 1px Hairline or a surface tone step; keep panels flat.
- **Do** label Replay Mode, Cache-only and Live on the run header, and show "not assessed" for anything that was not run.
- **Do** keep Evidence masking intact and quote Provisions as supplied.
- **Do** test both themes and large-type mode when adding a surface.

### Don't:
- **Don't** nest bordered panels inside panels, or build a stack of identical stat cards.
- **Don't** add a hero-metric strip, a gradient, gradient text, or a coloured side-stripe on a row or callout.
- **Don't** place a small uppercase kicker above a heading.
- **Don't** use a severity colour for anything that is not a Severity.
- **Don't** put a shadow on a panel, row or button at rest; the popover shadow is the only one.
- **Don't** use text lighter than Ink Subtle, or colour as the only carrier of meaning.
- **Don't** let any element widen the page; wide content scrolls inside its own wrapper.
- **Don't** write "vulnerability", "issue", "user", "PII" or "demo mode" in interface text; use CONTEXT.md terms.
