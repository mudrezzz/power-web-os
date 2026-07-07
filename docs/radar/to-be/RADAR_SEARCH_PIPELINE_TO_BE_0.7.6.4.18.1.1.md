# Radar Search Pipeline TO BE 0.7.6.4.18.1.1

Status: Implemented design input

Product area: Radar candidate discovery pipeline

Slice: 0.7.6.4.18.1.1 Candidate discovery recall-first upstream semantics and benchmark target protection

Last updated: 2026-07-06

Generated PDF: `docs/radar/to-be/RADAR_SEARCH_PIPELINE_TO_BE_0.7.6.4.18.1.1.pdf`

## Goal

Candidate discovery must behave as a recall-first upstream finder after the
signal-monitoring split. Source-backed upstream leads must not collapse into a
flat `Monitor` result only because signal monitoring has not run. Downstream
product acceptance stays strict and separate.

## Intended Behavior

1. Candidate discovery keeps source-backed upstream leads when there is valid
   retrieved-source, official-domain, or registry identity evidence.
2. `upstream_discovery_outcome` explains what discovery found:
   `confirmed_upstream_lead`, `review_needed_upstream_lead`,
   `retained_upstream_lead`, or `rejected_noise`.
3. `product_acceptance_status` explains whether the entity is a strict product
   candidate, requires review, or is not product accepted.
4. In normal `signal_execution_mode="handoff"`, missing signal observations do
   not create `Monitor`, `signal_requires_human_review`, or `not_observed`.
5. Official high-trust domains can promote source-backed relation and
   industrial coverage evidence when the candidate name or alias appears in
   product-safe source diagnostics.
6. Concrete registry identity evidence, such as INN, OGRN, or legal name, is
   retained as upstream evidence and is not weak by construction.
7. `benchmark_live` protects explicit baseline targets before optional
   exploration by carrying lane minimums, completion slots, reserve budgets,
   and benchmark metadata through dedupe, selection, scheduling, and reporting.

## Reporting Contract

Evaluation reports separate upstream recall from strict product precision:

- `product_candidate_count` counts only strict product-accepted candidates;
- `retained_upstream_lead_count` counts retained upstream material;
- `confirmed_upstream_lead_count` and `review_needed_upstream_lead_count`
  explain the quality of retained upstream leads;
- `benchmark_target_funnel` gives every baseline target a path state such as
  generated, selected, admitted, executed, source found, projected, or a
  path-level miss reason.

## Guardrails

- No signal-monitoring live runtime is added in this slice.
- No SIBUR production hardcode is allowed outside benchmark fixtures/hints.
- Upstream false positives are acceptable as retained/review-needed leads, but
  must not become accepted product accounts without strict evidence.
- Every remaining false negative must have a path-level reason instead of a
  generic budget symptom.

## Validation Plan

- Unit tests cover official-domain admission, open-web retention, registry
  identity retention, handoff normalization, benchmark target metadata dedupe,
  and benchmark-present source projection.
- Regression gates cover search expansion, benchmark profile generation,
  evaluation reports, live candidate discovery, adaptive execution, API/jobs,
  signal-monitoring isolation, documentation, roadmap, and static diff checks.
