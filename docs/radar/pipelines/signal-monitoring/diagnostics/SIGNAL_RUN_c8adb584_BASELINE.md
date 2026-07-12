# Signal Monitoring Baseline Diagnosis

Status: baseline evidence

Pipeline id: `signal-monitoring`

Run id: `signal-run-c8adb584-da26-4c31-84d1-37c067e7cf89`

Source candidate run: `radar-run-3bbf9c0f-330e-4468-8901-966a751234a8`

Target slice: `0.7.6.4.18.2.1`

## Observed Facts

- The run completed and persisted a standalone signal-monitoring report.
- The immutable input contained three candidates: two accepted product candidates and one review-needed candidate.
- Two signal criteria produced six planned tasks and six accepted OpenRouter provider attempts.
- Every task was assigned to the `known_source` lane even though source strategy also selected official-company and open-web capabilities.
- The task planner selected one source decision per candidate/criterion pair; selected alternative lanes did not become scheduled or explicitly unscheduled work.
- Known source references such as `retrieved_1` were passed to the provider without the corresponding product-safe URL, title and snippet.
- All six observations were `not_observed`.
- The three maintenance/reliability results exposed one, two and three source references respectively.
- The three modernization/investment results exposed zero source references and no persisted search receipt.
- The live demo explicitly supplied a seven-day lookback and therefore overrode the Radar monitoring policy.

## Root Causes

1. Source strategy and task planning use different completeness contracts. Strategy may select several lanes, while planning silently keeps one decision.
2. The live adapter parses only model-authored JSON and does not reuse the candidate-discovery retrieval normalization that captures sanitized OpenRouter annotations and citations.
3. `not_observed` is gated by an accepted provider attempt, but not by complete required-lane coverage or an auditable no-results receipt.
4. The demo CLI owns a seven-day default instead of deferring to the persisted Radar monitoring policy.
5. Existing tests prove source-decision ordering, but do not prove that every selected decision reaches scheduling, execution or an explicit terminal ledger state.

## Preserved Invariants

- Signal monitoring starts from an immutable completed candidate-discovery snapshot and never rediscovers candidates.
- Signal budgets, models, jobs and output persistence remain independent from candidate discovery.
- Provider failures and unsearched work never become `not_observed`.
- Product reports and traces exclude secrets, authorization headers, raw provider payloads and hidden reasoning.

## Required Correction

The target design is specified in
`docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.1.md`.
The slice cannot close until every mandatory requirement in the adjacent
acceptance manifest has product-safe test and persisted-run evidence.
