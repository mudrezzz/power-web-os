# ADR: Radar source obligations and adaptive execution checkpoints

## Status

Accepted

## Context

Live Radar runs now have planner output, active persisted definitions, DaData as a
structured company-data provider, OpenRouter-backed web retrieval, run dossier,
and technical trace. Recent run analysis showed that those pieces are not enough
when source policy is treated as a hint and execution is linear.

The planner can reasonably choose high-trust sources such as DaData and the
official SIBUR site, but that choice can still be insufficient. If a configured
web source is intended to be mandatory for coverage, the planner must not be able
to silently skip it. If an early discovery strategy returns too few candidates,
unlinked sources, schema-invalid extraction, or weak coverage, the backend must
review the result and adapt before it freezes the candidate universe or starts
signal search.

## Decision

Radar source policy will distinguish source trust from source usage obligation.
Source definitions may be required, preferred, optional, fallback-only, or
disabled, and future slices may scope those obligations to identity, coverage, or
signal evidence.

The backend remains the owner of source-policy enforcement. LLM planner output is
accepted only if it satisfies source obligations, names concrete sources for
coverage work, and provides explicit skip rationale where skipping is allowed.
Required source omissions are blocking validation or review-stop conditions, not
silent fallbacks.

Live Radar execution will use application-owned checkpoints after candidate
discovery, qualification gates, coverage checks, and before signal search.
Checkpoints evaluate candidate counts, linked-source counts, required-source
usage, coverage risk, schema/linking failures, and budget pressure. The current
safety layer records checkpoint decisions and blocks signal search when the
pre-signal checkpoint is weak or invalid.

Full adaptive recovery requires a separate application action executor. A
checkpoint decision must not be treated as implemented recovery unless the
executor actually performs the selected action: retry a bounded task, expand to
an allowed source scope, request and apply a planner revision, stop as
review-needed, or fail hard. Those actions must be governed by explicit retry,
revision, source-policy, and total-run budgets and must be covered by
fake/recorded tests before broad live runs are used as validation.

DaData will be treated as a backend source provider, not as a string in a prompt.
The backend calls DaData, normalizes company observations, and passes structured
facts to later extraction/evaluation steps. Web retrieval remains the managed
source for public evidence and signals.

## Consequences

- Planner prompts and validation must carry source obligations, not just source
  ids and trust levels.
- Dossier, journal, and trace must show source obligation decisions, checkpoint
  decisions, and analyzed-versus-used source lifecycle.
- Full live benchmarks must wait until strict extraction gates, entity
  resolution, effective runtime config checks, source obligations, adaptive
  recovery actions, DaData hardening, and product source projection repair are
  in place.
- The product may complete runs with explicit review-needed coverage warnings,
  but it must not present unlinked or unsearched results as normal negative
  evidence.

## Alternatives considered

- Let the LLM fully own strategy and retry behavior. Rejected because it makes
  source-policy enforcement opaque and hard to test.
- Treat every configured source as mandatory. Rejected because some sources are
  useful fallback or optional enrichment, not required for every stage.
- Keep source lifecycle only in technical trace. Rejected because users need a
  product-safe explanation when sources were found but not used.
