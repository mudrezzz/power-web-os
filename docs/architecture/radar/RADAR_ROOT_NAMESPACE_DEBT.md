# Radar Root Namespace Debt

This inventory is the source of truth for root-level Radar-prefixed files under
`src/power_web_os/application`.

The flat namespace is transition debt. It is not an extension path for new
Radar backend work. New behavior belongs under
`power_web_os.application.radar.*`; old root imports are allowed only for thin
compatibility shims, explicit compatibility tests, or deferred behavior modules
that have an owning migration slice.

## Status Values

- `moved_shim`: behavior source of truth already moved; the root file must stay
  a thin compatibility shim with `Source of truth:`.
- `deferred_behavior`: root file still owns real behavior until its owning
  migration slice moves it behind a package-owned service/contract.
- `target_for_migration`: root file is not a legacy `live_radar_*` shim but is
  still Radar behavior in the flat namespace and must move before closure.
- `compatibility_only`: legacy import surface retained only for compatibility
  assertions; behavior tests and production code should use package-owned paths.

## Inventory

| Root file | Status | Target package | Owning slice |
|---|---|---|---|
| `live_radar_candidate_refs.py` | `deferred_behavior` | `power_web_os.application.radar.candidate_discovery.universe` | `0.7.6.4.17.2` |
| `live_radar_checkpoint_actions.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.checkpoints.recovery` | `compatibility_only` |
| `live_radar_checkpoint_execution.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.checkpoints.recording` | `compatibility_only` |
| `live_radar_checkpoints.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.checkpoints` | `compatibility_only` |
| `live_radar_collection_utils.py` | `deferred_behavior` | `power_web_os.application.radar.candidate_discovery.diagnostics` | `0.7.6.4.17.3` |
| `live_radar_contracts.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.contracts` | `compatibility_only` |
| `live_radar_cross_disambiguation.py` | `deferred_behavior` | `power_web_os.application.radar.candidate_discovery.execution` | `0.7.6.4.17.2` |
| `live_radar_definition.py` | `deferred_behavior` | `power_web_os.application.radar.shared` | `0.7.6.4.17.1` |
| `live_radar_definition_runtime.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.planning` | `compatibility_only` |
| `live_radar_discovery_planning.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.planning` | `compatibility_only` |
| `live_radar_entity_resolution.py` | `deferred_behavior` | `power_web_os.application.radar.candidate_discovery.universe` | `0.7.6.4.17.2` |
| `live_radar_execution_budget.py` | `deferred_behavior` | `power_web_os.application.radar.shared` | `0.7.6.4.17` |
| `live_radar_execution_plan.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.planning` | `compatibility_only` |
| `live_radar_external_budget.py` | `deferred_behavior` | `power_web_os.application.radar.shared` | `0.7.6.4.17` |
| `live_radar_external_budget_context.py` | `deferred_behavior` | `power_web_os.application.radar.shared` | `0.7.6.4.17` |
| `live_radar_external_budget_reservations.py` | `deferred_behavior` | `power_web_os.application.radar.shared` | `0.7.6.4.17` |
| `live_radar_external_budget_settings.py` | `deferred_behavior` | `power_web_os.application.radar.shared` | `0.7.6.4.17` |
| `live_radar_extraction_contract.py` | `deferred_behavior` | `power_web_os.application.radar.candidate_discovery.extraction` | `0.7.6.4.17.3` |
| `live_radar_extraction_diagnostics.py` | `deferred_behavior` | `power_web_os.application.radar.candidate_discovery.extraction` | `0.7.6.4.17.3` |
| `live_radar_normalization.py` | `deferred_behavior` | `power_web_os.application.radar.candidate_discovery.diagnostics` | `0.7.6.4.17.3` |
| `live_radar_pipeline_support.py` | `deferred_behavior` | `power_web_os.application.radar.candidate_discovery.diagnostics` | `0.7.6.4.17.3` |
| `live_radar_plan_acceptance.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.planning` | `compatibility_only` |
| `live_radar_planning_pipeline.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.planning` | `compatibility_only` |
| `live_radar_product_sources.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.retrieval` | `compatibility_only` |
| `live_radar_retrieval_plan.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.planning` | `compatibility_only` |
| `live_radar_retrieved_candidates.py` | `deferred_behavior` | `power_web_os.application.radar.candidate_discovery.universe` | `0.7.6.4.17.2` |
| `live_radar_search_expansion_execution.py` | `deferred_behavior` | `power_web_os.application.radar.candidate_discovery.execution` | `0.7.6.4.16` |
| `live_radar_search_expansion_payloads.py` | `deferred_behavior` | `power_web_os.application.radar.candidate_discovery.execution` | `0.7.6.4.16` |
| `live_radar_service.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.service` | `compatibility_only` |
| `live_radar_source_cards.py` | `moved_shim` | `power_web_os.application.radar.shared.source_cards` | `compatibility_only` |
| `live_radar_source_risk.py` | `deferred_behavior` | `power_web_os.application.radar.candidate_discovery.sources` | `0.7.6.4.17.3` |
| `live_radar_staged_execution.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.execution` | `compatibility_only` |
| `live_radar_staged_helpers.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.execution` | `compatibility_only` |
| `live_radar_staged_merge.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.execution` | `compatibility_only` |
| `live_radar_staged_support.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.execution` | `compatibility_only` |
| `live_radar_universe.py` | `deferred_behavior` | `power_web_os.application.radar.candidate_discovery.universe` | `0.7.6.4.17.2` |
| `live_radar_useful_budget.py` | `deferred_behavior` | `power_web_os.application.radar.candidate_discovery.execution` | `0.7.6.4.17` |
| `live_radar_web_retrieval.py` | `deferred_behavior` | `power_web_os.application.radar.candidate_discovery.retrieval` | `0.7.6.4.17.1` |
| `radar_search_expansion.py` | `target_for_migration` | `power_web_os.application.radar.candidate_discovery.execution` | `0.7.6.4.16` |
| `radar_search_expansion_models.py` | `target_for_migration` | `power_web_os.application.radar.candidate_discovery.execution` | `0.7.6.4.16` |
| `radar_search_expansion_scheduler.py` | `target_for_migration` | `power_web_os.application.radar.candidate_discovery.execution` | `0.7.6.4.16` |
| `radar_search_expansion_selection.py` | `target_for_migration` | `power_web_os.application.radar.candidate_discovery.execution` | `0.7.6.4.16` |
| `radar_search_expansion_support.py` | `target_for_migration` | `power_web_os.application.radar.candidate_discovery.execution` | `0.7.6.4.16` |
| `signal_monitoring_contracts.py` | `target_for_migration` | `power_web_os.application.radar.signal_monitoring` | `0.7.6.4.18` |
| `signal_monitoring_executor.py` | `target_for_migration` | `power_web_os.application.radar.signal_monitoring` | `0.7.6.4.18` |
| `signal_monitoring_source_strategy.py` | `target_for_migration` | `power_web_os.application.radar.signal_monitoring` | `0.7.6.4.18` |

## Import Policy

Behavior tests and production code must import already moved behavior from
package-owned paths. Legacy moved imports are allowed only in
`tests/test_radar_backend_package_contract.py`, where compatibility is the
behavior under test.

Deferred behavior modules may remain root-level until their owning slice runs,
but they should not import already moved root shims. They should depend on the
package-owned source of truth for moved contracts, planning, source cards,
retrieval-plan, product-source, service, and staged-execution behavior.

## Closure Path

- `0.7.6.4.15`: checkpoint behavior moved to candidate-discovery checkpoints.
- `0.7.6.4.16`: move search-expansion execution/payload behavior to
  candidate-discovery execution.
- `0.7.6.4.17`: decide whether budget contracts belong in `radar/shared`.
- `0.7.6.4.17.1`: move definition and retrieval primitives into shared and
  candidate-discovery retrieval packages.
- `0.7.6.4.17.2`: move candidate universe, retrieved-candidate extraction,
  entity resolution, candidate refs, and cross-source disambiguation.
- `0.7.6.4.17.3`: move extraction contract, diagnostics, normalization,
  collection utilities, pipeline support, and source-risk helpers.
- `0.7.6.4.18`: move signal-monitoring behavior into `radar/signal_monitoring`.
- `0.7.6.4.19`: verify that every root Radar-prefixed file is deleted, a thin
  documented shim, or an explicit remaining exception with its own follow-up.
