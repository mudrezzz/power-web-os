# Radar Preflight

This package owns deterministic readiness checks for Radar definitions,
connectors, provider fixtures, credentials, and source obligations.

Preflight reports readiness; it does not execute providers, persist runs, or
change pipeline decisions. Integration-specific connector probes stay behind
the connector profile contracts.
