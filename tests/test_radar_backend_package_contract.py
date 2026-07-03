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
]

LEGACY_KEY_MODULES = [
    "power_web_os.application.live_radar_contracts",
    "power_web_os.application.live_radar_service",
    "power_web_os.application.live_radar_staged_execution",
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
    assert "power_web_os.application.live_radar_staged_execution" in module.LEGACY_HOTSPOTS

    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "import power_web_os.application.live_radar" not in source
    assert "from power_web_os.application.live_radar" not in source
