from __future__ import annotations

import json
from pathlib import Path

import pytest

from power_web_os.application.radar_model_profiles import (
    DEFAULT_MODEL_PROFILE_DIR,
    RadarModelProfileError,
    RadarModelProfileRegistry,
    load_model_profile,
)


def test_default_model_profiles_load_and_signal_roles_are_complete() -> None:
    registry = RadarModelProfileRegistry.from_directory(DEFAULT_MODEL_PROFILE_DIR)

    candidate = registry.require("candidate_discovery_default")
    signal = registry.require("signal_monitoring_default")

    assert candidate.pipeline_id == "candidate-discovery"
    assert signal.pipeline_id == "signal-monitoring"
    assert set(signal.roles) >= {
        "signal_task_builder",
        "signal_extractor",
        "signal_backup_extractor",
        "signal_evidence_judge",
        "signal_dedupe_judge",
    }


def test_candidate_and_signal_profiles_are_independent() -> None:
    registry = RadarModelProfileRegistry.from_directory(DEFAULT_MODEL_PROFILE_DIR)

    candidate_summary = registry.require("candidate_discovery_default").to_summary()
    signal_summary = registry.require("signal_monitoring_default").to_summary()

    assert candidate_summary["pipeline_id"] == "candidate-discovery"
    assert signal_summary["pipeline_id"] == "signal-monitoring"
    assert "planner" in candidate_summary["roles"]
    assert "signal_extractor" not in candidate_summary["roles"]
    assert "signal_extractor" in signal_summary["roles"]
    assert "planner" not in signal_summary["roles"]


def test_default_model_profiles_match_runtime_model_row() -> None:
    registry = RadarModelProfileRegistry.from_directory(DEFAULT_MODEL_PROFILE_DIR)

    candidate = registry.require("candidate_discovery_default").to_summary()
    signal = registry.require("signal_monitoring_default").to_summary()

    assert candidate["roles"]["planner"]["primary_model"] == "google/gemini-3.1-pro-preview"
    assert candidate["roles"]["planner"]["backup_model"] == "anthropic/claude-sonnet-4.6"
    assert candidate["roles"]["extractor"]["primary_model"] == "openai/gpt-5-mini"
    assert candidate["roles"]["extractor"]["backup_model"] == "anthropic/claude-sonnet-4.6"
    assert signal["roles"]["signal_task_builder"]["primary_model"] == "google/gemini-3.1-pro-preview"
    assert signal["roles"]["signal_extractor"]["primary_model"] == "openai/gpt-5-mini"
    assert signal["roles"]["signal_backup_extractor"]["primary_model"] == "anthropic/claude-sonnet-4.6"


def test_missing_signal_role_fails_with_actionable_error(tmp_path: Path) -> None:
    profile = {
        "profile_id": "broken_signal",
        "pipeline_id": "signal-monitoring",
        "roles": {
            "signal_extractor": {
                "primary_model": "model/a",
                "temperature": 0,
                "max_attempts": 1,
            }
        },
    }
    path = tmp_path / "broken.json"
    path.write_text(json.dumps(profile), encoding="utf-8")

    with pytest.raises(RadarModelProfileError, match="missing required roles"):
        load_model_profile(path)


def test_invalid_role_shape_fails_with_profile_path(tmp_path: Path) -> None:
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps({"profile_id": "x", "pipeline_id": "candidate-discovery", "roles": []}), encoding="utf-8")

    with pytest.raises(RadarModelProfileError, match="Invalid model profile"):
        load_model_profile(path)
