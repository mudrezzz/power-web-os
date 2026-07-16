from __future__ import annotations

from pathlib import Path

import pytest

from power_web_os.application.radar.validation.acceptance_freeze import (
    verify_acceptance_freeze,
    write_acceptance_freeze,
)
from power_web_os.signal_monitoring_quality_acceptance import (
    _assert_initial_aggregate_gate,
    _assert_initial_quality_gate,
)


def test_acceptance_manifest_freeze_rejects_post_freeze_changes(tmp_path: Path) -> None:
    manifest = tmp_path / "acceptance.json"
    freeze = tmp_path / "acceptance-freeze.json"
    manifest.write_text('{"slice_id":"test"}\n', encoding="utf-8")
    write_acceptance_freeze(manifest_path=manifest, output_path=freeze, git_commit="abc123")

    assert verify_acceptance_freeze(manifest_path=manifest, freeze_path=freeze)["git_commit"] == "abc123"
    manifest.write_text('{"slice_id":"changed"}\n', encoding="utf-8")

    with pytest.raises(RuntimeError, match="changed after freeze"):
        verify_acceptance_freeze(manifest_path=manifest, freeze_path=freeze)


def test_revised_gate_requires_three_per_run_one_complete_and_complete_union() -> None:
    controls = [_control(index) for index in range(1, 5)]
    live = {
        "positive_controls": controls,
        "reproducibility_policy": {
            "minimum_positive_controls_per_initial_run": 3,
            "require_one_complete_initial_run": True,
            "accepted_provider_search_drift_control_ids": ["control-4"],
        },
    }
    run_a = _control_report("run-a", ["control-1", "control-2", "control-3", "control-4"])
    run_b = _control_report("run-b", ["control-1", "control-2", "control-3"])

    _assert_initial_quality_gate(report=run_a, live=live)
    _assert_initial_quality_gate(report=run_b, live=live)
    _assert_initial_aggregate_gate(reports=[run_a, run_b], live=live)


def test_revised_gate_rejects_two_runs_missing_the_same_control() -> None:
    controls = [_control(index) for index in range(1, 5)]
    live = {
        "positive_controls": controls,
        "reproducibility_policy": {
            "minimum_positive_controls_per_initial_run": 3,
            "require_one_complete_initial_run": True,
            "accepted_provider_search_drift_control_ids": ["control-4"],
        },
    }
    run_a = _control_report("run-a", ["control-1", "control-2", "control-3"])
    run_b = _control_report("run-b", ["control-1", "control-2", "control-3"])

    with pytest.raises(RuntimeError, match="aggregate reproducibility gate"):
        _assert_initial_aggregate_gate(reports=[run_a, run_b], live=live)


def _control_report(run_id: str, matched_ids: list[str]) -> dict[str, object]:
    observations = [{
        "candidate_id": "candidate-a",
        "signal_code": "S1",
        "observation_status": "observed",
        "source_refs": [control_id],
        "evidence": [{
            "source_ref": control_id,
            "event_at": "2026-06-15",
            "temporal_status": "confirmed_in_window",
        }],
    } for control_id in matched_ids]
    return {
        "run_id": run_id,
        "task_observations": observations,
        "sources": [{
            "source_ref": control_id,
            "url": f"https://source.test/{control_id}",
            "published_at": "2026-06-15",
        } for control_id in matched_ids],
    }


def _control(index: int) -> dict[str, str]:
    return {
        "id": f"control-{index}",
        "candidate_id": "candidate-a",
        "signal_code": "S1",
        "url": f"https://source.test/control-{index}",
        "date_start": "2026-06-01",
        "date_end": "2026-06-30",
    }
