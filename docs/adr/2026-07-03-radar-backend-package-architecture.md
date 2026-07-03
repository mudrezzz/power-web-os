# ADR: Radar Backend Package Architecture

## Status

Accepted

## Context

Candidate-discovery Radar has outgrown the original extracted live Radar module
layout. The backend application layer now has many root-level
`live_radar_*.py` files. This shape still respects the coarse backend boundary
rules: application code does not import FastAPI, SQLAlchemy, Celery, Redis, or
provider SDKs. But it fails at the next level down: Radar itself has no clear
internal package architecture.

Measured baseline before this decision:

- `38` root-level `src/power_web_os/application/live_radar_*.py` files;
- `10 378` total lines in those files;
- `332` top-level functions;
- `78` top-level classes;
- `live_radar_staged_execution.py` is the largest hotspot;
- `live_radar_service.py` is the service-facade hotspot;
- `live_radar_staged_execution.py` has the highest application import fan-out.

This happened because each slice could add another provider-neutral helper,
diagnostic projection, checkpoint action, or budget rule without choosing an
internal Radar package boundary. The result is not a single old monolith, but a
flat micro-monolith: many small files that still require global knowledge to
change safely.

## Decision

Radar backend code inside `application` must move toward an internal package
structure:

```text
src/power_web_os/application/radar/
  shared/
  candidate_discovery/
    planning/
    retrieval/
    extraction/
    sources/
    universe/
    checkpoints/
    execution/
    diagnostics/
  signal_monitoring/
  power_web_discovery/
```

The root-level `application/live_radar_*.py` namespace is migration debt. It is
allowed only for the current explicitly documented files and compatibility
wrappers while the migration proceeds. New Radar backend code must not add new
root-level `live_radar_*.py` modules.

Radar components should use consistent contract names:

- `Input` for a service or phase input record;
- `Result` for successful phase/service output;
- `Decision` for policy, admission, validation, or checkpoint choices;
- `Issue` for validation, policy, schema, or evidence-linking problems;
- `Event` for product-safe journal/trace events;
- `Service` for the component that owns a use-case decision.

Pure helper functions are allowed when they are private implementation details
or explicit projections such as `*_payload` and `*_summary`. Public top-level
helpers must not become an unowned API between phases.

The existing coarse dependency direction still applies:

```text
API / CLI / workers / scheduler
  -> application services
    -> domain services + ports
      -> persistence / integrations / job adapters
```

Within Radar packages, candidate-discovery implementation may depend on
`radar.shared`, but shared code must not depend on candidate discovery, signal
monitoring, or Power Web discovery. Signal monitoring and Power Web discovery
must live beside candidate discovery, not inside it.

## Consequences

- The next refactoring slices can move code into package-owned locations
  without changing runtime behavior.
- Architecture contract tests can prevent new root-level `live_radar_*.py`
  files before the migration is complete.
- The current large/high-fan-out files remain explicitly documented migration
  debt, not examples for new backend work.
- Developers and agents get one backend Radar architecture document instead of
  reverse-engineering a flat module list.
- Some old imports will need compatibility wrappers during migration. Those
  wrappers are temporary and must not own new behavior.

## Alternatives considered

- **Keep root-level `live_radar_*` files and add more docstrings.** Rejected
  because the issue is package ownership and phase boundaries, not lack of
  one-line module descriptions.
- **Move every file immediately.** Rejected because candidate discovery is a
  live application path with many tests and provider-facing contracts. A
  package contract and compatibility skeleton should come first.
- **Create provider-specific packages such as `dadata` or `openrouter` under
  application.** Rejected because provider implementation belongs in
  `integrations`; application packages should own Radar use-case phases and
  provider-neutral contracts.
