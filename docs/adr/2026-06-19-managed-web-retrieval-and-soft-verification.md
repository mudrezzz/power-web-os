# ADR: Managed web retrieval and soft source verification

## Status

Accepted

## Context

Live Radar quality is currently limited less by scoring and more by the web
retrieval boundary. A run can receive provider output with candidate names and
source references, then lose the entire candidate universe because URL
reachability checks fail after the model response. This makes the product hard
to debug: the technical trace shows provider activity, but product candidates
and sources can be empty.

The product needs a controlled pipeline where the backend owns search strategy,
source policy, verification state, useful-result budgets, and candidate status
degradation. LLM/provider calls should execute bounded retrieval or extraction
tasks, not own the whole decision about whether a candidate exists.

## Decision

Web search will be treated as a managed retrieval pipeline, not as a single
opaque chat-completion step.

The pipeline direction is:

```text
plan bounded task
  -> retrieve sources
  -> classify verification / reachability
  -> extract facts and candidate observations
  -> link evidence refs
  -> decide candidate status
  -> score signals only after qualified universe freeze
```

Source verification is stateful. The implemented modes are:

- `strict`: currently reachable sources are required before findings can be
  product evidence.
- `soft`: unreachable or blocked URLs preserve source-linked findings as
  risk-bearing evidence and mark candidates for review instead of deleting them.
- `off`: skip HTTP reachability checks and rely on provider/source refs as
  preliminary evidence.

Discovery and coverage tasks also use useful-result budgets. A provider task that
returns no useful source/candidate material, or only unverified material, may be
retried within a bounded retry limit. The existing
`POWER_WEB_OS_RADAR_MAX_WEB_TASKS_PER_SUBJECT` remains a hard safety limit on
provider task calls.

Retrieval providers will be isolated behind a provider-neutral port. OpenRouter
and Perplexity-style retrieval adapters must stay in `integrations`; application
services own source policy, verification semantics, retry decisions, candidate
status, and scoring.

## Consequences

- Empty live Radar runs can be explained as provider-empty, verification-limited,
  budget-limited, or extraction/linking-limited.
- Candidates linked only to unverified sources remain reviewable but do not
  become confident matches without evidence state and review warnings.
- Product source lists remain evidence-bearing, while dossier/trace surfaces
  retrieval, verification, and discarded-source lifecycle.
- Provider comparisons become possible because retrieval records are explicit.
- Provider selection and run-level empty-result diagnostics still need
  dedicated slices before the multi-radar benchmark.

## Alternatives considered

- Keep strict URL reachability filtering. Rejected because many business sites
  block `HEAD`, redirect inconsistently, or return transient failures, causing
  usable provider evidence to vanish without a reviewable trail.
- Disable verification entirely. Rejected because it would hide source quality
  risk and could admit hallucinated or stale evidence as product truth.
- Tune only the model. Rejected because model quality cannot compensate for an
  opaque retrieval/verification boundary owned by a single prompt.
