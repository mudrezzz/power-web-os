# Candidate Discovery Extraction

## Ownership

Owns structured extraction contracts, schema validation, repair decisions, and
diagnostic issues.

Source-of-truth modules:

- `contract.py`: extraction payload validation, deterministic safe repair,
  validation issues, repair results, and qualification-contract issue
  projection from extraction diagnostics.
- `diagnostics.py`: extraction validation issue dedupe, repair-result
  projection, aggregate contract state, and product-safe validation events.

## Allowed imports

- Python standard library.
- `power_web_os.application.radar.shared`.
- Candidate-discovery records needed for extracted findings.

## Forbidden imports

- Provider SDKs, HTTP clients, FastAPI, SQLAlchemy, Celery, Redis, dotenv, and
  legacy `live_radar_*` modules.

## How to extend

Treat malformed provider output as explicit diagnostic state. Do not silently
turn invalid extraction payloads into successful product state.

Root-level `live_radar_extraction_contract.py` and
`live_radar_extraction_diagnostics.py` are compatibility shims only.
