# Auditor LLM training data

## Classification (`classification-v1`)

The 20 pinned public inputs are listed in [`sources.yaml`](sources.yaml), with their repository licence and inventory framework. The Auditor inventories local shallow clones without running Target Application code. The four Report Targets are held out; they do not appear in either split.

From the inventory, `capture.py` uses the production classification code to construct the masked Evidence and context. For deterministically classified Personal Data Elements it reconstructs the same prompt and supplies the dictionary/validator label and reason (silver). For unresolved Elements `dataset.py` uses one teacher, Opus 5.5 through `omp` (`anthropic/claude-opus-5-5`). This single-teacher run is not the two-teacher agreement experiment proposed in ADR 0004. The files preserve the production system and user message verbatim. They are git-ignored; the committed evaluation inputs and methodology live in [`accuracy/llm-eval`](../accuracy/llm-eval/).

| Classification Data Category | Train | Validation |
| --- | ---: | ---: |
| Authentication Secret | 343 | 37 |
| Biometric | 2 | 0 |
| Child Data | 0 | 0 |
| Contact | 150 | 35 |
| Financial | 13 | 2 |
| Government Identifier | 0 | 0 |
| Health | 0 | 0 |
| Profile | 434 | 32 |
| **Total** | **942** | **106** |

| Split | Deterministic (silver) | Opus teacher | Approx. tokens p50 / p95 / max |
| --- | ---: | ---: | ---: |
| Train (19 repositories) | 529 (56.2%) | 413 (43.8%) | 171 / 259 / 316 |
| Validation (`documenso`) | 73 (68.9%) | 33 (31.1%) | 166 / 241 / 295 |

Validation is 10.1% of accepted classification rows and shares no repository with training. Of 1,070 captured Elements, 18 were dropped for held-out Evidence overlap and 4 for invalid teacher verdicts. Opus returned valid values for 363 of 367 distinct requests. Token lengths are the ceiling of total message characters divided by 3.5, with nearest-rank percentiles; they exclude chat-template overhead. Dataset composition is imbalanced; meeting the row target does not establish performance on rare or absent Data Categories. The validation split is for training decisions, not the Report Target evaluation.

| Local file | SHA-256 |
| --- | --- |
| `training/data/train/classification.jsonl` | `2c7c8b13770961249249d85d63ede94b743f0a6667a39dc7315de4e8e8b163c9` |
| `training/data/val/classification.jsonl` | `dca48eb0ef0f3cb1f96d710a30b9239c69fafbf04630334139ea0ad8a56953dd` |

From the repository root, with the Auditor dependencies and `omp` installed:

```sh
python -m training.dataset train
python training/leakage.py
```

The leakage check compares declared source paths and masked Evidence hashes to the held-out data, and rejects any Report Target path or repository reused across splits. This is not a near-duplicate or pretraining-contamination check. A fresh teacher run without the local cache may produce different values.

## Triage (`triage-v2`)

`triage.py` runs the Auditor with a recording session. Classification uses the Auditor's deterministic labels and replays successful Opus classification responses from the local cache, except for Evidence hashes shared with the held-out classification set. Triage capture itself does not contact a provider. The script sends the resulting masked Evidence and retrieval context to Opus 5.5 through `omp` and keeps only valid JSON whose citations are among the Provisions retrieved for that prompt.

For Labelled Corpus rows, a Finding inherits the fixture's deterministic verdict only when its `rules_fired` includes that fixture's designated Rule and the triage context names the same Issue Type. A merged Finding can otherwise ask the model about a different Issue Type. Positive fixtures are `true-positive`; Findings from negative fixtures for the designated Rule would be `false-positive`. None of the negative fixtures fired its designated Rule. Opus supplies the explanation and citations for agreeing fixture rows; we dropped 13 disagreements because their explanations did not support the deterministic label. Public repository verdicts are teacher-labeled, not checked against a separate reference. No Report Target prompt is sent to the teacher by the triage build.

Validation uses the same repository as classification (`documenso`) to prevent a repository from appearing in both splits across roles. Labelled Corpus rows are training-only. The triage build excludes exact Evidence matches to offline Report Target captures and to the triage validation split. Of 61 eligible fixture Finding inputs, 60 retrieved their own fixture as an example. They can teach the response format but cannot independently measure generalization.

`edx-platform` is excluded from triage only: the Auditor crashes at `auditor/rules/rights_config.py:67` on a strict UTF-8 read of a binary HLS fixture with a `.ts` extension. It remains in the classification dataset.

| Triage verdict | Train | Validation |
| --- | ---: | ---: |
| `true-positive` | 51 | 0 |
| `false-positive` | 156 | 0 |
| `uncertain` | 41 | 1 |
| **Total** | **248** | **1** |

| Split | Deterministic | Opus teacher | Approx. tokens p50 / p95 / max |
| --- | ---: | ---: | ---: |
| Train | 48 (19.4%) | 200 (80.6%) | 1,807 / 2,287 / 3,661 |
| Validation (`documenso`) | 0 | 1 (100%) | 1,689 / 1,689 / 1,689 |

The lone validation row is a smoke signal, not a quality estimate. Use the 52 reviewed Juice Shop Finding labels to assess adoption. The 394 captured Findings yielded 201 repository candidates and 61 fixture candidates after excluding 125 unrelated Rule emissions and 7 merged Findings whose triage Issue Type differed from the fixture's. Opus returned valid JSON and grounded citations for all 262 distinct requests in the final run, and all 249 retained rows passed the same validation.

| Source | True positive | False positive | Uncertain | Captured |
| --- | ---: | ---: | ---: | ---: |
| Labelled Corpus (65 positive and 65 negative fixtures) | 48 | 0 | 0 | 193 |
| Django-CRM | 1 | 1 | 4 | 6 |
| django-allauth | 0 | 8 | 0 | 8 |
| django-appointment | 0 | 0 | 0 | 0 |
| django-oscar | 0 | 0 | 0 | 0 |
| documenso (validation) | 0 | 0 | 1 | 1 |
| dub | 0 | 3 | 5 | 8 |
| ecommerce | 0 | 0 | 0 | 0 |
| fastapi-realworld-example-app | 0 | 0 | 0 | 0 |
| formbricks | 0 | 8 | 1 | 9 |
| full-stack-fastapi-template | 0 | 4 | 0 | 4 |
| healthchecks | 0 | 0 | 0 | 0 |
| node-express-realworld-example-app | 1 | 0 | 0 | 1 |
| open-webui | 1 | 4 | 1 | 6 |
| plunk | 0 | 0 | 9 | 9 |
| pretix | 0 | 0 | 0 | 0 |
| saleor | 0 | 114 | 1 | 115 |
| taxonomy | 0 | 0 | 1 | 1 |
| trigger.dev | 0 | 14 | 19 | 33 |
| wagtail | 0 | 0 | 0 | 0 |

| Local file | SHA-256 |
| --- | --- |
| `training/data/train/triage.jsonl` | `eff0034cdcfb628ad51bcc9de4988ef98fdad94b098e24f8a8149469f092b940` |
| `training/data/val/triage.jsonl` | `a8d279b636870d04690a43afc36a7faccd8ea21a80ca98d5bea8f24b228b2155` |

```sh
python -m training.triage all
python training/leakage.py
```
