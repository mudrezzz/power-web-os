# Radar Signal Monitoring

This package owns the provider-neutral recurring "what changed" Radar
pipeline. It supports recorded execution and a separately persisted live
runtime without taking ownership of transport or infrastructure.

## Ownership

Signal monitoring owns recurring signal checks over known candidates:

- `contracts.py`: monitoring inputs, plans, tasks, observations, source
  decisions, provider port, and outcome records.
- `source_strategy.py`: deterministic source-lane selection from source policy,
  source cards, and reusable known sources.
- `planning.py`: multi-lane planning input, deterministic plan construction and backend acceptance.
- `policy.py`: effective per-signal depth, overlap, cadence and source-lane normalization.
- `scheduling.py`: explicit scheduled/budget-limited lane ledger.
- `windows.py`: initial and per-lane incremental window policy.
- `receipts.py`: product-safe execution receipts and source lifecycle.
- `evidence.py`: entity, criterion, date, source-ref and domain validation.
- `checkpoints.py`: pair-level coverage and observation decisions.
- `revisions.py`: one bounded policy-safe query revision.
- `budgets.py`: signal task, provider-call, retry, and lookback counters.
- `payloads.py`: provider payload parsing and bounded repair.
- `projection.py`: observation, diagnostic, fingerprint, and outcome shaping.
- `executor.py`: recorded/no-network orchestration against a provider port.
- `input_assembler.py`: immutable evidence-complete handoff from a completed
  candidate-discovery run.
- `runtime.py`: queued and persisted signal-run lifecycle services.
- `artifact.py`: product-safe standalone signal report projection.
- `surface.py`: cumulative product read model for current versus retained
  candidate-criterion outcomes and resolvable evidence.
- `service_factory.py`: application collaborator composition from provider
  ports.

Root-level `signal_monitoring_*` files are compatibility shims only. They are
tracked in `docs/architecture/radar/RADAR_ROOT_NAMESPACE_DEBT.md` and must not
regain behavior.

## Allowed imports

- `power_web_os.application.radar.shared`.
- `power_web_os.application.radar_model_profiles`.
- Explicit known-candidate/source references exposed by stable shared
  contracts.

## Forbidden imports

- Candidate-discovery internals, Power Web discovery internals, FastAPI,
  SQLAlchemy, Celery, Redis, HTTP clients, provider SDKs, dotenv, and legacy
  `live_radar_*` modules.

## How to extend

Do not reuse candidate-discovery internals by shortcut. The handoff enters as
persisted public candidate/source records through application ports. Add shared
contracts first when another direct dependency is genuinely needed.

When adding new monitoring behavior, add it under this package or first create
the missing package-owned contract. Keep legacy root imports only for explicit
compatibility coverage.

Behavior-changing work starts from the current Signal Monitoring AS IS and a
persisted-run RCA, then registers TO BE Markdown/PDF plus an acceptance
manifest. It is complete only after the pipeline validator emits PASS and the
validated behavior is reconciled back into AS IS.

The cumulative surface is query-only. It may join completed signal reports
that share Radar and source-run lineage, but it must not mutate reports,
candidate-discovery artifacts, budgets or monitoring decisions.
