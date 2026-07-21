# Baseline diagnostic 0.7.6.6.0.2

Captured before production changes for slice `0.7.6.6.0.2`.

## UI baseline

- Product detail and catalog are rendered simultaneously.
- The product rail reserves 260 px on wide desktop and 208 px at 1366 px.
- Opening a role adds a 320-400 px right inspector; at 1366 px it still
  reserves 240-320 px.
- A role editor therefore competes with both the application sidebar and two
  feature-owned side columns.
- Radar candidate rows already use the safer inline-expansion pattern.
- Radar detail, candidate detail, run diagnostics and Access Plans use pill
  controls for section navigation, while the new Playbook uses underline tabs.

## Contract baseline

- `SemanticBuyingRole` requires decision rights, reason and expected evidence.
- Publishing creates ProductDefinition, BuyingRolePolicy and AccessPlaybook
  versions as one mandatory composite.
- `access_playbook_version_id` is non-nullable.
- Access route references can block removal of a semantic role.
- Planned slice `0.7.6.6.1` requires AccessPlaybook and authored expected
  evidence even though neither is necessary to decide which people to find.

## Root cause

The first foundation slice combined discovery configuration with downstream
sales orchestration and used a local master-detail layout instead of the
existing full-width/inline patterns. The correction must change both domain
ownership and UI composition; CSS-only concealment would preserve the hidden
dependency.
