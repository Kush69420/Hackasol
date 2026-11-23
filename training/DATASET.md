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
