"""Declarative migration map from legacy Radar modules to target packages.

This module intentionally does not import legacy `live_radar_*` modules. It is
an inventory for documentation, architecture tests, and future migration slices,
not a runtime facade or re-export layer.
"""

from __future__ import annotations


LEGACY_MODULE_TARGETS: dict[str, str] = {
    "power_web_os.application.live_radar_candidate_refs": (
        "power_web_os.application.radar.candidate_discovery.universe.identity"
    ),
    "power_web_os.application.live_radar_checkpoint_actions": "power_web_os.application.radar.candidate_discovery.checkpoints.recovery",
    "power_web_os.application.live_radar_checkpoint_execution": "power_web_os.application.radar.candidate_discovery.checkpoints.recording",
    "power_web_os.application.live_radar_checkpoints": "power_web_os.application.radar.candidate_discovery.checkpoints",
    "power_web_os.application.live_radar_collection_utils": (
        "power_web_os.application.radar.candidate_discovery.diagnostics.collections"
    ),
    "power_web_os.application.live_radar_contracts": "power_web_os.application.radar.candidate_discovery.contracts",
    "power_web_os.application.live_radar_cross_disambiguation": (
        "power_web_os.application.radar.candidate_discovery.universe.cross_source_disambiguation"
    ),
    "power_web_os.application.live_radar_definition": (
        "power_web_os.application.radar.candidate_discovery.retrieval.definition"
    ),
    "power_web_os.application.live_radar_definition_runtime": "power_web_os.application.radar.candidate_discovery.planning",
    "power_web_os.application.live_radar_discovery_planning": "power_web_os.application.radar.candidate_discovery.planning",
    "power_web_os.application.live_radar_entity_resolution": (
        "power_web_os.application.radar.candidate_discovery.universe.entity_resolution"
    ),
    "power_web_os.application.live_radar_execution_budget": (
        "power_web_os.application.radar.candidate_discovery.execution.task_budget"
    ),
    "power_web_os.application.live_radar_execution_plan": "power_web_os.application.radar.candidate_discovery.planning",
    "power_web_os.application.live_radar_external_budget": "power_web_os.application.radar.shared.budgets",
    "power_web_os.application.live_radar_external_budget_context": (
        "power_web_os.application.radar.shared.budgets.external_context"
    ),
    "power_web_os.application.live_radar_external_budget_reservations": (
        "power_web_os.application.radar.shared.budgets.external_reservations"
    ),
    "power_web_os.application.live_radar_external_budget_settings": (
        "power_web_os.application.radar.shared.budgets.external_settings"
    ),
    "power_web_os.application.live_radar_extraction_contract": (
        "power_web_os.application.radar.candidate_discovery.extraction.contract"
    ),
    "power_web_os.application.live_radar_extraction_diagnostics": (
        "power_web_os.application.radar.candidate_discovery.extraction.diagnostics"
    ),
    "power_web_os.application.live_radar_normalization": (
        "power_web_os.application.radar.candidate_discovery.diagnostics.normalization"
    ),
    "power_web_os.application.live_radar_pipeline_support": (
        "power_web_os.application.radar.candidate_discovery.diagnostics.pipeline_support"
    ),
    "power_web_os.application.live_radar_plan_acceptance": "power_web_os.application.radar.candidate_discovery.planning",
    "power_web_os.application.live_radar_planning_pipeline": "power_web_os.application.radar.candidate_discovery.planning",
    "power_web_os.application.live_radar_product_sources": "power_web_os.application.radar.candidate_discovery.retrieval",
    "power_web_os.application.live_radar_retrieval_plan": "power_web_os.application.radar.candidate_discovery.planning",
    "power_web_os.application.live_radar_retrieved_candidates": (
        "power_web_os.application.radar.candidate_discovery.universe.retrieved_candidates"
    ),
    "power_web_os.application.live_radar_search_expansion_execution": (
        "power_web_os.application.radar.candidate_discovery.search_expansion.targeted_execution"
    ),
    "power_web_os.application.live_radar_search_expansion_payloads": (
        "power_web_os.application.radar.candidate_discovery.search_expansion.payloads"
    ),
    "power_web_os.application.live_radar_service": "power_web_os.application.radar.candidate_discovery.service",
    "power_web_os.application.live_radar_source_cards": "power_web_os.application.radar.shared.source_cards",
    "power_web_os.application.live_radar_source_risk": (
        "power_web_os.application.radar.candidate_discovery.sources.risk"
    ),
    "power_web_os.application.live_radar_staged_execution": "power_web_os.application.radar.candidate_discovery.execution",
    "power_web_os.application.live_radar_staged_helpers": "power_web_os.application.radar.candidate_discovery.execution",
    "power_web_os.application.live_radar_staged_merge": "power_web_os.application.radar.candidate_discovery.execution",
    "power_web_os.application.live_radar_staged_support": "power_web_os.application.radar.candidate_discovery.execution",
    "power_web_os.application.live_radar_universe": "power_web_os.application.radar.candidate_discovery.universe",
    "power_web_os.application.live_radar_useful_budget": (
        "power_web_os.application.radar.candidate_discovery.execution.useful_budget"
    ),
    "power_web_os.application.live_radar_web_retrieval": (
        "power_web_os.application.radar.candidate_discovery.retrieval.web_retrieval"
    ),
    "power_web_os.application.radar_search_expansion": (
        "power_web_os.application.radar.candidate_discovery.search_expansion.service"
    ),
    "power_web_os.application.radar_search_expansion_models": (
        "power_web_os.application.radar.candidate_discovery.search_expansion.models"
    ),
    "power_web_os.application.radar_search_expansion_scheduler": (
        "power_web_os.application.radar.candidate_discovery.search_expansion.scheduler"
    ),
    "power_web_os.application.radar_search_expansion_selection": (
        "power_web_os.application.radar.candidate_discovery.search_expansion.selection"
    ),
    "power_web_os.application.radar_search_expansion_support": (
        "power_web_os.application.radar.candidate_discovery.search_expansion.support"
    ),
    "power_web_os.application.radar_work_scheduler": (
        "power_web_os.application.radar.candidate_discovery.search_expansion.work_scheduler"
    ),
    "power_web_os.application.radar_work_scheduler_metadata": (
        "power_web_os.application.radar.candidate_discovery.search_expansion.work_scheduler_metadata"
    ),
    "power_web_os.application.radar_upstream_disambiguation": (
        "power_web_os.application.radar.candidate_discovery.universe.upstream_disambiguation"
    ),
    "power_web_os.application.signal_monitoring_contracts": (
        "power_web_os.application.radar.signal_monitoring.contracts"
    ),
    "power_web_os.application.signal_monitoring_executor": (
        "power_web_os.application.radar.signal_monitoring.executor"
    ),
    "power_web_os.application.signal_monitoring_source_strategy": (
        "power_web_os.application.radar.signal_monitoring.source_strategy"
    ),
    "power_web_os.application.radar_catalog_seed": (
        "power_web_os.application.radar.configuration.catalog_seed"
    ),
    "power_web_os.application.radar_definition_update": (
        "power_web_os.application.radar.configuration.definition_update"
    ),
    "power_web_os.application.radar_model_profiles": (
        "power_web_os.application.radar.configuration.model_profiles"
    ),
    "power_web_os.application.radar_runtime_model_profiles": (
        "power_web_os.application.radar.configuration.runtime_model_profiles"
    ),
    "power_web_os.application.radar_runtime_settings": (
        "power_web_os.application.radar.configuration.runtime_settings"
    ),
    "power_web_os.application.radar_runtime_config": (
        "power_web_os.application.radar.configuration.runtime_config"
    ),
    "power_web_os.application.radar_records": (
        "power_web_os.application.radar.lifecycle.records"
    ),
    "power_web_os.application.radar_review": (
        "power_web_os.application.radar.lifecycle.review"
    ),
    "power_web_os.application.radar_run_journal": (
        "power_web_os.application.radar.lifecycle.run_journal"
    ),
    "power_web_os.application.radar_technical_trace": (
        "power_web_os.application.radar.lifecycle.technical_trace"
    ),
    "power_web_os.application.radar_output_summary_reconciliation": (
        "power_web_os.application.radar.lifecycle.output_summary_reconciliation"
    ),
    "power_web_os.application.radar_preflight": (
        "power_web_os.application.radar.preflight.service"
    ),
    "power_web_os.application.radar_preflight_connectors": (
        "power_web_os.application.radar.preflight.connectors"
    ),
    "power_web_os.application.radar_lookup_terms": (
        "power_web_os.application.radar.candidate_discovery.sources.lookup_terms"
    ),
    "power_web_os.application.radar_registry_lookup_terms": (
        "power_web_os.application.radar.candidate_discovery.sources.registry_lookup_terms"
    ),
    "power_web_os.application.radar_registry_observation_helpers": (
        "power_web_os.application.radar.candidate_discovery.sources.registry_observation_helpers"
    ),
    "power_web_os.application.radar_source_obligations": (
        "power_web_os.application.radar.candidate_discovery.sources.obligations"
    ),
    "power_web_os.application.radar_source_providers": (
        "power_web_os.application.radar.candidate_discovery.sources.providers"
    ),
    "power_web_os.application.radar_source_registry_helpers": (
        "power_web_os.application.radar.candidate_discovery.sources.registry_helpers"
    ),
}

LEGACY_MODULE_MIGRATION_STATUS: dict[str, str] = {
    module_name: "deferred"
    for module_name in LEGACY_MODULE_TARGETS
}
for module_name in [
    "power_web_os.application.live_radar_checkpoint_actions",
    "power_web_os.application.live_radar_checkpoint_execution",
    "power_web_os.application.live_radar_checkpoints",
    "power_web_os.application.live_radar_candidate_refs",
    "power_web_os.application.live_radar_collection_utils",
    "power_web_os.application.live_radar_contracts",
    "power_web_os.application.live_radar_cross_disambiguation",
    "power_web_os.application.live_radar_definition",
    "power_web_os.application.live_radar_definition_runtime",
    "power_web_os.application.live_radar_discovery_planning",
    "power_web_os.application.live_radar_execution_budget",
    "power_web_os.application.live_radar_execution_plan",
    "power_web_os.application.live_radar_external_budget",
    "power_web_os.application.live_radar_external_budget_context",
    "power_web_os.application.live_radar_external_budget_reservations",
    "power_web_os.application.live_radar_external_budget_settings",
    "power_web_os.application.live_radar_extraction_contract",
    "power_web_os.application.live_radar_extraction_diagnostics",
    "power_web_os.application.live_radar_entity_resolution",
    "power_web_os.application.live_radar_normalization",
    "power_web_os.application.live_radar_pipeline_support",
    "power_web_os.application.live_radar_plan_acceptance",
    "power_web_os.application.live_radar_planning_pipeline",
    "power_web_os.application.live_radar_product_sources",
    "power_web_os.application.live_radar_retrieval_plan",
    "power_web_os.application.live_radar_retrieved_candidates",
    "power_web_os.application.live_radar_search_expansion_execution",
    "power_web_os.application.live_radar_search_expansion_payloads",
    "power_web_os.application.live_radar_service",
    "power_web_os.application.live_radar_source_cards",
    "power_web_os.application.live_radar_source_risk",
    "power_web_os.application.live_radar_staged_execution",
    "power_web_os.application.live_radar_staged_helpers",
    "power_web_os.application.live_radar_staged_merge",
    "power_web_os.application.live_radar_staged_support",
    "power_web_os.application.live_radar_universe",
    "power_web_os.application.live_radar_useful_budget",
    "power_web_os.application.live_radar_web_retrieval",
    "power_web_os.application.radar_search_expansion",
    "power_web_os.application.radar_search_expansion_models",
    "power_web_os.application.radar_search_expansion_scheduler",
    "power_web_os.application.radar_search_expansion_selection",
    "power_web_os.application.radar_search_expansion_support",
    "power_web_os.application.radar_work_scheduler",
    "power_web_os.application.radar_work_scheduler_metadata",
    "power_web_os.application.radar_upstream_disambiguation",
]:
    LEGACY_MODULE_MIGRATION_STATUS[module_name] = "moved"

# Slice 0.7.6.4.19 closes the remaining root namespace debt.
for module_name in LEGACY_MODULE_TARGETS:
    LEGACY_MODULE_MIGRATION_STATUS[module_name] = "moved"

LEGACY_SHIM_MODULES: tuple[str, ...] = tuple(
    module_name
    for module_name, status in LEGACY_MODULE_MIGRATION_STATUS.items()
    if status == "moved"
)

LEGACY_HOTSPOTS: tuple[str, ...] = ()

__all__ = [
    "LEGACY_MODULE_TARGETS",
    "LEGACY_MODULE_MIGRATION_STATUS",
    "LEGACY_SHIM_MODULES",
    "LEGACY_HOTSPOTS",
]
