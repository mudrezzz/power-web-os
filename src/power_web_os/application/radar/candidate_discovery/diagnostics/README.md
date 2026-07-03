# Candidate Discovery Diagnostics

## Ownership

Owns product-safe projection helpers for dossier, trace, journal, benchmark,
and developer diagnostics.

## Allowed imports

- `power_web_os.application.radar.shared`.
- Candidate-discovery result, decision, issue, and event records.

## Forbidden imports

- Raw provider dumps, headers, secrets, hidden reasoning fields, FastAPI,
  SQLAlchemy, Celery, Redis, HTTP clients, provider SDKs, dotenv, and legacy
  `live_radar_*` modules.

## How to extend

Diagnostics should explain what happened without mutating runtime behavior.
Redaction rules are part of the contract.
