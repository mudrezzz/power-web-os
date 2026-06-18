# ADR: LLM-Planned Radar Discovery With Backend Source Policy Validation

Date: 2026-06-18

## Status

Accepted

## Context

The qualification-first Radar pipeline separated discovery, qualification gates,
signal search, evaluation, and validation. That fixed the previous mixed prompt
shape, but discovery strategy was still too deterministic and too shallow for
real account-universe search. In realistic radars, the first problem is not
always "find holding subsidiaries"; it can be industry, region, revenue,
registry coverage, local source constraints, or another combination of
qualification rules.

We need the model to help plan discovery, but not to own truth decisions,
source-policy enforcement, stage ordering, or fallback behavior.

## Decision

Live Radar discovery uses a separate planning loop:

1. Application code builds a `RadarDiscoveryPlanningInput` from the active
   radar definition, qualification rules, global/local source policy, task
   context, model/web metadata, and run limits.
2. A `RadarDiscoveryPlanner` proposes a structured JSON plan with bounded
   discovery steps, source-policy decisions, coverage hypotheses, and warnings.
3. `RadarDiscoveryPlanValidator` checks source policy, configured source
   selection/skip rationale, qualification-before-signal ordering, and step
   limits.
4. If the plan is invalid, the backend allows one revision attempt with
   sanitized validation errors.
5. Only an accepted plan is compiled into `RadarExecutionPlan` and executed.

The LLM planner may explain why a source base was selected or skipped, why a
criterion is first, and what evidence is expected. It must not store or expose
raw hidden chain-of-thought. Planner prompts and responses may appear only in
the sanitized technical trace.

Product source lists contain only used, evidence-bearing sources. Sources that
were analyzed but not used remain available through execution metadata and
technical trace, not in the user-facing source table.

## Consequences

- Discovery strategy becomes generic across holding-contour, industry/region/
  revenue, and source-constrained registry radars.
- Configured source policy becomes visible and enforceable instead of advisory.
- Runs can fail clearly when planning remains invalid, rather than silently
  falling back to one broad search.
- More provider calls may increase cost and latency; benchmark slices must
  measure both.
- The backend remains the source of truth for accepted execution strategy,
  candidate filtering, status, and audit semantics.

## Guardrails

- Application modules define planner contracts, validator rules, and execution
  compilation without importing provider SDKs, HTTP clients, FastAPI, SQLAlchemy,
  Celery, or Redis.
- Integrations may call OpenRouter for planning/search, but return typed records
  and sanitized trace observations.
- Product dossier shows discovery settings, selected/skipped source bases,
  accepted steps, and coverage summaries.
- Technical trace may show sanitized planner request/response details.
- No raw hidden chain-of-thought fields are requested, persisted, or displayed.
