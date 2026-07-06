# Radar Signal Monitoring

This package owns the recorded/no-network recurring "what changed" Radar
pipeline.

## Ownership

Signal monitoring owns recurring signal checks over known candidates:

- `contracts.py`: monitoring inputs, plans, tasks, observations, source
  decisions, provider port, and outcome records.
- `source_strategy.py`: deterministic source-lane selection from source policy,
  source cards, and reusable known sources.
- `planning.py`: task construction for selected candidate/signal/source lanes.
- `budgets.py`: signal task, provider-call, retry, and lookback counters.
- `payloads.py`: provider payload parsing and bounded repair.
- `projection.py`: observation, diagnostic, fingerprint, and outcome shaping.
- `executor.py`: recorded/no-network orchestration against a provider port.

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

Do not reuse candidate-discovery internals by shortcut. Add shared contracts
first when signal monitoring needs data from candidate discovery.

When adding new monitoring behavior, add it under this package or first create
the missing package-owned contract. Keep legacy root imports only for explicit
compatibility coverage.
