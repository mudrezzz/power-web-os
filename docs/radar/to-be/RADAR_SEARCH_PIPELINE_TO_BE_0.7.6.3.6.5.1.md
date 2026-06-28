# Radar Search Pipeline TO BE 0.7.6.3.6.5.1

Status: TO BE

Slice: 0.7.6.3.6.5.1

Generated PDF: `docs/radar/to-be/RADAR_SEARCH_PIPELINE_TO_BE_0.7.6.3.6.5.1.pdf`

## Purpose

The Radar pipeline must stop treating malformed structured LLM output as a
role-specific accident. Planner, extraction, repair, revision, signal, and
diagnostic probe calls all depend on machine-readable JSON. A non-JSON or
schema-invalid response must follow one shared recovery contract.

## Target Behavior

Every pipeline-critical structured LLM role follows this order:

| Step | Action | Budget | Terminal diagnostic if blocked |
|---|---|---|---|
| 1 | Call primary role model | OpenRouter role + total budget | provider unavailable or HTTP error |
| 2 | Validate JSON and application schema | no extra external call | `primary_non_json` or `primary_schema_invalid` |
| 3 | Retry primary model with strict repair context | provider retry + OpenRouter budget | `primary_retry_non_json` or `primary_retry_schema_invalid` |
| 4 | Retry role backup model when configured | provider retry + OpenRouter budget | `backup_non_json` or `backup_schema_invalid` |
| 5 | Stop affected branch if still invalid | no external call | exact recovery-exhausted reason |

The planner now participates in the same contract. Extraction already has
primary retry and backup recovery; this slice makes planner behavior explicit
and governed by the same ADR.

## Model Roles

| Role | Primary setting | Backup setting | Temperature setting | Default |
|---|---|---|---|---|
| Planner | `OPENROUTER_PLANNER_MODEL` | `OPENROUTER_PLANNER_BACKUP_MODEL`, then `OPENROUTER_BACKUP_MODEL` | `OPENROUTER_PLANNER_TEMPERATURE` | 0 |
| Extraction | `OPENROUTER_EXTRACTOR_MODEL` | `OPENROUTER_EXTRACTION_BACKUP_MODEL`, then `OPENROUTER_BACKUP_MODEL` | `OPENROUTER_EXTRACTOR_TEMPERATURE` | 0 |
| Signal/default | `OPENROUTER_MODEL` | future role-specific backup | `OPENROUTER_SIGNAL_TEMPERATURE` | 0 |
| Backup attempt | role backup model | none | `OPENROUTER_BACKUP_TEMPERATURE` | role temperature |

## Diagnostics

Technical trace and dossier metadata should show:

- role;
- primary model;
- backup model when attempted;
- attempt role: primary, primary_retry, backup;
- attempt index;
- temperature;
- budget decision;
- precise failure reason.

The payload must remain product-safe: no headers, API keys, hidden reasoning, or
raw provider dumps.

## Tests Required

The slice is not complete unless tests prove:

- planner non-JSON primary and primary retry can recover through backup;
- planner schema-invalid JSON triggers primary retry before backup;
- extraction non-JSON recovery still routes primary retry and backup;
- runtime config exposes role models and role temperatures;
- ADR exists and states that every new structured LLM role needs non-JSON and
  schema-invalid tests.

## Acceptance

After implementation, run two bounded Docker smoke/evaluation passes:

1. balanced model preset;
2. light model preset.

Compare:

- terminal run outcome;
- planner/extraction attempts;
- JSON/schema failure count;
- backup usage;
- OpenRouter budget usage;
- strict recall, review recall, and precision;
- whether benchmark remains blocked or can move to broader live evaluation.
