# ADR: Universal LLM Call Contract For Radar Structured Outputs

Status: Accepted

Date: 2026-06-28

## Context

Radar depends on several structured LLM calls:

- discovery planner;
- discovery, qualification, coverage, and signal extraction;
- extraction repair;
- plan revision;
- benchmark coverage probes.

These calls are allowed to use different OpenRouter models, but they share one
failure class: the provider can return HTTP 200 with non-JSON text, JSON that
does not match the application schema, unresolved evidence references, or a
shape that only partially satisfies the task contract.

The product must not treat those failures as normal empty discovery. It also
must not keep fixing each role one by one after every failed smoke run.

## Decision

Every Radar LLM call that expects structured JSON and can affect pipeline
continuation must follow the same bounded contract:

1. Call the primary role model.
2. Validate transport JSON and the role-specific application schema.
3. If invalid, retry the primary model once with strict repair context.
4. If still invalid and a backup model is configured, retry once with the
   backup model.
5. If still invalid, stop the affected branch with a precise diagnostic reason.

All retry and backup attempts must:

- pass through external-call budgets;
- pass through provider-retry budgets;
- be recorded in technical trace and dossier metadata;
- preserve product-safe diagnostics only;
- never expose API keys, headers, hidden reasoning, or raw provider dumps.

The generic fallback alias is `OPENROUTER_BACKUP_MODEL`. Role-specific backup
variables override it when present, for example:

- `OPENROUTER_PLANNER_BACKUP_MODEL`;
- `OPENROUTER_EXTRACTION_BACKUP_MODEL`.

Role temperature settings are configuration, not code constants:

- `OPENROUTER_PLANNER_TEMPERATURE`;
- `OPENROUTER_EXTRACTOR_TEMPERATURE`;
- `OPENROUTER_SIGNAL_TEMPERATURE`;
- `OPENROUTER_BACKUP_TEMPERATURE`.

Default temperature remains `0` for deterministic structured output unless a
run profile or environment explicitly changes it.

## Consequences

- Planner and extraction failures become comparable in diagnostics.
- Model experiments can vary role model and role temperature without changing
  Radar code.
- Tests must cover non-JSON and schema-invalid responses for every new
  structured LLM role.
- A future connector or model-provider adapter must implement this contract
  before it can be used for a pipeline-critical structured output.

## Non-goals

- This ADR does not choose one permanent best model.
- This ADR does not make backup calls unlimited.
- This ADR does not change product scoring or candidate projection.
- This ADR does not allow continuing after unrecoverable malformed output.
