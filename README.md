# DPDP Compliance Auditor

The Auditor scans a Target Application and maps Personal Data mishandling to India's DPDP Act 2023 and DPDP Rules 2025. It produces a schema-valid JSON Report with a Personal Data Map and source-anchored Findings.

## Installation

Requires Python 3.11 or newer, Git and [uv](https://docs.astral.sh/uv/):

```sh
uv venv && uv pip install -e '.[dev]'
```

## Scan

```sh
.venv/bin/dpdp-audit scan targets/juice-shop --format json
.venv/bin/dpdp-audit scan https://github.com/juice-shop/juice-shop --commit c9f99228d9d56afb5f5ca7925376292f7fa44b13 --out reports/juice-shop/report.json
```

The positional input is a local directory or Git URL. Git URLs are cloned under `targets/<name>` and existing clones are reused; `--commit SHA` selects a commit for a Git URL. Local directories are not checked out or modified. One scan writes the canonical `report.json` plus `report.md`, `report.html` and `report.pdf` rendered from it (default `reports/<target-name>/`; `--out FILE` sets the JSON path and the other formats are written beside it). PDF output uses WeasyPrint, which needs the system Pango libraries. The command prints the Report path. `--cache-dir DIR` selects the LLM cache (default `.dpdp-cache`); `--provider P` and `--model M` override provider configuration. `--inventory-only` writes the source-anchored inventory (`reports/<target-name>/inventory.json`) without Findings or LLM calls.

`dpdp-audit rules list` prints the Rules List generated from the Rule files; `RULES.md` is its committed output (`dpdp-audit rules list | diff -u RULES.md -` checks it is current).

## Pipeline

1. Inventory: the TypeScript analyser (`auditor/ts/`, TypeScript compiler API) lists routes with middleware roles, models, Angular forms, service calls, client storage and outbound headers; `auditor/analysers/config.py` reads Docker, config files and Terraform.
2. Personal Data Elements: `auditor/classify.py` classifies deterministically; the LLM classifies only what stays unresolved.
3. Data Flows: cross-file TypeScript flows (`auditor/flows.py`), log/retention/region flows (`auditor/analysers/`) and Semgrep operation Rules (`rules/semgrep/operations/`) produce Processing Operation steps and the Personal Data Map.
4. Rules (`auditor/rules/`): each Rule is a `@rule`-registered detector over the `ScanContext`; it binds to Elements, Data Flows and positive Gate Evidence, never to filenames or line numbers.
5. Mapping and Severity: `auditor/mapping.py` merges Rules on shared Evidence, cites registry Provisions, and scores CVSS 4.0 (technical) or the Risk Matrix (compliance gap, disclosure).

Every Rule has a Labelled Corpus pair, `corpus/<rule-id>/positive/` and `negative/`, checked by `tests/test_labelled_corpus.py`.

## Slice 1 coverage (Juice Shop)

`tests/test_juice_shop_slice_1.py` scans the pinned Primary Target (`targets/juice-shop` at `c9f99228`) in cache-only mode and checks each case:

| Issue Type | Case | Rules |
|---|---|---|
| SEC-07 + SEC-08 | Account records nested in unauthenticated `/rest/memories` | `SEC-07-ts-unchecked-nested-records`, `SEC-08-ts-nested-records` |
| SEC-09 + SEC-01 | Password query parameters written to the `combined` access log | `SEC-09-ts-query-authentication-secret`, `SEC-01-ts-morgan-query-secrets` |
| SEC-13 | Access log of Personal Data kept two days | `SEC-13-ts-access-log-retention` |
| SEC-08 | All account records returned to any authenticated Data Principal (Public through open registration) | `SEC-08-ts-account-list` |
| SEC-08 | Review authors' email addresses public | `SEC-08-ts-review-author` |
| SEC-02 | TOTP secret, deluxe token, card number and security answer without field-level protection | `SEC-02-sequelize-plain-fields` |
| SEC-04 | MD5 password hashing | `SEC-04-ts-md5-password-hash` |
| SEC-05 | Hard-coded JWT signing key (never reproduced) | `SEC-05-ts-hardcoded-jwt-key` |
| SEC-10 | Email and token in localStorage, attached to requests | `SEC-10-ts-storage-header` |
| RET-02 | Erasure request records a flag instead of erasing | `RET-02-express-erasure-request` |
| RIG-01 | Export omits Elements the app holds | `RIG-01-express-incomplete-export` |
| RIG-02 | No correction path for email | `RIG-02-express-email-correction` |
| TRF-02 | Terraform storage defaults to `eu-west-1` (disclosure, Needs Legal Review) | `TRF-02-terraform-storage-region` |
| SEC-11 | Wildcard CORS on Personal Data routes | `SEC-11-ts-wildcard-cors` |

Not claimed: SEC-16 (load balancer egress and LB-only task ingress are not exposure) and the CloudWatch 30-day retention (no Personal Data log stream is linked to it). Volume encryption on EFS is not credited for SEC-02 because its mount path differs from the SQLite path.

Excluded from Juice Shop scans: `data/static/codefixes/**`, `test/**`, `frontend/**/*.spec.ts`.

## Slice 2 coverage

Slice 2 adds a Rule, with a Labelled Corpus pair, for every remaining catalogue Issue Type. `tests/test_slice2.py` checks them: `-k pinned` scans the Primary Target, and `-k corpus` and `-k legal` need no Target.

| Primary Target outcome | Issue Types |
|---|---|
| Finding | SEC-14 (EFS store without backup selection), MON-01 (no monitoring of Personal Data stores) |
| Conditional (Third Schedule class, AA-3) | RET-03 |
| Not determinable (Gate unmet) | RIG-04, CHI-01 |
| Not raised | SEC-03, SEC-12 (morgan configured), SEC-15 (only seed data and role mailboxes committed), SEC-16, RIG-03, CON-01…CON-08 |

SEC-03 and CHI-* are covered only on synthetic corpus cases; the Coverage Matrix marks them "covered, not exercised on a real Target". SEC-15 recognises validated values in committed YAML/JSON/CSV, SQL dumps, logs and SQLite files. It does not recognise Government Identifier document images, because that needs OCR.

## LLM configuration

Set `DPDP_LLM_PROVIDER` to `anthropic`, `openai`, `gemini`, `ollama` or `omp`, and optionally set `DPDP_LLM_MODEL`. Hosted providers use `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` or `GEMINI_API_KEY`, respectively. Ollama uses `OLLAMA_HOST`; `omp` runs headlessly and must be available on PATH. Personal Data is masked before LLM egress.

Every scan probes its configured LLM provider. If unavailable, cache-only mode replays matching entries; uncached LLM fields are `not assessed`. The Report discloses this through `llm.mode` and `llm.reason`, and the command reports it on stderr. Cache-only mode does not imply that unassessed fields were assessed.

## Report contract and layout

`auditor/schema/report.schema.json` is the contract for the Report and its consumers. When changing it, bump `schema_version` and update every consumer together.

- `auditor/`: CLI, input handling, Report assembly, schema, Provision registry, recommended fixes, masking and LLM integration.
- `auditor/analysers/` and `auditor/ts/`: configuration and TypeScript analysers; `auditor/rules/`: Rules.
- `rules/semgrep/`: Semgrep Rules; `corpus/`: Labelled Corpus.
- `dashboard/`: Dashboard backend, React frontend and Replay Mode recordings (`dashboard/recordings/`); `reports/`: generated Reports (submission Reports tracked, see below); `demo/`: presenter script and comparison tool.
- `targets/`: ignored Target Application clones, including the pinned Primary Target.
- `docs/`: Issue Types and architecture decisions.

See the [Target Application decision](docs/adr/0001-target-applications.md) and [hybrid engine and LLM decision](docs/adr/0003-hybrid-engine-llm-required.md).

## Submission deliverables

| Deliverable | Where |
|---|---|
| Scanner and its source | [`auditor/`](auditor/) with Rules in [`auditor/rules/`](auditor/rules/) and [`rules/semgrep/`](rules/semgrep/) |
| Primary Target Report (unmodified Juice Shop at `c9f99228`) | [`reports/juice-shop/report.md`](reports/juice-shop/report.md), [json](reports/juice-shop/report.json), [html](reports/juice-shop/report.html), [pdf](reports/juice-shop/report.pdf) |
| Rules List | [`RULES.md`](RULES.md) (regenerate with `dpdp-audit rules list`) |

Also: [Live Probes](docs/live-probes.md), [Fix Patches](docs/fix-patches.md), [build plan](docs/plan.md), [domain glossary](CONTEXT.md), [eight-step demo script](demo/script.md) and the [Replay Mode manifest](dashboard/recordings/manifest.json). Target notes: [ai-kyc-platform](docs/targets/ai-kyc-platform.md), [singharya E-KYC](docs/targets/singharya-e-kyc.md), [TrackMyRupee](docs/targets/trackmyrupee.md).

### Set-up

Requirements: Python 3.11+, [uv](https://docs.astral.sh/uv/), Git, Node 20+ (the TypeScript analyser and the dashboard frontend), and Semgrep OSS (installed by `uv pip install -e '.[dev]'`). Docker is needed only for [Live Probes](docs/live-probes.md).

```sh
uv venv && uv pip install -e '.[dev]'
npm --prefix dashboard/frontend ci && npm --prefix dashboard/frontend run build   # dashboard UI
```

Scanning needs no network once the clones exist; the ignored `targets/` directory holds them. Clone and pin each Target Application:

| Target Application | Clone | Pinned revision |
|---|---|---|
| Juice Shop (Primary) | `https://github.com/juice-shop/juice-shop` → `targets/juice-shop` | `c9f99228d9d56afb5f5ca7925376292f7fa44b13` |
| ai-kyc-platform | `https://github.com/JhashankKumar/ai-kyc-platform` → `targets/ai-kyc-platform` | `70a821487c193be445810d836dd9b9b9ae22eb18` |
| TrackMyRupee | `https://github.com/OmkarPathak/TrackMyRupee` → `targets/trackmyrupee` | `47990e4f19d7debea70c5d56bab77e3c3f051546` |
| singharya E-KYC | `https://github.com/singharya-btech/ML-Based-E-KYC-Fraud-Detection-System` → `targets/singharya-e-kyc` | `e6e78d53edd30fd5be88dcd82d5afc1a2010d025` |
| Juice Shop fork PR head | `https://github.com/TanKaizokuO/juice-shop` (branch `dpdp-fix-patches`) → `targets/juice-shop-fork` | `2a66c603ea543aea6ab642c472431a27846b9e63` |

```sh
git clone https://github.com/juice-shop/juice-shop.git targets/juice-shop
git -C targets/juice-shop checkout c9f99228d9d56afb5f5ca7925376292f7fa44b13
DPDP_LLM_PROVIDER=ollama OLLAMA_HOST=http://127.0.0.1:1 .venv/bin/dpdp-audit scan targets/juice-shop --format json   # writes reports/juice-shop/report.{json,md,html,pdf}
```

The scan above is the documented Primary Target command; it writes the four Report files to `reports/juice-shop/` and prints the LLM mode on stderr. The committed Juice Shop Report was produced this way in cache-only mode (`llm.mode`, `llm.provider`, `llm.model` and `llm.prompt_versions` in the Report state exactly what ran; uncached LLM fields are "not assessed"). Findings do not depend on the LLM; only classification and triage fields do. With a reachable provider, set `DPDP_LLM_PROVIDER` (`anthropic`, `openai`, `gemini`, `ollama` or `omp`), `DPDP_LLM_MODEL` and the matching key as described under [LLM configuration](#llm-configuration).

### Dashboard and Replay Mode

```sh
.venv/bin/python -m uvicorn dashboard.backend.app:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/`. Start a live scan, or click a **Replay Mode** button to play back a recorded scan at its recorded pace with no scanner, provider or Target Application access. Replay Mode is labelled in the UI and never publishes: Live Probes and Open PR are unavailable and answer 409 for a recorded run. Each recording's pin, Report digest, scan date and LLM provenance are in the [manifest](dashboard/recordings/manifest.json). Recordings are not newly measured results: they are the times and Reports of the scans that made them. See [dashboard/README.md](dashboard/README.md).

Re-record a Target Application (the cache-only provider setting keeps it deterministic):

```sh
DPDP_LLM_PROVIDER=ollama OLLAMA_HOST=http://127.0.0.1:1 .venv/bin/python -m dashboard.backend.replay record targets/<name>
```

The Juice Shop recording also carries the Live Probe outcomes of the pinned image, which is why its recorded Report holds one more Finding than [`reports/juice-shop/report.json`](reports/juice-shop/report.json); the manifest says which.

### Check the package

```sh
.venv/bin/python -m pytest -q tests/test_submission_package.py        # -k manifest | replay | masking
```
