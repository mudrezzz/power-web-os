# Radar Lifecycle

This package owns provider-neutral Radar run records, review decisions, audit
journals, technical traces, and persisted output-summary reconciliation.

API, persistence, Celery, workflows, and provider integrations may depend on
these contracts. This package must not import transport, persistence adapters,
job runners, HTTP clients, or provider SDKs.

Extend lifecycle behavior here. Root-level application Radar paths are
compatibility shims only.
