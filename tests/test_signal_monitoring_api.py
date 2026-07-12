from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from power_web_os.api import create_app
from power_web_os.api.config import ApiSettings
from power_web_os.application.radar.signal_monitoring.contracts import (
    SignalAttemptRole,
    SignalMonitoringProviderResult,
    SignalSearchTask,
)
from power_web_os.application.radar.signal_monitoring.executor import SignalMonitoringExecutor
from power_web_os.application.radar_records import (
    RadarDefinitionRecord,
    RadarRecord,
    RadarRunOutputRecord,
    RadarRunRecord,
    RadarRunStatus,
)
from power_web_os.jobs.radar_jobs import execute_signal_monitoring_run_once
from power_web_os.persistence import (
    Base,
    SqlAlchemyRadarDefinitionRepository,
    SqlAlchemyRadarRepository,
    SqlAlchemyRadarRunOutputRepository,
    SqlAlchemyRadarRunRepository,
    create_database_engine,
    create_session_factory,
    session_scope,
)


class _SignalQueue:
    def __init__(self) -> None:
        self.run_ids: list[str] = []

    def enqueue_signal_monitoring_run(self, run: RadarRunRecord) -> None:
        self.run_ids.append(run.run_id)


class _Provider:
    runtime_name = "api-recorded-signal"
    model_id = "api-recorded-model"

    def run_signal_task(self, *, task: SignalSearchTask, attempt_role: SignalAttemptRole):
        _ = attempt_role
        source_contract = task.source_contracts[0] if task.source_contracts else None
        ref = source_contract.source_ref if source_contract else f"api-source-{task.candidate_id}"
        url = source_contract.url if source_contract else f"https://example.test/{ref}"
        return SignalMonitoringProviderResult(
            runtime_name=self.runtime_name,
            model_id=self.model_id,
            payload={
                "sources": [{
                    "source_ref": ref,
                    "title": "API source",
                    "url": url,
                    "published_at": "2026-07-10",
                    "date_basis": "provider_extracted",
                    "date_confidence": "medium",
                }],
                "observations": [{
                    "candidate_id": task.candidate_id,
                    "signal_code": task.signal_code,
                    "status": "observed",
                    "summary": "API recorded signal",
                    "evidence_refs": [ref],
                    "event_at": "2026-07-10",
                }],
            },
        )


def test_signal_monitoring_api_queues_reads_and_persists_independent_run(tmp_path: Path) -> None:
    database_url = _seed_database(tmp_path)
    queue = _SignalQueue()
    app = create_app(
        ApiSettings(database_url=database_url, environment="test"),
        signal_monitoring_job_queue_factory=lambda: queue,
    )
    app.state.runtime_config_report = {"config": {"openrouter": {"api_key_present": True}}}
    client = TestClient(app)
    candidate_before = client.get("/api/radar-runs/candidate-run-api/candidates").json()

    preflight = client.get(
        "/api/radars/signal-radar/signal-monitoring/preflight",
        params={"source_candidate_run_id": "candidate-run-api"},
    )
    assert preflight.status_code == 200
    assert preflight.json()["ready_for_live_run"] is True
    assert preflight.json()["candidate_count"] == 2

    request = {
        "source_candidate_run_id": "candidate-run-api",
        "candidate_ids": ["accepted-api", "review-api"],
        "signal_codes": ["S1"],
        "idempotency_key": "signal-api-once",
    }
    queued = client.post("/api/radars/signal-radar/signal-monitoring-runs", json=request)
    assert queued.status_code == 202
    signal_run = queued.json()
    assert signal_run["pipeline_id"] == "signal_monitoring"
    assert signal_run["source_run_id"] == "candidate-run-api"
    assert signal_run["run_id"].startswith("signal-run-")
    assert queue.run_ids == [signal_run["run_id"]]
    assert client.get(f"/api/signal-monitoring-runs/{signal_run['run_id']}/report").status_code == 409

    duplicate = client.post("/api/radars/signal-radar/signal-monitoring-runs", json=request)
    assert duplicate.status_code == 202
    assert duplicate.json()["run_id"] == signal_run["run_id"]
    assert queue.run_ids == [signal_run["run_id"]]

    execute_signal_monitoring_run_once(
        run_id=signal_run["run_id"],
        signal_executor=SignalMonitoringExecutor(_Provider()),
        session_factory=app.state.session_factory,
    )
    report = client.get(f"/api/signal-monitoring-runs/{signal_run['run_id']}/report")
    assert report.status_code == 200
    payload = report.json()
    assert payload["pipeline_id"] == "signal_monitoring"
    assert payload["source_candidate_run_id"] == "candidate-run-api"
    assert payload["summary"]["candidate_count"] == 2
    assert payload["summary"]["provider_call_count"] == 2
    assert payload["summary"]["task_count"] == 2
    assert len(payload["search_execution_receipts"]) == 2

    second_request = {**request, "idempotency_key": "signal-api-twice"}
    second = client.post("/api/radars/signal-radar/signal-monitoring-runs", json=second_request).json()
    assert second["run_id"] != signal_run["run_id"]
    assert second["source_run_id"] == "candidate-run-api"
    execute_signal_monitoring_run_once(
        run_id=second["run_id"],
        signal_executor=SignalMonitoringExecutor(_Provider()),
        session_factory=app.state.session_factory,
    )

    surface = client.get(f"/api/signal-monitoring-runs/{second['run_id']}/candidate-surface")
    assert surface.status_code == 200
    surface_payload = surface.json()
    assert surface_payload["pipeline_id"] == "signal_monitoring"
    assert surface_payload["source_candidate_run_id"] == "candidate-run-api"
    assert surface_payload["summary"]["monitored_candidate_count"] == 2
    assert surface_payload["summary"]["criterion_count"] == 1
    assert surface_payload["summary"]["pair_count"] == 2
    assert surface_payload["summary"]["new_confirmed_count"] == 0
    assert surface_payload["summary"]["cumulative_confirmed_count"] == 2
    assert surface_payload["summary"]["unresolved_source_ref_count"] == 0
    assert all(
        outcome["cumulative"]["evidence"]
        for candidate in surface_payload["candidates"]
        for outcome in candidate["outcomes"]
    )
    assert {
        outcome["cumulative"]["origin_run_id"]
        for candidate in surface_payload["candidates"]
        for outcome in candidate["outcomes"]
    } == {signal_run["run_id"]}

    history = client.get("/api/radars/signal-radar/signal-monitoring-runs").json()
    assert [item["run_id"] for item in history] == [second["run_id"], signal_run["run_id"]]
    assert all(item["pipeline_id"] == "signal_monitoring" for item in history)
    assert all(item["source_run_id"] == "candidate-run-api" for item in history)
    candidate_history = client.get("/api/radars/signal-radar/runs").json()
    assert [item["run_id"] for item in candidate_history] == ["candidate-run-api"]
    assert client.get("/api/radar-runs/candidate-run-api/candidates").json() == candidate_before
    catalog_radar = next(item for item in client.get("/api/radars").json() if item["radar_id"] == "signal-radar")
    assert catalog_radar["latest_run"]["run_id"] == "candidate-run-api"


def test_signal_monitoring_api_blocks_missing_credentials_and_invalid_source(tmp_path: Path) -> None:
    database_url = _seed_database(tmp_path)
    queue = _SignalQueue()
    app = create_app(
        ApiSettings(database_url=database_url, environment="test"),
        signal_monitoring_job_queue_factory=lambda: queue,
    )
    app.state.runtime_config_report = {"config": {"openrouter": {"api_key_present": False}}}
    client = TestClient(app)

    preflight = client.get(
        "/api/radars/signal-radar/signal-monitoring/preflight",
        params={"source_candidate_run_id": "candidate-run-api"},
    ).json()
    assert preflight["ready_for_live_run"] is False
    assert any("OPENROUTER_API_KEY" in issue for issue in preflight["issues"])
    assert client.post(
        "/api/radars/signal-radar/signal-monitoring-runs",
        json={"source_candidate_run_id": "candidate-run-api"},
    ).status_code == 422

    app.state.runtime_config_report = {"config": {"openrouter": {"api_key_present": True}}}
    invalid = client.post(
        "/api/radars/signal-radar/signal-monitoring-runs",
        json={"source_candidate_run_id": "missing-run"},
    )
    assert invalid.status_code == 422
    assert queue.run_ids == []


def _seed_database(tmp_path: Path) -> str:
    database_url = f"sqlite:///{(tmp_path / 'signal-api.db').as_posix()}"
    engine = create_database_engine(database_url=database_url)
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)
    with session_scope(session_factory) as session:
        SqlAlchemyRadarRepository(session).upsert(RadarRecord(
            radar_id="signal-radar", name="Signal Radar", status="active", owner="ABM"
        ))
        SqlAlchemyRadarDefinitionRepository(session).upsert(RadarDefinitionRecord(
            definition_id="signal-def-api",
            radar_id="signal-radar",
            definition_version="1",
            definition_payload={
                "global_search_policy": {"sources": [], "allow_open_web": False},
                "monitoring_policy": {"lookback_window": "7 days"},
                "intent_signals": [{"code": "S1", "name": "Tender"}],
            },
        ))
        SqlAlchemyRadarRunRepository(session).create(RadarRunRecord(
            run_id="candidate-run-api",
            radar_id="signal-radar",
            status=RadarRunStatus.COMPLETED,
        ))
        artifact = {
            "artifact_type": "icp_radar_live_run",
            "sources": [
                {
                    "source_ref": "source-accepted-api",
                    "title": "Accepted API source",
                    "url": "https://example.test/accepted-api/news",
                    "snippet": "Accepted API source-backed signal.",
                },
                {
                    "source_ref": "source-review-api",
                    "title": "Review API source",
                    "url": "https://example.test/review-api/news",
                    "snippet": "Review API source-backed signal.",
                },
            ],
            "candidates": [
                {
                    "candidate_id": "accepted-api",
                    "legal_name": "Accepted API",
                    "entity_type": "legal_entity",
                    "candidate_surface_status": "accepted_product_candidate",
                    "product_acceptance_status": "product_candidate",
                    "evidence_refs": ["source-accepted-api"],
                },
                {
                    "candidate_id": "review-api",
                    "legal_name": "Review API",
                    "entity_type": "legal_entity",
                    "candidate_surface_status": "review_needed_candidate",
                    "product_acceptance_status": "review_required",
                    "evidence_refs": ["source-review-api"],
                },
            ],
        }
        SqlAlchemyRadarRunOutputRepository(session).upsert(RadarRunOutputRecord(
            run_id="candidate-run-api",
            artifact_version="candidate.v1",
            radar_payload={},
            search_plan_payload={},
            sources_payload=artifact["sources"],
            candidates_payload=artifact["candidates"],
            artifact_payload=artifact,
        ))
    return database_url
