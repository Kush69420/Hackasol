# Report

## Applicability Assumptions

- AA-1: The Act applies: the Target Application processes digital Personal Data in India, or offers goods or services to Data Principals in India. Provisions: DPDP-Act-3 — Section 3. Dependent Findings: none

- AA-2: The Data Fiduciary is not a Significant Data Fiduciary; its duties are shown as conditional. Provisions: DPDP-Act-10 — Section 10. Dependent Findings: none

- AA-3: The Data Fiduciary is not a Third Schedule class; its duties are shown as conditional. Provisions: DPDP-Rule-8(1) — Rule 8(1), DPDP-Rules-Schedule-Third — Third Schedule. Dependent Findings: none

- AA-4: Processing relies on consent unless the code shows a section 7 legitimate use, such as processing an order the Data Principal placed. Provisions: DPDP-Act-7 — Section 7. Dependent Findings: none

## Executive summary

| Severity | DPDP obligation | security dependent on Personal Data | Safeguard |
| --- | --- | --- | --- |
| critical | 0 | 0 | 0 |
| high | 0 | 0 | 0 |
| medium | 0 | 0 | 0 |
| low | 0 | 0 | 0 |

Penalty Ceilings: none; statutory maximum under the Schedule; the Board sets any amount.

### Fix before 14 May 2027

- None identified.

## Personal Data Map

| Element | Data Category | Processing Operations (Evidence) |
| --- | --- | --- |
| model:KycSessionOutput.access_token_id | Authentication Secret | None recorded |

## Findings

No Findings.

### Observations

No Observations.

## Consent Assessment

### recorded

Applicability: not determinable — No grant paths established by the static inventory; applicability is not established. Assessment: Not determinable: a consent grant and its linked Consent Record not established by the static inventory.

Issue Types: CON-06

Linked identifiers: none

### specific

Applicability: not determinable — No controls established by the static inventory; applicability is not established. Assessment: Not determinable: a consent control or multiple Purposes not established by the static inventory.

Issue Types: CON-02, CON-03

Linked identifiers: none

### enforced server-side

Applicability: not determinable — No purposes established by the static inventory; applicability is not established. Assessment: Not determinable: a Purpose linked to a Processing Operation and its lawful basis not established by the static inventory.

Issue Types: CON-01

Linked identifiers: none

### withdrawable with comparable ease

Applicability: not determinable — No grant paths established by the static inventory; applicability is not established. Assessment: Not determinable: a grant and a comparable Withdrawal Path for the same Purpose not established by the static inventory.

Issue Types: CON-04

Linked identifiers: none

Static step counts: {   "grant": [],   "withdrawal": [] }

### propagated to Data Processors

Applicability: not determinable — No processors established by the static inventory; applicability is not established. Assessment: Not determinable: a linked Data Processor transfer and withdrawal outcome not established by the static inventory.

Issue Types: CON-05

Linked identifiers: none

### preceded by notice

Applicability: not determinable — No controls established by the static inventory; applicability is not established. Assessment: Not determinable: a consent request linked to notice contents and language options not established by the static inventory.

Issue Types: CON-07

Linked identifiers: none

### verifiable parental consent

Applicability: not determinable — The existing CHI-01 Gate did not resolve age/DOB collection or an explicit Child audience. Assessment: Not determinable: the CHI-01 Gate and a linked parental verification mechanism not established by the static inventory.

Issue Types: CHI-01

Linked identifiers: none

LLM reasoning: not assessed; cache key: c1ac7ead7623ac93e03330544c8d9194c1bbc5172262f4824b3c6be1cea53009

Limitation: Only statically resolved Purpose-specific links are represented; missing links are not proof of absence.

Limitation: Step counts require a common, statically resolved starting template; credentials and text entry are not counted.

Limitation: A dispatched deletion, browser choice, or Data Processor call does not establish actual deletion or a contract.

## Coverage Matrix

| Provision | Citation | Classification | Covering Rules |
| --- | --- | --- | --- |
| DPDP-Act-1 | Section 1 | not code-checkable | none |
| DPDP-Act-1(1) | Section 1(1) | not code-checkable | none |
| DPDP-Act-1(2) | Section 1(2) | not code-checkable | none |
| DPDP-Act-2 | Section 2 | not code-checkable | none |
| DPDP-Act-2(f) | Section 2(f) | not code-checkable | none |
| DPDP-Act-2(i) | Section 2(i) | not code-checkable | none |
| DPDP-Act-2(j) | Section 2(j) | not code-checkable | none |
| DPDP-Act-2(k) | Section 2(k) | not code-checkable | none |
| DPDP-Act-2(t) | Section 2(t) | not code-checkable | none |
| DPDP-Act-2(za) | Section 2(za) | not code-checkable | none |
| DPDP-Act-3 | Section 3 | not code-checkable | none |
| DPDP-Act-4 | Section 4 | not determinable | CON-01-express-enforcement |
| DPDP-Act-4(1) | Section 4(1) | not determinable | CON-01-express-enforcement |
| DPDP-Act-4(2) | Section 4(2) | not code-checkable | none |
| DPDP-Act-5 | Section 5 | not determinable | CON-07-angular-consent-notice, CON-07-django-unitemised-notice |
| DPDP-Act-5(1) | Section 5(1) | not determinable | CON-07-angular-consent-notice, CON-07-django-unitemised-notice |
| DPDP-Act-5(2) | Section 5(2) | not code-checkable | none |
| DPDP-Act-5(3) | Section 5(3) | not determinable | CON-07-angular-consent-notice, CON-07-django-unitemised-notice |
| DPDP-Act-6 | Section 6 | not determinable | CON-01-express-enforcement, CON-02-angular-bundled-purposes, CON-03-angular-default-true, CON-03-django-default-selected, CON-04-django-comparable-paths, CON-04-express-withdrawal-path, CON-05-express-processor-withdrawal, CON-06-django-incomplete-record, CON-06-sequelize-consent-record, CON-07-angular-consent-notice, CON-07-django-unitemised-notice, CON-08-angular-excess-elements, SEC-08-ts-account-list, SEC-08-ts-nested-records, SEC-08-ts-review-author |
| DPDP-Act-6(1) | Section 6(1) | not determinable | CON-01-express-enforcement, CON-02-angular-bundled-purposes, CON-03-angular-default-true, CON-03-django-default-selected, CON-08-angular-excess-elements, SEC-08-ts-account-list, SEC-08-ts-nested-records, SEC-08-ts-review-author |
| DPDP-Act-6(2) | Section 6(2) | not code-checkable | none |
| DPDP-Act-6(3) | Section 6(3) | not determinable | CON-07-angular-consent-notice, CON-07-django-unitemised-notice |
| DPDP-Act-6(4) | Section 6(4) | not determinable | CON-04-django-comparable-paths, CON-04-express-withdrawal-path |
| DPDP-Act-6(5) | Section 6(5) | not code-checkable | none |
| DPDP-Act-6(6) | Section 6(6) | not determinable | CON-05-express-processor-withdrawal |
| DPDP-Act-6(7) | Section 6(7) | not code-checkable | none |
| DPDP-Act-6(8) | Section 6(8) | not code-checkable | none |
| DPDP-Act-6(9) | Section 6(9) | not code-checkable | none |
| DPDP-Act-6(10) | Section 6(10) | not determinable | CON-06-django-incomplete-record, CON-06-sequelize-consent-record |
| DPDP-Act-7 | Section 7 | not determinable | CON-01-express-enforcement |
| DPDP-Act-8 | Section 8 | not determinable | CON-05-express-processor-withdrawal, RET-01-express-purpose-end, RET-02-express-erasure-request, RIG-03-express-grievance, TRF-01-undisclosed-processor-transfer |
| DPDP-Act-8(1) | Section 8(1) | not code-checkable | none |
| DPDP-Act-8(2) | Section 8(2) | not code-checkable | TRF-01-undisclosed-processor-transfer |
| DPDP-Act-8(3) | Section 8(3) | not code-checkable | none |
| DPDP-Act-8(3)(a) | Section 8(3)(a) | not code-checkable | none |
| DPDP-Act-8(3)(b) | Section 8(3)(b) | not code-checkable | none |
| DPDP-Act-8(4) | Section 8(4) | not code-checkable | none |
| DPDP-Act-8(5) | Section 8(5) | not code-checkable | none |
| DPDP-Act-8(6) | Section 8(6) | not code-checkable | none |
| DPDP-Act-8(7) | Section 8(7) | not determinable | CON-05-express-processor-withdrawal, RET-01-express-purpose-end, RET-02-express-erasure-request |
| DPDP-Act-8(7)(a) | Section 8(7)(a) | not determinable | RET-01-express-purpose-end |
| DPDP-Act-8(7)(b) | Section 8(7)(b) | not determinable | CON-05-express-processor-withdrawal, RET-02-express-erasure-request |
| DPDP-Act-8(8) | Section 8(8) | not code-checkable | none |
| DPDP-Act-8(8)(a) | Section 8(8)(a) | not code-checkable | none |
| DPDP-Act-8(8)(b) | Section 8(8)(b) | not code-checkable | none |
| DPDP-Act-8(9) | Section 8(9) | not determinable | RIG-03-express-grievance |
| DPDP-Act-8(10) | Section 8(10) | not determinable | RIG-03-express-grievance |
| DPDP-Act-8(11) | Section 8(11) | not code-checkable | none |
| DPDP-Act-9 | Section 9 | not determinable; covered, not exercised on a real Target | CHI-01-age-parental-consent, CHI-02-child-tracking |
| DPDP-Act-9(1) | Section 9(1) | not determinable; covered, not exercised on a real Target | CHI-01-age-parental-consent |
| DPDP-Act-9(2) | Section 9(2) | not code-checkable; covered, not exercised on a real Target | none |
| DPDP-Act-9(3) | Section 9(3) | not determinable; covered, not exercised on a real Target | CHI-02-child-tracking |
| DPDP-Act-9(4) | Section 9(4) | not code-checkable; covered, not exercised on a real Target | none |
| DPDP-Act-9(5) | Section 9(5) | not code-checkable; covered, not exercised on a real Target | none |
| DPDP-Act-10 | Section 10 | not code-checkable | none |
| DPDP-Act-10(1) | Section 10(1) | not code-checkable | none |
| DPDP-Act-10(2) | Section 10(2) | not code-checkable | none |
| DPDP-Act-11 | Section 11 | not determinable | RIG-01-express-incomplete-export, TRF-01-undisclosed-processor-transfer |
| DPDP-Act-11(1) | Section 11(1) | not determinable | RIG-01-express-incomplete-export, TRF-01-undisclosed-processor-transfer |
| DPDP-Act-11(1)(a) | Section 11(1)(a) | not determinable | RIG-01-express-incomplete-export |
| DPDP-Act-11(1)(b) | Section 11(1)(b) | not determinable | RIG-01-express-incomplete-export, TRF-01-undisclosed-processor-transfer |
| DPDP-Act-11(1)(c) | Section 11(1)(c) | not code-checkable | none |
| DPDP-Act-11(2) | Section 11(2) | not code-checkable | none |
| DPDP-Act-12 | Section 12 | not determinable | RET-02-express-erasure-request, RIG-02-express-email-correction |
| DPDP-Act-12(1) | Section 12(1) | not code-checkable | none |
| DPDP-Act-12(2) | Section 12(2) | not determinable | RIG-02-express-email-correction |
| DPDP-Act-12(2)(a) | Section 12(2)(a) | not code-checkable | none |
| DPDP-Act-12(2)(b) | Section 12(2)(b) | not code-checkable | none |
| DPDP-Act-12(2)(c) | Section 12(2)(c) | not code-checkable | none |
| DPDP-Act-12(3) | Section 12(3) | not determinable | RET-02-express-erasure-request |
| DPDP-Act-13 | Section 13 | not determinable | RIG-03-express-grievance |
| DPDP-Act-13(1) | Section 13(1) | not code-checkable | none |
| DPDP-Act-13(2) | Section 13(2) | not code-checkable | none |
| DPDP-Act-13(3) | Section 13(3) | not code-checkable | none |
| DPDP-Act-14 | Section 14 | not determinable | RIG-04-rights-notice |
| DPDP-Act-14(1) | Section 14(1) | not code-checkable | none |
| DPDP-Act-14(2) | Section 14(2) | not code-checkable | none |
| DPDP-Act-15 | Section 15 | not code-checkable | none |
| DPDP-Act-16 | Section 16 | static | TRF-02-terraform-storage-region |
| DPDP-Act-16(1) | Section 16(1) | static | TRF-02-terraform-storage-region |
| DPDP-Act-16(2) | Section 16(2) | not code-checkable | none |
| DPDP-Act-17 | Section 17 | not code-checkable | none |
| DPDP-Act-17(1) | Section 17(1) | not code-checkable | none |
| DPDP-Act-17(2) | Section 17(2) | not code-checkable | none |
| DPDP-Act-17(3) | Section 17(3) | not code-checkable | none |
| DPDP-Act-17(4) | Section 17(4) | not code-checkable | none |
| DPDP-Act-17(5) | Section 17(5) | not code-checkable | none |
| DPDP-Act-18 | Section 18 | not code-checkable | none |
| DPDP-Act-18(1) | Section 18(1) | not code-checkable | none |
| DPDP-Act-18(2) | Section 18(2) | not code-checkable | none |
| DPDP-Act-18(3) | Section 18(3) | not code-checkable | none |
| DPDP-Act-19 | Section 19 | not code-checkable | none |
| DPDP-Act-19(1) | Section 19(1) | not code-checkable | none |
| DPDP-Act-19(2) | Section 19(2) | not code-checkable | none |
| DPDP-Act-19(3) | Section 19(3) | not code-checkable | none |
| DPDP-Act-20 | Section 20 | not code-checkable | none |
| DPDP-Act-20(1) | Section 20(1) | not code-checkable | none |
| DPDP-Act-20(2) | Section 20(2) | not code-checkable | none |
| DPDP-Act-21 | Section 21 | not code-checkable | none |
| DPDP-Act-21(1) | Section 21(1) | not code-checkable | none |
| DPDP-Act-21(2) | Section 21(2) | not code-checkable | none |
| DPDP-Act-22 | Section 22 | not code-checkable | none |
| DPDP-Act-22(1) | Section 22(1) | not code-checkable | none |
| DPDP-Act-22(2) | Section 22(2) | not code-checkable | none |
| DPDP-Act-22(3) | Section 22(3) | not code-checkable | none |
| DPDP-Act-23 | Section 23 | not code-checkable | none |
| DPDP-Act-23(1) | Section 23(1) | not code-checkable | none |
| DPDP-Act-23(2) | Section 23(2) | not code-checkable | none |
| DPDP-Act-23(3) | Section 23(3) | not code-checkable | none |
| DPDP-Act-24 | Section 24 | not code-checkable | none |
| DPDP-Act-25 | Section 25 | not code-checkable | none |
| DPDP-Act-26 | Section 26 | not code-checkable | none |
| DPDP-Act-27 | Section 27 | not code-checkable | none |
| DPDP-Act-27(1) | Section 27(1) | not code-checkable | none |
| DPDP-Act-27(1)(d) | Section 27(1)(d) | not code-checkable | none |
| DPDP-Act-27(2) | Section 27(2) | not code-checkable | none |
| DPDP-Act-27(3) | Section 27(3) | not code-checkable | none |
| DPDP-Act-28 | Section 28 | not code-checkable | none |
| DPDP-Act-28(1) | Section 28(1) | not code-checkable | none |
| DPDP-Act-28(2) | Section 28(2) | not code-checkable | none |
| DPDP-Act-28(3) | Section 28(3) | not code-checkable | none |
| DPDP-Act-28(4) | Section 28(4) | not code-checkable | none |
| DPDP-Act-28(5) | Section 28(5) | not code-checkable | none |
| DPDP-Act-28(6) | Section 28(6) | not code-checkable | none |
| DPDP-Act-28(7) | Section 28(7) | not code-checkable | none |
| DPDP-Act-28(8) | Section 28(8) | not code-checkable | none |
| DPDP-Act-28(9) | Section 28(9) | not code-checkable | none |
| DPDP-Act-28(10) | Section 28(10) | not code-checkable | none |
| DPDP-Act-28(11) | Section 28(11) | not code-checkable | none |
| DPDP-Act-28(12) | Section 28(12) | not code-checkable | none |
| DPDP-Act-29 | Section 29 | not code-checkable | none |
| DPDP-Act-29(1) | Section 29(1) | not code-checkable | none |
| DPDP-Act-29(2) | Section 29(2) | not code-checkable | none |
| DPDP-Act-29(3) | Section 29(3) | not code-checkable | none |
| DPDP-Act-29(4) | Section 29(4) | not code-checkable | none |
| DPDP-Act-29(5) | Section 29(5) | not code-checkable | none |
| DPDP-Act-29(6) | Section 29(6) | not code-checkable | none |
| DPDP-Act-29(7) | Section 29(7) | not code-checkable | none |
| DPDP-Act-29(8) | Section 29(8) | not code-checkable | none |
| DPDP-Act-29(9) | Section 29(9) | not code-checkable | none |
| DPDP-Act-29(10) | Section 29(10) | not code-checkable | none |
| DPDP-Act-30 | Section 30 | not code-checkable | none |
| DPDP-Act-30(1) | Section 30(1) | not code-checkable | none |
| DPDP-Act-30(2) | Section 30(2) | not code-checkable | none |
| DPDP-Act-31 | Section 31 | not code-checkable | none |
| DPDP-Act-32 | Section 32 | not code-checkable | none |
| DPDP-Act-32(1) | Section 32(1) | not code-checkable | none |
| DPDP-Act-32(2) | Section 32(2) | not code-checkable | none |
| DPDP-Act-32(3) | Section 32(3) | not code-checkable | none |
| DPDP-Act-32(4) | Section 32(4) | not code-checkable | none |
| DPDP-Act-32(5) | Section 32(5) | not code-checkable | none |
| DPDP-Act-33 | Section 33 | not code-checkable | none |
| DPDP-Act-33(1) | Section 33(1) | not code-checkable | none |
| DPDP-Act-33(2) | Section 33(2) | not code-checkable | none |
| DPDP-Act-34 | Section 34 | not code-checkable | none |
| DPDP-Act-35 | Section 35 | not code-checkable | none |
| DPDP-Act-36 | Section 36 | not code-checkable | none |
| DPDP-Act-37 | Section 37 | not code-checkable | none |
| DPDP-Act-37(1) | Section 37(1) | not code-checkable | none |
| DPDP-Act-37(2) | Section 37(2) | not code-checkable | none |
| DPDP-Act-37(3) | Section 37(3) | not code-checkable | none |
| DPDP-Act-38 | Section 38 | not code-checkable | none |
| DPDP-Act-38(1) | Section 38(1) | not code-checkable | none |
| DPDP-Act-38(2) | Section 38(2) | not code-checkable | none |
| DPDP-Act-39 | Section 39 | not code-checkable | none |
| DPDP-Act-40 | Section 40 | not code-checkable | none |
| DPDP-Act-40(1) | Section 40(1) | not code-checkable | none |
| DPDP-Act-40(2) | Section 40(2) | not code-checkable | none |
| DPDP-Act-41 | Section 41 | not code-checkable | none |
| DPDP-Act-42 | Section 42 | not code-checkable | none |
| DPDP-Act-42(1) | Section 42(1) | not code-checkable | none |
| DPDP-Act-42(2) | Section 42(2) | not code-checkable | none |
| DPDP-Act-43 | Section 43 | not code-checkable | none |
| DPDP-Act-43(1) | Section 43(1) | not code-checkable | none |
| DPDP-Act-43(2) | Section 43(2) | not code-checkable | none |
| DPDP-Act-43(3) | Section 43(3) | not code-checkable | none |
| DPDP-Act-44 | Section 44 | not code-checkable | none |
| DPDP-Act-44(1) | Section 44(1) | not code-checkable | none |
| DPDP-Act-44(2) | Section 44(2) | not code-checkable | none |
| DPDP-Act-44(3) | Section 44(3) | not code-checkable | none |
| DPDP-Act-Schedule | Schedule | not code-checkable | none |
| DPDP-Act-Schedule-1 | Schedule, item 1 | not code-checkable | none |
| DPDP-Act-Schedule-2 | Schedule, item 2 | not code-checkable | none |
| DPDP-Act-Schedule-3 | Schedule, item 3 | not code-checkable | none |
| DPDP-Act-Schedule-4 | Schedule, item 4 | not code-checkable | none |
| DPDP-Act-Schedule-5 | Schedule, item 5 | not code-checkable | none |
| DPDP-Act-Schedule-6 | Schedule, item 6 | not code-checkable | none |
| DPDP-Act-Schedule-7 | Schedule, item 7 | not code-checkable | none |
| DPDP-Rule-1 | Rule 1 | not code-checkable | none |
| DPDP-Rule-1(2) | Rule 1(2) | not code-checkable | none |
| DPDP-Rule-1(3) | Rule 1(3) | not code-checkable | none |
| DPDP-Rule-1(4) | Rule 1(4) | not code-checkable | none |
| DPDP-Rule-2 | Rule 2 | not code-checkable | none |
| DPDP-Rule-3 | Rule 3 | not determinable | CON-04-django-comparable-paths, CON-04-express-withdrawal-path, CON-07-angular-consent-notice, CON-07-django-unitemised-notice |
| DPDP-Rule-3(a) | Rule 3(a) | not determinable | CON-07-angular-consent-notice, CON-07-django-unitemised-notice |
| DPDP-Rule-3(b) | Rule 3(b) | not determinable | CON-07-angular-consent-notice, CON-07-django-unitemised-notice |
| DPDP-Rule-3(c) | Rule 3(c) | not determinable | CON-04-django-comparable-paths, CON-04-express-withdrawal-path |
| DPDP-Rule-3(c)(i) | Rule 3(c)(i) | not determinable | CON-04-django-comparable-paths, CON-04-express-withdrawal-path |
| DPDP-Rule-4 | Rule 4 | not code-checkable | none |
| DPDP-Rule-5 | Rule 5 | not code-checkable | none |
| DPDP-Rule-6 | Rule 6 | not determinable | MON-01-monitoring-coverage, SEC-01-nginx-query-logging, SEC-01-ts-morgan-query-secrets, SEC-02-django-plain-fields, SEC-02-sequelize-plain-fields, SEC-03-django-aadhaar-storage, SEC-03-fastapi-aadhaar-response, SEC-03-sequelize-aadhaar-storage, SEC-04-ts-md5-password-hash, SEC-05-ts-hardcoded-jwt-key, SEC-06-express-error-disclosure, SEC-07-ts-unchecked-nested-records, SEC-08-ts-account-list, SEC-08-ts-nested-records, SEC-08-ts-review-author, SEC-09-ts-query-authentication-secret, SEC-10-ts-storage-header, SEC-11-fastapi-wildcard-cors, SEC-11-ts-wildcard-cors, SEC-12-express-access-logging, SEC-13-ts-access-log-retention, SEC-14-terraform-store-backup, SEC-15-committed-personal-data, SEC-16-docker-root-container, SEC-16-kubernetes-privileged-store, SEC-16-kubernetes-public-store, SEC-16-terraform-public-storage, SEC-16-terraform-public-store |
| DPDP-Rule-6(1) | Rule 6(1) | not determinable | MON-01-monitoring-coverage, SEC-01-nginx-query-logging, SEC-01-ts-morgan-query-secrets, SEC-02-django-plain-fields, SEC-02-sequelize-plain-fields, SEC-03-django-aadhaar-storage, SEC-03-fastapi-aadhaar-response, SEC-03-sequelize-aadhaar-storage, SEC-04-ts-md5-password-hash, SEC-05-ts-hardcoded-jwt-key, SEC-06-express-error-disclosure, SEC-07-ts-unchecked-nested-records, SEC-08-ts-account-list, SEC-08-ts-nested-records, SEC-08-ts-review-author, SEC-09-ts-query-authentication-secret, SEC-10-ts-storage-header, SEC-11-fastapi-wildcard-cors, SEC-11-ts-wildcard-cors, SEC-12-express-access-logging, SEC-13-ts-access-log-retention, SEC-14-terraform-store-backup, SEC-15-committed-personal-data, SEC-16-docker-root-container, SEC-16-kubernetes-privileged-store, SEC-16-kubernetes-public-store, SEC-16-terraform-public-storage, SEC-16-terraform-public-store |
| DPDP-Rule-6(1)(a) | Rule 6(1)(a) | not determinable | SEC-01-nginx-query-logging, SEC-01-ts-morgan-query-secrets, SEC-02-django-plain-fields, SEC-02-sequelize-plain-fields, SEC-03-django-aadhaar-storage, SEC-03-fastapi-aadhaar-response, SEC-03-sequelize-aadhaar-storage, SEC-04-ts-md5-password-hash, SEC-09-ts-query-authentication-secret, SEC-10-ts-storage-header, SEC-11-fastapi-wildcard-cors, SEC-11-ts-wildcard-cors, SEC-15-committed-personal-data |
| DPDP-Rule-6(1)(b) | Rule 6(1)(b) | static | SEC-05-ts-hardcoded-jwt-key, SEC-06-express-error-disclosure, SEC-07-ts-unchecked-nested-records, SEC-08-ts-account-list, SEC-08-ts-nested-records, SEC-08-ts-review-author, SEC-16-docker-root-container, SEC-16-kubernetes-privileged-store, SEC-16-kubernetes-public-store, SEC-16-terraform-public-storage, SEC-16-terraform-public-store |
| DPDP-Rule-6(1)(c) | Rule 6(1)(c) | not determinable | MON-01-monitoring-coverage, SEC-12-express-access-logging |
| DPDP-Rule-6(1)(d) | Rule 6(1)(d) | not determinable | SEC-14-terraform-store-backup |
| DPDP-Rule-6(1)(e) | Rule 6(1)(e) | not determinable | SEC-13-ts-access-log-retention |
| DPDP-Rule-6(1)(f) | Rule 6(1)(f) | not code-checkable | none |
| DPDP-Rule-6(1)(g) | Rule 6(1)(g) | not code-checkable | none |
| DPDP-Rule-6(2) | Rule 6(2) | not code-checkable | none |
| DPDP-Rule-7 | Rule 7 | not code-checkable | none |
| DPDP-Rule-7(1) | Rule 7(1) | not code-checkable | none |
| DPDP-Rule-7(2) | Rule 7(2) | not code-checkable | none |
| DPDP-Rule-8 | Rule 8 | not determinable | RET-03-express-erasure-notice, SEC-13-ts-access-log-retention |
| DPDP-Rule-8(1) | Rule 8(1) | not determinable | RET-03-express-erasure-notice |
| DPDP-Rule-8(2) | Rule 8(2) | not determinable | RET-03-express-erasure-notice |
| DPDP-Rule-8(3) | Rule 8(3) | not determinable | SEC-13-ts-access-log-retention |
| DPDP-Rule-9 | Rule 9 | not determinable | RIG-03-express-grievance |
| DPDP-Rule-10 | Rule 10 | not determinable; covered, not exercised on a real Target | CHI-01-age-parental-consent |
| DPDP-Rule-11 | Rule 11 | not code-checkable | none |
| DPDP-Rule-12 | Rule 12 | not determinable; covered, not exercised on a real Target | CHI-02-child-tracking |
| DPDP-Rule-13 | Rule 13 | static | TRF-02-terraform-storage-region |
| DPDP-Rule-13(4) | Rule 13(4) | static | TRF-02-terraform-storage-region |
| DPDP-Rule-14 | Rule 14 | not determinable | RIG-01-express-incomplete-export, RIG-02-express-email-correction, RIG-03-express-grievance, RIG-04-rights-notice |
| DPDP-Rule-14(3) | Rule 14(3) | not determinable | RIG-03-express-grievance |
| DPDP-Rule-14(4) | Rule 14(4) | not determinable | RIG-04-rights-notice |
| DPDP-Rule-15 | Rule 15 | static | TRF-02-terraform-storage-region |
| DPDP-Rule-16 | Rule 16 | not code-checkable | none |
| DPDP-Rule-17 | Rule 17 | not code-checkable | none |
| DPDP-Rule-18 | Rule 18 | not code-checkable | none |
| DPDP-Rule-19 | Rule 19 | not code-checkable | none |
| DPDP-Rule-20 | Rule 20 | not code-checkable | none |
| DPDP-Rule-21 | Rule 21 | not code-checkable | none |
| DPDP-Rule-22 | Rule 22 | not code-checkable | none |
| DPDP-Rule-23 | Rule 23 | not code-checkable | none |
| DPDP-Rules-Schedule-First | First Schedule | not code-checkable | none |
| DPDP-Rules-Schedule-Second | Second Schedule | not code-checkable | none |
| DPDP-Rules-Schedule-Third | Third Schedule | not determinable | RET-03-express-erasure-notice |
| DPDP-Rules-Schedule-Fourth | Fourth Schedule | not determinable; covered, not exercised on a real Target | CHI-02-child-tracking |
| DPDP-Rules-Schedule-Fifth | Fifth Schedule | not code-checkable | none |
| DPDP-Rules-Schedule-Sixth | Sixth Schedule | not code-checkable | none |
| DPDP-Rules-Schedule-Seventh | Seventh Schedule | not code-checkable | none |

## Method, accuracy and limitations

Static Rules use Semgrep, TypeScript AST and configuration analysers. Cache-only mode replays matching cached LLM fields; uncached fields are not assessed. Live Probe outcomes, when available, appear with their Findings.

| Method | Value |
| --- | --- |
| Target Application | singharya-e-kyc |
| Target revision | e6e78d53edd30fd5be88dcd82d5afc1a2010d025 |
| Target source | targets/singharya-e-kyc |
| Exclusions | **/.git/**, **/node_modules/**, tests/**, **/__pycache__/**, **/*.pyc |
| Files scanned | 41 |
| Files excluded | 45 |
| Rule count | 51 |
| LLM provider | ollama |
| LLM model | llama3.1 |
| Prompt versions | classification: classification-v1, triage: triage-v1, consent: consent-v1, fix: fix-v1 |
| LLM mode | cache-only |
| Cache hits | 0 |
| Cache misses | 4 |
| LLM fields not assessed | 4 |
| Cache-only reason | ollama is unreachable or authentication failed |
