from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from power_web_os.application.persisted_live_radar import (
    PersistedLiveRadarRunCommand,
    PersistedLiveRadarRunService,
)
from power_web_os.application.radar_run_journal import RadarRunEventCommand, RadarRunJournal
from power_web_os.application.radar_records import RadarRecord, RadarRunRecord, RadarRunStatus
from power_web_os.integrations.live_radar_openrouter import RecordedWebSearchProvider
from power_web_os.persistence import (
    Base,
    SqlAlchemyRadarRepository,
    SqlAlchemyRadarRunEventRepository,
    SqlAlchemyRadarRunOutputRepository,
    SqlAlchemyRadarRunRepository,
    SqlAlchemyRadarRunTechnicalTraceRepository,
    create_database_engine,
    create_session_factory,
    session_scope,
)
from power_web_os.workflows.live_radar_executor import WorkflowLiveRadarArtifactExecutor


def sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


def test_persisted_live_radar_run_completes_and_stores_artifact_snapshot(tmp_path: Path) -> None:
    engine = create_database_engine(database_url=sqlite_url(tmp_path / "persisted-live.db"))
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    with session_scope(session_factory) as session:
        SqlAlchemyRadarRepository(session).upsert(
            RadarRecord(
                radar_id="toir-quick-live",
                name="TOIR Quick Live Radar",
                status="experimental_live",
                owner="Industrial ABM",
            )
        )
        run_repo = SqlAlchemyRadarRunRepository(session)
        output_repo = SqlAlchemyRadarRunOutputRepository(session)
        event_repo = SqlAlchemyRadarRunEventRepository(session)
        trace_repo = SqlAlchemyRadarRunTechnicalTraceRepository(session)
        service = PersistedLiveRadarRunService(
            run_repository=run_repo,
            output_repository=output_repo,
            executor=WorkflowLiveRadarArtifactExecutor(
                provider=RecordedWebSearchProvider(_recorded_payload()),
                technical_trace_repository=trace_repo,
            ),
            journal=RadarRunJournal(repository=event_repo),
        )

        result = service.run(
            PersistedLiveRadarRunCommand(
                run_id="run-live-1",
                live=False,
                idempotency_key="radar:toir-quick-live:once",
                correlation_id="corr-live-1",
            )
        )
        result_again = service.run(
            PersistedLiveRadarRunCommand(
                live=False,
                idempotency_key="radar:toir-quick-live:once",
            )
        )

        stored_output = output_repo.get("run-live-1")
        stored_run = run_repo.get("run-live-1")
        events = event_repo.list_for_run("run-live-1")
        traces = trace_repo.list_for_run("run-live-1")

    assert result.run.status is RadarRunStatus.COMPLETED
    assert result.output is not None
    assert result.output.artifact_payload["artifact_type"] == "icp_radar_live_run"
    assert result.output.candidates_payload[0]["legal_name"] == "Candidate A"
    assert result.output.sources_payload[0]["evidence_ref"] == "src_1"
    assert result.output.artifact_payload == stored_output.artifact_payload
    assert result_again.run.run_id == "run-live-1"
    assert stored_run is not None
    assert stored_run.run_metadata["candidate_count"] == 1
    assert stored_run.run_metadata["source_count"] == 1
    assert [event.event_type for event in events][:2] == ["run_queued", "run_started"]
    assert {event.node_name for event in events} >= {
        "build_search_plan",
        "run_web_search",
        "extract_candidates",
        "evaluate_candidates",
        "validate_artifact",
    }
    assert "source_collected" in {event.event_type for event in events}
    assert "candidate_extracted" in {event.event_type for event in events}
    assert "signal_evaluated" in {event.event_type for event in events}
    assert [event.event_type for event in events][-1] == "run_completed"
    assert {trace.trace_type for trace in traces} >= {
        "pipeline_input",
        "pipeline_output",
        "normalization_result",
        "validation_result",
    }
    assert {trace.node_name for trace in traces} >= {
        "build_search_plan",
        "run_web_search",
        "extract_candidates",
        "evaluate_candidates",
        "validate_artifact",
        "shape_artifact",
    }
    assert not any("hidden_reasoning" in json.dumps(trace.payload) for trace in traces)
    assert "Authorization" not in json.dumps(result.output.artifact_payload, ensure_ascii=False)


def test_persisted_live_radar_run_failure_persists_failed_state_without_output(tmp_path: Path) -> None:
    engine = create_database_engine(database_url=sqlite_url(tmp_path / "persisted-live-failed.db"))
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    with session_scope(session_factory) as session:
        SqlAlchemyRadarRepository(session).upsert(
            RadarRecord(
                radar_id="toir-quick-live",
                name="TOIR Quick Live Radar",
                status="experimental_live",
                owner="Industrial ABM",
            )
        )
        run_repo = SqlAlchemyRadarRunRepository(session)
        output_repo = SqlAlchemyRadarRunOutputRepository(session)
        event_repo = SqlAlchemyRadarRunEventRepository(session)
        service = PersistedLiveRadarRunService(
            run_repository=run_repo,
            output_repository=output_repo,
            executor=_FailingExecutor(),
            journal=RadarRunJournal(repository=event_repo),
        )

        result = service.run(PersistedLiveRadarRunCommand(run_id="run-failed-1", live=True))
        stored_run = run_repo.get("run-failed-1")
        stored_output = output_repo.get("run-failed-1")
        events = event_repo.list_for_run("run-failed-1")

    assert result.run.status is RadarRunStatus.FAILED
    assert result.output is None
    assert stored_output is None
    assert stored_run is not None
    assert stored_run.status is RadarRunStatus.FAILED
    assert stored_run.error_message == "provider unavailable"
    assert stored_run.error_metadata["exception_type"] == "RuntimeError"
    assert [event.event_type for event in events] == ["run_queued", "run_started", "run_failed"]
    assert events[-1].payload == {"exception_type": "RuntimeError"}


def test_radar_run_journal_rejects_raw_hidden_reasoning_fields(tmp_path: Path) -> None:
    engine = create_database_engine(database_url=sqlite_url(tmp_path / "journal-validation.db"))
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    with session_scope(session_factory) as session:
        SqlAlchemyRadarRepository(session).upsert(
            RadarRecord(radar_id="toir-quick-live", name="TOIR Quick Live Radar", status="active", owner="ABM")
        )
        SqlAlchemyRadarRunRepository(session).create(RadarRunRecord(run_id="run-journal", radar_id="toir-quick-live"))
        journal = RadarRunJournal(repository=SqlAlchemyRadarRunEventRepository(session))

        with pytest.raises(ValueError, match="Raw hidden reasoning"):
            journal.append(
                RadarRunEventCommand(
                    run_id="run-journal",
                    event_type="self_check_completed",
                    phase="validation",
                    actor="validator",
                    summary="Unsafe payload.",
                    payload={"hidden_reasoning": "do not store this"},
                )
            )


class _FailingExecutor:
    def execute(self, *, live: bool, task_context: dict[str, object]) -> dict[str, object]:
        _ = live, task_context
        raise RuntimeError("provider unavailable")


def _recorded_payload() -> dict[str, Any]:
    return {
        "sources": [
            {
                "evidence_ref": "src_1",
                "title": "Candidate A modernization",
                "url": "https://example.test/a",
                "snippet": "Candidate A reports maintenance modernization and diagnostics investment.",
                "query_id": "q1-sibur-holding",
            }
        ],
        "candidate_observations": [
            {
                "legal_name": "Candidate A",
                "description": "Industrial site with maintenance modernization agenda.",
                "qualification": [
                    {
                        "criterion_code": "Q1",
                        "status": "confirmed",
                        "confidence": "high",
                        "rationale": "Source links Candidate A to the target industrial group.",
                        "evidence_refs": ["src_1"],
                    }
                ],
                "signals": [
                    {
                        "signal_code": "S1",
                        "status": "observed",
                        "score": 2,
                        "confidence": "high",
                        "summary": "Maintenance modernization is explicitly mentioned.",
                        "evidence_refs": ["src_1"],
                    }
                ],
            }
        ],
        "provider_metadata": {
            "provider": "recorded",
            "model": "recorded-model",
            "web_mode": "recorded",
        },
    }
