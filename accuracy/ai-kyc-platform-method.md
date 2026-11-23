# Method note: ai-kyc-platform reference list

Target `ai-kyc-platform` at pin `70a821487c193be445810d836dd9b9b9ae22eb18` (verified with `git -C targets/ai-kyc-platform rev-parse HEAD`, clean tree). Reference list: `accuracy/ai-kyc-platform.json` (34 entries: 22 confirmed, 12 not-determinable).

## Independence

Read only: the Target source at the pin, `docs/issue-types.md`, `auditor/registry/*.yaml`, `CONTEXT.md`, the review-procedure and anchor-policy parts of `accuracy/README.md`, and the field names and value conventions of `accuracy/juice-shop.json`. Not read or run: `reports/`, `dashboard/recordings/`, `accuracy/cache/`, `accuracy/results.md`, `RULES.md`, `auditor/rules/`, `auditor/ts/`, `corpus/`, `benchmark/`, `docs/targets/`, `docs/live-probes.md`, Target-named tests, `dpdp-audit`, Semgrep, or any git history of those paths. No `leads` were used; every `leads` array is empty.

The earlier draft was re-derived from the source, not edited. Its duplicate ids (REF-010, REF-017) are gone: ids REF-001 to REF-034 are sequential and unique. Entries use the juice-shop fields plus `evidence` (source lines copied verbatim, prefixed `file:line`), `personal_data` and `provisions` (registry ids; every id was checked against `auditor/registry/*.yaml` by script). The SECRET_KEY fallback and the PostgreSQL password are masked as `<masked>` in evidence.

Provisions left uncited on purpose: `ITAct-43A` and `Aadhaar-SIR-2016` are listed as related in the catalogue but their registry entries are `verified: false` with the excerpt withheld, so they are not cited.

## Files reviewed

Everything below was read in full unless marked "scanned".

- Root: `LICENSE` (scanned), `README.md`, `SETUP.md` (scanned for credentials, transport, consent, retention), `RUN_COMMANDS.md` (scanned for backup, credentials, logs), `docker-compose.yml`
- `backend/`: `Dockerfile`, `requirements.txt`, `manage.py`, `celerybeat-schedule` (empty), `logs/django.log` (all 5841 lines pattern-checked for emails, IP addresses and identifiers; none found, only DisallowedHost and 404 traces for `/metrics`)
- `backend/kyc_platform/`: `__init__.py`, `asgi.py`, `wsgi.py`, `celery.py`, `middleware.py`, `settings.py`, `urls.py`
- `backend/kyc/`: `__init__.py`, `admin.py`, `apps.py`, `models.py`, `serializers.py`, `tests.py`, `urls.py`, `views.py`
- `backend/users/`: `__init__.py`, `admin.py`, `apps.py`, `models.py`, `tests.py`, `views.py`
- `backend/compliance/`: `__init__.py`, `admin.py`, `apps.py`, `models.py`, `tests.py`, `views.py`
- `ai-services/`: `Dockerfile`, `requirements.txt`, `main.py`, `models/schemas.py`, `services/ocr_service.py`, `services/face_service.py`, `services/forgery_service.py`, `services/liveness_service.py`
- `frontend/`: `Dockerfile`, `.gitignore`, `.eslintrc.json`, `eslint.config.mjs`, `next.config.js`, `next.config.ts`, `package.json`, `postcss.config.mjs`, `tsconfig.json`, `README.md` (scanned), `public/*.svg` (five empty files), `src/app/favicon.ico` (binary asset, not reviewed as code)
- `frontend/src/app/`: `globals.css`, `layout.tsx`, `page.tsx`, `kyc/start/page.tsx`, `kyc/results/page.tsx`
- `frontend/src/components/`: `DocumentUpload.tsx`, `ErrorAlert.tsx`, `Loader.tsx`, `VerificationStepper.tsx`
- `frontend/src/hooks/useErrorHandler.ts`, `frontend/src/services/api.ts`
- `monitoring/prometheus.yml`, `monitoring/grafana/datasources/prometheus.yml`, `monitoring/grafana/dashboards/kyc-dashboard.json`

Excluded as vendored, generated or migrations: `backend/venv/**` (a committed virtualenv, about 9,500 files), `**/__pycache__/**`, `backend/{users,kyc,compliance}/migrations/**`, `backend/celerybeat-schedule`, `**/node_modules/**`, `**/package-lock.json`, `**/*.min.js` (the last two have no tracked instance).

## Issue Types with no entries

- SEC-01 (logs): the Django `LOGGING` config and every `logger.*` call in `kyc/views.py`, `middleware.py` and the AI services log only exception text, never request bodies, document numbers or OCR text. Frontend `console.log` and `console.error` calls print file ids, statuses and error objects, not Personal Data. The committed `django.log` holds no Personal Data.
- SEC-04 (password hashing): `AUTH_USER_MODEL` extends `AbstractUser` and `settings.py` defines no `PASSWORD_HASHERS`, so Django's default PBKDF2 hasher applies. `passlib[bcrypt]` in `ai-services/requirements.txt` is never imported. No custom hashing exists.
- SEC-09 (URLs): no Personal Data or Authentication Secret is placed in a path or query string. `api.ts:407` interpolates only a random `KYC-` identifier, and the AI service echoes `request.url`, whose only query parameter is `document_type`.
- SEC-10 (browser storage): no `localStorage`, `sessionStorage`, `document.cookie` or custom header use exists in `frontend/src`. Image previews use `URL.createObjectURL`, which is not persistent storage.
- SEC-12 (access logging): the gate (no request or access logger configured anywhere) is not met. `LOGGING` routes the `django` logger to `logs/django.log`, and that file already holds `basehttp` request lines; uvicorn logs requests in the AI service. The `AuditLog` model (`compliance/models.py:7`) has no writer, but the gate is about the logger, not the model.
- SEC-13 (log retention under one year): the gate (a log retention setting exists) is not met. `FileHandler` has no rotation or retention. The only retention setting is Prometheus `--storage.tsdb.retention.time=200h` (`docker-compose.yml:129`), which covers aggregate metrics, not logs of Personal Data processing.
- SEC-15 (committed real Personal Data): no ID images, database dumps, fixtures or Personal Data logs are tracked. `django.log` has no identifiers, `celerybeat-schedule` is empty, and the only tracked images are third-party static assets under `venv/`.
- CON-02, CON-03, CON-04, CON-05, CON-06, CON-07: the gates are not met because the code has no consent control, grant, Consent Record or notice to assess, and no code sends Personal Data to a Data Processor (the Government API model has no caller; see TRF-01). The missing consent step itself is covered by the CON-01 entries.
- CON-08 (collection beyond Purpose): the one stated Purpose is identity verification. The only Elements the flow collects are the identity document and selfie. The extra account fields (phone, address, nationality, occupation, bio) are defined in models but no form or route collects them.
- RET-02 (erasure that does not erase): the gate (an erasure route or request exists) is not met. No delete, erasure or withdrawal route exists.
- RET-03 (48-hour erasure notice): applies only to Third Schedule classes, which the Applicability Assumptions do not assume.
- RIG-04 (nomination): the gate needs an in-repo rights notice that lists Data Principal rights and omits nomination. No notice or rights page exists, so this is not determinable.
- CHI-02 (tracking of children): the code has no tracking, analytics, advertising or behavioural monitoring (no analytics SDK, no ad calls). Only `next/font/google` appears, which Next.js self-hosts at build time.

## Judgement calls worth checking

- CON-01 is `not-determinable` in both entries because the upload is user-initiated and may fall under a §7 legitimate use (Applicability Assumption 4); the code states no lawful basis.
- SEC-02 `users/models.py:8-11` is `not-determinable` because the Tier A/B assignment of Contact elements is not in code.
- SEC-08 is `not-determinable`: the serializer lists explicit fields rather than dumping the model. The unauthenticated exposure is recorded under SEC-07.
- RET-01 is `confirmed` on the evidence of an end-of-purpose marker (the "valid for 12 months" and rejected-verification text) with no erasure code anywhere.
- Considered and not raised: Grafana default `admin/admin` (`docker-compose.yml:140`; no Personal Data nexus, as dashboards show aggregate metrics), published Redis port 6379 (no Personal Data in the broker is shown, since no Celery task is defined), Django cookie and session flags (sessions serve only the admin site), and `next.config.js` ignoring build errors (not a Personal Data issue).

Review complete: yes
