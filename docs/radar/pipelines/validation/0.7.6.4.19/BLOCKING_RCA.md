# Radar Root Namespace Closure: Blocking Live RCA

Status: **BLOCKED BY LIVE QUALITY REGRESSION**

This is an interim RCA, not the final validation report. Slice `0.7.6.4.19`
remains In Progress until the complete live chain produces a machine-generated
`PASS` report.

## Candidate Discovery Proof

Fresh run: `radar-run-b03fac86-7307-448f-8deb-c1ea1794956c`.

- benchmark mode: blind;
- benchmark hints used: false;
- strict recall: `1.0`;
- visible recall: `0.8889`;
- legal baseline targets visible: `8/9`;
- visible candidates: `91`;
- retained upstream leads: `110`;
- accepted candidates: `84`;
- review-needed candidates: `7`;
- duplicate candidate IDs: `0`;
- visible candidates without provenance: `0`;
- unexplained candidate drops: `0`;
- remaining false negative: `tobolsk-site`, reason `not_generated`.

The candidate-discovery quality gate passed. The run also supplied an
evidence-complete Signal Monitoring scope of three accepted and three
review-needed candidates.

## Initial Signal Monitoring Proof

Fresh run: `signal-run-55a9cfb4-b0f1-48ee-8aef-df20a236266f`.

- source candidate run: `radar-run-b03fac86-7307-448f-8deb-c1ea1794956c`;
- candidates: `6` (`3` accepted and `3` review-needed);
- criteria: `2`;
- candidate/criterion pairs: `12`;
- tasks and provider calls: `28`;
- receipt gaps: `0`;
- orphan source decisions: `0`;
- cross-entity known-source tasks: `0`;
- false `not_observed`: `0`;
- confirmed observations with score zero: `0`;
- sources without capability: `0`;
- required budget-limited lanes: `0`.

After fixing evaluator URL canonicalization, the control result is:

- positive controls: `2/4`;
- negative controls classified as required: `1` (DoD requires at least `2`);
- unknown-date review controls: `1/1`;
- false-positive controls: `0`.

The missing positive controls are:

- `voronezh-special-component-2026`;
- `voronezh-kommersant-plant-2026`.

The run also confirmed one S1 observation for
`ppo-v-ooo-sibur-kstovo` from an XLSX source classified as `identity_only`.
That violates the accepted source-capability rule: an identity-only or registry
source may support entity identity, but cannot prove a fresh signal.

## Root Cause

Three independent defects were exposed:

1. The evaluator previously compared raw URLs, so an otherwise identical URL
   with an `erid` query parameter was treated as a different source. This local
   validation defect is fixed and covered by a regression test.
2. Evidence found while searching one criterion is not reconciled against the
   other configured criteria for the same candidate. Relevant VSK material can
   therefore be retained under S1 while an S2 control remains missed. Any reuse
   must pass the same candidate, criterion, time and source validation rather
   than being copied by keyword.
3. The accepted negative-control set is not reliably reached by ordinary live
   search. The earlier acceptance process proved one run, but did not prove
   cross-run reachability. Exact old URLs can disappear from provider search
   results even when the temporal classifier itself remains correct.

The identity-only confirmation is a fourth product-semantic defect in source
capability enforcement, not a reporting issue.

## Process Retrospective

The five bounded autofix cycles repaired migration-adjacent runtime failures:

1. extraction salvage after evidence-link revision exhaustion;
2. task-level handling of OpenRouter transport failures;
3. safe completion of truncated planner JSON followed by full schema validation;
4. planner output headroom and a bounded backup attempt;
5. fresh candidate and Signal Monitoring regression execution.

The final live run then exposed a behavior-level Signal Monitoring defect.
Continuing to patch it inside the namespace migration would exceed the bounded
autofix contract and mix an algorithm change into a migration-only slice.

The previous Signal Monitoring quality closeout was too dependent on one
provider result. Future quality gates must prove that controls remain reachable
across a fresh run, that controls never enter planning, and that capability
rules are checked directly by the namespace validator.

## Decision

- Do not start the incremental signal run: it cannot repair failed initial
  positive and negative control recall.
- Keep `0.7.6.4.19` In Progress.
- Implement corrective slice `0.7.6.4.19.1`.
- Freeze the acceptance manifest, accepted URL sets and date intervals before
  live execution and record its SHA-256 in validation evidence.
- Prove initial-search reproducibility with two independently initialized live
  runs using the same frozen controls. Do not edit controls after seeing either
  result.
- Run a third, normal incremental search to prove watermarks and deduplication.
- After `0.7.6.4.19.1` passes, repeat the complete fresh candidate and Signal
  Monitoring validation chain required by `0.7.6.4.19`.
