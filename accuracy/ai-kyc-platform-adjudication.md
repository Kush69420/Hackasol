# Adjudication: ai-kyc-platform reference list

Target `ai-kyc-platform` at pin `70a821487c193be445810d836dd9b9b9ae22eb18` (verified clean). Independent adjudication of `accuracy/ai-kyc-platform.json` (34 entries as submitted). Read: Target source at the pin, `docs/issue-types.md`, `auditor/registry/*.yaml`, `CONTEXT.md`, `accuracy/README.md`, the reference and method note. Not read or run: any isolated path. Incidentally, one `grep` over `docs/adr/` and the registry for the word "tier" returned a single table-header line from `docs/adr/0002-severity-model.md`; nothing from it was used.

Mechanical checks, all 34 entries: every `file:line: text` evidence line matches the source at the pin (masked secrets compared by line only); every cited Provision id exists in `auditor/registry/*.yaml`; every Issue Type's primary Provision matches the catalogue.

Findings that drove the corrections: the Django backend has no route that uses authentication (every view is `AllowAny`, no model is registered in any `admin.py`); the frontend defaults and Compose set the API URLs to loopback `http://localhost`; the results page and `saveVerificationResult` do not match the serializer's field names, so they are not a reliable source for what reaches a field at runtime.

## Entries

| id | verdict | justification |
|---|---|---|
| REF-001 | upheld | `document_number` is a plain CharField beside Aadhaar/PAN choices, with no field-level protection. |
| REF-002 | upheld | Document and selfie images are plain ImageFields under MEDIA_ROOT with no protection before write. |
| REF-003 | upheld | `extracted_text` and `extracted_data` receive OCR output that the OCR service fills with Aadhaar, PAN, passport and date of birth. |
| REF-004 | upheld | Tier A/B assignment for email, phone, date of birth and address is not settled by the allowed sources, so not-determinable is right. |
| REF-005 | upheld | No code writes `VerificationAttempt`, so the content of `ocr_result` is unknown. |
| REF-006 | upheld | No code builds `GovernmentVerification` payloads, so the content is unknown. |
| REF-007 | upheld | Aadhaar is a document type and `document_number` is stored in a plain column with no vault or token indirection. |
| REF-008 | upheld | `/ocr/extract` returns `structured_data` that holds the full 12-digit Aadhaar number with no masking. |
| REF-009 | corrected | The unmasked render of `extractedData.documentNumber` is real, but the rationale wrongly said the history route supplies it; the field mapping in `api.ts` is inconsistent, so the rationale now states only the rendering and the AI service's full Aadhaar output. |
| REF-010 | corrected | The committed fallback key is real, but no route or admin model is protected by sessions or JWTs signed with it (all views `AllowAny`, admin registers nothing), so the nexus is not shown: status changed to not-determinable with a reason. |
| REF-011 | upheld | The committed PostgreSQL password protects the database that stores document numbers and OCR data. |
| REF-012 | upheld | DEBUG defaults to True and Compose sets DEBUG=1, but no error path is shown to place Personal Data in a response. |
| REF-013 | upheld | `str(e)` is returned in 500 details at the cited lines, but the exceptions come from image processing and are not shown to carry Personal Data. |
| REF-014 | corrected | The unauthenticated `KYCDocument.objects.all()` route is confirmed; the rationale overstated that the results page shows the first record (it receives a wrapper object, not a list), so that sentence was reworded. |
| REF-015 | upheld | The OCR route has no authentication but returns only data derived from the caller's own upload, so exposure of another Data Principal's record is not shown. |
| REF-016 | upheld | The serializer is an explicit field list, not a whole-model dump, so the Issue Type boundary is not met on code alone. |
| REF-017 | upheld | `allow_origins=["*"]` with credentials on the service that handles identity documents and returns identifiers. |
| REF-018 | corrected | The URL is a loopback `http://localhost` default overridden by env, so plaintext transport over a network is not shown: status changed to not-determinable with a reason. |
| REF-019 | corrected | Same loopback-default basis as REF-018: status changed to not-determinable with a reason. |
| REF-020 | corrected | Same loopback-default basis as REF-018: status changed to not-determinable with a reason. |
| REF-021 | upheld | Persistent `postgres_data` volume with no backup service or setting; `RUN_COMMANDS.md:200-206` documents only a manual `pg_dump`. |
| REF-022 | upheld | Compose publishes `5432:5432` for the database holding Government Identifiers. |
| REF-023 | upheld | The backend image declares no USER and runs the Django development server as root. |
| REF-024 | upheld | The AI service image declares no USER and runs uvicorn with `--reload` as root. |
| REF-025 | upheld | No consent step precedes the uploads, but a user-initiated upload may fall under a §7 legitimate use, so not-determinable. |
| REF-026 | upheld | The backend create route has no consent check; the same unresolved §7 question applies. |
| REF-027 | upheld | The app collects date of birth (OCR and the user model) and no age gate or parental-consent step exists anywhere. |
| REF-028 | upheld | The results page marks end of purpose (approved 12 months, rejected) and no erasure, expiry or retention code exists. |
| REF-029 | upheld | The only Data Principal-facing view shows four fields and omits stored images, OCR text and contact fields; no access summary route exists. |
| REF-030 | upheld | No code collects or edits phone, date of birth or address, so the user-editable gate is not shown. |
| REF-031 | upheld | The footer, README and results page give no named grievance or query contact. |
| REF-032 | upheld | Prometheus rule_files are commented out and the dashboard queries cover only verification, latency, document-type and risk metrics, no access or authentication events. |
| REF-033 | upheld | `GovernmentAPI` is modelled but no outbound call exists in code. |
| REF-034 | upheld | Only the README names third-party image storage; no client, region or hosting config exists in code. |
| REF-035 | added | New entry for the SEC-01 disagreement below. |

## Absent Issue Types

| Issue Type | verdict | justification |
|---|---|---|
| SEC-01 | disagree | The catch-all handler at `backend/kyc/views.py:48-49` logs the exception text of `serializer.save()` on a Personal Data row; PostgreSQL puts the failing row in the error DETAIL, so the log can carry the document number: added as REF-035, not-determinable. |
| SEC-04 | agree | No `PASSWORD_HASHERS` override or custom hashing exists, so Django's default PBKDF2 applies; `passlib` is listed but never imported. |
| SEC-09 | agree | No Personal Data or secret is placed in a path or query string; the only interpolated path value is a random `KYC-` id and the only query parameter is `document_type`. |
| SEC-10 | agree | The frontend uses no localStorage, sessionStorage, cookie or custom auth header; the results page shares only `window.location.href`. |
| SEC-12 | agree | A request logger exists: the `django` logger writes `basehttp` request lines to `django.log` (seen in the committed log) and uvicorn logs requests. |
| SEC-13 | agree | No log retention setting exists; the only retention flag is Prometheus `retention.time=200h`, which covers aggregate metrics, not logs of Personal Data processing. |
| SEC-15 | agree | No ID images, dumps or fixtures are tracked (no image or SQL files outside `venv/`); the committed `django.log` and `celerybeat-schedule` hold no Personal Data. |
| CON-02 | agree | No consent request exists to bundle across Purposes. |
| CON-03 | agree | No consent control exists, so the gate is not met. |
| CON-04 | agree | No consent grant exists, so no Withdrawal Path comparison is possible. |
| CON-05 | agree | No code sends Personal Data to a Data Processor; the Government API model has no caller and the AI service is the Data Fiduciary's own. |
| CON-06 | agree | No consent grant exists to record. |
| CON-07 | agree | No consent is requested and no notice exists, so the gate is not met. |
| CON-08 | agree | The flow collects only the identity document and selfie; the extra account fields are defined but never collected by any form or route. |
| RET-02 | agree | No delete, erasure or withdrawal route or request exists, so the gate is not met. |
| RET-03 | agree | Applies only to a Third Schedule class, which the Applicability Assumptions do not assume. |
| RIG-04 | agree | No rights notice or page exists, so the gate (a notice that lists rights and omits nomination) cannot be met. |
| CHI-02 | agree | No analytics, advertising or behavioural monitoring exists; `next/font/google` is build-time font hosting only. |

## Summary

Entries: upheld 28, corrected 6 (REF-009, REF-010, REF-014, REF-018, REF-019, REF-020), rejected 0, added 1 (REF-035). Absences: 17 agree, 1 disagree. Reference now has 35 entries: 18 confirmed, 17 not-determinable.

Adjudication complete: yes
