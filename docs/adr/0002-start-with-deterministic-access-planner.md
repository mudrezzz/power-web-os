# ADR 0002: Start With Deterministic Access Planner

## Status

Accepted

## Context

Access Plan recommendations must be explainable. Starting with a fully LLM-driven planner would make route ranking hard to test and trust.

## Decision

Start with deterministic route scoring over typed domain entities. Wrap this planner in LangGraph workflow later.

## Consequences

- Baseline tests can verify ranking, evidence refs, unresolved gaps, and HITL flags.
- LLM usage can be added around extraction, synthesis, and explanation without replacing core policy logic.
