# ADR: Connector profiles compile to source capabilities

## Status

Accepted

## Context

Live Radar now supports source obligations, structured company providers such
as DaData, managed web retrieval, source lifecycle diagnostics, and adaptive
execution checkpoints. A smoke run with DaData and OpenRouter Perplexity showed
that hardcoding source behavior per provider is the wrong scaling path: DaData
was invoked with broad holding-contour discovery text even though it is a
company lookup/enrichment source, not a universe-enumeration engine.

Future sources should be plugin-like. Independent connector authors should be
able to describe a source without knowing Power Web OS internal pipeline names
or stages.

## Decision

Power Web OS will separate external connector profiles from internal source
capabilities.

External connector profiles are human-readable and plugin-friendly. They
describe:

- connector id and display name;
- what the source is for;
- examples of good inputs;
- examples of bad inputs;
- facts the source can return;
- limitations and credential requirements.

They must not require the author to name internal Radar stages such as
qualification discovery, coverage checks, gates, or signal search.

The application compiles those profiles into an internal, machine-checkable
capability model. The compiled model is allowed to use internal concepts such
as lookup-only, enumeration-capable, identity/enrichment-oriented,
signal-evidence-capable, accepted input shape, forbidden input shape, and
useful-result criteria.

Radar definitions remain responsible for selecting sources and assigning usage
obligations such as `required_for_identity`, `required_for_coverage`,
`preferred`, `fallback`, or `disabled`. Connector profiles explain what those
selected sources can actually do. The planner receives compact source cards
derived from compiled capabilities, and backend validators enforce capability
compatibility before execution.

Accepted planner steps must declare, or be normalized into, explicit
`source_use` records: selected source, intended use, input shape, expected fact
kinds, and rationale. The validator checks those records against the compiled
source card. This keeps provider-specific behavior out of the planner and out
of hardcoded executor branches.

Source cards are mandatory live planner input. An empty `source_cards` array
for a Radar definition that has configured sources is a wiring defect, not an
acceptable degraded mode. Live planning, dossier metadata, and technical trace
must preserve the source cards and capability validation decisions so smoke
diagnostics can prove that connector capabilities are actually active.

## Consequences

- DaData-specific behavior must not be hardcoded in planner or executor logic.
- Broad universe discovery cannot be sent to a lookup-only source unless the
  compiled connector capability explicitly supports enumeration.
- A registry source can be selected by Radar settings but still be skipped at
  runtime with `not_executed_input_not_available` if no concrete lookup terms
  exist.
- Source capability compilation becomes part of static preflight before long
  live runs.
- Planner source-card validation prevents invalid source use before provider
  calls spend live budget.
- Smoke diagnostics must show non-empty source cards for configured sources and
  must show lookup-only sources skipped when only placeholder or broad input is
  available.
- Backend Docker images must package `config/connectors` so API/worker smoke
  runs use the same connector profiles as local preflight/tests. Missing
  containerized profiles are a runtime parity failure, not model behavior.
- Smoke profile caps promoted product candidates; extra provider observations
  remain diagnostic/review-needed material until a longer benchmark run is
  explicitly selected.
- Runtime execution must materialize concrete candidate names from the current
  candidate universe before lookup-only registry enrichment. Placeholder scopes
  such as `candidates from step 1` are internal planning references, not valid
  connector input. If no concrete candidate exists, the provider call is skipped
  with `not_executed_input_not_available`.
- Concrete registry enrichment should use bounded lookup-term generation, not a
  single planner alias. The application can derive identifiers, Russian
  legal-form terms, short names, and English aliases from candidate/source
  context, then execute those terms under the same provider budget.
- Ambiguous lookup-only registry observations are not automatic rejection in
  upstream discovery. If they include source-backed company, branch, site, or
  asset facts, execution may retain them as review-needed universe entities or
  linked facts and request bounded cross-checks through allowed official/web
  connector capabilities.
- Weak discovery can trigger recall-first source expansion through compiled
  source capabilities: official-domain, open-web relation, identity, and
  industrial/site query variants are generated only for policy-allowed sources
  and remain bounded by execution/external-call budgets.
- Source cards can drive executable cross-source disambiguation tasks, not only
  planner validation. A smoke run should record whether each cross-check was
  executed, skipped by budget or policy, failed schema validation, found no
  support, or confirmed a relation.
- Extraction schema recovery is distinct from plan revision. Malformed
  extraction output should first use bounded repair/retry records; `revise_plan`
  is reserved for invalid strategy, source capability, or policy problems.
- Future connector/plugin authors can provide source descriptions without
  learning the Power Web OS execution pipeline.

## Alternatives considered

- Hardcode rules for DaData, then repeat for each future source. Rejected
  because it does not scale and makes plugin authors depend on application
  internals.
- Ask the LLM to infer all source behavior from source names. Rejected because
  smoke evidence showed that this leads to invalid source use and wasted live
  budget.
- Put internal pipeline-stage configuration directly in connector YAML.
  Rejected because connector authors should not need to know Radar stage names.
