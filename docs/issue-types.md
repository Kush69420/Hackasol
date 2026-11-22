# Issue Types

The approved catalogue of Issue Types (see CONTEXT.md). Each Issue Type owns the Provisions its Rules cite. **Primary** marks the Provision with the highest Penalty Ceiling. **Verify** says whether static Rules, Live Probes, or both can detect it.

Penalty Ceilings (Act, Schedule): §8(5) ₹250 cr · §8(6) ₹200 cr · §9 ₹200 cr · §10 ₹150 cr · any other provision ₹50 cr.
Enforceable From: Act obligations and Rules 3, 5–16 commence 13 May 2027 (Rules notified 13 Nov 2025, G.S.R. 846(E)).

## Security safeguards

| ID | Issue Type | Primary | Related Provisions | Verify |
|---|---|---|---|---|
| SEC-01 | Personal Data written to logs | Act §8(5) | Rule 6(1)(a), Rule 6(1)(e), CWE-532 | static |
| SEC-02 | Tier A/B Personal Data Elements stored unencrypted | Act §8(5) | Rule 6(1)(a), IT Act §43A, CWE-311 | static |
| SEC-03 | Aadhaar number stored outside a vault or displayed unmasked | Act §8(5) | Rule 6(1)(a), Aadhaar Act 2016 §29, Aadhaar (Sharing of Information) Regulations 2016 | static, live |
| SEC-04 | Weak or missing password hashing | Act §8(5) | Rule 6(1)(a), CWE-916 | static |
| SEC-05 | Hard-coded secret or committed .env (Safeguard Finding) | Act §8(5) | Rule 6(1)(b), CWE-798 | static |
| SEC-06 | Debug mode or verbose errors in deployment config (Safeguard Finding) | Act §8(5) | Rule 6(1)(b), CWE-489, CWE-209 | static, live |
| SEC-07 | Missing authentication or ownership check on a route returning Personal Data | Act §8(5) | Rule 6(1)(b), CWE-639, OWASP API1 | static, live |
| SEC-08 | Over-exposed responses (whole model or `fields='__all__'` serialised) | Act §8(5) | Act §6(1), CWE-213, OWASP API3 | static, live |
| SEC-09 | Personal Data in URLs or query strings | Act §8(5) | Rule 6(1)(a), CWE-598 | static, live |
| SEC-10 | Personal Data in localStorage, sessionStorage or cookies | Act §8(5) | Rule 6(1)(a), CWE-922 | static, live |
| SEC-11 | Insecure transport, cookie flags or CORS wildcard (Safeguard Finding) | Act §8(5) | Rule 6(1)(a), CWE-319, CWE-614, CWE-942 | static, live |
| SEC-12 | No access logging on reads of Personal Data | Act §8(5) | Rule 6(1)(c) | static |
| SEC-13 | Log retention under one year | Act §8(5) | Rule 6(1)(e), Rule 8(3) | static |
| SEC-14 | No backup for Personal Data stores | Act §8(5) | Rule 6(1)(d) | static |
| SEC-15 | Real Personal Data committed (fixtures, ID images, logs, DB dumps) | Act §8(5) | Rule 6(1)(a), Aadhaar Act 2016 §29 | static |
| SEC-16 | Infrastructure misconfiguration (container as root, exposed DB port, public bucket) | Act §8(5) | Rule 6(1)(b), CWE-250 | static |

## Consent and notice

| ID | Issue Type | Primary | Related Provisions | Verify |
|---|---|---|---|---|
| CON-01 | Processing without an Enforcement Point, or with client-side gating only | Act §4(1) | Act §6(1) | static, live |
| CON-02 | Consent bundled across Purposes | Act §6(1) | Rule 3(b) | static |
| CON-03 | Pre-ticked or default-true consent | Act §6(1) | Rule 3 | static, live |
| CON-04 | No Withdrawal Path, or one harder than the grant | Act §6(4) | Rule 3(c)(i) | static, live |
| CON-05 | Withdrawal not propagated to Data Processors | Act §6(6) | Act §8(7)(b) | static, live |
| CON-06 | Consent Record missing Purpose, notice version or time | Act §6(10) | Rule 3 | static |
| CON-07 | Notice not itemised, or no English/Eighth Schedule language option | Act §5(1) | Act §5(3), Act §6(3), Rule 3 | static, live |
| CON-08 | Personal Data Elements collected beyond the Purpose | Act §6(1) | Rule 3(b) | static |

## Retention, erasure and rights

| ID | Issue Type | Primary | Related Provisions | Verify |
|---|---|---|---|---|
| RET-01 | No erasure once the Purpose is served | Act §8(7)(a) | Act §8(8), Rule 8(1) | static |
| RET-02 | Incomplete erasure (soft delete; skipped Elements, Data Processors or backups) | Act §8(7) | Act §12(3), Act §8(7)(b) | static, live |
| RET-03 | No 48-hour notice before erasure | Rule 8(2) | Act §8(8) | static |
| RIG-01 | No access/summary route, or it omits the Data Processors data was shared with | Act §11(1) | Rule 14 | static, live |
| RIG-02 | No correction or update route | Act §12(2) | Rule 14 | static, live |
| RIG-03 | No grievance mechanism or DPO/contact details | Act §8(10) | Act §8(9), Act §13, Rule 9, Rule 14(3) | static, live |
| RIG-04 | No nomination | Act §14 | Rule 14(4) | static |
| RIG-05 | Personal Data used for decisions without validation | Act §8(3) | — | static |

## Children, transfers and breach

| ID | Issue Type | Primary | Related Provisions | Verify |
|---|---|---|---|---|
| CHI-01 | No age gate or verifiable parental consent | Act §9(1) | Rule 10 | static, live |
| CHI-02 | Analytics, tracking or ads with no exclusion for Child Data | Act §9(3) | Rule 12 | static |
| TRF-01 | Personal Data sent to a third-party SDK or API | Act §8(2) | Act §11(1)(b) | static, live |
| TRF-02 | Personal Data sent or stored outside India | Act §16 | Rule 15, Rule 13(4) | static, live |
| BRE-01 | No breach detection or intimation capability | Act §8(6) | Rule 7 | static |

Legal tensions raise a Finding with status Needs Legal Review. Known example: RET-02 or CON-04 (immediate deletion on withdrawal) against Rule 8(3) (retain processing logs for at least one year).
