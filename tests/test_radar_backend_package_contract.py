from __future__ import annotations

import ast
import importlib
from pathlib import Path


NEW_RADAR_PACKAGES = [
    "power_web_os.application.radar",
    "power_web_os.application.radar.shared",
    "power_web_os.application.radar.shared.budgets",
    "power_web_os.application.radar.shared.budgets.external_budget",
    "power_web_os.application.radar.shared.budgets.external_context",
    "power_web_os.application.radar.shared.budgets.external_models",
    "power_web_os.application.radar.shared.budgets.external_reservations",
    "power_web_os.application.radar.shared.budgets.external_settings",
    "power_web_os.application.radar.candidate_discovery",
    "power_web_os.application.radar.candidate_discovery.planning",
    "power_web_os.application.radar.candidate_discovery.retrieval",
    "power_web_os.application.radar.candidate_discovery.extraction",
    "power_web_os.application.radar.candidate_discovery.sources",
    "power_web_os.application.radar.candidate_discovery.universe",
    "power_web_os.application.radar.candidate_discovery.checkpoints",
    "power_web_os.application.radar.candidate_discovery.checkpoints.models",
    "power_web_os.application.radar.candidate_discovery.checkpoints.policy",
    "power_web_os.application.radar.candidate_discovery.checkpoints.recording",
    "power_web_os.application.radar.candidate_discovery.checkpoints.recovery",
    "power_web_os.application.radar.candidate_discovery.checkpoints.recovery_salvage",
    "power_web_os.application.radar.candidate_discovery.search_expansion",
    "power_web_os.application.radar.candidate_discovery.search_expansion.models",
    "power_web_os.application.radar.candidate_discovery.search_expansion.payloads",
    "power_web_os.application.radar.candidate_discovery.search_expansion.scheduler",
    "power_web_os.application.radar.candidate_discovery.search_expansion.selection",
    "power_web_os.application.radar.candidate_discovery.search_expansion.service",
    "power_web_os.application.radar.candidate_discovery.search_expansion.support",
    "power_web_os.application.radar.candidate_discovery.search_expansion.target_merge",
    "power_web_os.application.radar.candidate_discovery.search_expansion.targeted_execution",
    "power_web_os.application.radar.candidate_discovery.search_expansion.work_scheduler",
    "power_web_os.application.radar.candidate_discovery.search_expansion.work_scheduler_metadata",
    "power_web_os.application.radar.candidate_discovery.execution",
    "power_web_os.application.radar.candidate_discovery.diagnostics",
    "power_web_os.application.radar.signal_monitoring",
    "power_web_os.application.radar.power_web_discovery",
    "power_web_os.application.radar.shared.source_cards",
    "power_web_os.application.radar.candidate_discovery.contracts",
    "power_web_os.application.radar.candidate_discovery.planning.definition_runtime",
    "power_web_os.application.radar.candidate_discovery.planning.discovery_planning",
    "power_web_os.application.radar.candidate_discovery.planning.execution_plan",
    "power_web_os.application.radar.candidate_discovery.planning.plan_acceptance",
    "power_web_os.application.radar.candidate_discovery.planning.planning_pipeline",
    "power_web_os.application.radar.candidate_discovery.planning.retrieval_plan",
    "power_web_os.application.radar.candidate_discovery.retrieval.definition",
    "power_web_os.application.radar.candidate_discovery.retrieval.product_sources",
    "power_web_os.application.radar.candidate_discovery.retrieval.web_retrieval",
    "power_web_os.application.radar.candidate_discovery.extraction.contract",
    "power_web_os.application.radar.candidate_discovery.extraction.diagnostics",
    "power_web_os.application.radar.candidate_discovery.extraction.recovery",
    "power_web_os.application.radar.candidate_discovery.diagnostics.collections",
    "power_web_os.application.radar.candidate_discovery.diagnostics.contract_validation",
    "power_web_os.application.radar.candidate_discovery.diagnostics.normalization",
    "power_web_os.application.radar.candidate_discovery.diagnostics.pipeline_support",
    "power_web_os.application.radar.candidate_discovery.diagnostics.upstream_projection",
    "power_web_os.application.radar.candidate_discovery.sources.risk",
    "power_web_os.application.radar.candidate_discovery.universe.admission",
    "power_web_os.application.radar.candidate_discovery.universe.coverage",
    "power_web_os.application.radar.candidate_discovery.universe.cross_source_disambiguation",
    "power_web_os.application.radar.candidate_discovery.universe.entity_resolution",
    "power_web_os.application.radar.candidate_discovery.universe.gaps",
    "power_web_os.application.radar.candidate_discovery.universe.identity",
    "power_web_os.application.radar.candidate_discovery.universe.metadata",
    "power_web_os.application.radar.candidate_discovery.universe.projection",
    "power_web_os.application.radar.candidate_discovery.universe.retrieved_candidates",
    "power_web_os.application.radar.candidate_discovery.universe.signal_scope",
    "power_web_os.application.radar.candidate_discovery.universe.upstream_disambiguation",
    "power_web_os.application.radar.signal_monitoring.contracts",
    "power_web_os.application.radar.signal_monitoring.source_strategy",
    "power_web_os.application.radar.signal_monitoring.planning",
    "power_web_os.application.radar.signal_monitoring.budgets",
    "power_web_os.application.radar.signal_monitoring.payloads",
    "power_web_os.application.radar.signal_monitoring.projection",
    "power_web_os.application.radar.signal_monitoring.executor",
    "power_web_os.application.radar.signal_monitoring.input_assembler",
    "power_web_os.application.radar.signal_monitoring.artifact",
    "power_web_os.application.radar.signal_monitoring.runtime",
    "power_web_os.application.radar.signal_monitoring.service_factory",
    "power_web_os.application.radar.candidate_discovery.execution.coverage",
    "power_web_os.application.radar.candidate_discovery.execution.context",
    "power_web_os.application.radar.candidate_discovery.execution.discovery",
    "power_web_os.application.radar.candidate_discovery.execution.expansion",
    "power_web_os.application.radar.candidate_discovery.execution.expansion_diagnostics",
    "power_web_os.application.radar.candidate_discovery.execution.finalization",
    "power_web_os.application.radar.candidate_discovery.execution.finalization_metadata",
    "power_web_os.application.radar.candidate_discovery.execution.finalization_signals",
    "power_web_os.application.radar.candidate_discovery.execution.finalization_universe",
    "power_web_os.application.radar.candidate_discovery.execution.gates",
    "power_web_os.application.radar.candidate_discovery.execution.merge",
    "power_web_os.application.radar.candidate_discovery.execution.orchestrator",
    "power_web_os.application.radar.candidate_discovery.execution.options",
    "power_web_os.application.radar.candidate_discovery.execution.projection",
    "power_web_os.application.radar.candidate_discovery.execution.public_surface",
    "power_web_os.application.radar.candidate_discovery.execution.reconciliation",
    "power_web_os.application.radar.candidate_discovery.execution.signal_modes",
    "power_web_os.application.radar.candidate_discovery.execution.service_contracts",
    "power_web_os.application.radar.candidate_discovery.execution.signals",
    "power_web_os.application.radar.candidate_discovery.execution.state",
    "power_web_os.application.radar.candidate_discovery.execution.task_budget",
    "power_web_os.application.radar.candidate_discovery.execution.task_runner",
    "power_web_os.application.radar.candidate_discovery.execution.task_runner_payloads",
    "power_web_os.application.radar.candidate_discovery.execution.useful_budget",
    "power_web_os.application.radar.candidate_discovery.service",
    "power_web_os.application.radar.candidate_discovery.service_budget",
    "power_web_os.application.radar.candidate_discovery.service_context",
    "power_web_os.application.radar.candidate_discovery.service_events",
    "power_web_os.application.radar.candidate_discovery.service_factory",
    "power_web_os.application.radar.candidate_discovery.diagnostics.live_run_artifact",
]

LEGACY_KEY_MODULES = [
    "power_web_os.application.live_radar_contracts",
    "power_web_os.application.live_radar_checkpoint_actions",
    "power_web_os.application.live_radar_checkpoint_execution",
    "power_web_os.application.live_radar_checkpoints",
    "power_web_os.application.live_radar_candidate_refs",
    "power_web_os.application.live_radar_collection_utils",
    "power_web_os.application.live_radar_source_cards",
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
    "power_web_os.application.live_radar_source_risk",
    "power_web_os.application.live_radar_staged_execution",
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
    "power_web_os.application.signal_monitoring_contracts",
    "power_web_os.application.signal_monitoring_executor",
    "power_web_os.application.signal_monitoring_source_strategy",
]

MOVED_LEGACY_SHIMS = [
    "live_radar_contracts.py",
    "live_radar_checkpoint_actions.py",
    "live_radar_checkpoint_execution.py",
    "live_radar_checkpoints.py",
    "live_radar_candidate_refs.py",
    "live_radar_collection_utils.py",
    "live_radar_source_cards.py",
    "live_radar_cross_disambiguation.py",
    "live_radar_definition.py",
    "live_radar_definition_runtime.py",
    "live_radar_discovery_planning.py",
    "live_radar_execution_budget.py",
    "live_radar_execution_plan.py",
    "live_radar_external_budget.py",
    "live_radar_external_budget_context.py",
    "live_radar_external_budget_reservations.py",
    "live_radar_external_budget_settings.py",
    "live_radar_extraction_contract.py",
    "live_radar_extraction_diagnostics.py",
    "live_radar_entity_resolution.py",
    "live_radar_normalization.py",
    "live_radar_pipeline_support.py",
    "live_radar_plan_acceptance.py",
    "live_radar_planning_pipeline.py",
    "live_radar_product_sources.py",
    "live_radar_retrieval_plan.py",
    "live_radar_retrieved_candidates.py",
    "live_radar_search_expansion_execution.py",
    "live_radar_search_expansion_payloads.py",
    "live_radar_service.py",
    "live_radar_source_risk.py",
    "live_radar_staged_execution.py",
    "live_radar_staged_helpers.py",
    "live_radar_staged_merge.py",
    "live_radar_staged_support.py",
    "live_radar_universe.py",
    "live_radar_useful_budget.py",
    "live_radar_web_retrieval.py",
    "radar_search_expansion.py",
    "radar_search_expansion_models.py",
    "radar_search_expansion_scheduler.py",
    "radar_search_expansion_selection.py",
    "radar_search_expansion_support.py",
    "radar_work_scheduler.py",
    "radar_work_scheduler_metadata.py",
    "radar_upstream_disambiguation.py",
    "signal_monitoring_contracts.py",
    "signal_monitoring_executor.py",
    "signal_monitoring_source_strategy.py",
]


def test_new_radar_packages_import_without_runtime_side_effects() -> None:
    for module_name in NEW_RADAR_PACKAGES:
        module = importlib.import_module(module_name)
        assert module.__name__ == module_name


def test_key_legacy_radar_modules_still_import() -> None:
    for module_name in LEGACY_KEY_MODULES:
        module = importlib.import_module(module_name)
        assert module.__name__ == module_name


def test_candidate_discovery_compatibility_map_is_declarative() -> None:
    module = importlib.import_module("power_web_os.application.radar.candidate_discovery.compatibility")

    assert module.LEGACY_MODULE_TARGETS["power_web_os.application.live_radar_staged_execution"] == (
        "power_web_os.application.radar.candidate_discovery.execution"
    )
    assert module.LEGACY_MODULE_TARGETS["power_web_os.application.live_radar_service"] == (
        "power_web_os.application.radar.candidate_discovery.service"
    )
    assert module.LEGACY_MODULE_TARGETS["power_web_os.application.live_radar_contracts"] == (
        "power_web_os.application.radar.candidate_discovery.contracts"
    )
    assert module.LEGACY_MODULE_TARGETS["power_web_os.application.live_radar_candidate_refs"] == (
        "power_web_os.application.radar.candidate_discovery.universe.identity"
    )
    assert module.LEGACY_MODULE_TARGETS["power_web_os.application.live_radar_collection_utils"] == (
        "power_web_os.application.radar.candidate_discovery.diagnostics.collections"
    )
    assert module.LEGACY_MODULE_TARGETS["power_web_os.application.live_radar_cross_disambiguation"] == (
        "power_web_os.application.radar.candidate_discovery.universe.cross_source_disambiguation"
    )
    assert module.LEGACY_MODULE_TARGETS["power_web_os.application.live_radar_entity_resolution"] == (
        "power_web_os.application.radar.candidate_discovery.universe.entity_resolution"
    )
    assert module.LEGACY_MODULE_TARGETS["power_web_os.application.live_radar_retrieved_candidates"] == (
        "power_web_os.application.radar.candidate_discovery.universe.retrieved_candidates"
    )
    assert module.LEGACY_MODULE_TARGETS["power_web_os.application.live_radar_universe"] == (
        "power_web_os.application.radar.candidate_discovery.universe"
    )
    assert module.LEGACY_MODULE_TARGETS["power_web_os.application.radar_upstream_disambiguation"] == (
        "power_web_os.application.radar.candidate_discovery.universe.upstream_disambiguation"
    )
    assert module.LEGACY_MODULE_TARGETS["power_web_os.application.live_radar_checkpoints"] == (
        "power_web_os.application.radar.candidate_discovery.checkpoints"
    )
    assert module.LEGACY_MODULE_TARGETS["power_web_os.application.live_radar_checkpoint_execution"] == (
        "power_web_os.application.radar.candidate_discovery.checkpoints.recording"
    )
    assert module.LEGACY_MODULE_TARGETS["power_web_os.application.live_radar_checkpoint_actions"] == (
        "power_web_os.application.radar.candidate_discovery.checkpoints.recovery"
    )
    assert module.LEGACY_MODULE_TARGETS["power_web_os.application.live_radar_source_cards"] == (
        "power_web_os.application.radar.shared.source_cards"
    )
    assert module.LEGACY_MODULE_TARGETS["power_web_os.application.live_radar_definition"] == (
        "power_web_os.application.radar.candidate_discovery.retrieval.definition"
    )
    assert module.LEGACY_MODULE_TARGETS["power_web_os.application.live_radar_execution_budget"] == (
        "power_web_os.application.radar.candidate_discovery.execution.task_budget"
    )
    assert module.LEGACY_MODULE_TARGETS["power_web_os.application.live_radar_external_budget"] == (
        "power_web_os.application.radar.shared.budgets"
    )
    assert module.LEGACY_MODULE_TARGETS["power_web_os.application.live_radar_external_budget_context"] == (
        "power_web_os.application.radar.shared.budgets.external_context"
    )
    assert module.LEGACY_MODULE_TARGETS["power_web_os.application.live_radar_external_budget_reservations"] == (
        "power_web_os.application.radar.shared.budgets.external_reservations"
    )
    assert module.LEGACY_MODULE_TARGETS["power_web_os.application.live_radar_external_budget_settings"] == (
        "power_web_os.application.radar.shared.budgets.external_settings"
    )
    assert module.LEGACY_MODULE_TARGETS["power_web_os.application.live_radar_extraction_contract"] == (
        "power_web_os.application.radar.candidate_discovery.extraction.contract"
    )
    assert module.LEGACY_MODULE_TARGETS["power_web_os.application.live_radar_extraction_diagnostics"] == (
        "power_web_os.application.radar.candidate_discovery.extraction.diagnostics"
    )
    assert module.LEGACY_MODULE_TARGETS["power_web_os.application.live_radar_normalization"] == (
        "power_web_os.application.radar.candidate_discovery.diagnostics.normalization"
    )
    assert module.LEGACY_MODULE_TARGETS["power_web_os.application.live_radar_pipeline_support"] == (
        "power_web_os.application.radar.candidate_discovery.diagnostics.pipeline_support"
    )
    assert module.LEGACY_MODULE_TARGETS["power_web_os.application.live_radar_useful_budget"] == (
        "power_web_os.application.radar.candidate_discovery.execution.useful_budget"
    )
    assert module.LEGACY_MODULE_TARGETS["power_web_os.application.live_radar_web_retrieval"] == (
        "power_web_os.application.radar.candidate_discovery.retrieval.web_retrieval"
    )
    assert module.LEGACY_MODULE_TARGETS["power_web_os.application.live_radar_search_expansion_execution"] == (
        "power_web_os.application.radar.candidate_discovery.search_expansion.targeted_execution"
    )
    assert module.LEGACY_MODULE_TARGETS["power_web_os.application.live_radar_search_expansion_payloads"] == (
        "power_web_os.application.radar.candidate_discovery.search_expansion.payloads"
    )
    assert module.LEGACY_MODULE_TARGETS["power_web_os.application.live_radar_source_risk"] == (
        "power_web_os.application.radar.candidate_discovery.sources.risk"
    )
    assert module.LEGACY_MODULE_TARGETS["power_web_os.application.radar_search_expansion"] == (
        "power_web_os.application.radar.candidate_discovery.search_expansion.service"
    )
    assert module.LEGACY_MODULE_TARGETS["power_web_os.application.radar_work_scheduler"] == (
        "power_web_os.application.radar.candidate_discovery.search_expansion.work_scheduler"
    )
    assert module.LEGACY_MODULE_MIGRATION_STATUS["power_web_os.application.live_radar_checkpoint_actions"] == "moved"
    assert module.LEGACY_MODULE_MIGRATION_STATUS["power_web_os.application.live_radar_checkpoint_execution"] == "moved"
    assert module.LEGACY_MODULE_MIGRATION_STATUS["power_web_os.application.live_radar_checkpoints"] == "moved"
    assert module.LEGACY_MODULE_MIGRATION_STATUS["power_web_os.application.live_radar_candidate_refs"] == "moved"
    assert module.LEGACY_MODULE_MIGRATION_STATUS["power_web_os.application.live_radar_collection_utils"] == "moved"
    assert module.LEGACY_MODULE_MIGRATION_STATUS["power_web_os.application.live_radar_contracts"] == "moved"
    assert module.LEGACY_MODULE_MIGRATION_STATUS["power_web_os.application.live_radar_cross_disambiguation"] == "moved"
    assert module.LEGACY_MODULE_MIGRATION_STATUS["power_web_os.application.live_radar_definition"] == "moved"
    assert module.LEGACY_MODULE_MIGRATION_STATUS["power_web_os.application.live_radar_entity_resolution"] == "moved"
    assert module.LEGACY_MODULE_MIGRATION_STATUS["power_web_os.application.live_radar_execution_budget"] == "moved"
    assert module.LEGACY_MODULE_MIGRATION_STATUS["power_web_os.application.live_radar_external_budget"] == "moved"
    assert module.LEGACY_MODULE_MIGRATION_STATUS["power_web_os.application.live_radar_external_budget_context"] == "moved"
    assert module.LEGACY_MODULE_MIGRATION_STATUS["power_web_os.application.live_radar_external_budget_reservations"] == "moved"
    assert module.LEGACY_MODULE_MIGRATION_STATUS["power_web_os.application.live_radar_external_budget_settings"] == "moved"
    assert module.LEGACY_MODULE_MIGRATION_STATUS["power_web_os.application.live_radar_extraction_contract"] == "moved"
    assert module.LEGACY_MODULE_MIGRATION_STATUS["power_web_os.application.live_radar_extraction_diagnostics"] == "moved"
    assert module.LEGACY_MODULE_MIGRATION_STATUS["power_web_os.application.live_radar_search_expansion_execution"] == "moved"
    assert module.LEGACY_MODULE_MIGRATION_STATUS["power_web_os.application.live_radar_normalization"] == "moved"
    assert module.LEGACY_MODULE_MIGRATION_STATUS["power_web_os.application.live_radar_pipeline_support"] == "moved"
    assert module.LEGACY_MODULE_MIGRATION_STATUS["power_web_os.application.live_radar_search_expansion_payloads"] == "moved"
    assert module.LEGACY_MODULE_MIGRATION_STATUS["power_web_os.application.live_radar_retrieved_candidates"] == "moved"
    assert module.LEGACY_MODULE_MIGRATION_STATUS["power_web_os.application.live_radar_service"] == "moved"
    assert module.LEGACY_MODULE_MIGRATION_STATUS["power_web_os.application.live_radar_source_risk"] == "moved"
    assert module.LEGACY_MODULE_MIGRATION_STATUS["power_web_os.application.live_radar_staged_execution"] == "moved"
    assert module.LEGACY_MODULE_MIGRATION_STATUS["power_web_os.application.live_radar_universe"] == "moved"
    assert module.LEGACY_MODULE_MIGRATION_STATUS["power_web_os.application.live_radar_useful_budget"] == "moved"
    assert module.LEGACY_MODULE_MIGRATION_STATUS["power_web_os.application.live_radar_web_retrieval"] == "moved"
    assert module.LEGACY_MODULE_MIGRATION_STATUS["power_web_os.application.radar_search_expansion"] == "moved"
    assert module.LEGACY_MODULE_MIGRATION_STATUS["power_web_os.application.radar_work_scheduler"] == "moved"
    assert module.LEGACY_MODULE_MIGRATION_STATUS["power_web_os.application.radar_upstream_disambiguation"] == "moved"
    assert "power_web_os.application.live_radar_service" not in module.LEGACY_HOTSPOTS
    assert "power_web_os.application.live_radar_staged_execution" not in module.LEGACY_HOTSPOTS
    assert "power_web_os.application.live_radar_checkpoint_actions" not in module.LEGACY_HOTSPOTS
    assert "power_web_os.application.live_radar_search_expansion_execution" not in module.LEGACY_HOTSPOTS

    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "import power_web_os.application.live_radar" not in source
    assert "from power_web_os.application.live_radar" not in source


def test_moved_legacy_modules_are_thin_shims() -> None:
    root = Path("src/power_web_os/application")
    for filename in MOVED_LEGACY_SHIMS:
        source = (root / filename).read_text(encoding="utf-8")
        assert "Source of truth:" in source
        assert "import *" in source
        assert len(source.splitlines()) <= 8


def test_live_radar_service_old_and_new_import_paths_are_compatible() -> None:
    legacy = importlib.import_module("power_web_os.application.live_radar_service")
    package_owned = importlib.import_module("power_web_os.application.radar.candidate_discovery.service")

    assert legacy.LiveRadarRunService is package_owned.LiveRadarRunService


def test_budget_old_and_new_import_paths_are_compatible() -> None:
    legacy_external = importlib.import_module("power_web_os.application.live_radar_external_budget")
    shared_external = importlib.import_module("power_web_os.application.radar.shared.budgets")
    legacy_context = importlib.import_module("power_web_os.application.live_radar_external_budget_context")
    shared_context = importlib.import_module("power_web_os.application.radar.shared.budgets.external_context")
    legacy_task = importlib.import_module("power_web_os.application.live_radar_execution_budget")
    package_task = importlib.import_module("power_web_os.application.radar.candidate_discovery.execution.task_budget")
    legacy_useful = importlib.import_module("power_web_os.application.live_radar_useful_budget")
    package_useful = importlib.import_module("power_web_os.application.radar.candidate_discovery.execution.useful_budget")

    assert legacy_external.RadarExternalCallBudget is shared_external.RadarExternalCallBudget
    assert legacy_external.RadarExternalCallBudgetSettings is shared_external.RadarExternalCallBudgetSettings
    assert legacy_context.reserve_external_call is shared_context.reserve_external_call
    assert legacy_task.RadarExecutionBudget is package_task.RadarExecutionBudget
    assert legacy_task.budget_settings_from_context is package_task.budget_settings_from_context
    assert legacy_useful.UsefulResultBudget is package_useful.UsefulResultBudget
    assert legacy_useful.run_task_with_useful_retries is package_useful.run_task_with_useful_retries


def test_definition_and_retrieval_old_and_new_import_paths_are_compatible() -> None:
    legacy_definition = importlib.import_module("power_web_os.application.live_radar_definition")
    package_definition = importlib.import_module(
        "power_web_os.application.radar.candidate_discovery.retrieval.definition"
    )
    legacy_retrieval = importlib.import_module("power_web_os.application.live_radar_web_retrieval")
    package_retrieval = importlib.import_module(
        "power_web_os.application.radar.candidate_discovery.retrieval.web_retrieval"
    )

    assert legacy_definition.build_live_mini_radar_definition is (
        package_definition.build_live_mini_radar_definition
    )
    assert legacy_definition.build_live_mini_radar_search_plan is (
        package_definition.build_live_mini_radar_search_plan
    )
    assert legacy_definition.build_live_mini_radar_search_plan_artifact is (
        package_definition.build_live_mini_radar_search_plan_artifact
    )
    assert legacy_retrieval.RadarWebRetrievalRequest is package_retrieval.RadarWebRetrievalRequest
    assert legacy_retrieval.RadarRetrievedSource is package_retrieval.RadarRetrievedSource
    assert legacy_retrieval.RadarRetrievalSourceOutcome is package_retrieval.RadarRetrievalSourceOutcome
    assert legacy_retrieval.RadarWebRetrievalResult is package_retrieval.RadarWebRetrievalResult
    assert legacy_retrieval.RadarWebRetrievalProvider is package_retrieval.RadarWebRetrievalProvider
    assert legacy_retrieval.RecordedRadarWebRetrievalProvider is (
        package_retrieval.RecordedRadarWebRetrievalProvider
    )
    assert legacy_retrieval.retrieval_request_from_search_plan is (
        package_retrieval.retrieval_request_from_search_plan
    )


def test_extraction_diagnostics_old_and_new_import_paths_are_compatible() -> None:
    legacy_contract = importlib.import_module("power_web_os.application.live_radar_extraction_contract")
    package_contract = importlib.import_module(
        "power_web_os.application.radar.candidate_discovery.extraction.contract"
    )
    legacy_diagnostics = importlib.import_module("power_web_os.application.live_radar_extraction_diagnostics")
    package_diagnostics = importlib.import_module(
        "power_web_os.application.radar.candidate_discovery.extraction.diagnostics"
    )
    legacy_normalization = importlib.import_module("power_web_os.application.live_radar_normalization")
    package_normalization = importlib.import_module(
        "power_web_os.application.radar.candidate_discovery.diagnostics.normalization"
    )
    legacy_collections = importlib.import_module("power_web_os.application.live_radar_collection_utils")
    package_collections = importlib.import_module(
        "power_web_os.application.radar.candidate_discovery.diagnostics.collections"
    )
    legacy_pipeline_support = importlib.import_module("power_web_os.application.live_radar_pipeline_support")
    package_pipeline_support = importlib.import_module(
        "power_web_os.application.radar.candidate_discovery.diagnostics.pipeline_support"
    )
    legacy_source_risk = importlib.import_module("power_web_os.application.live_radar_source_risk")
    package_source_risk = importlib.import_module(
        "power_web_os.application.radar.candidate_discovery.sources.risk"
    )

    assert legacy_contract.ExtractionValidationIssue is package_contract.ExtractionValidationIssue
    assert legacy_contract.ExtractionRepairResult is package_contract.ExtractionRepairResult
    assert legacy_contract.validate_and_repair_extraction_payload is (
        package_contract.validate_and_repair_extraction_payload
    )
    assert legacy_contract.extraction_validation_state is package_contract.extraction_validation_state
    assert legacy_diagnostics.extraction_contract_state is package_diagnostics.extraction_contract_state
    assert legacy_diagnostics.extraction_validation_event is package_diagnostics.extraction_validation_event
    assert legacy_normalization.normalize_live_candidate is package_normalization.normalize_live_candidate
    assert legacy_normalization.validate_live_radar_qualification_contract is (
        package_normalization.validate_live_radar_qualification_contract
    )
    assert legacy_collections.dedupe_sources is package_collections.dedupe_sources
    assert legacy_collections.rank_candidates is package_collections.rank_candidates
    assert legacy_pipeline_support.trace_pipeline_step is package_pipeline_support.trace_pipeline_step
    assert legacy_pipeline_support.planned_event_type is package_pipeline_support.planned_event_type
    assert legacy_source_risk.source_supports_evidence is package_source_risk.source_supports_evidence
    assert legacy_source_risk.refs_have_verification_risk is package_source_risk.refs_have_verification_risk


def test_universe_old_and_new_import_paths_are_compatible() -> None:
    legacy_refs = importlib.import_module("power_web_os.application.live_radar_candidate_refs")
    package_identity = importlib.import_module(
        "power_web_os.application.radar.candidate_discovery.universe.identity"
    )
    legacy_universe = importlib.import_module("power_web_os.application.live_radar_universe")
    package_universe = importlib.import_module("power_web_os.application.radar.candidate_discovery.universe")
    legacy_retrieved = importlib.import_module("power_web_os.application.live_radar_retrieved_candidates")
    package_retrieved = importlib.import_module(
        "power_web_os.application.radar.candidate_discovery.universe.retrieved_candidates"
    )
    legacy_resolution = importlib.import_module("power_web_os.application.live_radar_entity_resolution")
    package_resolution = importlib.import_module(
        "power_web_os.application.radar.candidate_discovery.universe.entity_resolution"
    )
    legacy_cross = importlib.import_module("power_web_os.application.live_radar_cross_disambiguation")
    package_cross = importlib.import_module(
        "power_web_os.application.radar.candidate_discovery.universe.cross_source_disambiguation"
    )
    legacy_upstream = importlib.import_module("power_web_os.application.radar_upstream_disambiguation")
    package_upstream = importlib.import_module(
        "power_web_os.application.radar.candidate_discovery.universe.upstream_disambiguation"
    )

    assert legacy_refs.candidate_source_refs is package_identity.candidate_source_refs
    assert legacy_universe.merge_provider_metadata is package_universe.merge_provider_metadata
    assert legacy_universe.candidate_universe_entries is package_universe.candidate_universe_entries
    assert legacy_universe.filter_signal_result is package_universe.filter_signal_result
    assert legacy_universe.gap_payloads is package_universe.gap_payloads
    assert legacy_universe.stable_id is package_universe.stable_id
    assert legacy_retrieved.candidates_from_retrieved_sources is (
        package_retrieved.candidates_from_retrieved_sources
    )
    assert legacy_resolution.RadarEntityResolutionService is package_resolution.RadarEntityResolutionService
    assert legacy_resolution.RadarEntityResolutionResult is package_resolution.RadarEntityResolutionResult
    assert legacy_resolution.RadarLinkedEntityFact is package_resolution.RadarLinkedEntityFact
    assert legacy_cross.execute_cross_source_disambiguation is (
        package_cross.execute_cross_source_disambiguation
    )
    assert legacy_upstream.review_needed_ambiguous_registry_observations is (
        package_upstream.review_needed_ambiguous_registry_observations
    )
    assert legacy_upstream.cross_source_disambiguation_tasks is (
        package_upstream.cross_source_disambiguation_tasks
    )


def test_signal_monitoring_old_and_new_import_paths_are_compatible() -> None:
    legacy_contracts = importlib.import_module("power_web_os.application.signal_monitoring_contracts")
    package_contracts = importlib.import_module("power_web_os.application.radar.signal_monitoring.contracts")
    legacy_executor = importlib.import_module("power_web_os.application.signal_monitoring_executor")
    package_executor = importlib.import_module("power_web_os.application.radar.signal_monitoring.executor")
    legacy_strategy = importlib.import_module("power_web_os.application.signal_monitoring_source_strategy")
    package_strategy = importlib.import_module("power_web_os.application.radar.signal_monitoring.source_strategy")

    assert legacy_contracts.SignalMonitoringInput is package_contracts.SignalMonitoringInput
    assert legacy_contracts.SignalMonitoringOutcome is package_contracts.SignalMonitoringOutcome
    assert legacy_contracts.SignalMonitoringProviderResult is package_contracts.SignalMonitoringProviderResult
    assert legacy_executor.SignalMonitoringExecutor is package_executor.SignalMonitoringExecutor
    assert legacy_strategy.SignalMonitoringSourceStrategy is package_strategy.SignalMonitoringSourceStrategy


def test_live_radar_run_service_does_not_expose_module_level_helpers() -> None:
    path = Path("src/power_web_os/application/radar/candidate_discovery/service.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    functions = [
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]

    assert functions == []


def test_live_radar_run_service_support_components_are_importable() -> None:
    required = {
        "power_web_os.application.radar.candidate_discovery.service_budget": [
            "ExternalBudgetMetadataMerger",
        ],
        "power_web_os.application.radar.candidate_discovery.service_context": [
            "LiveRadarTaskContextReader",
        ],
        "power_web_os.application.radar.candidate_discovery.service_events": [
            "LiveRadarEventStateProjector",
        ],
        "power_web_os.application.radar.candidate_discovery.execution.options": [
            "CandidateDiscoveryExecutionOptions",
        ],
        "power_web_os.application.radar.candidate_discovery.execution.signal_modes": [
            "CandidateDiscoverySignalExecutionMode",
        ],
        "power_web_os.application.radar.candidate_discovery.service_factory": [
            "LiveRadarRunComposition",
            "LiveRadarRunServiceFactory",
        ],
    }
    for module_name, names in required.items():
        module = importlib.import_module(module_name)
        for name in names:
            assert hasattr(module, name)


def test_live_radar_run_service_uses_named_staged_execution_options() -> None:
    path = Path("src/power_web_os/application/radar/candidate_discovery/service.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "run_staged_radar_execution"
    ]

    assert len(calls) == 1
    assert any(keyword.arg == "options" for keyword in calls[0].keywords)
    assert all(keyword.arg is not None for keyword in calls[0].keywords)


def test_live_radar_run_service_facade_does_not_own_collaborator_assembly() -> None:
    path = Path("src/power_web_os/application/radar/candidate_discovery/service.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden_calls = {
        "SourceRegistryWebSearchProvider",
        "DeterministicRadarDiscoveryPlanner",
        "LiveRadarRunArtifactProjector",
        "ExternalBudgetMetadataMerger",
        "LiveRadarEventStateProjector",
    }
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }

    assert forbidden_calls.isdisjoint(called_names)
    assert "LiveRadarRunServiceFactory" in called_names


def test_live_icp_radar_workflow_uses_package_service_factory() -> None:
    path = Path("src/power_web_os/workflows/live_icp_radar_workflow.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }

    assert "LiveRadarRunServiceFactory" in called_names
    assert "LiveRadarRunService" not in called_names


def test_candidate_discovery_execution_service_classes_are_importable() -> None:
    required = {
        "power_web_os.application.radar.candidate_discovery.execution.context": [
            "CandidateDiscoveryExecutionContext",
            "PhaseResult",
        ],
        "power_web_os.application.radar.candidate_discovery.execution.orchestrator": [
            "CandidateDiscoveryOrchestrator",
            "run_staged_radar_execution",
        ],
        "power_web_os.application.radar.candidate_discovery.execution.options": [
            "CandidateDiscoveryExecutionOptions",
        ],
        "power_web_os.application.radar.candidate_discovery.execution.discovery": ["DiscoveryPhaseExecutor"],
        "power_web_os.application.radar.candidate_discovery.execution.gates": ["GatePhaseExecutor"],
        "power_web_os.application.radar.candidate_discovery.execution.coverage": ["CoveragePhaseExecutor"],
        "power_web_os.application.radar.candidate_discovery.execution.expansion": ["ExpansionPhaseExecutor"],
        "power_web_os.application.radar.candidate_discovery.execution.signals": [
            "CandidateDiscoverySignalHandoffProjector",
            "SignalCompatibilityPhaseExecutor",
        ],
        "power_web_os.application.radar.candidate_discovery.execution.finalization": ["FinalizationProjector"],
        "power_web_os.application.radar.candidate_discovery.execution.merge": ["ExecutionResultMerger"],
        "power_web_os.application.radar.candidate_discovery.execution.projection": [
            "CandidateProjectionService",
            "PipelineEventFactory",
        ],
        "power_web_os.application.radar.candidate_discovery.execution.public_surface": [
            "CandidateDiscoveryProductAcceptancePromoter",
            "CandidateDiscoveryPublicSurfaceProjector",
        ],
        "power_web_os.application.radar.candidate_discovery.execution.service_contracts": [
            "CandidateDiscoveryFactory",
            "CandidateDiscoveryPhaseExecutor",
            "CandidateDiscoveryPolicy",
            "CandidateDiscoveryProjector",
        ],
        "power_web_os.application.radar.candidate_discovery.execution.state": [
            "CandidateDiscoveryExecutionState",
            "ExecutionMetadataFactory",
            "SmokeLimitPolicy",
        ],
        "power_web_os.application.radar.candidate_discovery.execution.task_runner": ["TaskExecutionService"],
    }

    for module_name, names in required.items():
        module = importlib.import_module(module_name)
        for name in names:
            assert hasattr(module, name), f"{module_name} must export {name}"


def test_candidate_discovery_checkpoint_classes_are_importable() -> None:
    required = {
        "power_web_os.application.radar.candidate_discovery.checkpoints.models": [
            "RadarExecutionCheckpointInput",
            "RadarExecutionCheckpointDecision",
            "RadarExecutionCheckpointPolicy",
        ],
        "power_web_os.application.radar.candidate_discovery.checkpoints.policy": [
            "RadarExecutionCheckpointService",
            "checkpoint_summary",
        ],
        "power_web_os.application.radar.candidate_discovery.checkpoints.recording": [
            "record_execution_checkpoint",
        ],
        "power_web_os.application.radar.candidate_discovery.checkpoints.recovery": [
            "RadarCheckpointActionExecutor",
            "RadarCheckpointRecoveryContext",
            "RadarCheckpointRecoveryState",
        ],
    }

    for module_name, names in required.items():
        module = importlib.import_module(module_name)
        for name in names:
            assert hasattr(module, name), f"{module_name} must export {name}"


def test_candidate_discovery_search_expansion_classes_are_importable() -> None:
    required = {
        "power_web_os.application.radar.candidate_discovery.search_expansion.models": [
            "RadarExpansionTarget",
            "RadarSearchExpansionPlan",
            "RadarSearchExpansionVariant",
        ],
        "power_web_os.application.radar.candidate_discovery.search_expansion.service": [
            "RadarSearchExpansionService",
        ],
        "power_web_os.application.radar.candidate_discovery.search_expansion.selection": [
            "RadarVariantSelection",
            "select_guaranteed_variants",
        ],
        "power_web_os.application.radar.candidate_discovery.search_expansion.scheduler": [
            "RadarExpansionSchedule",
            "schedule_guaranteed_expansion_variants",
        ],
        "power_web_os.application.radar.candidate_discovery.search_expansion.targeted_execution": [
            "TargetedSearchExpansionExecutionResult",
            "execute_targeted_search_expansion",
        ],
        "power_web_os.application.radar.candidate_discovery.search_expansion.work_scheduler": [
            "RadarWorkScheduler",
            "RadarWorkPortfolio",
        ],
    }

    for module_name, names in required.items():
        module = importlib.import_module(module_name)
        for name in names:
            assert hasattr(module, name), f"{module_name} must export {name}"


def test_candidate_discovery_universe_admission_classes_are_importable() -> None:
    module = importlib.import_module("power_web_os.application.radar.candidate_discovery.universe.admission")

    assert hasattr(module, "CandidateDiscoveryUpstreamAdmissionPolicy")
    assert hasattr(module, "CandidateDiscoveryUpstreamAdmissionDecision")
