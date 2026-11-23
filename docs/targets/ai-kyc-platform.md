# Secondary Target: ai-kyc-platform

| Item | Value |
|---|---|
| Remote | https://github.com/JhashankKumar/ai-kyc-platform |
| Pinned commit | `70a821487c193be445810d836dd9b9b9ae22eb18` (2025-09-11) |
| Local clone | `targets/ai-kyc-platform/` (git-ignored; never committed) |
| Exclusion profile | `ai-kyc-platform`: `backend/venv/**`, `**/__pycache__/**`, `**/*.pyc` (plus `.git`, `node_modules`) |

## Verified layout

The issue expected Next.js and FastAPI. The pinned code has three parts, and the Government Identifier storage is in Django, so Django is in scope:

- `frontend/src`: Next.js (App Router pages, `services/api.ts` client).
- `backend/`: Django REST Framework. The `users`, `kyc` and `compliance` apps; the `kyc_platform` project (settings, urls, middleware, Celery); a committed `backend/logs/django.log`.
- `ai-services/`: FastAPI. OCR, face match, liveness and forgery services; pydantic models in `models/schemas.py`.
- `backend/venv/` (9,533 files) is a committed virtualenv and is excluded.

## Scan

```sh
dpdp-audit scan targets/ai-kyc-platform          # writes reports/ai-kyc-platform/report.{json,md,html,pdf}
dpdp-audit scan targets/ai-kyc-platform --inventory-only
```

## Supported idioms

- **Django** (`auditor/analysers/django.py`): model fields and choices; `urls.py` path/re_path/include and router registrations joined to views; DRF ViewSet/APIView/@api_view with permission classes and the settings defaults; serializer fields; logging handlers; Collect/Store/Expose/Log steps inside handlers.
- **FastAPI** (`auditor/analysers/fastapi.py`): app and APIRouter routes with `include_router` prefixes and `Depends`; pydantic request/response models; `UploadFile` Collect; fields returned from service dictionaries (for example `OCRService.aadhaar_number`); CORS middleware.
- **Next.js** (`auditor/ts/src/nextjs.mjs`): JSX form inputs as Collect, fetch/axios service calls joined to backend routes by method and normalised path, browser storage, `app/` and `pages/` route files.

## Classification

- **Government Identifier:**
  - `KYCDocument.document_number` (`backend/kyc/models.py:30`), because the model's `document_type` choices declare Aadhaar and PAN (`:11-12`).
  - The OCR fields `aadhaar_number`, `pan_number` and `passport_number` (`ai-services/services/ocr_service.py:182,200,126`).
- **Biometric:** only uploads the code processes as a face. The `/face/match` `document_image` and `selfie_image` (`ai-services/main.py:194-195`, processed at `:211`) and the `/liveness/detect` `selfie_image` (`:230`, processed at `:243`). An upload alone is not Biometric. Match and liveness scores are recorded as Profile, because neither docs/issue-types.md nor CONTEXT.md treats derived scores as Biometric data.

## Findings at the pin

| Issue Type | Evidence | Element |
|---|---|---|
| SEC-03 | `ai-services/main.py:145` returns the OCR Aadhaar number unmasked | `collection:OCRService.aadhaar_number` |
| SEC-03 | `backend/kyc/models.py:11` stores Aadhaar in a plain model field | `model:KYCDocument.document_number` |
| SEC-02 | `backend/kyc/models.py:30` has no field-level protection | `model:KYCDocument.document_number` |
| SEC-11 | `ai-services/main.py:36` wildcard CORS on the OCR and biometric routes | n/a (configuration Finding) |
| SEC-12 | `backend/kyc/urls.py:5` | `model:KYCDocument.document_number` |
| MON-01 | `monitoring/grafana/dashboards/kyc-dashboard.json:11` | `model:AuditLog.ip_address` |
| RIG-03 | `backend/users/models.py:8` | `model:User.email` |

Government Identifier values are masked in every Report format.

## Known limits (recorded, not manufactured)

- **No Biometric Finding.** Biometric Elements are in the Personal Data Map. However, the selfie is never stored by Django: `frontend/src/app/kyc/start/page.tsx:95,195,236` sends `selfieFile` only to face matching and liveness, and `services/api.ts:382-386` sends Django only `JSON.stringify(result)`. The document upload in `components/DocumentUpload.tsx:97-108` is simulated. No traced flow shows Biometric data stored or exposed unsafely.
- **Path mismatch.** The front end calls `POST /liveness/check` (`services/api.ts:289`), but FastAPI registers `/liveness/detect` (`ai-services/main.py:228`). The two are not joined.
- **Not yet supported for Django:** SEC-05 and SEC-11 checks on `settings.py` (hard-coded `SECRET_KEY`, `DEBUG`, cookie flags), and SEC-15 on the committed `backend/logs/django.log`.
- `frontend/src/app/page.tsx:123` partly fails Semgrep parsing (JSX text). Semgrep reports this as a warning and scans the rest of the file.
