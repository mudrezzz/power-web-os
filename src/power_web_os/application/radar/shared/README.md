# Radar Shared

Shared code is allowed only when it is genuinely useful to more than one Radar
pipeline.

## Ownership

This package owns pipeline-neutral records and helpers such as source
capability primitives, model/runtime summaries, budget records, and
product-safe issue/event shapes.

## Allowed imports

- Python standard library.
- Stable application/domain records that do not depend on a specific Radar
  pipeline.

## Forbidden imports

- Candidate discovery, signal monitoring, or Power Web discovery packages.
- FastAPI, SQLAlchemy, Celery, Redis, HTTP clients, provider SDKs, and dotenv.
- Already-moved legacy shims such as `live_radar_source_cards`.

## How to extend

Add shared code only after checking that at least two pipeline packages need the
same concept. If only candidate discovery needs it, keep it under
`candidate_discovery`.

Current source-of-truth modules:

- `source_cards.py`: planner-facing source cards and source capability
  validation.
