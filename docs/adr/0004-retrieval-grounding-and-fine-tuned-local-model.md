# Retrieval-grounded prompts and a fine-tuned local model for classification, triage and consent

ADR 0003 stands: every Finding comes from the deterministic core, and the LLM never creates or drops one. This decision changes what the LLM is shown and which model answers each role.

**Retrieval (RAG).**
- **Corpus.** Three sources, all committed and all offline at scan time:
  - the Provision registry (`auditor/registry/*.yaml`), with the official DPDP Act and DPDP Rules text segmented per section and rule and joined to registry ids;
  - the remediation catalogue (`auditor/remediation/catalogue.yaml`);
  - the Labelled Corpus fixtures.
  A statute segment with no registry id is not indexed.
- **Retrieval method.** A structured seed first: the Issue Type's primary and related Provisions, plus their parents. Then BM25 expansion over statute segments, and BM25 nearest fixtures as worked examples. There are no dense embeddings: the corpus is small, and cache-only replay must retrieve deterministically without Ollama.
- **Grounding.** Triage and consent prompts receive the retrieved set and must return `citations`. Each citation has to be a Provision id from that retrieved set. A response that cites anything else is invalid and handled like any invalid response, so the field is "not assessed". Classification gets no statute retrieval.
- **Caching.** The retrieved set goes in the `context` and therefore in the cache key. The changed prompts are new versions (`*-v2`), so the accuracy manifest is regenerated under P1.6's rule.

**Fine-tuned model.**
- **Roles.** One model answers classification, triage and consent. Fix generation stays on the hosted default.
- **Routing.** Each role gets its own provider and model. The Report and accuracy manifest record them per role.
- **Training.** QLoRA on an open-weight instruct model, run on the project's RTX A4000 (16 GB VRAM, 125 GB RAM). The model is exported to GGUF and served through the existing Ollama provider, so masked snippets for these roles never leave machines we control.
- **Data.** Distilled from teacher models over masked inputs. A label is kept only when two teachers agree, or when a teacher label agrees with a deterministic label. Training text is the exact `*-v2` prompt the Auditor sends.
- **Evaluation.**
  - The Report Targets (Juice Shop at `c9f99228`, ai-kyc-platform, TrackMyRupee) are evaluation only. Training on them would contaminate the published accuracy.
  - The base model is the one that wins a zero-shot bake-off on the held-out set, among models that fit QLoRA within 16 GB at the measured p95 input length.
- **Adoption bar.** The fine-tuned model becomes a role's default only if, for that role on the held-out set:
  - it beats its own base model;
  - it comes within 5 percentage points of the hosted default on the role's primary metric;
  - it returns valid JSON for 100% of items;
  - all of its citations resolve to registry Provisions.
  A role that misses the bar stays on the hosted default, and the Report says why.

## Considered Options

- **Dense or hybrid embeddings.** Better recall on paraphrase, but they add an embedding model to cache-only replay. The structured seed already covers the lexical gap between code and statute.
- **Retrieval over Target code.** Gives cross-file context, but the TypeScript and Python analysers already supply Data Flows. It also enlarges masked egress. Not selected.
- **Hosted fine-tune APIs.** No infrastructure to run, but data leaves the machine, every call costs money, and models can be retired from under the cache.
- **One adapter per role.** Isolates each role, but means three models to serve and three cache identities. One multi-task model is simpler to serve and to replay.
- **Fine-tuning for fix generation too.** Fix Patches are proven by a re-scan, which is not a held-out metric, and long diffs push sequence length past what fits in 16 GB.
- **Hand-labelled data only.** Highest trust, but too small: the cache holds 121 verdicts in total. Hand labels are kept for the evaluation set only.

## Consequences

- The report schema's `llm` block and the accuracy manifest carry per-role provider, model and prompt version. Every consumer changes with them: `auditor/report.py`, `auditor/accuracy.py` and the dashboard.
- Live scans for the three fine-tuned roles need the Ollama host (the A4000, reached through an SSH tunnel). Offline demos still run in cache-only mode.
- A model or prompt change invalidates the cache for that role. The model name carries its training-run id, so a cached verdict always names the weights that produced it.
- The training data contains masked Target code, so it stays git-ignored. Only build scripts, the dataset card and digests are committed.

## Outcome

This outcome covers the Retrieval section only (P3.1 in `docs/plan.md`). The fine-tuned model and per-role routing are not covered.

- **Corpus.** The index is built from the committed Provision registry excerpts and the Labelled Corpus fixtures. The remediation catalogue supplies seed Provisions and Issue Type titles; it is not a document set. No statute PDF text (indiacode or egazette) is extracted or indexed, and there is no index file or build command.
- **Retrieval.** Triage receives 8 Provisions and the nearest positive and negative fixture. Consent receives 24 Provisions: 20 seed Provisions for CON-01 to CON-07, then BM25 over the masked serialised consent graph. These counts are set in `auditor/mapping.py` and `auditor/consent/criteria.py`; the decision above does not state them.
- **Grounding.** A citation outside the retrieved set makes the response invalid, and the field is `not assessed`, as decided.
- **Regeneration.** Commit `69ac7bf` replaced the cache, the Juice Shop Report, `accuracy/results.md` and the manifest. The model changed from `anthropic/claude-haiku-5-5` to `anthropic/claude-opus-5-5` for every role, so the regeneration was a model change as well as a prompt change. The commit removed 178 cache entries and added 192: 79 classification-v1, 64 triage-v2, 1 consent-v2 and 48 fix-v1, all via `omp`.
