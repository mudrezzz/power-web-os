from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from power_web_os.application.radar.signal_monitoring.contracts import (
    SignalAttemptRole,
    SignalMonitoringProviderResult,
    SignalSearchTask,
)
from power_web_os.application.radar.signal_monitoring.executor import SignalMonitoringExecutor
from power_web_os.application.radar.signal_monitoring.input_assembler import SignalMonitoringInputError
from power_web_os.application.radar.signal_monitoring.runtime import (
    PersistedSignalMonitoringRunExecutor,
    QueuedSignalMonitoringRunService,
    SignalMonitoringRunCommand,
)
from power_web_os.application.radar_records import (
    RadarDefinitionRecord,
    RadarRecord,
    RadarRunOutputRecord,
    RadarRunRecord,
    RadarRunStatus,
)
from power_web_os.persistence import (
    Base,
    SqlAlchemyRadarDefinitionRepository,
    SqlAlchemyRadarRepository,
    SqlAlchemyRadarRunEventRepository,
    SqlAlchemyRadarRunOutputRepository,
    SqlAlchemyRadarRunRepository,
    SqlAlchemySignalMonitoringRunOutputRepository,
    create_database_engine,
    create_session_factory,
    session_scope,
)


class _SignalProvider:
    runtime_name = "recorded-signal-runtime"
    model_id = "recorded-signal-model"

    def run_signal_task(
        self,
        *,
        task: SignalSearchTask,
        attempt_role: SignalAttemptRole,
    ) -> SignalMonitoringProviderResult:
        _ = attempt_role
        source_ref = f"signal-source-{task.candidate_id}-{task.signal_code}"
        source_url = (
            task.source_contracts[0].url
            if task.source_lane == "known_source" and task.source_contracts
            else f"https://example.test/{source_ref}"
        )
        return SignalMonitoringProviderResult(
            runtime_name=self.runtime_name,
            model_id=self.model_id,
            payload={
                "sources": [{
                    "source_ref": source_ref,
                    "title": "Recorded signal source",
                    "url": source_url,
                    "snippet": f"{task.candidate_name} fresh source-backed signal.",
                    "published_at": "2026-07-10",
                }],
                "observations": [{
                    "candidate_id": task.candidate_id,
                    "signal_code": task.signal_code,
                    "status": "observed",
                    "summary": "Fresh source-backed signal.",
                    "score": 2,
                    "evidence_refs": [source_ref],
                    "event_at": "2026-07-10",
                    "confidence": "strong",
                }],
            },
        )


class _FailingProvider:
    runtime_name = "failing-signal-runtime"
    model_id = "failing-signal-model"

    def run_signal_task(self, *, task: SignalSearchTask, attempt_role: SignalAttemptRole):
        _ = task, attempt_role
        raise TimeoutError("recorded timeout")


def test_persisted_signal_monitoring_uses_separate_run_output_and_incremental_dedupe(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_scope(session_factory) as session:
        repositories = _seed_source_run(session)
        queue_service = _queue_service(repositories)

        first = queue_service.create(SignalMonitoringRunCommand(
            radar_id="signal-radar",
            source_candidate_run_id="candidate-run-1",
            run_id="signal-run-1",
        ))
        assert first.should_enqueue is True
        assert first.run.pipeline_id == "signal_monitoring"
        assert first.run.source_run_id == "candidate-run-1"
        snapshot = first.run.run_metadata["signal_monitoring_input"]
        assert [item["candidate_id"] for item in snapshot["candidates"]] == ["accepted-a", "review-b"]

        first_completed = _executor(repositories, session, _SignalProvider()).execute(first.run.run_id)
        assert first_completed.status is RadarRunStatus.COMPLETED
        first_output = repositories["signal_output"].get(first.run.run_id)
        assert first_output is not None
        assert first_output.artifact_payload["pipeline_id"] == "signal_monitoring"
        assert first_output.artifact_payload["source_candidate_run_id"] == "candidate-run-1"
        assert first_output.artifact_payload["summary"]["candidate_count"] == 2
        assert first_output.artifact_payload["summary"]["provider_call_count"] == 2
        assert first_output.artifact_payload["search_plan"]["tasks"]
        assert len(first_output.artifact_payload["search_execution_receipts"]) == 2
        assert first_output.artifact_payload["watermarks_after"]
        assert repositories["candidate_output"].get("signal-run-1") is None

        second = queue_service.create(SignalMonitoringRunCommand(
            radar_id="signal-radar",
            source_candidate_run_id="candidate-run-1",
            run_id="signal-run-2",
        ))
        second_snapshot = second.run.run_metadata["signal_monitoring_input"]
        assert second_snapshot["previous_watermarks"]
        _executor(repositories, session, _SignalProvider()).execute(second.run.run_id)
        second_output = repositories["signal_output"].get(second.run.run_id)
        assert second_output is not None
        assert {
            item["search_status"] for item in second_output.artifact_payload["observations"]
        } == {"duplicate_existing_signal"}
        assert {
            task["window_basis"] for task in second_output.artifact_payload["tasks"]
        } == {"incremental"}

        assert repositories["runs"].latest_for_radar("signal-radar").run_id == "candidate-run-1"
        assert repositories["runs"].latest_for_radar(
            "signal-radar", pipeline_id="signal_monitoring"
        ).run_id == "signal-run-2"


def test_signal_monitoring_scope_and_whitelist_are_explicit(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_scope(session_factory) as session:
        repositories = _seed_source_run(session)
        service = _queue_service(repositories)

        accepted_only = service.create(SignalMonitoringRunCommand(
            radar_id="signal-radar",
            source_candidate_run_id="candidate-run-1",
            run_id="signal-accepted",
            candidate_scope_mode="accepted_only",
        ))
        candidates = accepted_only.run.run_metadata["signal_monitoring_input"]["candidates"]
        assert [item["candidate_id"] for item in candidates] == ["accepted-a"]

        whitelisted = service.create(SignalMonitoringRunCommand(
            radar_id="signal-radar",
            source_candidate_run_id="candidate-run-1",
            run_id="signal-review",
            candidate_ids=("review-b",),
        ))
        candidates = whitelisted.run.run_metadata["signal_monitoring_input"]["candidates"]
        assert [item["candidate_id"] for item in candidates] == ["review-b"]

        with pytest.raises(SignalMonitoringInputError, match="outside the selected scope"):
            service.create(SignalMonitoringRunCommand(
                radar_id="signal-radar",
                source_candidate_run_id="candidate-run-1",
                run_id="signal-invalid-scope",
                candidate_scope_mode="accepted_only",
                candidate_ids=("review-b",),
            ))


def test_signal_monitoring_rejects_wrong_pipeline_and_source_less_candidates(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_scope(session_factory) as session:
        repositories = _seed_source_run(session)
        source = repositories["runs"].get("candidate-run-1")
        assert source is not None
        repositories["runs"].create(RadarRunRecord(
            run_id="signal-as-source",
            radar_id="signal-radar",
            pipeline_id="signal_monitoring",
            source_run_id=source.run_id,
            status=RadarRunStatus.COMPLETED,
        ))
        with pytest.raises(SignalMonitoringInputError, match="candidate-discovery"):
            _queue_service(repositories).create(SignalMonitoringRunCommand(
                radar_id="signal-radar",
                source_candidate_run_id="signal-as-source",
                run_id="invalid-signal-run",
            ))

        output = repositories["candidate_output"].get(source.run_id)
        assert output is not None
        broken = dict(output.artifact_payload)
        broken["candidates"] = [dict(broken["candidates"][0], evidence_refs=["missing-ref"])]
        repositories["candidate_output"].upsert(RadarRunOutputRecord(
            run_id=source.run_id,
            artifact_version=output.artifact_version,
            radar_payload=output.radar_payload,
            search_plan_payload=output.search_plan_payload,
            sources_payload=output.sources_payload,
            candidates_payload=broken["candidates"],
            artifact_payload=broken,
        ))
        with pytest.raises(SignalMonitoringInputError, match="no resolvable provenance"):
            _queue_service(repositories).create(SignalMonitoringRunCommand(
                radar_id="signal-radar",
                source_candidate_run_id=source.run_id,
                run_id="source-less-run",
                candidate_ids=("accepted-a",),
            ))


def test_provider_error_is_review_needed_not_false_not_observed(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_scope(session_factory) as session:
        repositories = _seed_source_run(session)
        queued = _queue_service(repositories).create(SignalMonitoringRunCommand(
            radar_id="signal-radar",
            source_candidate_run_id="candidate-run-1",
            run_id="signal-provider-error",
            candidate_ids=("accepted-a",),
        ))
        _executor(repositories, session, _FailingProvider()).execute(queued.run.run_id)
        output = repositories["signal_output"].get(queued.run.run_id)
        assert output is not None
        observation = output.artifact_payload["observations"][0]
        assert observation["search_status"] == "review_needed"
        assert observation["observation_status"] == "unclear"
        assert output.artifact_payload["provider_attempts"][0]["outcome"] == "provider_error"


def test_input_assembler_prefers_canonical_user_visible_candidate_surface(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_scope(session_factory) as session:
        repositories = _seed_source_run(session)
        source = repositories["candidate_output"].get("candidate-run-1")
        assert source is not None
        artifact = dict(source.artifact_payload)
        artifact["sources"] = [
            *artifact["sources"],
            {"source_ref": "source-review", "title": "Registry evidence", "url": "https://example.test/review"},
        ]
        artifact["run_metadata"] = {"execution_results": {"user_visible_candidates": [{
            "candidate_id": "visible-review-only",
            "legal_name": "Visible Review LLC",
            "candidate_surface_status": "review_needed_candidate",
            "product_acceptance_status": "review_required",
            "evidence_refs": ["source-review"],
        }]}}
        repositories["candidate_output"].upsert(replace(source, artifact_payload=artifact))

        preflight = _queue_service(repositories).preflight(SignalMonitoringRunCommand(
            radar_id="signal-radar",
            source_candidate_run_id="candidate-run-1",
            candidate_ids=("visible-review-only",),
        ))

    assert preflight["ready_for_live_run"] is True
    assert preflight["candidate_count"] == 1


def test_signal_monitoring_lookback_defaults_to_365_when_radar_policy_is_missing(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_scope(session_factory) as session:
        repositories = _seed_source_run(session)
        repositories["definitions"].upsert(RadarDefinitionRecord(
            definition_id="signal-definition",
            radar_id="signal-radar",
            definition_version="2",
            definition_payload={
                "global_search_policy": {"sources": [], "allow_open_web": False},
                "intent_signals": [{"code": "S1", "name": "Tender"}],
            },
        ))
        queued = _queue_service(repositories).create(SignalMonitoringRunCommand(
            radar_id="signal-radar",
            source_candidate_run_id="candidate-run-1",
            run_id="signal-default-window",
        ))

    snapshot = queued.run.run_metadata["signal_monitoring_input"]
    assert snapshot["lookback_days"] == 365
    assert snapshot["lookback_basis"] == "default_365"


def _session_factory(tmp_path: Path):
    engine = create_database_engine(database_url=f"sqlite:///{(tmp_path / 'signal.db').as_posix()}")
    Base.metadata.create_all(engine)
    return create_session_factory(engine)


def _seed_source_run(session):
    SqlAlchemyRadarRepository(session).upsert(RadarRecord(
        radar_id="signal-radar",
        name="Signal Radar",
        status="active",
        owner="ABM",
    ))
    definitions = SqlAlchemyRadarDefinitionRepository(session)
    definitions.upsert(RadarDefinitionRecord(
        definition_id="signal-definition",
        radar_id="signal-radar",
        definition_version="1",
        definition_payload={
            "global_search_policy": {"sources": [], "allow_open_web": False},
            "monitoring_policy": {"lookback_window": "7 days"},
            "intent_signals": [{"code": "S1", "name": "Tender", "description": "Fresh tender"}],
        },
    ))
    runs = SqlAlchemyRadarRunRepository(session)
    runs.create(RadarRunRecord(
        run_id="candidate-run-1",
        radar_id="signal-radar",
        status=RadarRunStatus.COMPLETED,
    ))
    candidate_output = SqlAlchemyRadarRunOutputRepository(session)
    artifact = _candidate_artifact()
    candidate_output.upsert(RadarRunOutputRecord(
        run_id="candidate-run-1",
        artifact_version="candidate.v1",
        radar_payload={"radar_id": "signal-radar"},
        search_plan_payload={},
        sources_payload=artifact["sources"],
        candidates_payload=artifact["candidates"],
        artifact_payload=artifact,
    ))
    return {
        "runs": runs,
        "definitions": definitions,
        "candidate_output": candidate_output,
        "signal_output": SqlAlchemySignalMonitoringRunOutputRepository(session),
        "events": SqlAlchemyRadarRunEventRepository(session),
    }


def _queue_service(repositories):
    return QueuedSignalMonitoringRunService(
        run_repository=repositories["runs"],
        candidate_output_repository=repositories["candidate_output"],
        signal_output_repository=repositories["signal_output"],
        definition_repository=repositories["definitions"],
        event_repository=repositories["events"],
    )


def _executor(repositories, session, provider):
    return PersistedSignalMonitoringRunExecutor(
        run_repository=repositories["runs"],
        output_repository=repositories["signal_output"],
        executor=SignalMonitoringExecutor(provider),
        event_repository=repositories["events"],
        commit_after_start=session.commit,
    )


def _candidate_artifact() -> dict:
    return {
        "artifact_type": "icp_radar_live_run",
        "sources": [
            {
                "source_ref": "source-accepted-a",
                "title": "Accepted A news",
                "url": "https://example.test/accepted-a/news",
                "snippet": "Accepted A source-backed signal evidence.",
            },
            {
                "source_ref": "source-review-b",
                "title": "Review B news",
                "url": "https://example.test/review-b/news",
                "snippet": "Review B source-backed signal evidence.",
            },
        ],
        "candidates": [
            {
                "candidate_id": "accepted-a",
                "legal_name": "Accepted A",
                "entity_type": "legal_entity",
                "candidate_surface_status": "accepted_product_candidate",
                "product_acceptance_status": "product_candidate",
                "evidence_refs": ["source-accepted-a"],
            },
            {
                "candidate_id": "review-b",
                "legal_name": "Review B",
                "entity_type": "legal_entity",
                "candidate_surface_status": "review_needed_candidate",
                "product_acceptance_status": "review_required",
                "evidence_refs": ["source-review-b"],
                "review_flags": ["requires_human_review"],
            },
        ],
        "run_metadata": {"execution_results": {}},
    }
