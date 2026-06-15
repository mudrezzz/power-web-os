# ADR: Qualification Evidence And Review Contract

- Status: Accepted
- Date: 2026-06-15

## Context

ICP Radar settings define account qualification rules, but candidate detail screens must show more than a pass/fail label. A sales or ABM user needs to understand which sources were used, how trustworthy they are, whether cross-validation was required, what exact evidence was found, and how the final qualification assessment follows from the rule strictness.

## Decision

Every provider-backed ICP Radar candidate must expose qualification results through a structured contract:

- the rule id/code and the exact rule text snapshot used for the run;
- logical operator: `AND`, `OR`, `AND NOT`, or `OR NOT`;
- requirement level: required or recommended;
- source usages with source origin: global base, local rule source, or additional system-found source;
- trust/check policy: trusted, cross-checked, or HITL required;
- evidence findings: fact, source ref, short excerpt or explicit no-excerpt marker, why it matches or contradicts the rule, and evidence strength;
- cross-validation status;
- requirement evaluation;
- final assessment: matches, partially matches, does not match, or unknown;
- optional human review decision with comment.

The UI must render qualification as a table-first review surface. Rows start compact, expand to show evidence cards that combine source, excerpt, fact, and match rationale, and provide local review actions: approve, reject, or correct with a comment. Cross-validation is part of the requirement-fit summary, not a separate standalone block. The generated artifact remains immutable; human review is stored in local demo state until backend persistence exists.

## Consequences

- Live LLM/search workflows may return a simpler shape, but the backend normalizer must enrich it into this contract before writing artifacts.
- Candidate detail screens may not show raw Q1/Q2 rows without source, trust, cross-validation, evidence, and final-assessment context.
- New radar providers must adapt their findings into the same qualification contract before entering the canonical ICP Radar UX.
- The model must not expose hidden chain-of-thought. It may expose structured evidence, rationale, and review flags.
