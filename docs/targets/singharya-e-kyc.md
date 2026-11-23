# singharya E-KYC Target

Third Target Application, scanned for framework coverage: `singharya-btech/ML-Based-E-KYC-Fraud-Detection-System`, revision `e6e78d53edd30fd5be88dcd82d5afc1a2010d025`. Target Application code, document images and logs are not part of this repository (`targets/` is git-ignored). Reproduce with:

```sh
git clone https://github.com/singharya-btech/ML-Based-E-KYC-Fraud-Detection-System.git targets/singharya-e-kyc
git -C targets/singharya-e-kyc checkout e6e78d53edd30fd5be88dcd82d5afc1a2010d025
OLLAMA_HOST=http://127.0.0.1:1 .venv/bin/dpdp-audit scan targets/singharya-e-kyc --provider ollama --out reports/singharya-e-kyc/report.json
```

The scan writes `report.json`, `report.md`, `report.html` and `report.pdf` to `reports/singharya-e-kyc/`. With the unreachable Ollama host the run is cache-only: no model call is made, so every value below is deterministic.

## Scope

The `singharya-e-kyc` profile excludes `tests/**`, bytecode and cache directories (`auditor/exclusions.py`). The scan read 41 files and excluded 45 under 51 Rules. Committed identity-document images under `data/Data2/` and `data/02_intermediate_data/` are neither read nor copied; the Report quotes no Personal Data.

## Result

The Report has no Findings and no Observations. This is the honest outcome of the existing Rules on this pin, not a claim that the code is compliant:

- The Kubernetes manifests set `runAsNonRoot`, a read-only root filesystem, dropped capabilities and ClusterIP Services; only the Ingress is public. `SEC-16-kubernetes-privileged-store` and `SEC-16-kubernetes-public-store` therefore stay silent, and in any case neither would fire here because no Prisma datasource or Mongoose connection ties a workload to a Personal Data store.
- `logs/ekyc_logs.log` contains no value that the existing validators in `SEC-15-committed-personal-data` accept, so that Rule does not fire on it.
- Gap, not a result: committed identity-document images are an `SEC-15` qualifier in `docs/issue-types.md`, but the existing `SEC-15` Rule reads only text formats. The images are therefore not assessed.
- The Coverage Matrix still lists every Provision with its Rule coverage; nothing here is a statement about consent or notice, which the static Rules do not establish for this Target.

## Coverage by framework

| Framework | Exercised by this Target | Where proven |
|---|---|---|
| Python (FastAPI, SQLite store) | Yes: 4 routes, 2 models, 5 Python flows | the scan |
| Kubernetes | Yes: 10 resources parsed (ConfigMap, 2 PersistentVolumeClaims, 3 Deployments, 3 Services, Ingress) with inbound exposure per resource | the scan inventory; hardened manifests produce no Finding |
| nginx as Ingress class | Parsed as a Kubernetes Ingress with TLS and public inbound rules | the scan inventory |
| nginx `nginx.conf` | No file in the Target | fixtures only: `tests/fixtures/frameworks/nginx/**` |
| Prisma, Mongoose, React | Not used by the Target | fixtures only: `tests/fixtures/frameworks/{prisma,mongoose,react}/**` |
| Django | Not used by the Target | `tests/fixtures/django` via the existing analyser |

## Framework Rules added

`SEC-01-nginx-query-logging`, `SEC-16-kubernetes-privileged-store` and `SEC-16-kubernetes-public-store` (`auditor/rules/framework_config.py`), each with a `corpus/<rule-id>/{positive,negative}/` pair. `SEC-15` and `TRF-01` already exist and the new analysers add no coverage beyond them, so no new variants were added.
