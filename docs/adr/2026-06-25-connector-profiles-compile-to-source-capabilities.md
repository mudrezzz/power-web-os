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

## Consequences

- DaData-specific behavior must not be hardcoded in planner or executor logic.
- Broad universe discovery cannot be sent to a lookup-only source unless the
  compiled connector capability explicitly supports enumeration.
- A registry source can be selected by Radar settings but still be skipped at
  runtime with `not_executed_input_not_available` if no concrete lookup terms
  exist.
- Source capability compilation becomes part of static preflight before long
  live runs.
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
