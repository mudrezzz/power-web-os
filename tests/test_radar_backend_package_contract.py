from __future__ import annotations

import importlib
from pathlib import Path


NEW_RADAR_PACKAGES = [
    "power_web_os.application.radar",
    "power_web_os.application.radar.shared",
    "power_web_os.application.radar.candidate_discovery",
    "power_web_os.application.radar.candidate_discovery.planning",
    "power_web_os.application.radar.candidate_discovery.retrieval",
    "power_web_os.application.radar.candidate_discovery.extraction",
    "power_web_os.application.radar.candidate_discovery.sources",
    "power_web_os.application.radar.candidate_discovery.universe",
    "power_web_os.application.radar.candidate_discovery.checkpoints",
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
    "power_web_os.application.radar.candidate_discovery.retrieval.product_sources",
]

LEGACY_KEY_MODULES = [
    "power_web_os.application.live_radar_contracts",
    "power_web_os.application.live_radar_source_cards",
    "power_web_os.application.live_radar_definition_runtime",
    "power_web_os.application.live_radar_discovery_planning",
    "power_web_os.application.live_radar_execution_plan",
    "power_web_os.application.live_radar_plan_acceptance",
    "power_web_os.application.live_radar_planning_pipeline",
    "power_web_os.application.live_radar_product_sources",
    "power_web_os.application.live_radar_retrieval_plan",
    "power_web_os.application.live_radar_service",
    "power_web_os.application.live_radar_staged_execution",
]

MOVED_LEGACY_SHIMS = [
    "live_radar_contracts.py",
    "live_radar_source_cards.py",
    "live_radar_definition_runtime.py",
    "live_radar_discovery_planning.py",
    "live_radar_execution_plan.py",
    "live_radar_plan_acceptance.py",
    "live_radar_planning_pipeline.py",
    "live_radar_product_sources.py",
    "live_radar_retrieval_plan.py",
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
        "power_web_os.application.radar.candidate_discovery.execution"
    )
    assert module.LEGACY_MODULE_TARGETS["power_web_os.application.live_radar_contracts"] == (
        "power_web_os.application.radar.candidate_discovery.contracts"
    )
    assert module.LEGACY_MODULE_TARGETS["power_web_os.application.live_radar_source_cards"] == (
        "power_web_os.application.radar.shared.source_cards"
    )
    assert module.LEGACY_MODULE_MIGRATION_STATUS["power_web_os.application.live_radar_contracts"] == "moved"
    assert module.LEGACY_MODULE_MIGRATION_STATUS["power_web_os.application.live_radar_staged_execution"] == "deferred"
    assert "power_web_os.application.live_radar_staged_execution" in module.LEGACY_HOTSPOTS

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
