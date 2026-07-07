# Candidate Discovery Diagnostics

## Ownership

Owns product-safe projection helpers for dossier, trace, journal, benchmark,
and developer diagnostics.

Source-of-truth modules:

- `live_run_artifact.py`: final live-run artifact shaping from completed
  service state.
- `normalization.py`: candidate, qualification, signal, score, and source-backed
  evidence normalization.
- `contract_validation.py`: normalized qualification contract validation.
- `upstream_projection.py`: upstream admission decision projection into display
  tier, promoted qualification, and product acceptance fields.
- `collections.py`: candidate ranking and source dedupe helpers.
- `pipeline_support.py`: planned event type, rejected-candidate payload, and
  sanitized technical trace helpers.

## Allowed imports

- `power_web_os.application.radar.shared`.
- Candidate-discovery result, decision, issue, and event records.

## Forbidden imports

- Raw provider dumps, headers, secrets, hidden reasoning fields, FastAPI,
  SQLAlchemy, Celery, Redis, HTTP clients, provider SDKs, and dotenv.
- Moved legacy compatibility shims.

## How to extend

Diagnostics should explain what happened without mutating runtime behavior.
Redaction rules are part of the contract.

Root-level `live_radar_normalization.py`, `live_radar_collection_utils.py`, and
`live_radar_pipeline_support.py` are compatibility shims only.
