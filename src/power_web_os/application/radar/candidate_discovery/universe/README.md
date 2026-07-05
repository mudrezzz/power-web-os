# Candidate Discovery Universe

## Ownership

Owns candidate-universe entities, entity resolution, retrieved-candidate
materialization, review-needed flags, provider metadata merge semantics,
candidate source refs, gap payloads, upstream/cross-source disambiguation, and
product-candidate projection inputs.

## Allowed imports

- `power_web_os.application.radar.shared`.
- Candidate-discovery source and extraction records.

## Forbidden imports

- Signal-monitoring internals, Power Web discovery internals, FastAPI,
  SQLAlchemy, Celery, Redis, HTTP clients, provider SDKs, dotenv, and legacy
  `live_radar_*` modules.

## How to extend

Keep upstream universe recall-first and product candidate projection
precision-first. Review-needed sites or branches must not become confident
account rows without explicit resolution evidence.

Current source-of-truth modules:

- `identity.py`: candidate names, stable ids, source refs, and candidate source
  ref extraction.
- `metadata.py`: provider metadata merge contract and typed dict-list helper.
- `gaps.py`: candidate-universe gap observations and payload projection.
- `coverage.py`: coverage risk and warning extraction.
- `projection.py`: final candidate-universe row projection.
- `retrieved_candidates.py`: conservative source-backed candidate extraction
  from retrieved sources.
- `entity_resolution.py`: legal entity vs branch/site/project/asset
  classification, linked facts, and review-needed gap output.
- `cross_source_disambiguation.py`: bounded execution of planned cross-source
  checks for review-needed upstream entities.
- `upstream_disambiguation.py`: registry ambiguity retention and planned
  cross-source task creation.
