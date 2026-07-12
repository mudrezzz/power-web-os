from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from power_web_os.application.radar.validation.signal_monitoring_quality import control_match_summary


MANIFEST = Path(
    "docs/radar/pipelines/signal-monitoring/to-be/"
    "RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.2.acceptance.json"
)


def test_expanded_quality_manifest_has_six_candidates_and_twelve_pairs() -> None:
    live = _manifest()["live_acceptance"]

    assert len(live["candidate_ids"]) == 6
    assert live["accepted_candidate_count"] == 3
    assert live["review_candidate_count"] == 3
    assert live["signal_codes"] == ["S1", "S2"]
    assert len(live["candidate_ids"]) * len(live["signal_codes"]) == 12


def test_control_evaluator_matches_explicit_positive_controls() -> None:
    live = _manifest()["live_acceptance"]
    report = _control_report(live)

    summary = control_match_summary(report, live["positive_controls"], expected="confirmed")

    assert summary["matched"] == 4
    assert summary["missing"] == []


def test_control_evaluator_accepts_event_interval_overlap() -> None:
    live = _manifest()["live_acceptance"]
    report = _control_report(live)
    first = live["positive_controls"][0]
    ref = "positive-1"
    observation = next(item for item in report["task_observations"] if item["source_refs"] == [ref])
    observation["evidence"][0]["event_at"] = "2025-09-01"
    observation["evidence"][0]["event_end_at"] = first["date_end"]

    summary = control_match_summary(report, [first], expected="confirmed")

    assert summary["matched"] == 1


def test_control_evaluator_separates_negative_and_unknown_date_controls() -> None:
    live = _manifest()["live_acceptance"]
    report = _control_report(live)

    negative = control_match_summary(report, live["negative_controls"], expected="negative")
    unknown = control_match_summary(report, live["unknown_date_controls"], expected="unknown")

    assert negative["matched"] == len(live["negative_controls"])
    assert unknown["matched"] == 1


def _manifest() -> dict[str, Any]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _control_report(live: dict[str, Any]) -> dict[str, Any]:
    task_observations: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    for index, control in enumerate(live["positive_controls"], start=1):
        ref = f"positive-{index}"
        sources.append({
            "source_ref": ref,
            "url": control["url"],
            "published_at": control["date_start"],
            "capability": "official_press",
            "capability_basis": "test",
        })
        task_observations.append({
            "task_id": f"positive-task-{index}",
            "candidate_id": control["candidate_id"],
            "signal_code": control["signal_code"],
            "observation_status": "observed",
            "search_status": "searched",
            "score": 2,
            "source_refs": [ref],
            "evidence": [{
                "source_ref": ref,
                "event_at": control["date_start"],
                "temporal_status": "confirmed_in_window",
            }],
        })
    for index, control in enumerate(live["negative_controls"], start=1):
        ref = f"negative-{index}"
        sources.append({
            "source_ref": ref,
            "url": control["url"],
            "published_at": "2024-01-25",
            "capability": "official_press",
            "capability_basis": "test",
        })
        if control["expected_reason"] == "cross_entity":
            continue
        task_observations.append({
            "task_id": f"negative-task-{index}",
            "candidate_id": control["candidate_id"],
            "signal_code": control["signal_code"],
            "observation_status": "unclear",
            "search_status": control["expected_reason"],
            "source_refs": [ref],
            "evidence": [{
                "source_ref": ref,
                "event_at": "2024-01-25",
                "temporal_status": "rejected_out_of_window",
            }],
        })
    unknown = live["unknown_date_controls"][0]
    sources.append({
        "source_ref": "unknown-date",
        "url": unknown["url"],
        "capability": "official_press",
        "capability_basis": "test",
    })
    task_observations.append({
        "task_id": "unknown-date-task",
        "candidate_id": unknown["candidate_id"],
        "signal_code": unknown["signal_code"],
        "observation_status": "unclear",
        "search_status": "review_needed_date_unknown",
        "source_refs": ["unknown-date"],
        "evidence": [{
            "source_ref": "unknown-date",
            "temporal_status": "review_needed_date_unknown",
        }],
    })
    cross_entity_bindings = [
        {
            "candidate_id": control["candidate_id"],
            "source_ref": f"negative-{index}",
            "status": "cross_entity",
        }
        for index, control in enumerate(live["negative_controls"], start=1)
        if control["expected_reason"] == "cross_entity"
    ]
    return {
        "sources": sources,
        "task_observations": task_observations,
        "source_binding_decisions": cross_entity_bindings,
    }
