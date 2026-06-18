# ADR: Qualification-first Radar execution

## Status

Accepted

## Context

The first live Radar pipeline was observable through journal, dossier, and
technical trace, but the provider still received mixed qualification and signal
instructions in one broad prompt. That made the agent inefficient: it could
skip real account-universe discovery, blur required qualification gates with
intent signals, and make benchmark failures hard to diagnose.

Radar definitions already distinguish account qualification from intent
signals. Required `AND` qualification rules imply sequential filtering: discover
the candidate universe, apply each gate, and only then search intent signals for
the remaining candidates.

## Decision

Application services own Radar execution strategy. A live Radar run compiles a
generic `RadarExecutionPlan` from the Radar definition:

- `qualification_discovery` discovers the initial candidate universe.
- `qualification_gate` tasks apply required account-fit gates in order.
- `signal_search` tasks run only for candidates not rejected by qualification.
- evaluation and validation read collected observations and do not perform
  provider searches.

Provider adapters receive one bounded task at a time. OpenRouter prompts are
scoped to the current task: qualification prompts do not include intent signals,
and signal prompts include only the current signal and candidate scope.

The existing `search_plan.queries` artifact remains as a backward-compatible
projection, enriched with stage, subject, dependency, rule snapshot, and
candidate-scope metadata. No database migration is required; execution details
are persisted through the existing output snapshot, journal, dossier, and
technical trace paths.

## Consequences

- Live Radar behavior becomes debuggable per stage before the SIBUR benchmark.
- The LLM is a bounded task executor/extractor, not the owner of search
  strategy.
- Rejected qualification candidates are not searched for intent signals.
- Live runs may make more provider calls, so latency and cost must be measured
  during benchmark work.
- The design is generic over Radar definitions and must not special-case SIBUR.

## Alternatives Considered

- **Use a stronger model with the existing broad prompt.** Rejected because it
  hides planning mistakes and makes Power Web OS less differentiated from a
  generic chat workflow.
- **Let the LLM produce and execute its own multi-step plan.** Rejected for this
  slice because backend-owned gates and auditability are required before model
  experiments.
- **Normalize candidates/evidence into new tables first.** Deferred. The staged
  plan can be represented in current snapshots and traces; normalized storage
  can follow after benchmark learning.
