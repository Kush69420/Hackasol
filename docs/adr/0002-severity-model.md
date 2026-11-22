# Severity is CVSS 4.0 with Data-Category-driven CR; the Risk Matrix and Penalty Ceiling only order

A Finding's Severity band comes from its CVSS 4.0 score. Data Category sets the Environmental Confidentiality Requirement (Government Identifier, Biometric, Health, Child Data, Financial → CR:H; Authentication Secret, Contact → CR:M; Profile → CR:L), so data sensitivity is counted exactly once, in a form anyone can check in the FIRST calculator. The Risk Matrix (Data Category × Exposure) orders Findings within a band and alone sets the band for Compliance Gaps, which carry no CVSS score. A Finding with no single Personal Data Element (a Safeguard Finding, an absence check, log retention) takes the highest Data Category among the Elements the weakened resource protects: the JWT signing key protects every Authentication Secret, and an access log records every Element it captures. Exposure is derived from Evidence, never assumed: route reachable without authentication, or behind authentication anyone can obtain through open self-registration → Public; destination outside India → Cross-Border; outbound to another organisation → Third-Party; reachable by every authenticated user of a closed user base → Internal-Broad; otherwise Internal-Restricted. Disclosure Findings (processing presumed lawful but owed to the Data Principal as information or a legal review, e.g. transfer outside India) take their Risk Matrix band capped at Medium, so a lawful transfer never outranks a breach. The Primary Provision is the most specific obligation breached; its parent Act section's Penalty Ceiling only breaks remaining ties. Enforceable From is displayed and never changes Severity.

## Considered Options

- Weighted composite (0.5·CVSS + 0.3·matrix + 0.2·penalty): a single number, but the weights are arbitrary and indefensible to a reviewer.
- CVSS band shifted ±1 by the matrix: counts sensitivity twice, because CVSS 4.0 already has the CR slot for it.
- Penalty-anchored bands: no comparable scanner multiplies by statutory fines (HCL AppScan, Checkmarx, Snyk, Semgrep, CodeQL all use CVSS or assigned bands). DPDP §33 makes the Schedule a cap the Board scales by gravity and data type, not an estimate.
- Adapted CVSS for Compliance Gaps: a non-standard use of CVSS. The CNIL PIA method treats obligations as binding regardless of attack likelihood, so these use the matrix instead.

## Risk Matrix

| Tier \ Exposure | Public | Cross-Border | Third-Party | Internal-Broad | Internal-Restricted |
|---|---|---|---|---|---|
| A: Government Identifier, Biometric, Child Data, Health, Financial | critical | critical | critical | high | medium |
| B: Authentication Secret | critical | high | high | high | medium |
| C: Contact, Profile | high | medium | medium | medium | low |

Within a cell, Findings are ordered by Exposure rank (Cross-Border before Third-Party), then by Penalty Ceiling.
