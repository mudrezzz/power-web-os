# Candidate Discovery Sources

## Ownership

Owns source obligations, capability-card interpretation for candidate
discovery, registry/source orchestration records, and lookup-term contracts.

Source-of-truth modules:

- `risk.py`: source verification-risk helpers used by candidate normalization
  and signal/qualification evidence projection.
- `lookup_terms.py`, `registry_lookup_terms.py`: bounded deterministic lookup
  terms for company and registry lanes.
- `obligations.py`: source obligations and execution diagnostics.
- `providers.py`: provider-neutral company/source registry ports.
- `registry_helpers.py`, `registry_observation_helpers.py`: structured
  registry projection and deduplication.

## Allowed imports

- `power_web_os.application.radar.shared`.
- Candidate-discovery planning and universe records when source decisions need
  target context.

## Forbidden imports

- Provider SDKs, HTTP clients, FastAPI, SQLAlchemy, Celery, Redis, dotenv, and
  legacy `live_radar_*` modules.

## How to extend

Use source capabilities and source policy. Do not hardcode provider names such
as DaData or SPARK into generic source-selection rules.

Root-level `live_radar_source_risk.py` is a compatibility shim only.
