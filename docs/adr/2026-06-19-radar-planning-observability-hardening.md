# ADR: Harden Radar planning and observability before retrieval benchmarking

## Status

Accepted

## Context

Live Radar runs are now qualification-first, iterative, journaled, and traced.
Recent real runs showed that this is not enough for useful debugging or quality
work:

- LLM discovery plans can contain reasonable strategic intent but fail rigid
  validation because the contract mixes where a source is configured with how it
  is applied in a step.
- Qualification rules are not all equal. Some rules define the upstream
  candidate universe, while others are downstream gates or enrichment checks.
- Signal search can be budget-limited to a subset of candidates, but the UI does
  not yet make that clear.
- Technical trace rows contain useful data, but they are still hard to analyze
  because they expose raw JSON-oriented records instead of a logical run
  timeline with inputs, outputs, provider calls, validation, and budgets.

Benchmarking OpenRouter/Perplexity or stronger models before fixing these
issues would make provider quality hard to interpret.

## Decision

Before provider comparison and multi-radar benchmarking, introduce three
planning/observability hardening slices:

1. Infer qualification criterion roles before execution. The backend should
   distinguish upstream discovery criteria, downstream gates, enrichment
   criteria, exclusion criteria, and signal criteria. The LLM may propose the
   roles, but the backend validates and compiles them into execution tasks.
2. Separate source configuration scope from application scope. A source can be
   configured globally, such as `sibur.ru`, while being applied to a specific
   rule or candidate-scoped task. Validator mistakes that are safe to normalize
   should become warnings/corrections, not immediate fallback to a simplistic
   deterministic plan.
3. Add run-level diagnostics and a readable trace viewer before judging
   retrieval/provider quality. Users should see which candidates were
   discovered, gated, skipped, budget-limited, source-limited, or searched for
   signals. Developers should inspect provider requests/responses through a
   phase-grouped, wrapped, searchable trace UI instead of raw JSON dumps.

Raw hidden chain-of-thought remains out of scope. The product dossier shows
safe reasoning summaries, plan decisions, source lifecycle, and budget
outcomes. The technical trace shows sanitized prompt/request/response and
pipeline payloads for developer/admin use only.

`Slice 0.7.6.1.7.2` implements the first two decisions through
`RadarDiscoveryPlanAcceptanceService`. The service infers missing criterion
roles, accepts product-safe planner role decisions, normalizes repairable
source-scope mismatches, splits multi-rule strategic steps into rule-scoped
executable tasks, and records corrections/fallback metadata in dossier,
journal, and technical trace payloads.

## Consequences

- Provider comparison is deferred until the pipeline can explain planning,
  compact task prompts, budget semantics, source lifecycle, and trace behavior.
- Implementation work should fix prompt shape, hierarchical budgets, and
  structured company-source support before adding another web retrieval
  provider.
- Future benchmark failures should be diagnosable per criterion role, source
  policy decision, candidate universe stage, budget limit, provider result,
  normalization result, and score/evidence decision.

## Alternatives considered

- Add Perplexity adapter immediately. Rejected for now because provider
  comparison is not meaningful while the system still cannot clearly explain why
  candidates did not receive signal tasks or why an LLM plan was rejected.
- Increase model strength and search limits only. Rejected because this may hide
  pipeline problems and increase cost without making results auditable.
- Store raw chain-of-thought. Rejected because the product needs structured,
  safe audit artifacts, not hidden reasoning transcripts.
