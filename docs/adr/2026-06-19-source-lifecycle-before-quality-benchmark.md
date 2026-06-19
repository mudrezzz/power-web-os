# ADR: Source Lifecycle Must Be Visible Before Quality Benchmarking

- Status: Proposed
- Date: 2026-06-19

## Context

Live Radar technical trace can show provider requests, responses, and analyzed
sources while the product artifact still has zero `sources` and zero scores.
That is possible because product output intentionally keeps only evidence-bearing
used sources, while trace stores broader provider activity.

This is safer than showing unsupported evidence, but it makes debugging hard:
users see that searches happened, yet cannot tell whether sources were discarded
because they were unreachable, unlinked to candidates, missing evidence refs,
or only present in technical trace.

## Decision

Before multi-radar quality benchmarking, live Radar work should proceed through
three smaller hardening slices:

1. Make the source lifecycle visible in the product dossier:
   collected, parsed, reachable, linked to candidates, used in product, and
   discarded with reasons.
2. Harden evidence linking and source verification so evidence-bearing sources
   are not silently lost because of brittle `HEAD`/`GET` checks or missing
   provider-to-candidate links.
3. Prove the score contract with recorded fixtures and a minimal quality-mode
   smoke run before testing broader discovery quality.

Product source lists remain evidence-bearing only. Technical trace remains the
place for analyzed-but-unused sources and sanitized provider details.

## Consequences

- A run with `0` product sources must be explainable without reading raw trace
  payloads.
- Source verification becomes a stateful risk signal, not only a binary drop.
- Confirmed qualification and observed signal scores must be backed by evidence
  refs that resolve to product-used or explicitly risk-marked sources.
- `Slice 0.7.6.2` should benchmark discovery quality only after source lifecycle,
  evidence linking, and score-contract wiring are observable and tested.
