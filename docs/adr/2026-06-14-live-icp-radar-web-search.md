# ADR: Live ICP Radar Runs Use Provider-Neutral Web Search And Produce Reviewable Artifacts

## Status

Accepted

## Context

Power Web OS needs to move beyond design-first demo fixtures and start exercising real source discovery. At the same time, ICP Radar results must remain explainable, reviewable, and safe to reject. A live provider can fail, hallucinate weak source URLs, or return no usable evidence.

OpenRouter is the first live provider for this project because it can expose web-search capabilities through server-side tools or plugins. It must not become the product boundary.

## Decision

Live ICP Radar execution goes through a provider-neutral `WebSearchProvider` boundary.

The first live slice adds:

- `LiveICPRadarRunWorkflow`;
- `OpenRouterWebSearchProvider`;
- `RecordedWebSearchProvider` for tests;
- a small `ТОиР Quick Live Radar` definition;
- CLI-only execution through `run-live-mini-icp-radar --live`.

OpenRouter provider details are isolated behind the provider implementation:

- `OPENROUTER_API_KEY`;
- `OPENROUTER_MODEL`;
- `OPENROUTER_WEB_MODE=auto|server_tools|plugin_web|model_native`.

Live run output is a reviewable artifact, not accepted account state. The workflow writes `icp_radar_live_run` only from provider output and does not create synthetic candidates. If no usable evidence is found, the correct product behavior is an empty or weak result requiring human review.

Model-supplied URLs are not enough to establish evidence. Source URLs must be filtered before they can support candidates, and artifacts must not include API keys, authorization headers, bearer tokens, or raw provider dumps.

Live findings are rendered inside the standard ICP Radar review UX. The live radar uses the same table-first shortlist, sticky identity column, bounded inline preview, and tabbed in-shell detail view as fixture-backed radars. Runtime metadata belongs to the candidate detail `journal` tab and must not become a second shortlist header, a separate product surface, or an always-visible side detail panel.

## Consequences

- OpenRouter can be replaced or supplemented without changing ICP Radar domain contracts.
- CLI live runs can be tested with recorded providers and dry-run plans without network calls.
- Live results are separated from the stable XLSX demo and from the accepted `Accounts` portfolio.
- A live run can legitimately produce no candidates.
- Human validation remains the trusted state transition before live findings affect downstream work.
- UI work for new providers must add data adapters into the shared shortlist pattern instead of creating provider-specific scan/detail layouts.

## Follow-Ups

- Add durable run history after production persistence exists.
- Add UI run control only after credentials, quotas, and job state are modeled.
- Add source connector implementations beyond OpenRouter web search.
- Add stronger source verification and citation handling when provider responses expose stable citation metadata.
