# Radar Configuration

This package owns active definition updates, deterministic catalog seeding,
model profiles, effective runtime settings, and redacted runtime configuration
reports.

It may depend on provider-neutral Radar contracts and application ports. It
must not import API routes, persistence implementations, jobs, workflows, HTTP
clients, or provider SDKs.

New configuration behavior belongs here. Root-level configuration modules are
compatibility shims only.
