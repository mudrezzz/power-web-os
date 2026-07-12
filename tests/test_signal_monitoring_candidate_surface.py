from datetime import UTC, datetime

from power_web_os.application.radar.signal_monitoring.surface import SignalMonitoringCandidateSurfaceProjector
from power_web_os.application.radar_records import RadarRunRecord, RadarRunStatus, SignalMonitoringRunOutputRecord


def test_candidate_surface_separates_current_delta_from_cumulative_evidence() -> None:
    first = _run("signal-first", minute=0)
    second = _run("signal-second", minute=1)

    surface = SignalMonitoringCandidateSurfaceProjector().project(
        selected_run=second,
        source_candidates=[_candidate(), _candidate(), {"candidate_id": "outside", "legal_name": "Outside"}],
        history=[
            (first, _output("signal-first", observation_status="observed", search_status="searched")),
            (
                second,
                _output(
                    "signal-second",
                    observation_status="not_observed",
                    search_status="searched",
                    evidence=False,
                ),
            ),
        ],
    )

    assert surface["summary"] == {
        "candidate_count": 2,
        "monitored_candidate_count": 1,
        "not_monitored_candidate_count": 1,
        "criterion_count": 1,
        "pair_count": 1,
        "current_confirmed_count": 0,
        "current_review_count": 0,
        "current_searched_negative_count": 1,
        "new_confirmed_count": 0,
        "cumulative_confirmed_count": 1,
        "cumulative_review_count": 0,
        "unresolved_source_ref_count": 0,
    }
    monitored = next(item for item in surface["candidates"] if item["candidate_id"] == "candidate-a")
    outcome = monitored["outcomes"][0]
    assert outcome["current"]["presentation_status"] == "not_found_after_complete_coverage"
    assert outcome["cumulative"]["presentation_status"] == "found_fresh"
    assert outcome["cumulative"]["origin_run_id"] == "signal-first"
    assert outcome["cumulative"]["evidence"][0]["url"] == "https://example.test/evidence-a"
    assert next(item for item in surface["candidates"] if item["candidate_id"] == "outside")["monitoring_status"] == "not_monitored"


def test_candidate_surface_keeps_unknown_date_for_review_and_reports_unresolved_ref() -> None:
    run = _run("signal-review", minute=0)
    output = _output(
        "signal-review",
        observation_status="unclear",
        search_status="review_needed_date_unknown",
        temporal_status="review_needed_date_unknown",
        source=False,
    )

    surface = SignalMonitoringCandidateSurfaceProjector().project(
        selected_run=run,
        source_candidates=[_candidate()],
        history=[(run, output)],
    )

    outcome = surface["candidates"][0]["outcomes"][0]
    assert outcome["current"]["presentation_status"] == "found_relevant_date_unknown"
    assert outcome["current"]["evidence"][0]["resolved"] is False
    assert surface["unresolved_source_refs"] == ["source-a"]


def _run(run_id: str, *, minute: int) -> RadarRunRecord:
    timestamp = datetime(2026, 7, 12, 12, minute, tzinfo=UTC)
    return RadarRunRecord(
        run_id=run_id,
        radar_id="radar-a",
        pipeline_id="signal_monitoring",
        source_run_id="candidate-run",
        status=RadarRunStatus.COMPLETED,
        queued_at=timestamp,
        completed_at=timestamp,
    )


def _candidate() -> dict[str, object]:
    return {"candidate_id": "candidate-a", "legal_name": "Candidate A"}


def _output(
    run_id: str,
    *,
    observation_status: str,
    search_status: str,
    temporal_status: str = "confirmed_in_window",
    evidence: bool = True,
    source: bool = True,
) -> SignalMonitoringRunOutputRecord:
    source_ref = "source-a"
    task_observation = {
        "task_id": "task-a",
        "candidate_id": "candidate-a",
        "signal_code": "S1",
        "observation_status": observation_status,
        "search_status": search_status,
        "source_refs": [source_ref],
        "evidence": [{
            "source_ref": source_ref,
            "fact": "Evidence A",
            "event_at": "2026-07-10",
            "temporal_status": temporal_status,
        }] if evidence else [],
        "sources": [{
            "source_ref": source_ref,
            "title": "Evidence A",
            "url": "https://example.test/evidence-a",
        }] if source else [],
    }
    artifact = {
        "candidates": [_candidate()],
        "signal_rules": [{"signal_code": "S1", "label": "Signal 1"}],
        "observations": [{
            "candidate_id": "candidate-a",
            "signal_code": "S1",
            "observation_status": observation_status,
            "search_status": search_status,
            "source_refs": [source_ref],
        }],
        "task_observations": [task_observation],
        "sources": task_observation["sources"],
        "source_lane_ledger": [{
            "candidate_id": "candidate-a",
            "signal_code": "S1",
            "required": True,
            "status": "executed",
        }],
    }
    return SignalMonitoringRunOutputRecord(
        run_id=run_id,
        source_run_id="candidate-run",
        artifact_version="signal_monitoring.v2",
        input_snapshot_payload={},
        plan_payload={},
        observations_payload=artifact["observations"],
        artifact_payload=artifact,
    )
