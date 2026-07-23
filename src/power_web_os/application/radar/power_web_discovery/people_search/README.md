# Power Web people search

This package owns the provider-neutral planning, source-lane, retrieval-audit,
lead-normalization and coverage-checkpoint stage between an immutable Power Web
handoff and future profile/identity resolution.

The stage emits source leads only. It does not create people, employment claims,
graph edges, persisted runs, jobs or UI state. Integrations implement the two
ports in `ports.py`; source and identity semantics remain application-owned.
