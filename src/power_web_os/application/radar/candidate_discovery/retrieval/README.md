# Candidate Discovery Retrieval

## Ownership

Owns live mini Radar definition builders, provider-neutral web retrieval
contracts, retrieval task cards, and retrieved source material.

## Allowed imports

- `power_web_os.application.radar.shared`.
- Candidate-discovery source and planning records that describe retrieval scope.

## Forbidden imports

- FastAPI, SQLAlchemy, Celery, Redis, HTTP clients, provider SDKs, dotenv, and
  legacy `live_radar_*` modules.

## How to extend

Keep retrieval records provider-neutral. Actual HTTP/provider execution belongs
in integration adapters and phase executors.

Current source-of-truth modules:

- `definition.py`: live mini Radar definition, execution/search-plan builders,
  and artifact projection for candidate-discovery runs.
- `product_sources.py`: strict product-source projection for candidate rows.
- `web_retrieval.py`: provider-neutral web retrieval request/result records,
  source outcomes, retrieval provider port, and recorded provider test adapter.
