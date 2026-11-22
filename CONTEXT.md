# DPDP Compliance Auditor

A tool that reads an application's source code and configuration, finds where personal data is mishandled, and maps each problem to India's Digital Personal Data Protection Act, 2023 and DPDP Rules, 2025.

## Language

### Statutory terms (used exactly as the Act defines them)

**Personal Data**:
Any data about an individual who is identifiable by or in relation to such data (Act §2(t)).
_Avoid_: PII, sensitive data, user data

**Data Principal**:
The individual to whom the Personal Data relates; for a child, includes the parent or lawful guardian (Act §2(j)).
_Avoid_: User, data subject, customer

**Data Fiduciary**:
The person who decides the purpose and means of processing Personal Data (Act §2(i)); for a scan, the owner of the Target Application.
_Avoid_: Controller, company, app owner

**Data Processor**:
A person who processes Personal Data on behalf of a Data Fiduciary (Act §2(k)), e.g. a third-party API or cloud service the Target Application sends data to.
_Avoid_: Vendor, third party, sub-processor

**Child**:
An individual who has not completed eighteen years of age (Act §2(f)).
_Avoid_: Minor, kid

### Audit terms

**Target Application**:
A codebase the Auditor scans and reports on.
_Avoid_: Target repo, victim app, project under test

**Primary Target**:
The Target Application whose Report is the main deliverable: OWASP Juice Shop, unmodified, at a pinned commit.
_Avoid_: Main app, demo app

**Secondary Target**:
Any other Target Application, scanned to show what the Primary Target lacks (Government Identifiers, real consent code) and that the checks generalise.
_Avoid_: Extra app, benchmark app

**Evidence**:
The file, line and code excerpt in a Target Application that supports a Finding. Personal Data is shown as found, except Authentication Secrets, keys and Government Identifiers, which are masked.
_Avoid_: Proof, snippet, location

**Applicability Assumption**:
A stated premise every Finding in a Report depends on: that the Act applies to the Target Application (§3), that its Data Fiduciary is not a Significant Data Fiduciary or a Third Schedule class, and that processing relies on consent unless the code shows a legitimate use (§7).
_Avoid_: Scope note, disclaimer

**Issue Type**:
A distinct, language-independent way Personal Data can be mishandled (e.g. "Personal Data written to logs"); it owns the Provisions that all its Rules cite.
_Avoid_: Check, control, category, vulnerability class

**Rule**:
One concrete detector that recognises an Issue Type in one language, framework or file kind; every Rule belongs to exactly one Issue Type.
_Avoid_: Check, signature, pattern, query

**Rules List**:
The published catalogue of Issue Types, each with its Rules nested beneath it.
_Avoid_: Checklist, rule dump

**Finding**:
One instance of an Issue Type at one location in a Target Application; when several Rules fire on the same Evidence they form a single Finding.
_Avoid_: Issue, alert, vulnerability, violation, hit

### Legal mapping terms

**Provision**:
A citable unit of law a Finding relates to: a DPDP Act section or sub-section, a DPDP Rule, an allied Indian law (Aadhaar Act 2016 and its regulations, IT Act 2000, RBI directions), or an OWASP/CWE reference.
_Avoid_: Clause, article, requirement, regulation

**Primary Provision**:
The most specific obligation a Finding breaches (e.g. Rule 6(1)(e) for short log retention). Its parent Act section sets the Finding's Penalty Ceiling, and the Provision itself sets its Enforceable From date.
_Avoid_: Main clause, root provision

**Coverage Matrix**:
The table of every DPDP Act section and Rule, each marked as statically checkable, checkable only against a running application, or not checkable from code, with the Rules covering it.
_Avoid_: Compliance map, traceability matrix

### Detection terms

**Personal Data Element**:
A named field, column, variable, form input, config key or committed file in a Target Application that holds Personal Data, tagged with one Data Category.
_Avoid_: PII field, sensitive field, data point, attribute

**Processing Operation**:
One of Collect, Store, Log, Transfer, Expose or Erase, applied to a Personal Data Element at one location in code or configuration.
_Avoid_: Sink, source, action, usage

**Data Flow**:
The ordered chain of Processing Operations one Personal Data Element goes through across a Target Application.
_Avoid_: Taint path, trace, lineage

**Anchor Point**:
The Evidence location for a Finding about something missing: the code performing the counterpart operation (e.g. the erasure view for Elements it skips), or the application entry point for gaps that span the whole application.
_Avoid_: Nearest line, placeholder location

**Safeguard Finding**:
A Finding about a security weakness that touches no single Personal Data Element but protects named ones (a hard-coded signing key, open CORS on Personal Data routes); it cites Act §8(5) and Rule 6 only when that link is shown in Evidence.
_Avoid_: Generic vulnerability, non-privacy finding

### Consent terms

**Purpose**:
The specified purpose a Data Fiduciary states in its notice for processing a set of Personal Data Elements (Act §2(za)); consent is given per Purpose.
_Avoid_: Use case, scope, reason

**Consent Record**:
A stored entry proving that a Data Principal granted or withdrew consent for one Purpose, with the notice version and time.
_Avoid_: Consent flag, opt-in, consent log

**Enforcement Point**:
A server-side check that consent for a Purpose is in force before a Processing Operation on that Purpose's Elements runs.
_Avoid_: Consent gate, guard, middleware check

**Withdrawal Path**:
The sequence of steps a Data Principal takes to withdraw consent for one Purpose, compared in step count against the path for granting it.
_Avoid_: Opt-out, unsubscribe flow

**Consent Assessment**:
The evaluation of whether a Target Application's consent is recorded, specific, enforced, withdrawable with comparable ease, propagated to Data Processors, preceded by notice, and parentally verified for Child Data.
_Avoid_: Consent audit, consent check

**Needs Legal Review**:
The status of a Finding where two Provisions pull in opposite directions (e.g. erasure on withdrawal against one-year log retention); both readings are shown.
_Avoid_: Ambiguous, uncertain, warning

### Live testing terms

**Live Probe**:
A request or browser interaction sent to a running instance of a Target Application on localhost or an explicit allowlist, to observe how it actually handles Personal Data.
_Avoid_: Dynamic scan, DAST, pentest, live check

**Confirmed / Refuted**:
The outcome a Live Probe attaches to a matching static Finding; the captured request and response become additional Evidence.
_Avoid_: Verified, validated, false positive

### Output terms

**Fix Patch**:
A unified diff against a Target Application that resolves one Finding, proven by a re-scan in which that Finding is gone and no new Finding appears.
_Avoid_: Auto-fix, remediation, suggestion

**Report**:
The complete output of one scan of one Target Application: Applicability Assumptions, the Personal Data Map, every Finding with Evidence, Provisions, Severity, recommended fix and any Fix Patch, plus the Consent Assessment and Coverage Matrix.
_Avoid_: Audit, results, output

**Personal Data Map**:
The Report's table of every Personal Data Element against the Processing Operations applied to it, with Evidence for each, whether or not a Finding arises.
_Avoid_: Data inventory, data catalogue, PII map

**Replay Mode**:
Playback of a recorded scan at its original pace, used when a live scan cannot run.
_Avoid_: Demo mode, cached scan, fake run

**Labelled Corpus**:
The Auditor's own set of small code fixtures, a true positive and a near-miss negative for each Rule, used to measure each Rule's precision and recall.
_Avoid_: Test data, benchmark, ground truth

### Risk terms

**Data Category**:
The Auditor's own sensitivity class for Personal Data, since the Act defines none: Government Identifier, Biometric, Financial, Health, Child Data, Authentication Secret, Contact, Profile.
_Avoid_: Sensitive personal data, SPDI, PII type, data class

**Government Identifier**:
An identifier issued by the State to an individual: Aadhaar, PAN, passport, voter ID, driving licence, ABHA.
_Avoid_: ID number, national ID, KYC data

**Authentication Secret**:
A value that proves identity to the Target Application (password, OTP, session token, security answer) and so unlocks other Personal Data.
_Avoid_: Credential, secret, key

**Severity**:
A Finding's rating of critical, high, medium or low. Its band comes from the CVSS 4.0 score, with the Data Category setting the Confidentiality Requirement. Where there is no technical attack path, the band comes from the Risk Matrix instead.
_Avoid_: Priority, risk level, criticality

**Risk Matrix**:
The Auditor's grid of Data Category against Exposure; it orders Findings within a Severity band and sets the band for Findings without a CVSS score.
_Avoid_: Heat map, risk score

**Compliance Gap**:
A Finding where an obligation is unmet but no technical attack path exists (e.g. no consent-withdrawal route); it carries no CVSS score.
_Avoid_: Policy violation, non-technical finding

**Disclosure Finding**:
A Finding about processing presumed lawful that the Data Principal is owed information about, or that needs legal review (e.g. Personal Data stored outside India); its Severity never exceeds medium.
_Avoid_: Informational finding, advisory, notice

**Exposure**:
How far Personal Data reaches beyond its intended handling, from most to least exposed: Public, Cross-Border, Third-Party, Internal-Broad, Internal-Restricted.
_Avoid_: Reach, visibility, attack surface

**Cross-Border**:
The Exposure level for Personal Data that is sent or stored outside India. Transfer is lawful unless the destination is restricted under Act §16, so on its own it raises a disclosure with status Needs Legal Review rather than a breach.
_Avoid_: Offshore, international transfer, data export

**Penalty Ceiling**:
The maximum penalty the Act's Schedule allows for breaching a Provision's parent section (₹250 crore for §8(5) down to ₹50 crore for the residual entry); the Data Protection Board sets the actual amount under §33.
_Avoid_: Fine, penalty amount, exposure

**Enforceable From**:
The date a Finding's Primary Provision commences under the Act and Rules (14 May 2027 for Rules 3 and 5–16, eighteen months after Gazette publication on 14 Nov 2025); it is shown on the Finding and never changes Severity.
_Avoid_: Effective date, deadline, go-live
