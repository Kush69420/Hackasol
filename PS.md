# TRACK 03

# Track 3: Cybersecurity

Find where software mishandles personal data.

CYBERSECURITY · CS-01

# Full-Stack Data Protection (DPDP) Compliance Auditor

Scan an application's code and configuration to find where personal data is mishandled, and map each finding to India's DPDP framework.

## Background

India's Digital Personal Data Protection (DPDP) Act, 2023 and the DPDP Rules, 2025 set out how organisations must collect, process, store, share and delete personal data. The Rules were notified in November 2025 and their main obligations phase in over 18 months. Most privacy checks today stop at the front end, at privacy policies and consent banners, while real problems sit in back-end services, APIs, databases, third-party integrations and cloud configuration.

## Problem Statement

Build an automated compliance assessment tool that analyses an application's source code and configuration, finds potential data protection gaps, privacy risks and security weaknesses, and maps each one to the relevant provisions of the DPDP Act and Rules. The goal is to check what the code actually does with personal data, not just whether a privacy policy exists.

## Must-have features

- Code and config scanning: analyse front end, back end, API routes, database schemas and infrastructure files (.env, Dockerfile, cloud config) of a target application.
- Personal data detection: identify where personal data is collected, stored, logged, transferred or exposed.
- DPDP mapping: link each finding to the relevant DPDP provision.
- Risk classification: rate each finding by severity (critical, high, medium, low) with a short justification.
- Compliance report: a report listing each finding with its evidence (file and line), provision, severity and recommended fix.

## Bonus features

- Consent flow assessment: check that consent is recorded, can be withdrawn, and is enforced before data is used.
- Code-level fixes generated as patches or pull requests.
- Live testing of running API endpoints.

## Deliverables

- The scanner and its source code.
- The report generated for your target application.
- The list of checks and rules your team wrote.
