# Deterministic detection core plus an LLM on every run, with cached verdicts and masked egress

Every Finding comes from the deterministic core; the LLM runs on every scan alongside it and never creates or drops a Finding on its own.

**Deterministic core.**
- **Semgrep OSS** (YAML) matches sources and sinks *inside one function*. The OSS edition does not trace data across functions or files, so it is never relied on for that.
- **A TypeScript AST analyser** joins the pieces across files:
  - Express mounts in `server.ts`;
  - finale-rest resources generated from the model list;
  - the handler factories each route points to;
  - the Sequelize models those handlers read and write;
  - Angular service calls (`this.host + '/…'`) matched to routes by method and normalised path.
- **Python analysers** read configuration and infrastructure: Dockerfile, YAML config, `app.json`, Terraform, `.env`, and log settings such as morgan formats and rotation.

Other frameworks (Django, FastAPI, Next.js, Prisma, Mongoose, Kubernetes, nginx) follow the same split once the Juice Shop Report is complete.

**LLM on every run**, in four roles:
- classifying Personal Data fields the dictionary and validators leave unresolved;
- false-positive triage, shown and never silently dropping a Finding;
- consent-flow reasoning;
- fix generation.

Each verdict is cached by a hash of its input snippet, prompt version and model, so a repeated scan reproduces the same Report and accuracy figures stay stable. Providers are pluggable: Anthropic, OpenAI or Gemini by environment variable; local Ollama; and headless `omp` for local demonstration. Personal Data values are masked before any snippet leaves the machine.

## Considered Options

- Semgrep only: fastest, but cannot follow Juice Shop's route → handler-factory → model → response chains across files.
- Semgrep Pro cross-file taint: closer, but paid, and still blind to finale-rest's generated routes.
- Own tree-sitter engine for every language at once: full control, but delays the Juice Shop Report.
- LLM-first detection: nondeterministic and weak for accuracy claims.
- LLM optional: reproducible without a provider, but drops the classification, triage, consent and fix layers the demo relies on.

## Consequences

A live scan needs a reachable LLM provider. With none reachable, a scan runs in cache-only mode: it replays cached verdicts for unchanged snippets, marks any uncached LLM field "not assessed", and says so in the Report, so a judging demo works offline. Accuracy figures record the provider, model and prompt version. Cross-file accuracy depends on the TypeScript analyser's coverage of each framework's routing idioms, so each new framework needs its own analyser work.
