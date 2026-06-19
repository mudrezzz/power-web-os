# ADR: Candidate Universe Is Expanded And Frozen Before Signal Search

- Status: Accepted
- Date: 2026-06-18

## Context

Live Radar results were still too sensitive to the first discovery query. Even
after adding LLM-planned discovery, a run could collect coverage hints but then
start signal search before expanding the candidate universe. That made the
pipeline look observable while still missing source-backed companies.

The product needs a generic strategy, not SIBUR-specific code. A Radar may ask
for a holding contour, industry/region/revenue criteria, registry-constrained
search, or another qualification shape. In every case, qualification and
coverage must finish before signal search.

## Decision

The backend owns candidate universe lifecycle:

1. Build or accept a validated discovery plan.
2. Execute candidate-universe discovery.
3. Apply required qualification gates.
4. Execute coverage checks.
5. Merge and dedupe source-backed gap candidates.
6. Re-run qualification gates for newly added candidates.
7. Freeze the final candidate universe.
8. Execute signal searches only for non-rejected candidates.

Signal tasks are not allowed to add candidates. If a signal task mentions a new
entity, the backend stores it as a `candidate_universe_gap` for dossier/trace
inspection instead of turning it into a candidate.

OpenRouter model routing is role-based:

- `OPENROUTER_MODEL` is the fast/default model for simple bounded tasks such as
  signal checks.
- `OPENROUTER_ADVANCED_MODEL` is the advanced fallback for planning/extraction.
- `OPENROUTER_PLANNER_MODEL` is used by the discovery planner.
- `OPENROUTER_EXTRACTOR_MODEL` is used by discovery, qualification, and coverage
  extraction.

Fallback precedence is explicit constructor argument, specific env var,
`OPENROUTER_ADVANCED_MODEL` for planner/extractor, then `OPENROUTER_MODEL`.

Live execution also has a bounded search budget:

- `POWER_WEB_OS_RADAR_MAX_WEB_TASKS_PER_SUBJECT` limits backend-controlled
  provider/search tasks per qualification rule or signal.
- The committed local `.env.example` is smoke-safe and sets this value to `1`.
- The code fallback is `20` when no environment value is configured.
- If the budget is exhausted, the run should finish with coverage/review
  warnings rather than silently continuing unbounded web search.

## Consequences

- Candidate discovery can use multiple iterations without a schema migration;
  metadata lives in the existing output snapshot, dossier, journal, and trace.
- Product source lists remain evidence-bearing only. Analyzed, skipped, and
  gap-only source outcomes remain in technical trace or output metadata.
- Runs may complete with coverage warnings; this is a successful but
  review-needed result, not silent confidence.
- The next benchmark slice should evaluate the iterative strategy across
  several radar definitions before tuning prompts or model policy further.
