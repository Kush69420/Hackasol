# Issue Types

The approved catalogue of Issue Types (see CONTEXT.md). Each Issue Type owns the Provisions its Rules cite.

- **Primary** is the most specific obligation the Finding breaches.
- **Ceiling** is the Penalty Ceiling of the Act section that obligation falls under (Rule 6 → §8(5); Rule 10 → §9). Rules that sit under no Schedule entry fall to the residual ₹50 cr.
- **Verify** says whether static Rules, Live Probes, or both can detect it.

Penalty Ceilings (Act, Schedule; maximums the Board scales under §33): §8(5) ₹250 cr · §8(6) ₹200 cr · §9 ₹200 cr · §10 ₹150 cr · any other provision ₹50 cr.

Enforceable From: the Rules and the Act commencement notice were published in the Gazette on 13 Nov 2025 (G.S.R. 846(E) and G.S.R. 843(E), same issue; header "NEW DELHI, THURSDAY, NOVEMBER 13, 2025"). The e-Gazette upload id carries 14112025, which is the upload date, not the publication date. Rule 4 commences 13 Nov 2026; Rules 3, 5–16, 22 and 23, and the Act obligations they operationalise, commence 13 May 2027. The Report states this basis.

## Applicability Assumptions

Every Report states these, and Findings depend on them:

1. The Act applies (§3): the Target Application processes digital Personal Data in India, or offers goods or services to Data Principals in India.
2. The Data Fiduciary is not a Significant Data Fiduciary (§10, Rule 13 duties shown as conditional).
3. The Data Fiduciary is not a Third Schedule class (Rule 8(1)–(2) duties shown as conditional).
4. Processing relies on consent unless the code shows a §7 legitimate use, e.g. processing an order the Data Principal placed.

## Safeguard nexus and absence gates

- A security weakness cites §8(5) / Rule 6 only when the Evidence links it to Personal Data, e.g. the weakened key or route protects named Personal Data Elements. With no link, it is reported as a security observation without a DPDP Provision.
- **Absence checks fire only with a positive reason to think the obligation applies.** Otherwise the Coverage Matrix marks them "not determinable". The **Gate** column says what that reason is.

## Security safeguards

| ID | Issue Type | Primary | Related | Ceiling | Gate | Verify |
|---|---|---|---|---|---|---|
| SEC-01 | Personal Data written to logs | Rule 6(1)(a) | CWE-532 | §8(5) | — | static |
| SEC-02 | Tier A/B Personal Data Elements without field-level protection at rest; disk- or volume-level encryption lowers severity, it does not clear the Finding | Rule 6(1)(a) | IT Act §43A (until 13 May 2027, when DPDP §44(2) omits it), CWE-311 | §8(5) | — | static |
| SEC-03 | Aadhaar number stored outside a vault or displayed unmasked | Rule 6(1)(a) | Aadhaar Act 2016 §29, Aadhaar (Sharing of Information) Regulations 2016 | §8(5) | — | static, live |
| SEC-04 | Weak or missing password hashing | Rule 6(1)(a) | CWE-916 | §8(5) | — | static |
| SEC-05 | Hard-coded secret or committed .env protecting Personal Data | Rule 6(1)(b) | CWE-798 | §8(5) | nexus | static |
| SEC-06 | Debug mode or verbose errors exposing Personal Data | Rule 6(1)(b) | CWE-489, CWE-209 | §8(5) | nexus | static, live |
| SEC-07 | Missing authentication or ownership check on a route returning Personal Data | Rule 6(1)(b) | CWE-639, OWASP API1 | §8(5) | — | static, live |
| SEC-08 | Over-exposed responses (whole model or nested records serialised) | Rule 6(1)(b) | §6(1), CWE-213, OWASP API3 | §8(5) | — | static, live |
| SEC-09 | Personal Data or Authentication Secrets in URLs or query strings | Rule 6(1)(a) | CWE-598 | §8(5) | — | static, live |
| SEC-10 | Personal Data in localStorage, sessionStorage, cookies or outbound headers | Rule 6(1)(a) | CWE-922 | §8(5) | — | static, live |
| SEC-11 | Insecure transport, cookie flags or CORS wildcard on Personal Data routes | Rule 6(1)(a) | CWE-319, CWE-614, CWE-942 | §8(5) | nexus | static, live |
| SEC-12 | No access logging on reads of Personal Data | Rule 6(1)(c) | — | §8(5) | no request or access logger configured anywhere | static |
| SEC-13 | Logs of Personal Data processing kept under one year | Rule 6(1)(e) | Rule 8(3) | §8(5) | a log retention setting exists | static |
| SEC-14 | No backup for Personal Data stores | Rule 6(1)(d) | — | §8(5) | deployment config for a persistent store exists and no backup is configured | static |
| SEC-15 | Real Personal Data committed (fixtures, ID images, logs, DB dumps) | Rule 6(1)(a) | Aadhaar Act 2016 §29 | §8(5) | values pass validators and are not seed or demo data (reserved or app-demo domains, placeholder names, documented test numbers); committed ID document images, logs and DB dumps always qualify | static |
| SEC-16 | Infrastructure misconfiguration exposing Personal Data stores (container as root, DB port public, public bucket) | Rule 6(1)(b) | CWE-250 | §8(5) | nexus | static |

## Consent and notice

| ID | Issue Type | Primary | Related | Ceiling | Gate | Verify |
|---|---|---|---|---|---|---|
| CON-01 | Processing without an Enforcement Point, or with client-side gating only | §4(1) | §6(1); §7 legitimate uses checked first | ₹50 cr | processing not covered by a §7 legitimate use | static, live |
| CON-02 | Consent bundled across Purposes | §6(1) | — | ₹50 cr | more than one Purpose found | static |
| CON-03 | Pre-ticked or default-true consent | §6(1) | — | ₹50 cr | a consent control exists | static, live |
| CON-04 | No Withdrawal Path, or one harder than the grant | §6(4) | Rule 3(c)(i) | ₹50 cr | a consent grant exists | static, live |
| CON-05 | Withdrawal not propagated to Data Processors | §6(6) | §8(7)(b) | ₹50 cr | a Data Processor receives Personal Data | static, live |
| CON-06 | Consent Record missing, or without Purpose, notice reference or time | §6(10) | — | ₹50 cr | a consent grant exists | static |
| CON-07 | Notice not itemised, or no English/Eighth Schedule language option | §5(1) | §5(3), §6(3), Rule 3(a)–(b) | ₹50 cr | consent is requested | static, live |
| CON-08 | Personal Data Elements collected beyond the Purpose | §6(1) | — | ₹50 cr | a Purpose is stated | static |

## Retention, erasure and rights

| ID | Issue Type | Primary | Related | Ceiling | Gate | Verify |
|---|---|---|---|---|---|---|
| RET-01 | No erasure once the Purpose is served | §8(7)(a) | Rule 8(1) (Third Schedule classes only) | ₹50 cr | an account-closure or end-of-purpose event exists | static |
| RET-02 | Erasure request that does not erase (flag only, soft delete, Elements or Data Processors skipped) | §12(3) | §8(7), §8(7)(b) | ₹50 cr | an erasure route or request exists | static, live |
| RET-03 | No 48-hour notice before erasure | Rule 8(2) | Rule 8(1), Third Schedule | ₹50 cr | Third Schedule class (conditional; not assumed) | static |
| RIG-01 | Access summary missing, or omitting Personal Data Elements the app processes for that Data Principal; omitting the Data Fiduciaries and Data Processors it shared data with counts only where a sharing flow is evidenced | §11(1)(a) | §11(1)(b), Rule 14 | ₹50 cr | user accounts holding Personal Data exist | static, live |
| RIG-02 | No route to correct, complete or update Personal Data Elements | §12(2) | Rule 14 | ₹50 cr | user-editable Personal Data Elements exist | static, live |
| RIG-03 | No grievance mechanism or contact for Personal Data queries | §8(10) | §13, Rule 9, Rule 14(3); §8(9) DPO (Significant Data Fiduciaries only) | ₹50 cr | user accounts exist | static, live |
| RIG-04 | No nomination | §14 | Rule 14(4) | ₹50 cr | an in-repo notice or rights page lists Data Principal rights under the DPDP Act and omits nomination; otherwise not determinable | static |

## Children, transfers and monitoring

| ID | Issue Type | Primary | Related | Ceiling | Gate | Verify |
|---|---|---|---|---|---|---|
| CHI-01 | No age gate or verifiable parental consent | §9(1) | Rule 10 | §9 | the app collects age or DOB, or targets children (education, school, games) | static, live |
| CHI-02 | Tracking, behavioural monitoring or targeted ads with no exclusion for Child Data | §9(3) | Rule 12 exemptions (Fourth Schedule) considered | §9 | CHI-01 gate met and tracking present | static |
| TRF-01 | Personal Data shared with a third-party SDK or API not disclosed to the Data Principal (disclosure; capped at Medium) | §11(1)(b) | §8(2) (valid contract; not code-checkable) | ₹50 cr | an outbound flow of Personal Data exists | static, live |
| TRF-02 | Personal Data sent or stored outside India (disclosure, capped at Medium; Needs Legal Review unless the destination is restricted under §16) | §16(1) | Rule 15 (data made available to foreign States); Rule 13(4) (Significant Data Fiduciaries only) | ₹50 cr | — | static, live |
| MON-01 | No monitoring or review of access logs to detect unauthorised access | Rule 6(1)(c) | — | §8(5) | in-repo monitoring or alerting config exists and covers no access-log or authentication events; otherwise not determinable | static |

Not checkable from code (Coverage Matrix only): §8(3) accuracy of Personal Data used for decisions or disclosure; §8(6) and Rule 7 breach intimation (they apply only once a breach occurs); §8(2) Data Processor contracts.

## Needs Legal Review

Raised when two Provisions pull in opposite directions. Example: erasure on consent withdrawal (§8(7)(a)) that also deletes the processing logs Rule 8(3) requires to be kept for one year. Erasing the account data itself does not conflict.
