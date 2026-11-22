# Hybrid detection engine; LLM required on every run, with masked egress

Code Rules run on Semgrep OSS (YAML, taint mode for Python and JS/TS) so the Rules List stays human-readable. Our own Python analysers cover what Semgrep handles poorly: schema parsing (Django models, Sequelize, Prisma, Mongoose, SQL DDL), configuration (Dockerfile, compose, Kubernetes, nginx, .env, settings files) and cross-file flow stitching. An LLM is required on every run for Personal Data classification of ambiguous fields, false-positive triage verdicts (shown, never silently dropping a Finding), consent-flow reasoning and fix generation. LLM providers are pluggable: Anthropic, OpenAI or Gemini by environment variable; local Ollama; and headless `omp` for local demonstration. Personal Data values are masked before any snippet leaves the machine, even though the report itself shows raw Evidence. Otherwise the Auditor would itself make the Cross-Border transfer it flags.

## Considered Options

- Semgrep only: fastest, but schema and config checks stay shallow.
- Own tree-sitter engine: full control of cross-file taint, too slow to build in the time available.
- LLM-first detection: nondeterministic and weak for accuracy claims.
- Deterministic core with optional LLM: reproducible, but rejected in favour of always-on LLM enrichment.

## Consequences

Runs are not bit-for-bit reproducible. Accuracy figures must record the provider and model used.
