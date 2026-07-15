# ADR: Close Radar root namespace and retain compatibility shims

## Status

Accepted

## Context

Radar behavior was historically spread across root-level application modules.
Pipeline migrations moved the largest components, but lifecycle,
configuration, preflight, and source-provider behavior still made the flat
namespace look authoritative.

External or hidden callers may still use old imports. Removing them in a
minor-version cleanup would create avoidable compatibility risk.

## Decision

All Radar behavior belongs under `power_web_os.application.radar`:

- lifecycle records and services under `radar.lifecycle`;
- definitions, model profiles, and runtime configuration under
  `radar.configuration`;
- readiness checks under `radar.preflight`;
- candidate source planning and provider ports under
  `radar.candidate_discovery.sources`.

Every root-level Radar-prefixed module is a compatibility shim of at most eight
lines. The authoritative old-to-new map is
`power_web_os.application.radar.compatibility`. Production code and behavior
tests may not import the shims.

The shims emit no runtime warning. Removal requires an explicit major-version
sunset slice with public import-policy review.

## Consequences

- Filesystem ownership now matches the documented architecture.
- Existing callers keep object-identical imports.
- Architecture tests reject new root behavior and reverse dependencies.
- Moving configuration modules must preserve repository-relative config paths.
- Completion requires live Candidate Discovery and Signal Monitoring trace
  comparison, not only import and unit tests.

## Alternatives considered

- Delete all shims immediately: rejected because hidden callers are not
  inventoried.
- Keep root lifecycle/configuration modules as permanent exceptions: rejected
  because the visible architecture would remain misleading.
- Emit deprecation warnings now: rejected because no major-version removal
  window has been approved.
