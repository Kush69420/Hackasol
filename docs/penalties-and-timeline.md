# Statutory Penalty Ceilings and Enforcement Timeline

A derived view of a Report: it reads the Findings and the Provision registry and changes neither.
Code: `auditor/legal_view.py`. Endpoint: `GET /api/scans/{run_id}/legal` (completed live runs and Replay Mode;
optional `?as_of=YYYY-MM-DD`, default the scan date in the Report). Dashboard: `LegalView.tsx`.
Report: the section "Statutory Penalty Ceilings and Enforcement Timeline" in the md, html and pdf renderings.

## Wording

Every rendering states: *statutory maximum per Schedule; not a predicted or estimated fine; the actual penalty is
determined by the Data Protection Board under section 33(2) factors.* Section 33(2) lists the factors (nature, gravity
and duration of the breach; type of personal data; repetition; gain or loss avoided; mitigation; proportionality;
likely impact on the person).

## No total exposure

Schedule ceilings are per breach instance ("may extend to"). Adding them across Findings would present a figure
the Act never states, so the view never sums. The **highest applicable ceiling** considers only numeric ceilings
linked to applicable Primary Provisions under the Report's Applicability Assumptions. The headline is not a
determination by the Data Protection Board that a breach occurred.

## Ceiling view

One row per cited DPDP Provision: Provision, Schedule entry, statutory maximum, Finding applicability and Severity mix.
A single Provision can be an Applicable Primary Provision for one Finding and a Related Provision for another.
Conditional Provisions are labelled and excluded from the headline, including Rule 13(4) for Significant Data
Fiduciaries and Rule 8(2) for a Third Schedule class. Findings with status Needs Legal Review are labelled
as not establishing a breach and do not contribute to the headline. For example, a Report containing only a
TRF-02 Disclosure Finding with that status shows Rule 13(4)'s statutory maximum in its conditional row but has
no highest applicable ceiling. Allied Provisions (CWE, OWASP, Aadhaar, IT Act) have no Schedule entry and are
omitted. Section 15 duties carry “ten thousand rupees” (Schedule item 5), shown as text, not as a crore figure.

In the endpoint payload, `ceilings[].finding_ids_by_applicability` groups the Finding IDs under
`applicable_primary`, `related`, `conditional`, and `needs_legal_review`. The existing `finding_ids` and
`severity_mix` on a row summarize all citations; `highest_applicable_ceiling.finding_ids` includes only the
`applicable_primary` links of the Provisions that reach the highest ceiling.

## Enforcement timeline

Findings are grouped into phases by Enforceable From. Days until enforceable are relative to the scan date; a phase
with 0 or fewer days is marked already enforceable.

## Verification of dates and ceilings

| Item | Registry | Primary source text | Result |
|---|---|---|---|
| Rules 1, 2, 17-21 in force on publication | 2025-11-13 | G.S.R. 846(E) r.1(2) | matches |
| Rule 4 one year after publication | 2026-11-13 | r.1(3) | matches |
| Rules 3, 5-16, 22, 23 eighteen months after publication | 2027-05-13 | r.1(4) | matches |
| Schedule item 1 (s.8(5)) | 250 crore | "two hundred and fifty crore rupees" | matches |
| Schedule items 2, 3 (s.8(6), s.9) | 200 crore | "two hundred crore rupees" | matches |
| Schedule item 4 (s.10) | 150 crore | "one hundred and fifty crore rupees" | matches |
| Schedule item 5 (s.15) | no crore ceiling | "ten thousand rupees" | matches |
| Schedule item 7 (other) | 50 crore | "fifty crore rupees" | matches |
| Board determines amount under s.33(2) | cited as DPDP-Act-33(2) | s.33(2)(a)-(g) | matches |


Caveats, stated rather than hidden:

- The date basis is the Gazette publication date, 13 Nov 2025: the header of the Gazette issue carrying G.S.R. 843(E)
  (the Act commencement notice) and G.S.R. 846(E) (the Rules) reads "NEW DELHI, THURSDAY, NOVEMBER 13, 2025"
  (https://egazette.gov.in/WriteReadData/2025/267647.pdf). The e-Gazette upload id CG-DL-E-14112025 carries the upload
  date (14 Nov 2025), not the publication date. One year after publication is 13 Nov 2026 and eighteen months is
  13 May 2027.
- Penalty ceilings were read from the Act text, not from a secondary summary.

## Sources used

- DPDP Rules 2025, G.S.R. 846(E), MeitY copy: https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf
- DPDP Rules 2025 English text (r.1 commencement): https://www.dpdpa.in/dpdpa_rules_2025/dpdpa_rules_english_2.pdf
- DPDP Act 2023 (s.33 and the Schedule), India Code: https://indiacode.gov.in/server/api/core/bitstreams/52f9ecbb-b927-4ba6-ae6f-ca2fac50d4df/content
- PIB release (18-month phased timeline): https://www.pib.gov.in/PressReleasePage.aspx?PRID=2190014
