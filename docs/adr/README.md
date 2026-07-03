# Architecture Decision Records

ADRs capture decisions that shape product architecture.

## Index

- `0001-use-langgraph-document-ai-platform.md` - Use `mudrezzz/langgraph-document-ai-platform` as the AI workflow runtime.
- `0002-start-with-deterministic-access-planner.md` - Start with deterministic route scoring before LLM orchestration.
- `2026-06-12-frontend-workspace-ux-principles.md` - Umbrella entry for the frontend workspace UX ADR family.
- `2026-06-12-bounded-spa-workspace-shell.md` - Keep product screens inside a viewport-bounded SPA workspace shell.
- `2026-06-12-table-first-dense-data-ux.md` - Use table-first scan surfaces, sticky identity, and explicit drilldown for dense operational data.
- `2026-06-12-evidence-first-review-ux.md` - Make score, evidence, rationale, and review workflows scan-first and expandable.
- `2026-06-12-configurable-object-ux.md` - Use catalog-first navigation, explicit settings states, and clear local-draft boundaries for configurable product objects.
- `2026-06-12-bilingual-responsive-frontend-baseline.md` - Treat EN/RU i18n and small-screen/mobile constraints as frontend baseline requirements.
- `2026-06-13-icp-radar-definition-separates-qualification-and-signals.md` - Model ICP Radar configuration as structured qualification rules, intent signals, source policies, scoring, and validation.
- `2026-06-14-live-icp-radar-web-search.md` - Run live ICP Radar searches through a provider-neutral web search boundary and treat outputs as reviewable artifacts.
- `2026-06-15-canonical-icp-radar-ux-contract.md` - Render all fixture-backed and provider-backed ICP Radar shortlists through one canonical table-preview-detail UX contract.
- `2026-06-16-backend-architecture-guardrails.md` - Guard backend OOP boundaries, long-running job direction, and module-size limits before persistence grows.
- `2026-06-17-structured-radar-run-journal.md` - Persist structured Radar audit events and sanitized admin technical traces while excluding raw hidden chain-of-thought.
- `2026-06-18-qualification-first-radar-execution.md` - Make backend application services own qualification-first Radar execution while LLM providers execute bounded tasks.
- `2026-06-18-llm-planned-radar-discovery.md` - Let LLMs propose Radar discovery plans while backend validators enforce source policy and accepted execution.
- `2026-06-18-candidate-universe-expansion-before-signals.md` - Expand and freeze candidate universe before signal search.
- `2026-06-19-source-lifecycle-before-quality-benchmark.md` - Make source lifecycle, evidence linking, and score-contract hardening visible before multi-radar quality benchmarking.
- `2026-06-19-managed-web-retrieval-and-soft-verification.md` - Treat web search as managed retrieval with soft verification, useful-result budgets, and provider-isolated adapters.
- `2026-06-19-radar-planning-observability-hardening.md` - Harden criterion role inference, plan validation, run-level diagnostics, and trace UX before provider benchmarking.
- `2026-06-22-radar-retrieval-contract-and-source-providers.md` - Compact Radar execution prompts, formalize retrieval task cards, fix budget semantics, and introduce structured company-data source providers such as DaData.
- `2026-06-23-tdd-preflight-for-complex-llm-pipelines.md` - Require fast preflight, recorded fixtures, and targeted live probes before expensive full live runs for complex LLM pipelines.
- `2026-06-23-radar-source-obligations-and-adaptive-checkpoints.md` - Treat Radar source policies as enforceable obligations and add adaptive execution checkpoints before benchmark runs.
- `2026-06-23-radar-entity-resolution-before-account-scoring.md` - Resolve legal entities separately from sites, projects, and assets before Radar account scoring.
- `2026-06-25-connector-profiles-compile-to-source-capabilities.md` - Let external source connectors describe themselves in plugin-friendly profiles, then compile them into internal Radar source capabilities for planner and validator use.
- `2026-06-27-radar-search-pipeline-as-is-to-be-docs.md` - Maintain Radar search pipeline AS IS/TO BE documents and rendered PDF diagrams as part of the implementation control loop.
- `2026-07-03-radar-backend-package-architecture.md` - Treat root-level `live_radar_*` modules as migration debt and move Radar backend work toward package-owned candidate-discovery, signal-monitoring, and Power Web discovery boundaries.

## Template

Use `0000-template.md` for new ADRs.
