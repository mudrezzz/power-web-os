# Candidate Discovery Diagnostics

## Ownership

Owns product-safe projection helpers for dossier, trace, journal, benchmark,
and developer diagnostics.

## Allowed imports

- `power_web_os.application.radar.shared`.
- Candidate-discovery result, decision, issue, and event records.

## Forbidden imports

- Raw provider dumps, headers, secrets, hidden reasoning fields, FastAPI,
  SQLAlchemy, Celery, Redis, HTTP clients, provider SDKs, and dotenv.
- Moved legacy compatibility shims. Temporary imports from deferred diagnostic
  helpers such as normalization or pipeline support are allowed only while those
  modules remain marked as deferred in `candidate_discovery/compatibility.py`.

## How to extend

Diagnostics should explain what happened without mutating runtime behavior.
Redaction rules are part of the contract.
