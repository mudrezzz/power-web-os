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
| `live_radar_candidate_refs.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.universe.identity` | `compatibility_only` |
| `live_radar_checkpoint_actions.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.checkpoints.recovery` | `compatibility_only` |
| `live_radar_checkpoint_execution.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.checkpoints.recording` | `compatibility_only` |
| `live_radar_checkpoints.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.checkpoints` | `compatibility_only` |
| `live_radar_collection_utils.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.diagnostics.collections` | `compatibility_only` |
| `live_radar_contracts.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.contracts` | `compatibility_only` |
| `live_radar_cross_disambiguation.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.universe.cross_source_disambiguation` | `compatibility_only` |
| `live_radar_definition.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.retrieval.definition` | `compatibility_only` |
| `live_radar_definition_runtime.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.planning` | `compatibility_only` |
| `live_radar_discovery_planning.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.planning` | `compatibility_only` |
| `live_radar_entity_resolution.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.universe.entity_resolution` | `compatibility_only` |
| `live_radar_execution_budget.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.execution.task_budget` | `compatibility_only` |
| `live_radar_execution_plan.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.planning` | `compatibility_only` |
| `live_radar_external_budget.py` | `moved_shim` | `power_web_os.application.radar.shared.budgets` | `compatibility_only` |
| `live_radar_external_budget_context.py` | `moved_shim` | `power_web_os.application.radar.shared.budgets.external_context` | `compatibility_only` |
| `live_radar_external_budget_reservations.py` | `moved_shim` | `power_web_os.application.radar.shared.budgets.external_reservations` | `compatibility_only` |
| `live_radar_external_budget_settings.py` | `moved_shim` | `power_web_os.application.radar.shared.budgets.external_settings` | `compatibility_only` |
| `live_radar_extraction_contract.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.extraction.contract` | `compatibility_only` |
| `live_radar_extraction_diagnostics.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.extraction.diagnostics` | `compatibility_only` |
| `live_radar_normalization.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.diagnostics.normalization` | `compatibility_only` |
| `live_radar_pipeline_support.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.diagnostics.pipeline_support` | `compatibility_only` |
| `live_radar_plan_acceptance.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.planning` | `compatibility_only` |
| `live_radar_planning_pipeline.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.planning` | `compatibility_only` |
| `live_radar_product_sources.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.retrieval` | `compatibility_only` |
| `live_radar_retrieval_plan.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.planning` | `compatibility_only` |
| `live_radar_retrieved_candidates.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.universe.retrieved_candidates` | `compatibility_only` |
| `live_radar_search_expansion_execution.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.search_expansion.targeted_execution` | `compatibility_only` |
| `live_radar_search_expansion_payloads.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.search_expansion.payloads` | `compatibility_only` |
| `live_radar_service.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.service` | `compatibility_only` |
| `live_radar_source_cards.py` | `moved_shim` | `power_web_os.application.radar.shared.source_cards` | `compatibility_only` |
| `live_radar_source_risk.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.sources.risk` | `compatibility_only` |
| `live_radar_staged_execution.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.execution` | `compatibility_only` |
| `live_radar_staged_helpers.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.execution` | `compatibility_only` |
| `live_radar_staged_merge.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.execution` | `compatibility_only` |
| `live_radar_staged_support.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.execution` | `compatibility_only` |
| `live_radar_universe.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.universe` | `compatibility_only` |
| `live_radar_useful_budget.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.execution.useful_budget` | `compatibility_only` |
| `live_radar_web_retrieval.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.retrieval.web_retrieval` | `compatibility_only` |
| `radar_search_expansion.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.search_expansion.service` | `compatibility_only` |
| `radar_search_expansion_models.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.search_expansion.models` | `compatibility_only` |
| `radar_search_expansion_scheduler.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.search_expansion.scheduler` | `compatibility_only` |
| `radar_search_expansion_selection.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.search_expansion.selection` | `compatibility_only` |
| `radar_search_expansion_support.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.search_expansion.support` | `compatibility_only` |
| `radar_upstream_disambiguation.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.universe.upstream_disambiguation` | `compatibility_only` |
| `radar_work_scheduler.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.search_expansion.work_scheduler` | `compatibility_only` |
| `radar_work_scheduler_metadata.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.search_expansion.work_scheduler_metadata` | `compatibility_only` |
| `radar_catalog_seed.py` | `moved_shim` | `power_web_os.application.radar.configuration.catalog_seed` | `compatibility_only` |
| `radar_definition_update.py` | `moved_shim` | `power_web_os.application.radar.configuration.definition_update` | `compatibility_only` |
| `radar_lookup_terms.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.sources.lookup_terms` | `compatibility_only` |
| `radar_model_profiles.py` | `moved_shim` | `power_web_os.application.radar.configuration.model_profiles` | `compatibility_only` |
| `radar_output_summary_reconciliation.py` | `moved_shim` | `power_web_os.application.radar.lifecycle.output_summary_reconciliation` | `compatibility_only` |
| `radar_preflight.py` | `moved_shim` | `power_web_os.application.radar.preflight.service` | `compatibility_only` |
| `radar_preflight_connectors.py` | `moved_shim` | `power_web_os.application.radar.preflight.connectors` | `compatibility_only` |
| `radar_records.py` | `moved_shim` | `power_web_os.application.radar.lifecycle.records` | `compatibility_only` |
| `radar_registry_lookup_terms.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.sources.registry_lookup_terms` | `compatibility_only` |
| `radar_registry_observation_helpers.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.sources.registry_observation_helpers` | `compatibility_only` |
| `radar_review.py` | `moved_shim` | `power_web_os.application.radar.lifecycle.review` | `compatibility_only` |
| `radar_run_journal.py` | `moved_shim` | `power_web_os.application.radar.lifecycle.run_journal` | `compatibility_only` |
| `radar_runtime_config.py` | `moved_shim` | `power_web_os.application.radar.configuration.runtime_config` | `compatibility_only` |
| `radar_runtime_model_profiles.py` | `moved_shim` | `power_web_os.application.radar.configuration.runtime_model_profiles` | `compatibility_only` |
| `radar_runtime_settings.py` | `moved_shim` | `power_web_os.application.radar.configuration.runtime_settings` | `compatibility_only` |
| `radar_source_obligations.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.sources.obligations` | `compatibility_only` |
| `radar_source_providers.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.sources.providers` | `compatibility_only` |
| `radar_source_registry_helpers.py` | `moved_shim` | `power_web_os.application.radar.candidate_discovery.sources.registry_helpers` | `compatibility_only` |
| `radar_technical_trace.py` | `moved_shim` | `power_web_os.application.radar.lifecycle.technical_trace` | `compatibility_only` |
| `signal_monitoring_contracts.py` | `moved_shim` | `power_web_os.application.radar.signal_monitoring.contracts` | `compatibility_only` |
| `signal_monitoring_executor.py` | `moved_shim` | `power_web_os.application.radar.signal_monitoring.executor` | `compatibility_only` |
| `signal_monitoring_source_strategy.py` | `moved_shim` | `power_web_os.application.radar.signal_monitoring.source_strategy` | `compatibility_only` |

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
- `0.7.6.4.16`: search-expansion and work-admission behavior moved to
  candidate-discovery search expansion.
- `0.7.6.4.17`: provider-level external-call budgets moved to
  `radar/shared/budgets`; candidate-discovery task/useful budgets moved to
  `radar/candidate_discovery/execution`.
- `0.7.6.4.17.1`: live mini Radar definition builders and provider-neutral
  web retrieval contracts moved to candidate-discovery retrieval modules.
- `0.7.6.4.17.2`: candidate universe, retrieved-candidate extraction,
  entity resolution, candidate refs, and upstream/cross-source disambiguation
  moved to candidate-discovery universe modules.
- `0.7.6.4.17.3`: extraction contract, diagnostics, normalization,
  collection utilities, pipeline support, and source-risk helpers moved to
  package-owned candidate-discovery modules.
- `0.7.6.4.18`: signal-monitoring contracts, source strategy, task planning,
  budgets, payload parsing, projection, and recorded executor moved to
  `radar/signal_monitoring`.
- `0.7.6.4.19`: all remaining records, lifecycle, configuration, preflight,
  source-policy, lookup, registry, and provider behavior moved to package-owned
  modules. Every root Radar-prefixed file is now a documented compatibility
  shim protected by architecture tests.
