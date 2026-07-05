# Radar Signal Monitoring

This package is reserved for the recurring "what changed" Radar pipeline.

## Ownership

Signal monitoring owns recurring signal checks over known candidates, including
lookback windows, warm-start sources, signal-specific budgets, novelty/dedupe,
and signal evidence projection.

The current root-level `signal_monitoring_*` files still own recorded/no-network
behavior until slice `0.7.6.4.18` moves them into this package. They are tracked
in `docs/architecture/radar/RADAR_ROOT_NAMESPACE_DEBT.md` and should not be used
as the extension path for new monitoring work.

## Allowed imports

- `power_web_os.application.radar.shared`.
- Explicit known-candidate/source references exposed by stable shared contracts.

## Forbidden imports

- Candidate-discovery internals, Power Web discovery internals, FastAPI,
  SQLAlchemy, Celery, Redis, HTTP clients, provider SDKs, dotenv, and legacy
  `live_radar_*` modules.

## How to extend

Do not reuse candidate-discovery internals by shortcut. Add shared contracts
first when signal monitoring needs data from candidate discovery.

When adding new monitoring behavior, add it under this package or first create
the missing package-owned contract. Keep legacy root imports only for deferred
behavior and compatibility coverage.
