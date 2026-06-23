# ADR: TDD preflight for complex LLM pipelines

## Status

Accepted

## Context

Live Radar runs now involve LLM planning, source policy validation, structured
source providers, web retrieval, extraction, source verification, candidate
normalization, scoring, dossier projection, journal events, and technical
trace. A full live run can take tens of minutes and can fail late for reasons
that are detectable before the run starts, for example:

- the worker executes a hardcoded legacy Radar definition instead of the active
  persisted definition;
- configured source bases such as DaData are present in catalog data but absent
  from the runtime payload;
- a provider returns sources, but extraction output does not satisfy the
  expected schema;
- retrieved sources cannot be linked to candidate evidence refs;
- budget-limited or extraction-invalid work is normalized as negative signal
  evidence.

Using only full live runs as the feedback loop is too slow and makes root-cause
analysis expensive. Complex LLM pipelines need a fast TDD layer that proves the
pipeline is runnable before spending live-provider time.

## Decision

For complex LLM-backed pipelines, especially Radar discovery/extraction, we will
use a TDD-first validation ladder before broad live runs:

1. **Static/config preflight** validates active definitions, source policies,
   provider settings, runtime wiring, source ids, and known incompatibilities.
2. **Recorded pipeline tests** run the same application services with recorded
   planner, retrieval, source-provider, extraction, and error fixtures.
3. **Targeted live provider probes** make small, bounded live calls for one
   source-provider lookup, one retrieval request, and one extraction-only
   schema check.
4. **Full live run** is allowed only after the cheaper layers are green or the
   run is explicitly marked as exploratory.

Preflight failures must be explicit and product/developer readable. They should
identify the failed layer, for example `definition_runtime_mismatch`,
`source_base_not_executable`, `provider_unavailable`,
`extraction_schema_invalid`, or `evidence_linking_failed`.

LLM output contracts must be tested with negative fixtures. A provider response
that is prose-first, uses dicts where lists are required, omits source refs, or
links evidence to unknown refs should fail the schema gate or become an explicit
diagnostic state. It must not be silently normalized into zero scores or trusted
negative observations.

## Consequences

- Full live Radar runs become final smoke/benchmark steps, not the main
  development loop.
- A new Radar feature that changes planning, retrieval, extraction, source
  policy, scoring, or persistence must add fast red/green tests before relying
  on long live runs.
- Agent skills and roadmap slices must require preflight/TDD planning for
  complex LLM pipelines.
- Benchmark slices should depend on green preflight checks and recorded
  pipeline fixtures.
- The system will expose more controlled diagnostic states instead of hiding
  broken extraction or linking as normal `not_observed` results.

## Alternatives considered

- **Continue debugging through full live runs.** Rejected because a single run
  can take around 30 minutes and mixes configuration, provider, extraction,
  evidence-linking, and scoring failures into one expensive signal.
- **Rely on better models.** Rejected because stronger models do not fix runtime
  definition wiring, source-provider selection, or schema-gate semantics.
- **Mock everything and avoid live probes.** Rejected because provider routing,
  credentials, web-search engines, and source-provider availability can fail in
  ways mocks do not catch. Use small targeted live probes instead of full runs.
