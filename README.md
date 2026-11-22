# DPDP Compliance Auditor

The Auditor scans a Target Application and maps Personal Data mishandling to India's DPDP Act 2023 and DPDP Rules 2025. This foundation produces a schema-valid JSON Report; analysers and Rules are not yet implemented.

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

The positional input is a local directory or Git URL. Git URLs are cloned under `targets/<name>` and existing clones are reused; `--commit SHA` selects a commit for a Git URL. Local directories are not checked out or modified. `--format json` is the only supported format; `--out FILE` overrides the default `reports/<target-name>/report.json`. The command prints the Report path. `--cache-dir DIR` selects the LLM cache (default `.dpdp-cache`); `--provider P` and `--model M` override provider configuration.

## LLM configuration

Set `DPDP_LLM_PROVIDER` to `anthropic`, `openai`, `gemini`, `ollama` or `omp`, and optionally set `DPDP_LLM_MODEL`. Hosted providers use `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` or `GEMINI_API_KEY`, respectively. Ollama uses `OLLAMA_HOST`; `omp` runs headlessly and must be available on PATH. Personal Data is masked before LLM egress.

Every scan probes its configured LLM provider. If unavailable, cache-only mode replays matching entries; uncached LLM fields are `not assessed`. The Report discloses this through `llm.mode` and `llm.reason`, and the command reports it on stderr. Cache-only mode does not imply that unassessed fields were assessed.

## Report contract and layout

`auditor/schema/report.schema.json` is the contract for the Report and its consumers. When changing it, bump `schema_version` and update every consumer together.

- `auditor/`: CLI, input handling, Report assembly, schema, Provision registry, recommended fixes, masking and LLM integration.
- `auditor/analysers/` and `auditor/ts/`: future analysers.
- `rules/semgrep/`: Semgrep Rules; `corpus/`: Labelled Corpus.
- `dashboard/`: future Dashboard; `reports/`: generated Reports.
- `targets/`: ignored Target Application clones, including the pinned Primary Target.
- `docs/`: Issue Types and architecture decisions.

See the [Target Application decision](docs/adr/0001-target-applications.md) and [hybrid engine and LLM decision](docs/adr/0003-hybrid-engine-llm-required.md).
