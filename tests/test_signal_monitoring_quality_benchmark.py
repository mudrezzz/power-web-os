from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import httpx

from power_web_os.application.radar.validation.signal_monitoring_quality import (
    control_match_summary,
    evaluate_signal_report,
)
from power_web_os.signal_monitoring_quality_acceptance import (
    _assert_initial_quality_gate,
    _request_json,
    _reset_second_attempt,
    _verify_session,
)


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


def test_control_evaluator_accepts_publication_interval_when_event_is_earlier() -> None:
    live = _manifest()["live_acceptance"]
    first = live["positive_controls"][0]
    report = _control_report(live)
    observation = next(item for item in report["task_observations"] if item["candidate_id"] == first["candidate_id"])
    observation["evidence"][0]["event_at"] = "2025-08-01"
    observation["evidence"][0]["published_at"] = first["date_start"]

    summary = control_match_summary(report, [first], expected="confirmed")

    assert summary["matched"] == 1


def test_control_evaluator_ignores_tracking_query_and_fragment() -> None:
    live = _manifest()["live_acceptance"]
    first = live["positive_controls"][0]
    report = _control_report(live)
    source = next(item for item in report["sources"] if item["source_ref"] == "positive-1")
    source["url"] = f"{first['url']}?erid=tracking-value#article"

    summary = control_match_summary(report, [first], expected="confirmed")

    assert summary["matched"] == 1


def test_control_evaluator_keeps_host_and_path_strict() -> None:
    live = _manifest()["live_acceptance"]
    first = live["positive_controls"][0]
    report = _control_report(live)
    source = next(item for item in report["sources"] if item["source_ref"] == "positive-1")
    source["url"] = "https://different.example.test/not-the-control"

    summary = control_match_summary(report, [first], expected="confirmed")

    assert summary["matched"] == 0


def test_control_evaluator_separates_negative_and_unknown_date_controls() -> None:
    live = _manifest()["live_acceptance"]
    report = _control_report(live)

    negative = control_match_summary(report, live["negative_controls"], expected="negative")
    unknown = control_match_summary(report, live["unknown_date_controls"], expected="unknown")

    assert negative["matched"] == len(live["negative_controls"])
    assert unknown["matched"] == 1


def test_cross_criterion_acceptance_prevents_false_rejected_observed_metric() -> None:
    observation = {
        "task_id": "origin::reconcile::S2",
        "candidate_id": "candidate-a",
        "signal_code": "S2",
        "observation_status": "observed",
        "search_status": "searched",
        "score": 2,
        "source_refs": ["source-a"],
        "evidence": [{
            "source_ref": "source-a",
            "event_at": "2026-06-10",
            "temporal_status": "confirmed_in_window",
        }],
    }
    report = {
        "observations": [observation],
        "task_observations": [observation],
        "sources": [{
            "source_ref": "source-a",
            "url": "https://source.test/event",
            "capability": "official_press",
            "capability_basis": "test",
        }],
        "cross_criterion_validation_records": [{
            "origin_task_id": "origin",
            "origin_signal_code": "S1",
            "target_task_id": "target-S2",
            "target_signal_code": "S2",
            "accepted": True,
            "reason": "cross_criterion_evidence_validated",
        }],
    }

    metrics = evaluate_signal_report(report)

    assert metrics["rejected_observed_count"] == 0


def test_negative_control_passes_when_it_is_not_confirmed_by_live_search() -> None:
    live = _manifest()["live_acceptance"]
    report = _control_report(live)
    control = live["negative_controls"][0]
    report["task_observations"] = [
        item
        for item in report["task_observations"]
        if item.get("candidate_id") != control["candidate_id"]
        or item.get("signal_code") != control["signal_code"]
    ]

    summary = control_match_summary(report, [control], expected="negative")

    assert summary["matched"] == 1


def test_acceptance_runner_stops_after_a_when_a_misses_a_positive_control() -> None:
    live = _manifest()["live_acceptance"]
    report = _control_report(live)
    report["task_observations"] = report["task_observations"][1:]

    try:
        _assert_initial_quality_gate(report=report, live=live)
    except RuntimeError as exc:
        assert "B and C were not queued" in str(exc)
    else:
        raise AssertionError("The live acceptance runner must stop before B when A misses a control.")


def test_acceptance_runner_allows_b_after_a_matches_all_positive_controls() -> None:
    live = _manifest()["live_acceptance"]

    _assert_initial_quality_gate(report=_control_report(live), live=live)


def test_acceptance_runner_retries_a_transient_api_disconnect() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise httpx.RemoteProtocolError("temporary disconnect")
        return httpx.Response(200, json={"status": "running"})

    with httpx.Client(transport=httpx.MockTransport(handler), base_url="http://test") as client:
        result = _request_json(client, "GET", "/run")

    assert result == {"status": "running"}
    assert calls == 2


def test_acceptance_runner_replaces_only_failed_b_and_records_the_attempt(tmp_path: Path) -> None:
    freeze_path = tmp_path / "freeze.json"
    freeze = {
        "acceptance_session_id": "session",
        "monitoring_series_ids": ["series-a", "series-b"],
        "initial_live_run_ids": ["run-a", "run-b"],
        "incremental_live_run_id": "run-c",
        "partial_report_sha256": {"run-a": "hash-a", "run-b": "hash-b"},
        "pre_restart_report_sha256": {"run-a": "hash-a", "run-b": "hash-b", "run-c": "hash-c"},
    }

    _reset_second_attempt(freeze=freeze, freeze_path=freeze_path)

    assert freeze["initial_live_run_ids"] == ["run-a"]
    assert freeze["incremental_live_run_id"] == ""
    assert freeze["monitoring_series_ids"] == ["series-a", "sm-session-b2"]
    assert freeze["partial_report_sha256"] == {"run-a": "hash-a"}
    assert freeze["superseded_live_attempts"][0]["initial_run_id"] == "run-b"
    assert freeze["superseded_live_attempts"][0]["incremental_run_id"] == "run-c"
    assert json.loads(freeze_path.read_text(encoding="utf-8"))["initial_live_run_ids"] == ["run-a"]


def test_acceptance_runner_records_a_b_that_was_stopped_before_report(tmp_path: Path) -> None:
    freeze = {
        "acceptance_session_id": "session",
        "monitoring_series_ids": ["series-a", "series-b2"],
        "initial_live_run_ids": ["run-a"],
        "incremental_live_run_id": "",
        "partial_report_sha256": {"run-a": "hash-a"},
    }

    _reset_second_attempt(
        freeze=freeze,
        freeze_path=tmp_path / "freeze.json",
        failed_run_id="run-b2",
    )

    assert freeze["monitoring_series_ids"] == ["series-a", "sm-session-b3"]
    assert freeze["superseded_live_attempts"][0]["initial_run_id"] == "run-b2"


def test_acceptance_verifier_records_fail_when_incremental_run_is_missing(monkeypatch: Any) -> None:
    captured: dict[str, Any] = {}

    class _Validator:
        def validate(self, **kwargs: Any) -> Any:
            captured.update(kwargs)
            return SimpleNamespace(validation_status="FAIL", requirements=[])

    monkeypatch.setattr(
        "power_web_os.signal_monitoring_quality_acceptance._get",
        lambda _client, path: {"run_id": path.rsplit("/", 2)[-2]},
    )
    monkeypatch.setattr(
        "power_web_os.signal_monitoring_quality_acceptance.RadarPipelineSliceValidator",
        _Validator,
    )

    exit_code = _verify_session(
        manifest=SimpleNamespace(),
        manifest_path=Path("manifest.json"),
        freeze={"initial_live_run_ids": ["run-a", "run-b"], "incremental_live_run_id": ""},
        api_url="http://test",
        run_tests=False,
    )

    assert exit_code == 1
    assert captured["incremental_live_report"] == {}
    assert captured["restart_verified"] is False


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
