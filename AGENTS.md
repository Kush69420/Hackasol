# AGENTS.md

DPDP Compliance Auditor: scans a Target Application's code and configuration, finds where Personal Data is mishandled, and maps each Finding to India's DPDP Act 2023 and Rules 2025. Built for a hackathon demo (Hack-a-Sol, Track 3, CS-01).

## Read first

- `CONTEXT.md`: the domain glossary. Use its terms exactly in code, UI text and docs; never the `_Avoid_` words.
- `docs/adr/`: decisions that must not be silently reversed (targets, severity model, engine and LLM).
- `docs/issue-types.md`: the approved Issue Type catalogue and its Provisions.
- `docs/plan.md`: build order. Keep the vertical slice demo-ready at all times; breadth comes after.

## Stack

- Python for the Auditor; Semgrep OSS for code Rules (YAML); own Python analysers for schemas and configuration.
- Dashboard: FastAPI backend + React front end.
- LLM is required on every run through the provider interface (Anthropic, OpenAI, Gemini, Ollama, headless `omp`). Mask Personal Data in every snippet before it leaves the machine.

## Rules for agents

- The Finding JSON schema is the contract between the engine and every output; change it only deliberately, updating all consumers.
- Every new Rule ships with a Labelled Corpus pair (true positive + near-miss negative).
- Every Provision cited must exist in the Provision registry with its Penalty Ceiling and Enforceable From; never cite a section from memory without checking the Act or Rules text.
- Target clones live in `targets/` (git-ignored). Never commit Target code.
- Destructive Live Probes run only on accounts the Auditor creates.
