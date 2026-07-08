# Candidate Discovery Extraction

## Ownership

Owns structured extraction contracts, schema validation, repair decisions, and
diagnostic issues. It also owns deterministic post-extraction salvage for the
specific case where strict extraction remains invalid but product-safe source
diagnostics already contain source-backed upstream leads.

Source-of-truth modules:

- `contract.py`: extraction payload validation, deterministic safe repair,
  validation issues, repair results, and qualification-contract issue
  projection from extraction diagnostics.
- `diagnostics.py`: extraction validation issue dedupe, repair-result
  projection, aggregate contract state, and product-safe validation events.
- `recovery.py`: extraction failure classification and deterministic
  post-extraction salvage from product-safe source diagnostics.

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

Post-extraction salvage is allowed only after bounded extraction recovery fails
and only from source titles, snippets, URLs, annotations, and source lifecycle
metadata that are already product-safe. Without a source ref and source text,
salvage must report an unrecovered reason instead of creating a candidate.

Root-level `live_radar_extraction_contract.py` and
`live_radar_extraction_diagnostics.py` are compatibility shims only.
