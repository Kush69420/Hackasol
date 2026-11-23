# Report

## Applicability Assumptions

- AA-1: The Act applies: the Target Application processes digital Personal Data in India, or offers goods or services to Data Principals in India. Provisions: DPDP-Act-3 — Section 3. Dependent Findings: SEC-03-9a0640bc6639, SEC-03-efb9664725b2, SEC-02-1c18323367ce, MON-01-72fc143c58bf, SEC-12-e7116519cc6a, RIG-03-5210dafdc63d

- AA-2: The Data Fiduciary is not a Significant Data Fiduciary; its duties are shown as conditional. Provisions: DPDP-Act-10 — Section 10. Dependent Findings: none

- AA-3: The Data Fiduciary is not a Third Schedule class; its duties are shown as conditional. Provisions: DPDP-Rule-8(1) — Rule 8(1), DPDP-Rules-Schedule-Third — Third Schedule. Dependent Findings: none

- AA-4: Processing relies on consent unless the code shows a section 7 legitimate use, such as processing an order the Data Principal placed. Provisions: DPDP-Act-7 — Section 7. Dependent Findings: none

## Executive summary

| Severity | DPDP obligation | security dependent on Personal Data | Safeguard |
| --- | --- | --- | --- |
| critical | 0 | 0 | 0 |
| high | 0 | 2 | 1 |
| medium | 0 | 1 | 0 |
| low | 1 | 2 | 0 |

Penalty Ceilings: ₹250 crore, ₹50 crore; statutory maximum under the Schedule; the Board sets any amount.

### Fix before 13 May 2027

- SEC-11-f02c64b4ece0 — Enforceable From 2027-05-13
- SEC-03-9a0640bc6639 — Enforceable From 2027-05-13
- SEC-03-efb9664725b2 — Enforceable From 2027-05-13
- SEC-02-1c18323367ce — Enforceable From 2027-05-13
- MON-01-72fc143c58bf — Enforceable From 2027-05-13
- SEC-12-e7116519cc6a — Enforceable From 2027-05-13
- RIG-03-5210dafdc63d — Enforceable From 2027-05-13

## Personal Data Map

| Element | Data Category | Processing Operations (Evidence) |
| --- | --- | --- |
| param:POST /face/match#body.document_image | Biometric | Collect (ai-services/main.py:194–194); Expose (ai-services/main.py:213–221) |
| param:POST /face/match#body.selfie_image | Biometric | Collect (ai-services/main.py:195–195); Expose (ai-services/main.py:213–221) |
| param:POST /liveness/detect#body.selfie_image | Biometric | Collect (ai-services/main.py:230–230); Expose (ai-services/main.py:245–252) |
| model:LivenessResponse.liveness_score | Profile | None recorded |
| model:VerificationRequest.user_id | Profile | None recorded |
| param:POST /verify/complete#body.user_id | Profile | Collect (ai-services/models/schemas.py:69–69) |
| collection:LivenessDetectionService.liveness_score | Profile | None recorded |
| collection:OCRService.passport_number | Government Identifier | Expose (ai-services/main.py:145–151) |
| collection:OCRService.date_of_birth | Profile | Expose (ai-services/main.py:145–151) |
| collection:OCRService.aadhaar_number | Government Identifier | Expose (ai-services/main.py:145–151) |
| collection:OCRService.pan_number | Government Identifier | Expose (ai-services/main.py:145–151) |
| model:AuditLog.user | Profile | None recorded |
| model:AuditLog.ip_address | Contact | None recorded |
| model:AuditLog.user_agent | Profile | None recorded |
| model:RiskAssessment.user | Profile | None recorded |
| model:KYCDocument.user | Profile | None recorded |
| model:KYCDocument.document_number | Government Identifier | Store (backend/kyc/views.py:34–34); Expose (backend/kyc/views.py:39–39); Collect (backend/kyc/views.py:26–26); Expose (backend/kyc/views.py:66–66) |
| model:KYCDocument.face_match_score | Profile | Store (backend/kyc/views.py:34–34); Expose (backend/kyc/views.py:39–39); Collect (backend/kyc/views.py:26–26); Expose (backend/kyc/views.py:66–66) |
| model:KYCDocument.liveness_score | Profile | Store (backend/kyc/views.py:34–34); Expose (backend/kyc/views.py:39–39); Collect (backend/kyc/views.py:26–26); Expose (backend/kyc/views.py:66–66) |
| model:VerificationAttempt.user | Profile | None recorded |
| model:User.email | Contact | None recorded |
| model:User.phone_number | Contact | None recorded |
| model:User.date_of_birth | Profile | None recorded |
| model:User.address | Contact | None recorded |
| model:User.is_verified | Profile | None recorded |
| model:User.created_at | Profile | None recorded |
| model:User.updated_at | Profile | None recorded |
| model:UserProfile.user | Profile | None recorded |
| model:UserProfile.profile_picture | Profile | None recorded |
| form:frontend/src/components/DocumentUpload.tsx#file | Profile | Collect (frontend/src/components/DocumentUpload.tsx:211–217) |

## Findings

### SEC-11-f02c64b4ece0 — Insecure transport, cookie flags or CORS wildcard on Personal Data routes

Severity: high; CVSS CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:H, score 8.7. param:POST /face/match#body.document_image (Biometric) has Public Exposure based on Evidence at ai-services/main.py:192; CVSS CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:H scores 8.7. Primary Provision Rule 6(1)(a) has Penalty Ceiling ₹250 crore (maximum under the Schedule; actual amount set by the Board under s.33).

Exposure: Public; Evidence: ai-services/main.py:192–192

Primary Provision: DPDP-Rule-6(1)(a) — Rule 6(1)(a)

Other Provisions: CWE-319 — CWE-319, CWE-614 — CWE-614, CWE-942 — CWE-942

Penalty Ceiling: ₹250 crore (DPDP-Act-8(5)); Enforceable From: 2027-05-13.

Status: open.

Evidence:

ai-services/main.py:36–42

```
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

ai-services/main.py:192–192

```
@app.post("/face/match", response_model=FaceMatchResponse)
```

ai-services/main.py:194–194

```
    document_image: UploadFile = File(...),
```

ai-services/main.py:195–195

```
    selfie_image: UploadFile = File(...)
```

ai-services/main.py:228–228

```
@app.post("/liveness/detect", response_model=LivenessResponse)
```

ai-services/main.py:230–230

```
    selfie_image: UploadFile = File(...)
```

Data Flow:

- Collect — ai-services/main.py:194–194; backend; fastapi; evidenced
- Expose — ai-services/main.py:213–221; backend; fastapi; evidenced
- Collect — ai-services/main.py:230–230; backend; fastapi; evidenced
- Expose — ai-services/main.py:245–252; backend; fastapi; evidenced

Recommended fix: Serve every route that carries Personal Data over TLS only, and set Secure, HttpOnly and SameSite attributes on session cookies. Replace wildcard cross-origin rules with an explicit list of trusted origins. These transport and session controls are part of the safeguards Rule 6(1)(a) requires for the Personal Data they carry. Tailored: {'fix': 'Replace the wildcard CORS setup with an explicit allowlist of trusted origins. Right now allow_origins=["*"] is combined with allow_credentials=True, and in that case Starlette echoes back whatever Origin the request sent. Any website can then make authenticated cross-origin requests and read the Personal Data in the responses. Load the trusted HTTPS origins from configuration, for example: `ALLOWED_ORIGINS = [o.strip() for o in os.environ[\'ALLOWED_ORIGINS\'].split(\',\') if o.strip()]`. Stop the app at startup if the list is empty or contains \'*\'. Then use `app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_credentials=True, allow_methods=[\'GET\',\'POST\',\'PUT\',\'PATCH\',\'DELETE\',\'OPTIONS\'], allow_headers=[\'Authorization\',\'Content-Type\'], max_age=600)`, listing only the methods and headers the API actually uses. Only use allow_origin_regex if it is fully anchored to your own domains. Rule 6(1)(a) also calls for transport and session controls. Enforce TLS with `app.add_middleware(HTTPSRedirectMiddleware)` and `TrustedHostMiddleware(allowed_hosts=[...])`, or terminate TLS at the proxy and redirect HTTP to HTTPS there. Add the header `Strict-Transport-Security: max-age=31536000; includeSubDomains`. Set every session or auth cookie with `response.set_cookie(..., secure=True, httponly=True, samesite=\'lax\')`, or samesite=\'strict\' where the flows allow it. If a cookie truly has to be sent cross-site, use samesite=\'none\' only together with secure=True and the explicit origin allowlist.'}

LLM triage: true-positive — In ai-services/main.py, the FastAPI app adds CORSMiddleware with allow_origins=["*"], allow_credentials=True, allow_methods=["*"] and allow_headers=["*"]. The comment "Configure appropriately for production" shows nobody has narrowed it yet. The same app has public endpoints that take biometric data: /face/match accepts document_image and selfie_image, and /liveness/detect accepts selfie_image. Both endpoints send back face-match and liveness results, including confidence scores and analysis details. With this setup, a page on any origin can send requests to these endpoints from a user's browser and read the replies. Combining wildcard origins with credentials makes it worse, because Starlette echoes the requesting origin back when cookies are present. This matches the positive example (wildcard origins on a /face/match biometric endpoint) and not the negative one (a single trusted origin). It is a permissive cross-domain policy that trusts any domain, and a failure to apply reasonable security safeguards to biometric personal data.; cache key: 69cec8b3ee5307c33cf9cc130edebcf0cbc23befeb072eb27bbc0c5b99ed83c3

LLM triage citations: CWE-942 — CWE-942, DPDP-Rule-6(1) — Rule 6(1), DPDP-Rule-6 — Rule 6

### SEC-03-9a0640bc6639 — Aadhaar number stored outside a vault or displayed unmasked

Severity: high; CVSS CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:H, score 8.7. collection:OCRService.aadhaar_number (Government Identifier) has Internal-Restricted Exposure based on Evidence at ai-services/main.py:145; CVSS CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:H scores 8.7. Primary Provision Rule 6(1)(a) has Penalty Ceiling ₹250 crore (maximum under the Schedule; actual amount set by the Board under s.33).

Exposure: Internal-Restricted; Evidence: ai-services/main.py:145–151

Primary Provision: DPDP-Rule-6(1)(a) — Rule 6(1)(a)

Other Provisions: Aadhaar-Act-29 — Section 29, Aadhaar-SIR-2016 — Aadhaar (Sharing of Information) Regulations 2016

Penalty Ceiling: ₹250 crore (DPDP-Act-8(5)); Enforceable From: 2027-05-13.

Status: open.

Evidence:

ai-services/main.py:145–151

```
        return OCRResponse(
            success=True,
            extracted_text=result.get("text", ""),
            confidence=result.get("confidence", 0.0),
            structured_data=result.get("structured_data", {}),
            document_type=result.get("document_type", document_type)
        )
```

ai-services/services/ocr_service.py:182–182

```
            data["aadhaar_number"] = aadhaar_match.group().replace(" ", "")
```

Data Flow:

- Expose — ai-services/main.py:145–151; backend; fastapi; evidenced; Service structured data returned by handler

Recommended fix: Hold the Aadhaar number only in an encrypted vault or behind a reference token, and keep it out of application tables, logs, caches and files. Where a screen or response must show the number, display only the masked form. Keep every collection, storage and sharing path within the limits of Aadhaar Act 2016 §29 and the Aadhaar (Sharing of Information) Regulations 2016. Tailored: {'fix': 'Don\'t return the raw OCR output. The extracted text and structured data can contain a full 12-digit Aadhaar number (or a 16-digit VID), so redact them before building OCRResponse. Add a helper such as `mask_aadhaar(value)` that walks strings, dicts and lists recursively. It should replace any match of `\\b[2-9]\\d{3}[\\s-]?\\d{4}[\\s-]?\\d{4}\\b`, ideally confirmed with a Verhoeff checksum, and the VID pattern `\\b\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}\\b` with `XXXX XXXX ` followed by the last 4 digits. Call it as `extracted_text=mask_aadhaar(result.get("text", ""))` and `structured_data=mask_aadhaar(result.get("structured_data", {}))`. If later steps need the full number, send it straight to an encrypted Aadhaar Data Vault (HSM/KMS-backed). Put only the opaque reference token it returns (for example `structured_data["aadhaar_ref"]`) and the masked number (`aadhaar_masked`) into the response. Also make sure the raw `result`, the OCR text and the uploaded image are never logged, cached, written to temporary files or saved in application tables: delete temporary files after processing and scrub logger and exception output. Collect and share the number only for the purpose the user consented to, as Aadhaar Act 2016 §29 and the 2016 Sharing of Information Regulations require. Add a unit test that feeds OCR output containing a sample Aadhaar number and checks that the response shows only the masked form and the token.'}

LLM triage: true-positive — The evidence matches the positive example. At ocr_service.py:182 the full Aadhaar number is pulled from the document with only the spaces removed and stored as data["aadhaar_number"]. The FastAPI handler at main.py:145-151 then returns result.get("structured_data", {}) straight in the OCRResponse, with no masking, obfuscation or tokenisation. That differs from the negative example, which wraps the data in mask(). So the API response exposes the whole Aadhaar number, and the code shows none of the masking or obfuscation safeguards described in DPDP Rule 6(1)(a). One gap: the excerpt doesn't show the line where data becomes the structured_data value, but the data flow note and the matching pattern strongly suggest it does. Aadhaar Act s.29(4) is not cited because it covers publishing or displaying the number publicly, and this endpoint is marked Internal-Restricted. Provisions whose text was not fetched are also left out.; cache key: 8bec3f830e9138e79621f5f94510cdec3262eac97b0861484777766201ebc7c4

LLM triage citations: DPDP-Rule-6(1)(a) — Rule 6(1)(a), DPDP-Rule-6(1) — Rule 6(1)

### SEC-03-efb9664725b2 — Aadhaar number stored outside a vault or displayed unmasked

Severity: high; CVSS CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:H, score 8.7. model:KYCDocument.document_number (Government Identifier) has Internal-Restricted Exposure based on Evidence at backend/kyc/models.py:11; CVSS CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:H scores 8.7. Primary Provision Rule 6(1)(a) has Penalty Ceiling ₹250 crore (maximum under the Schedule; actual amount set by the Board under s.33).

Exposure: Internal-Restricted; Evidence: backend/kyc/models.py:11–11

Primary Provision: DPDP-Rule-6(1)(a) — Rule 6(1)(a)

Other Provisions: Aadhaar-Act-29 — Section 29, Aadhaar-SIR-2016 — Aadhaar (Sharing of Information) Regulations 2016

Penalty Ceiling: ₹250 crore (DPDP-Act-8(5)); Enforceable From: 2027-05-13.

Status: open.

Evidence:

backend/kyc/models.py:11–11

```
    AADHAAR = 'aadhaar', 'Aadhaar'
```

backend/kyc/models.py:30–30

```
    document_number = models.CharField(max_length=100)
```

Data Flow:

- Store — backend/kyc/views.py:34–34; handler; django; evidenced; Serializer save
- Expose — backend/kyc/views.py:39–39; response; django; evidenced; Serializer response
- Collect — backend/kyc/views.py:26–26; handler; django; evidenced; Serializer request data
- Expose — backend/kyc/views.py:66–66; response; django; evidenced; Serializer response

Recommended fix: Hold the Aadhaar number only in an encrypted vault or behind a reference token, and keep it out of application tables, logs, caches and files. Where a screen or response must show the number, display only the masked form. Keep every collection, storage and sharing path within the limits of Aadhaar Act 2016 §29 and the Aadhaar (Sharing of Information) Regulations 2016. Tailored: {'fix': "The line `AADHAAR = 'aadhaar', 'Aadhaar'` is just a label for a document type. It holds no Aadhaar number, so the line can stay as it is. The fix belongs in every model, serializer and view that stores a document number when the type is AADHAAR: (1) Remove the raw number from the application table. Send it to an encrypted vault or tokenization service, such as a UIDAI-compliant Aadhaar Data Vault or KMS envelope encryption with keys held outside the database, and store only the returned reference token, e.g. `«SECRET»)`. If you need lookups, add a keyed HMAC column. (2) Add a `masked_number` field that holds only the last 4 digits ('XXXX-XXXX-1234'), and have serializers, admin, templates and API responses return only that field. (3) Check the number before saving: 12 digits plus a Verhoeff checksum. Never write the full number to logs, Sentry or error messages, caches, sessions, the search index, exports or uploaded file names. Scrub it in logging filters and DRF exception handlers. (4) Collect it only with recorded consent for a stated purpose, as Aadhaar Act §29 and the Sharing of Information Regulations 2016 require. Do not share it with third parties, and do not publish or display it in full. Restrict and audit access to the vault lookup path. Also write a data migration that moves existing raw values into the vault, keeps the tokens and masked forms, and wipes the plaintext columns."}

LLM triage: true-positive — Line 11 of backend/kyc/models.py adds 'aadhaar' as a document type, so the model is meant to hold Aadhaar numbers. Line 30 stores `document_number` as a plain `models.CharField(max_length=100)`. Nothing in the Evidence shows encryption, masking, tokenization or any other protection on that field. This matches the positive example exactly and differs from the negative example only in having the AADHAAR choice. The data flow shows the number is taken from request data (views.py:26), saved through `serializer.save()` (views.py:34), and sent back unmasked in API responses through `serializer.data` (views.py:39, 66). Keeping a government identifier like Aadhaar in plaintext and returning it in full falls short of the reasonable security safeguards in DPDP Rule 6(1), which names encryption, obfuscation, masking and virtual tokens in clause (a). Section 29(4) of the Aadhaar Act is not cited because the exposure is internal-restricted, not public display. The Aadhaar Sharing of Information Regulations 2016 are not cited because their text was not available.; cache key: 3274fd7b1ccbba1334046091fba7ba05d0d6abf4c9fd4db391ab8b6f3793cee8

LLM triage citations: DPDP-Rule-6(1) — Rule 6(1), DPDP-Rule-6(1)(a) — Rule 6(1)(a)

### SEC-02-1c18323367ce — Tier A/B Personal Data Elements without field-level protection at rest; disk- or volume-level encryption lowers severity, it does not clear the Finding

Severity: medium; CVSS CVSS:4.0/AV:L/AC:L/AT:N/PR:H/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:H, score 6.7. model:KYCDocument.document_number (Government Identifier) has Internal-Restricted Exposure based on Evidence at backend/kyc/models.py:30; CVSS CVSS:4.0/AV:L/AC:L/AT:N/PR:H/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:H scores 6.7. Primary Provision Rule 6(1)(a) has Penalty Ceiling ₹250 crore (maximum under the Schedule; actual amount set by the Board under s.33).

Exposure: Internal-Restricted; Evidence: backend/kyc/models.py:30–30

Primary Provision: DPDP-Rule-6(1)(a) — Rule 6(1)(a)

Other Provisions: ITAct-43A — Section 43A, CWE-311 — CWE-311

Penalty Ceiling: ₹250 crore (DPDP-Act-8(5)); Enforceable From: 2027-05-13.

Status: open.

Evidence:

backend/kyc/models.py:30–30

```
    document_number = models.CharField(max_length=100)
```

backend/kyc/models.py:11–11

```
    AADHAAR = 'aadhaar', 'Aadhaar'
```

backend/kyc/models.py:12–12

```
    PAN = 'pan', 'PAN Card'
```

Data Flow:

- Store — backend/kyc/views.py:34–34; handler; django; evidenced; Serializer save
- Expose — backend/kyc/views.py:39–39; response; django; evidenced; Serializer response
- Collect — backend/kyc/views.py:26–26; handler; django; evidenced; Serializer request data
- Expose — backend/kyc/views.py:66–66; response; django; evidenced; Serializer response

Recommended fix: Protect each Tier A and Tier B Personal Data Element at field or column level before it is stored, with keys held outside the data store, so that a database dump or a restored backup does not reveal the values. Disk or volume encryption protects only the storage medium, so it lowers severity without clearing the Finding. Until DPDP §44(2) omits IT Act §43A, that section's reasonable-security duty applies alongside Rule 6(1)(a). Tailored: {'fix': "Encrypt `document_number` at the field level before it is stored. Replace `models.CharField(max_length=100)` with an encrypted field type, such as `EncryptedCharField` from django-cryptography or django-fernet-encrypted-fields, or with a custom field that uses AES-GCM in `get_prep_value`/`from_db_value`. Keep the key outside the database and outside the repo: load it from a KMS, Vault, or a secret injected through an environment variable. Use key versioning so keys can be rotated. Ciphertext is longer than the plaintext, so increase the column length (for example `max_length=512`) or use `TextField`. If you need lookups or uniqueness on this value, add a separate keyed hash column (an HMAC-SHA256 'blind index' with its own key held outside the database) and drop direct filters or indexes on the plaintext. Write a data migration that encrypts the existing rows, then confirm that a raw database dump or a restored backup no longer shows readable values. Leave the column out of logs, the admin `list_display`/`search_fields`, and plain serializer output. Disk or volume encryption alone does not resolve this finding. Field-level encryption is what meets DPDP Rule 6(1)(a) and the IT Act §43A reasonable-security duty."}

LLM triage: true-positive — In backend/kyc/models.py, document_number is a plain models.CharField(max_length=100). The same model defines document type choices AADHAAR ('aadhaar') and PAN ('pan'), so this field holds Aadhaar and PAN numbers, which are government identifiers. Nothing in the evidence shows field-level encryption, masking or tokenisation. This matches the positive example (a plain CharField holding an Aadhaar number) and not the negative one (EncryptedCharField). The data flow shows these values are collected from request.data, saved with serializer.save() and sent back in API responses through KYCVerificationSerializer(...).data, so they are stored in the database as cleartext. That falls short of the encryption, obfuscation, masking or tokenisation safeguards in DPDP Rule 6(1)(a) and is a case of CWE-311 (Missing Encryption of Sensitive Data). Two things are not visible in the evidence: whether the database itself is encrypted, and whether the serializer masks the field. Neither changes the finding that the model field is plaintext.; cache key: a9dcef4575ba23336e08457f9e84e5a917570c933cc14a9b611034cfe3ef8dba

LLM triage citations: DPDP-Rule-6(1)(a) — Rule 6(1)(a), DPDP-Rule-6(1) — Rule 6(1), DPDP-Rule-6 — Rule 6, CWE-311 — CWE-311

### MON-01-72fc143c58bf — No monitoring or review of access logs to detect unauthorised access

Severity: low; CVSS N/A (Compliance Gap: no CVSS score, so the band is the Risk Matrix cell); Risk Matrix cell low (C, Internal-Restricted). model:AuditLog.user (Profile) has Internal-Restricted Exposure based on Evidence at monitoring/grafana/dashboards/kyc-dashboard.json:11; Risk Matrix C/Internal-Restricted cell is low. Primary Provision Rule 6(1)(c) has Penalty Ceiling ₹250 crore (maximum under the Schedule; actual amount set by the Board under s.33).

Exposure: Internal-Restricted; Evidence: monitoring/grafana/dashboards/kyc-dashboard.json:11–11

Primary Provision: DPDP-Rule-6(1)(c) — Rule 6(1)(c)

Other Provisions: none

Penalty Ceiling: ₹250 crore (DPDP-Act-8(5)); Enforceable From: 2027-05-13.

Status: open.

Evidence:

monitoring/grafana/dashboards/kyc-dashboard.json:11–11

```
        "title": "KYC Verifications",
```

Data Flow:

- None recorded.

Recommended fix: Set up alerting or scheduled review on the access logs and authentication events for every store that holds Personal Data, so unauthorised access is detected and its cause and impact can be established. Rule 6(1)(c) requires monitoring and review of this kind, and investigation depends on it. Make sure the alert rules cover authentication failures and privileged reads, not only application errors. Tailored: {'fix': "The 'KYC Verifications' dashboard only displays data. Nothing alerts on access to the KYC store, so for MON-01 / Rule 6(1)(c) add monitoring on top of the panel. (1) Turn on audit logging for every store holding KYC Personal Data. That means the database (for example pgaudit, or MongoDB auditLog), any object storage holding KYC documents (S3/GCS data-access logs) and the auth/IdP layer. Log the actor identity, source IP, timestamp, the query or object accessed, the row or record count and success or failure. Send these logs to a central, tamper-resistant sink with a defined retention period (for example 1 year or more). (2) Add alert rules next to the dashboard, as Grafana/Prometheus alerting or SIEM rules, that fire on: repeated authentication failures against the KYC DB, API or admin console (for example 5 or more failures per principal or IP within 5 minutes); any privileged or admin role reading KYC tables or documents; bulk reads or exports above a baseline (for example more than 100 KYC records per session); access from unexpected service accounts, IPs or hours; and changes to roles, grants or audit configuration on KYC stores. These alerts are in addition to the existing application-error and 5xx alerts. (3) Send the alerts to an on-call channel with a named owner and a runbook that covers triage, finding the cause, assessing impact (which data principals and records were touched) and escalating to breach notification. (4) Schedule a documented periodic review, at least weekly, of privileged-access and authentication-failure reports for KYC stores, and record who reviewed them and what they found. (5) Keep the alert and dashboard definitions in version control, and test them with synthetic failed logins and a privileged read to confirm they fire."}

LLM triage: uncertain — The only Evidence is one line from the dashboard JSON: a panel title, "KYC Verifications". There is no query expression, metric name, or data source, and none of the other panels are shown. The title suggests a business throughput metric (how many KYC verifications ran) rather than monitoring of who accessed Profile/KYC personal data or of unauthorised access attempts. That would match the positive example, which has only generic metrics. But a KYC panel could also track failed or anomalous verification attempts, and the rest of the dashboard or other monitoring config may already provide the access visibility Rule 6(1)(c) requires. One title is not enough to tell whether access monitoring for this data is missing, so the Finding can't be confirmed or dismissed.; cache key: f1476fe33f9c47a20aa8b3dbd260db24dcb81078534beb3c89552b2e25b7190f

LLM triage citations: DPDP-Rule-6(1)(c) — Rule 6(1)(c), DPDP-Rule-6(1) — Rule 6(1)

### SEC-12-e7116519cc6a — No access logging on reads of Personal Data

Severity: low; CVSS N/A (Compliance Gap: no CVSS score, so the band is the Risk Matrix cell); Risk Matrix cell low (C, Internal-Restricted). model:KYCDocument.user (Profile) has Internal-Restricted Exposure based on Evidence at backend/kyc/urls.py:5; Risk Matrix C/Internal-Restricted cell is low. Primary Provision Rule 6(1)(c) has Penalty Ceiling ₹250 crore (maximum under the Schedule; actual amount set by the Board under s.33).

Exposure: Internal-Restricted; Evidence: backend/kyc/urls.py:5–5

Primary Provision: DPDP-Rule-6(1)(c) — Rule 6(1)(c)

Other Provisions: none

Penalty Ceiling: ₹250 crore (DPDP-Act-8(5)); Enforceable From: 2027-05-13.

Status: open.

Evidence:

backend/kyc/urls.py:5–5

```
    path('kyc/verifications/', views.KYCVerificationView.as_view(), name='kyc-verifications'),
```

backend/kyc/models.py:28–28

```
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kyc_documents')
```

Data Flow:

- None recorded.

Recommended fix: Enable request or access logging on every route and data store that reads Personal Data, recording who accessed which record and when, without writing the Personal Data itself. Make each entry attributable to an authenticated identity, and protect the log destination. Rule 6(1)(c) requires access to be visible through logs, monitoring and review, so that unauthorised access can be detected and investigated. Tailored: {'fix': "Add audit logging to KYCVerificationView, and keep the URL route as it is: path('kyc/verifications/', views.KYCVerificationView.as_view(), name='kyc-verifications'). (1) Require an authenticated user before anything is logged. Add LoginRequiredMixin or permission_classes=[IsAuthenticated] plus a KYC-specific permission. (2) Create a reusable AuditAccessMixin in a new file, e.g. audit/mixins.py, and add it to the view: class KYCVerificationView(AuditAccessMixin, LoginRequiredMixin, ...). In dispatch() or finalize_response(), write one structured entry to a dedicated logger, e.g. logging.getLogger('audit.pii_access'), on every request, including denied ones. Each entry records: the UTC timestamp, the actor's user ID (request.user.pk, never their name or email), the auth method or session ID hash, the request ID or correlation ID, the HTTP method, the route name ('kyc-verifications'), the action (list/retrieve/create/update), the IDs of the KYC records touched (primary keys or opaque references only), the result count for lists, the response status code, and the client IP and user agent. (3) Never log Personal Data. Leave out request and response bodies, query strings that may hold PII, document numbers, names, DOBs, addresses and images. Add a logging.Filter that drops or redacts any field not on an allow-list. (4) Log access at the data layer too. Add the same audit call to the KYC model manager/queryset or the service functions that read KYC records, so reads from Celery tasks, the admin and management commands are also tied to an identity (a service account or system actor). Enable audit logging on the KYC database tables or columns as well, e.g. pgaudit. (5) Protect where the logs go. Send 'audit.pii_access' to a separate handler, e.g. a SysLogHandler/HTTP handler shipping to a SIEM or an append-only/WORM bucket with object lock. Restrict read access to security staff. Make application roles write-only. Keep the logs for the required retention period and sync clocks with NTP. (6) Set up monitoring and review. Alert on unusual access, e.g. a large number of KYC reads per user, access outside working hours, or repeated 403s, and schedule regular access reviews. (7) To verify: write a Django test that calls the route as an authenticated user and as an anonymous user. Use assertLogs('audit.pii_access') to check that each request produces exactly one entry with the user ID, record IDs, timestamp and status, and that no PII fields from the KYC fixture appear in the log message."}

LLM triage: uncertain — The rule SEC-12-express-access-logging is written for Express apps, where the check is whether request-logging middleware such as morgan is present. This code is a Django backend. The Evidence has only two pieces: a URL route to KYCVerificationView and a ForeignKey linking KYC documents to User. Neither shows how access to KYC personal data is logged or monitored. The view code, settings.py LOGGING configuration, middleware stack and any audit-logging setup are all missing. In Django, access logging usually lives in exactly those places, or in the web server or reverse proxy, so a route and a model can't show that logging is absent. KYC data is sensitive, so Rule 6(1)(c) would apply if logging really is missing. But the Evidence can't confirm or rule out a violation, and CWE-639 isn't supported because no authorization logic is shown.; cache key: 0db893605cfb252514308b0da0331cd9f3eef2bdff6a3cd3fb8f4d0e58b83b6e

LLM triage citations: DPDP-Rule-6(1)(c) — Rule 6(1)(c), DPDP-Rule-6(1) — Rule 6(1)

### RIG-03-5210dafdc63d — No grievance mechanism or contact for Personal Data queries

Severity: low; CVSS N/A (Compliance Gap: no CVSS score, so the band is the Risk Matrix cell); Risk Matrix cell low (C, Internal-Restricted). model:User.email (Contact) has Internal-Restricted Exposure based on Evidence at backend/users/models.py:8; Risk Matrix C/Internal-Restricted cell is low. Primary Provision Section 8(10) has Penalty Ceiling ₹50 crore (maximum under the Schedule; actual amount set by the Board under s.33).

Exposure: Internal-Restricted; Evidence: backend/users/models.py:8–8

Primary Provision: DPDP-Act-8(10) — Section 8(10)

Other Provisions: DPDP-Act-8(9) — Section 8(9), DPDP-Act-13 — Section 13, DPDP-Rule-9 — Rule 9, DPDP-Rule-14(3) — Rule 14(3)

Penalty Ceiling: ₹50 crore (DPDP-Act-Schedule-7); Enforceable From: 2027-05-13.

Status: open.

Evidence:

backend/users/models.py:8–8

```
    email = models.EmailField(unique=True)
```

Data Flow:

- None recorded.

Recommended fix: Publish the business contact details of a person who can answer Personal Data queries, in the app and in its notices, as §8(9) and Rule 9 require. Establish an effective grievance mechanism under §8(10) and §13, and publish the response period as Rule 14(3) requires. Tailored: {'fix': "The `email = models.EmailField(unique=True)` field shows the app collects personal data (user email addresses). The code has nowhere to publish a Personal Data contact and no grievance mechanism. Add both: (1) Put the business contact details of the Data Protection Officer or another designated person who can answer Personal Data queries (name or role, email, phone, postal address) in settings or a `DataProtectionContact` model. Show them on a public privacy and contact page, in the app footer and account settings, and in every privacy or consent notice, as §8(9) and Rule 9 require. (2) Add a grievance mechanism under §8(10) and §13. This means a `Grievance` model (user FK or contact email, category such as access, correction, erasure, consent withdrawal or other, description, status, `created_at`, `acknowledged_at`, `resolved_at`, response), an authenticated form and API endpoint for submitting grievances, an emailed acknowledgement with a reference ID, and an admin workflow that tracks deadlines. (3) Publish the response period in the notice and on the grievance page (for example, 'We will respond within N days, up to the maximum Rule 14(3) allows'). Enforce it with an SLA field and an overdue alert. The notice should also tell users they can escalate to the Data Protection Board of India if they are not satisfied with the response."}

LLM triage: uncertain — The Evidence is one line from backend/users/models.py: a Django model field `email = models.EmailField(unique=True)`. It shows the system stores users' contact details, which makes it a Data Fiduciary handling personal data. RIG-03 is about a missing grievance mechanism under Section 8(10), Section 13 and Rule 14(3), plus missing published contact details under Section 8(9) and Rule 9. A missing mechanism can only be confirmed by looking at the whole codebase, and the Evidence doesn't do that. It says nothing about whether a complaints or grievance endpoint, view, URL route or published contact page exists anywhere else in the backend. There is no data_flow to go on either. The rule name suggests an Express check, but this code is Django, so the detector may not recognise Django-style grievance routes. The context.examples show the deciding factor is whether a complaints endpoint exists alongside the model. That can't be judged from this single model field, so the Evidence isn't enough to call this a true or false positive.; cache key: a5c73e8f382ddd4f886057a8f28d2e8a6595245e94d56c1b98773ee7e9ddfe11

LLM triage citations: DPDP-Act-8(10) — Section 8(10), DPDP-Act-13 — Section 13, DPDP-Rule-14(3) — Rule 14(3), DPDP-Act-8(9) — Section 8(9), DPDP-Rule-9 — Rule 9

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

LLM reasoning: not assessed; cache key: 91c971c7279695ec2edb6ecc9a6aaa05902e332fb7c56cedff4682e0eaefe99e

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
| DPDP-Act-6 | Section 6 | not determinable | CON-01-express-enforcement, CON-02-angular-bundled-purposes, CON-03-angular-default-true, CON-03-django-default-selected, CON-04-django-comparable-paths, CON-04-express-withdrawal-path, CON-05-express-processor-withdrawal, CON-06-django-incomplete-record, CON-06-sequelize-consent-record, CON-07-angular-consent-notice, CON-07-django-unitemised-notice, CON-08-angular-excess-elements, SEC-08-ts-account-list, SEC-08-ts-nested-records, SEC-08-ts-review-author, SEC-08-ts-whole-model-serialisation |
| DPDP-Act-6(1) | Section 6(1) | not determinable | CON-01-express-enforcement, CON-02-angular-bundled-purposes, CON-03-angular-default-true, CON-03-django-default-selected, CON-08-angular-excess-elements, SEC-08-ts-account-list, SEC-08-ts-nested-records, SEC-08-ts-review-author, SEC-08-ts-whole-model-serialisation |
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
| DPDP-Act-8 | Section 8 | not determinable | CON-05-express-processor-withdrawal, RET-01-express-purpose-end, RET-01-sequelize-soft-delete, RET-02-express-erasure-request, RIG-03-express-grievance, TRF-01-undisclosed-processor-transfer |
| DPDP-Act-8(1) | Section 8(1) | not code-checkable | none |
| DPDP-Act-8(2) | Section 8(2) | not code-checkable | TRF-01-undisclosed-processor-transfer |
| DPDP-Act-8(3) | Section 8(3) | not code-checkable | none |
| DPDP-Act-8(3)(a) | Section 8(3)(a) | not code-checkable | none |
| DPDP-Act-8(3)(b) | Section 8(3)(b) | not code-checkable | none |
| DPDP-Act-8(4) | Section 8(4) | not code-checkable | none |
| DPDP-Act-8(5) | Section 8(5) | not code-checkable | none |
| DPDP-Act-8(6) | Section 8(6) | not code-checkable | none |
| DPDP-Act-8(7) | Section 8(7) | not determinable | CON-05-express-processor-withdrawal, RET-01-express-purpose-end, RET-01-sequelize-soft-delete, RET-02-express-erasure-request |
| DPDP-Act-8(7)(a) | Section 8(7)(a) | not determinable | RET-01-express-purpose-end, RET-01-sequelize-soft-delete |
| DPDP-Act-8(7)(b) | Section 8(7)(b) | not determinable | CON-05-express-processor-withdrawal, RET-02-express-erasure-request |
| DPDP-Act-8(8) | Section 8(8) | not code-checkable | none |
| DPDP-Act-8(8)(a) | Section 8(8)(a) | not code-checkable | none |
| DPDP-Act-8(8)(b) | Section 8(8)(b) | not code-checkable | none |
| DPDP-Act-8(9) | Section 8(9) | static | RIG-03-express-grievance |
| DPDP-Act-8(10) | Section 8(10) | static | RIG-03-express-grievance |
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
| DPDP-Act-13 | Section 13 | static | RIG-03-express-grievance |
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
| DPDP-Rule-6 | Rule 6 | not determinable | MON-01-monitoring-coverage, SEC-01-nginx-query-logging, SEC-01-ts-morgan-query-secrets, SEC-02-django-plain-fields, SEC-02-sequelize-plain-fields, SEC-03-django-aadhaar-storage, SEC-03-fastapi-aadhaar-response, SEC-03-sequelize-aadhaar-storage, SEC-04-ts-constant-key-verifier, SEC-04-ts-md5-credential-compare, SEC-04-ts-md5-password-hash, SEC-05-ts-hardcoded-hmac-key, SEC-05-ts-hardcoded-jwt-key, SEC-06-express-error-disclosure, SEC-07-ts-lossy-owner-key, SEC-07-ts-public-personal-data-directory, SEC-07-ts-unauthenticated-record-read, SEC-07-ts-unchecked-nested-records, SEC-07-ts-unscoped-authenticated-read, SEC-08-ts-account-list, SEC-08-ts-nested-records, SEC-08-ts-review-author, SEC-08-ts-whole-model-serialisation, SEC-09-ts-query-authentication-secret, SEC-09-ts-query-personal-data, SEC-10-ts-storage-header, SEC-10-ts-token-storage-site, SEC-11-fastapi-wildcard-cors, SEC-11-terraform-plaintext-listener, SEC-11-ts-jsonp-response, SEC-11-ts-session-cookie-flags, SEC-11-ts-wildcard-cors, SEC-12-express-access-logging, SEC-13-ts-access-log-retention, SEC-14-terraform-store-backup, SEC-15-committed-personal-data, SEC-16-docker-root-container, SEC-16-kubernetes-privileged-store, SEC-16-kubernetes-public-store, SEC-16-terraform-public-storage, SEC-16-terraform-public-store |
| DPDP-Rule-6(1) | Rule 6(1) | not determinable | MON-01-monitoring-coverage, SEC-01-nginx-query-logging, SEC-01-ts-morgan-query-secrets, SEC-02-django-plain-fields, SEC-02-sequelize-plain-fields, SEC-03-django-aadhaar-storage, SEC-03-fastapi-aadhaar-response, SEC-03-sequelize-aadhaar-storage, SEC-04-ts-constant-key-verifier, SEC-04-ts-md5-credential-compare, SEC-04-ts-md5-password-hash, SEC-05-ts-hardcoded-hmac-key, SEC-05-ts-hardcoded-jwt-key, SEC-06-express-error-disclosure, SEC-07-ts-lossy-owner-key, SEC-07-ts-public-personal-data-directory, SEC-07-ts-unauthenticated-record-read, SEC-07-ts-unchecked-nested-records, SEC-07-ts-unscoped-authenticated-read, SEC-08-ts-account-list, SEC-08-ts-nested-records, SEC-08-ts-review-author, SEC-08-ts-whole-model-serialisation, SEC-09-ts-query-authentication-secret, SEC-09-ts-query-personal-data, SEC-10-ts-storage-header, SEC-10-ts-token-storage-site, SEC-11-fastapi-wildcard-cors, SEC-11-terraform-plaintext-listener, SEC-11-ts-jsonp-response, SEC-11-ts-session-cookie-flags, SEC-11-ts-wildcard-cors, SEC-12-express-access-logging, SEC-13-ts-access-log-retention, SEC-14-terraform-store-backup, SEC-15-committed-personal-data, SEC-16-docker-root-container, SEC-16-kubernetes-privileged-store, SEC-16-kubernetes-public-store, SEC-16-terraform-public-storage, SEC-16-terraform-public-store |
| DPDP-Rule-6(1)(a) | Rule 6(1)(a) | not determinable | SEC-01-nginx-query-logging, SEC-01-ts-morgan-query-secrets, SEC-02-django-plain-fields, SEC-02-sequelize-plain-fields, SEC-03-django-aadhaar-storage, SEC-03-fastapi-aadhaar-response, SEC-03-sequelize-aadhaar-storage, SEC-04-ts-constant-key-verifier, SEC-04-ts-md5-credential-compare, SEC-04-ts-md5-password-hash, SEC-09-ts-query-authentication-secret, SEC-09-ts-query-personal-data, SEC-10-ts-storage-header, SEC-10-ts-token-storage-site, SEC-11-fastapi-wildcard-cors, SEC-11-terraform-plaintext-listener, SEC-11-ts-jsonp-response, SEC-11-ts-session-cookie-flags, SEC-11-ts-wildcard-cors, SEC-15-committed-personal-data |
| DPDP-Rule-6(1)(b) | Rule 6(1)(b) | static | SEC-05-ts-hardcoded-hmac-key, SEC-05-ts-hardcoded-jwt-key, SEC-06-express-error-disclosure, SEC-07-ts-lossy-owner-key, SEC-07-ts-public-personal-data-directory, SEC-07-ts-unauthenticated-record-read, SEC-07-ts-unchecked-nested-records, SEC-07-ts-unscoped-authenticated-read, SEC-08-ts-account-list, SEC-08-ts-nested-records, SEC-08-ts-review-author, SEC-08-ts-whole-model-serialisation, SEC-16-docker-root-container, SEC-16-kubernetes-privileged-store, SEC-16-kubernetes-public-store, SEC-16-terraform-public-storage, SEC-16-terraform-public-store |
| DPDP-Rule-6(1)(c) | Rule 6(1)(c) | static | MON-01-monitoring-coverage, SEC-12-express-access-logging |
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
| DPDP-Rule-9 | Rule 9 | static | RIG-03-express-grievance |
| DPDP-Rule-10 | Rule 10 | not determinable; covered, not exercised on a real Target | CHI-01-age-parental-consent |
| DPDP-Rule-11 | Rule 11 | not code-checkable | none |
| DPDP-Rule-12 | Rule 12 | not determinable; covered, not exercised on a real Target | CHI-02-child-tracking |
| DPDP-Rule-13 | Rule 13 | static | TRF-02-terraform-storage-region |
| DPDP-Rule-13(4) | Rule 13(4) | static | TRF-02-terraform-storage-region |
| DPDP-Rule-14 | Rule 14 | not determinable | RIG-01-express-incomplete-export, RIG-02-express-email-correction, RIG-03-express-grievance, RIG-04-rights-notice |
| DPDP-Rule-14(3) | Rule 14(3) | static | RIG-03-express-grievance |
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

## Statutory Penalty Ceilings and Enforcement Timeline

Statutory maximum per Schedule; not a predicted or estimated fine. The actual penalty is determined by the Data Protection Board under section 33(2) factors. Ceilings apply per breach instance and are never added together. Under the Report's Applicability Assumptions, only applicable Primary Provisions contribute to the highest ceiling. Related and conditional Provisions and Findings that need legal review do not contribute.

Highest applicable ceiling: ₹250 crore (DPDP-Rule-6(1)(a), DPDP-Rule-6(1)(c)). Ceilings are not summed into a total exposure figure.

| Provision | Schedule entry | Statutory maximum | Finding applicability | Severity mix |
| --- | --- | --- | --- | --- |
| DPDP-Rule-6(1)(a) | Schedule, item 1 | ₹250 crore | Applicable Primary Provision: SEC-11-f02c64b4ece0, SEC-03-9a0640bc6639, SEC-03-efb9664725b2, SEC-02-1c18323367ce | high: 3, medium: 1 |
| DPDP-Rule-6(1)(c) | Schedule, item 1 | ₹250 crore | Applicable Primary Provision: MON-01-72fc143c58bf, SEC-12-e7116519cc6a | low: 2 |
| DPDP-Act-13 | Schedule, item 7 | ₹50 crore | Related Provision: RIG-03-5210dafdc63d | low: 1 |
| DPDP-Act-8(10) | Schedule, item 7 | ₹50 crore | Applicable Primary Provision: RIG-03-5210dafdc63d | low: 1 |
| DPDP-Act-8(9) | Schedule, item 7 | ₹50 crore | Related Provision: RIG-03-5210dafdc63d | low: 1 |
| DPDP-Rule-14(3) | Schedule, item 7 | ₹50 crore | Related Provision: RIG-03-5210dafdc63d | low: 1 |
| DPDP-Rule-9 | Schedule, item 7 | ₹50 crore | Related Provision: RIG-03-5210dafdc63d | low: 1 |

### Enforcement timeline (days relative to scan date 2026-11-23)

| Enforceable From | Status | Findings |
| --- | --- | --- |
| 2027-05-13 | enforceable in 171 days | SEC-11-f02c64b4ece0, SEC-03-9a0640bc6639, SEC-03-efb9664725b2, SEC-02-1c18323367ce, MON-01-72fc143c58bf, SEC-12-e7116519cc6a, RIG-03-5210dafdc63d |

## Method, accuracy and limitations

Static Rules use Semgrep, TypeScript AST and configuration analysers. Cache-only mode replays matching cached LLM fields; uncached fields are not assessed. Live Probe outcomes, when available, appear with their Findings.

| Method | Value |
| --- | --- |
| Target Application | ai-kyc-platform |
| Target revision | 70a821487c193be445810d836dd9b9b9ae22eb18 |
| Target source | targets/ai-kyc-platform |
| Exclusions | **/.git/**, **/node_modules/**, backend/venv/**, **/__pycache__/**, **/*.pyc |
| Files scanned | 85 |
| Files excluded | 9598 |
| Rule count | 65 |
| LLM provider | omp |
| LLM model | anthropic/claude-opus-5-5 |
| Prompt versions | classification: classification-v1, triage: triage-v2, consent: consent-v2, fix: fix-v1 |
| LLM mode | cache-only |
| Cache hits | 27 |
| Cache misses | 0 |
| LLM fields not assessed | 0 |
| Cache-only reason | forced offline for artifact regeneration |
