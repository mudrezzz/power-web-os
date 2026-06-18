from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from power_web_os.api import create_app
from power_web_os.api.config import ApiSettings
from power_web_os.application.radar_records import (
    RadarDefinitionRecord,
    RadarRecord,
    RadarRunRecord,
    RadarRunTechnicalTraceRecord,
)
from power_web_os.jobs.radar_jobs import execute_radar_run_once
from power_web_os.persistence import (
    Base,
    SqlAlchemyRadarDefinitionRepository,
    SqlAlchemyRadarRepository,
    SqlAlchemyRadarRunRepository,
    SqlAlchemyRadarRunTechnicalTraceRepository,
    create_database_engine,
    create_session_factory,
    session_scope,
)


def sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


def test_health_endpoint_returns_backend_identity(tmp_path: Path) -> None:
    app = _app(tmp_path)
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "Power Web OS API",
        "version": "0.7.6.1.4",
        "environment": "test",
    }


def test_api_health_alias_matches_root_health_contract(tmp_path: Path) -> None:
    client = TestClient(_app(tmp_path))

    assert client.get("/api/health").json() == client.get("/health").json()


def test_openapi_contains_system_and_radar_contracts(tmp_path: Path) -> None:
    client = TestClient(_app(tmp_path))

    schema = client.get("/openapi.json").json()

    assert schema["info"]["title"] == "Power Web OS API"
    assert schema["info"]["version"] == "0.7.6.1.4"
    for path in [
        "/health",
        "/api/health",
        "/api/radars",
        "/api/radars/{radar_id}",
        "/api/radars/{radar_id}/runs",
        "/api/radar-runs/{run_id}",
        "/api/radar-runs/{run_id}/candidates",
        "/api/radar-runs/{run_id}/journal",
        "/api/radar-runs/{run_id}/dossier",
        "/api/radar-runs/{run_id}/technical-trace",
        "/api/radar-runs/{run_id}/reviews",
        "/api/radar-runs/{run_id}/candidates/{candidate_id}/qualification/{rule_id}/review",
        "/api/radar-runs/{run_id}/candidates/{candidate_id}/signals/{signal_code}/review",
    ]:
        assert path in schema["paths"]


def test_api_allows_local_vite_frontend_origin(tmp_path: Path) -> None:
    client = TestClient(_app(tmp_path))

    response = client.options(
        "/api/radars",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"


def test_radar_catalog_and_detail_read_persisted_data(tmp_path: Path) -> None:
    database_url = _create_seeded_database(tmp_path)
    client = TestClient(_app(tmp_path, database_url=database_url))

    list_response = client.get("/api/radars")
    detail_response = client.get("/api/radars/toir-quick-live")

    assert list_response.status_code == 200
    assert list_response.json()[0]["radar_id"] == "toir-quick-live"
    assert list_response.json()[0]["run_count"] == 0
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["active_definition"]["definition_id"] == "radar-def-live"
    assert detail["runs"] == []


def test_post_radar_run_queues_work_and_polling_reads_output_after_worker_execution(tmp_path: Path) -> None:
    database_url = _create_seeded_database(tmp_path)
    queue = _RecordingJobQueue()
    app = _app(tmp_path, database_url=database_url, job_queue=queue)
    client = TestClient(app)

    response = client.post(
        "/api/radars/toir-quick-live/runs",
        json={
            "live": False,
            "idempotency_key": "radar:live:api",
            "correlation_id": "corr-api-1",
            "requester": "test",
        },
    )

    assert response.status_code == 202
    run = response.json()
    assert run["status"] == "queued"
    assert run["radar_id"] == "toir-quick-live"
    assert run["correlation_id"] == "corr-api-1"
    assert run["output"] is None
    assert queue.enqueued_run_ids == [run["run_id"]]

    detail = client.get(f"/api/radar-runs/{run['run_id']}").json()
    assert detail["status"] == "queued"
    assert detail["output"] is None
    assert client.get(f"/api/radar-runs/{run['run_id']}/candidates").status_code == 409
    queued_journal = client.get(f"/api/radar-runs/{run['run_id']}/journal").json()
    assert [event["event_type"] for event in queued_journal["events"]] == ["run_queued"]
    queued_dossier = client.get(f"/api/radar-runs/{run['run_id']}/dossier").json()
    assert queued_dossier["summary"]["output_state"] == "pending"
    assert queued_dossier["run_context"]["status"] == "queued"
    assert queued_dossier["search_plan"] == []

    execute_radar_run_once(
        run_id=run["run_id"],
        live_executor=_FakeExecutor(_artifact()),
        session_factory=app.state.session_factory,
    )

    candidates = client.get(f"/api/radar-runs/{run['run_id']}/candidates").json()
    journal = client.get(f"/api/radar-runs/{run['run_id']}/journal").json()
    dossier = client.get(f"/api/radar-runs/{run['run_id']}/dossier").json()
    trace_empty = client.get(f"/api/radar-runs/{run['run_id']}/technical-trace").json()
    assert candidates["radar_id"] == "toir-quick-live"
    assert candidates["sources"][0]["evidence_ref"] == "src_1"
    candidate = candidates["candidates"][0]
    assert candidate["legal_name"] == "Candidate A"
    assert candidate["score"]["tier"] == "Tier 1"
    assert candidate["qualification"][0]["source_usages"][0]["source_ref"] == "src_1"
    assert candidate["qualification"][0]["evidence_findings"][0]["why_it_matches_rule"]
    assert candidate["signals"][0]["score_evaluation"]["applied_score"] == 2
    event_types = [event["event_type"] for event in journal["events"]]
    assert event_types[:2] == ["run_queued", "run_started"]
    assert "source_collected" in event_types
    assert "candidate_extracted" in event_types
    assert "signal_evaluated" in event_types
    assert event_types[-1] == "run_completed"
    assert not any(marker in json.dumps(journal) for marker in ["chain_of_thought", "hidden_reasoning", "internal_thoughts"])
    assert dossier["run_context"]["correlation_id"] == "corr-api-1"
    assert dossier["run_context"]["requester"] == "test"
    assert dossier["summary"]["output_state"] == "available"
    assert dossier["summary"]["query_count"] == 1
    assert dossier["summary"]["used_source_count"] == 1
    assert dossier["summary"]["analyzed_source_count"] == 1
    assert dossier["summary"]["skipped_source_count"] == 1
    assert dossier["discovery_plan"]["plan_summary"] == "Test discovery plan."
    assert dossier["discovery_plan"]["steps"][0]["stage"] == "candidate_universe_discovery"
    assert dossier["source_policy_decisions"][0]["decision"] == "selected"
    assert dossier["coverage_summary"]["analyzed_source_reasons"] == ["not_used_by_candidate"]
    assert dossier["search_plan"][0]["query_id"] == "q1"
    assert dossier["search_plan"][0]["source_refs"] == ["src_1"]
    assert dossier["search_plan"][0]["candidate_refs"] == ["candidate-a"]
    assert dossier["sources"][0]["usage_status"] == "used"
    assert {usage["subject_type"] for usage in dossier["sources"][0]["usages"]} == {"candidate", "qualification", "signal"}
    assert [event["event_type"] for event in dossier["timeline"]][0] == "run_queued"
    assert not any(marker in json.dumps(dossier) for marker in ["chain_of_thought", "hidden_reasoning", "internal_thoughts"])
    assert trace_empty["traces"] == []

    with session_scope(app.state.session_factory) as session:
        SqlAlchemyRadarRunTechnicalTraceRepository(session).append(
            RadarRunTechnicalTraceRecord(
                trace_id=f"{run['run_id']}:trace:000001",
                run_id=run["run_id"],
                sequence=1,
                phase="provider",
                node_name="openrouter_web_search",
                trace_type="provider_request",
                title="OpenRouter request",
                summary="Sanitized request.",
                payload={"model": "test-model", "authorization": "[REDACTED]"},
                redaction_report={"masked_paths": ["$.authorization"]},
            )
        )
    trace = client.get(f"/api/radar-runs/{run['run_id']}/technical-trace").json()
    assert trace["traces"][0]["trace_type"] == "provider_request"
    serialized_trace = json.dumps(trace)
    assert not any(marker in serialized_trace for marker in [
        "OPENROUTER_API_KEY",
        "Authorization",
        "Bearer",
        "test-secret",
        "chain_of_thought",
        "hidden_reasoning",
        "internal_thoughts",
    ])

    qualification_review = client.put(
        f"/api/radar-runs/{run['run_id']}/candidates/candidate-a/qualification/rule-q1/review",
        json={
            "status": "corrected",
            "reviewer": "reviewer-a",
            "comment": "Evidence only partially supports this qualification.",
            "corrected_assessment": "partially_matches",
        },
    )
    signal_review = client.put(
        f"/api/radar-runs/{run['run_id']}/candidates/candidate-a/signals/S1/review",
        json={
            "status": "corrected",
            "reviewer": "reviewer-a",
            "comment": "Signal is present but should be lower strength.",
            "adjusted_score": 1,
            "confidence": "medium",
            "corrected_summary": "Moderate modernization signal.",
            "evidence_refs": ["src_1"],
        },
    )

    assert qualification_review.status_code == 200
    assert qualification_review.json()["score_impact"]["effective_assessment"] == "partially_matches"
    assert signal_review.status_code == 200
    assert signal_review.json()["score_impact"] == {"original_score": 2, "effective_score": 1, "delta": -1}

    reviews = client.get(f"/api/radar-runs/{run['run_id']}/reviews").json()
    assert [item["subject_type"] for item in reviews["decisions"]] == ["qualification", "signal"]

    reviewed_candidates = client.get(f"/api/radar-runs/{run['run_id']}/candidates").json()
    reviewed_candidate = reviewed_candidates["candidates"][0]
    assert reviewed_candidate["qualification"][0]["review_decision"]["status"] == "corrected"
    assert reviewed_candidate["qualification"][0]["review_decision"]["corrected_assessment"] == "partially_matches"
    assert reviewed_candidate["signals"][0]["review_decision"]["adjusted_score"] == 1

    reset = client.delete(f"/api/radar-runs/{run['run_id']}/candidates/candidate-a/signals/S1/review")
    assert reset.status_code == 204
    after_reset = client.get(f"/api/radar-runs/{run['run_id']}/candidates").json()
    assert after_reset["candidates"][0]["signals"][0]["review_decision"] is None


def test_post_radar_run_idempotency_does_not_enqueue_duplicate(tmp_path: Path) -> None:
    database_url = _create_seeded_database(tmp_path)
    queue = _RecordingJobQueue()
    client = TestClient(_app(tmp_path, database_url=database_url, job_queue=queue))

    payload = {"live": False, "idempotency_key": "radar:live:api"}
    first = client.post("/api/radars/toir-quick-live/runs", json=payload)
    second = client.post("/api/radars/toir-quick-live/runs", json=payload)

    assert first.status_code == 202
    assert second.status_code == 202
    assert first.json()["run_id"] == second.json()["run_id"]
    assert queue.enqueued_run_ids == [first.json()["run_id"]]


def test_api_missing_and_no_output_cases_return_explicit_statuses(tmp_path: Path) -> None:
    database_url = _create_seeded_database(tmp_path, queued_run=True)
    client = TestClient(_app(tmp_path, database_url=database_url))

    assert client.get("/api/radars/missing").status_code == 404
    assert client.post("/api/radars/missing/runs", json={"live": False}).status_code == 404
    assert client.get("/api/radar-runs/missing").status_code == 404
    assert client.get("/api/radar-runs/missing/candidates").status_code == 404
    assert client.get("/api/radar-runs/missing/journal").status_code == 404
    assert client.get("/api/radar-runs/missing/dossier").status_code == 404
    assert client.get("/api/radar-runs/missing/technical-trace").status_code == 404
    assert client.get("/api/radar-runs/queued-run/candidates").status_code == 409
    queued_dossier = client.get("/api/radar-runs/queued-run/dossier")
    assert queued_dossier.status_code == 200
    assert queued_dossier.json()["summary"]["output_state"] == "pending"
    assert client.get("/api/radar-runs/queued-run/reviews").status_code == 200
    assert client.get("/api/radar-runs/queued-run/journal").json()["events"] == []
    assert client.get("/api/radar-runs/queued-run/technical-trace").json()["traces"] == []
    assert client.put(
        "/api/radar-runs/queued-run/candidates/candidate-a/signals/S1/review",
        json={"status": "confirmed"},
    ).status_code == 409


def test_review_api_rejects_missing_subject_and_invalid_payload(tmp_path: Path) -> None:
    database_url = _create_seeded_database(tmp_path)
    queue = _RecordingJobQueue()
    app = _app(tmp_path, database_url=database_url, job_queue=queue)
    client = TestClient(app)
    run = client.post("/api/radars/toir-quick-live/runs", json={"live": False}).json()
    execute_radar_run_once(
        run_id=run["run_id"],
        live_executor=_FakeExecutor(_artifact()),
        session_factory=app.state.session_factory,
    )

    assert client.put(
        f"/api/radar-runs/{run['run_id']}/candidates/missing/signals/S1/review",
        json={"status": "confirmed"},
    ).status_code == 404
    assert client.put(
        f"/api/radar-runs/{run['run_id']}/candidates/candidate-a/signals/MISSING/review",
        json={"status": "confirmed"},
    ).status_code == 404
    invalid = client.put(
        f"/api/radar-runs/{run['run_id']}/candidates/candidate-a/signals/S1/review",
        json={"status": "stale", "comment": ""},
    )
    assert invalid.status_code == 422


def _app(
    tmp_path: Path,
    *,
    database_url: str | None = None,
    job_queue: object | None = None,
):
    return create_app(
        ApiSettings(environment="test", database_url=database_url or sqlite_url(tmp_path / "api.db")),
        job_queue_factory=lambda: job_queue or _RecordingJobQueue(),
    )


def _create_seeded_database(tmp_path: Path, *, queued_run: bool = False) -> str:
    database_url = sqlite_url(tmp_path / "api-seeded.db")
    engine = create_database_engine(database_url=database_url)
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    with session_scope(session_factory) as session:
        radar = SqlAlchemyRadarRepository(session).upsert(
            RadarRecord(
                radar_id="toir-quick-live",
                name="TOIR Quick Live Radar",
                status="experimental_live",
                owner="Industrial ABM",
                profile={"segment": "industrial"},
                summary={"mode": "live"},
            )
        )
        SqlAlchemyRadarDefinitionRepository(session).upsert(
            RadarDefinitionRecord(
                definition_id="radar-def-live",
                radar_id=radar.radar_id,
                definition_payload={"definition_id": "radar-def-live", "metadata": {"name": radar.name}},
                definition_version="0.7.3-test",
            )
        )
        if queued_run:
            SqlAlchemyRadarRunRepository(session).create(
                RadarRunRecord(run_id="queued-run", radar_id=radar.radar_id, correlation_id="corr-queued")
            )
    return database_url


class _RecordingJobQueue:
    def __init__(self) -> None:
        self.enqueued_run_ids: list[str] = []

    def enqueue_radar_run(self, run: RadarRunRecord) -> None:
        self.enqueued_run_ids.append(run.run_id)


class _FakeExecutor:
    def __init__(self, artifact: dict[str, Any]) -> None:
        self._artifact = artifact

    def execute(self, *, live: bool, task_context: dict[str, object]) -> dict[str, object]:
        _ = live, task_context
        return self._artifact


def _artifact() -> dict[str, Any]:
    return {
        "artifact_type": "icp_radar_live_run",
        "artifact_version": "0.6.3.4",
        "radar": {"radar_id": "toir-quick-live", "name": "TOIR Quick Live Radar"},
        "run_metadata": {
            "runtime": "recorded",
            "candidate_count": 1,
            "source_count": 1,
            "discovery_plan": {
                "plan_summary": "Test discovery plan.",
                "steps": [
                    {
                        "step_id": "discover-q1",
                        "stage": "candidate_universe_discovery",
                        "subject_rule_ids": ["rule-q1"],
                        "source_scope": "global",
                        "source_ids": ["registry"],
                        "query": "Candidate A target group",
                        "purpose": "Find candidate universe.",
                        "expected_evidence": ["target group relationship"],
                        "acceptance_criteria": ["Candidate belongs to target group."],
                    }
                ],
                "source_policy_decisions": [
                    {
                        "source_id": "registry",
                        "source_label": "Registry",
                        "decision": "selected",
                        "reason": "Best source for legal entity identity.",
                        "rule_ids": ["rule-q1"],
                    },
                    {
                        "source_id": "open-web",
                        "source_label": "Open web",
                        "decision": "skipped",
                        "reason": "Registry is sufficient for this fixture.",
                        "rule_ids": ["rule-q1"],
                    },
                ],
                "coverage_hypotheses": [
                    {
                        "summary": "Registry should cover the candidate universe.",
                        "expected_candidate_count": "1",
                        "completeness_risk": "low",
                    }
                ],
                "warnings": [],
            },
            "execution_results": {
                "analyzed_source_count": 1,
                "used_source_count": 1,
                "analyzed_sources": [
                    {
                        "evidence_ref": "unused_src",
                        "reason": "not_used_by_candidate",
                    }
                ],
            },
        },
        "search_plan": {
            "radar_id": "toir-quick-live",
            "queries": [
                {
                    "query_id": "q1",
                    "query": "Candidate A maintenance modernization SIBUR",
                    "purpose": "Find source-backed modernization evidence for Candidate A.",
                    "expected_evidence": ["maintenance modernization", "target group relationship"],
                }
            ],
        },
        "sources": [
            {
                "evidence_ref": "src_1",
                "title": "Candidate A modernization",
                "url": "https://example.test/a",
                "snippet": "Candidate A reports maintenance modernization.",
                "query_id": "q1",
                "source_type": "web",
            }
        ],
        "candidates": [
            {
                "candidate_id": "candidate-a",
                "legal_name": "Candidate A",
                "description": "Industrial candidate with maintenance agenda.",
                "score": {"fit_score": 2, "intent_score": 2, "tier": "Tier 1"},
                "review_flags": ["signal_requires_human_review"],
                "evidence_refs": ["src_1"],
                "qualification": [
                    {
                        "criterion_code": "Q1",
                        "criterion": "Belongs to target industrial group",
                        "status": "confirmed",
                        "confidence": "high",
                        "rationale": "Source confirms the relationship.",
                        "evidence_refs": ["src_1"],
                        "rule_id": "rule-q1",
                        "rule_text_snapshot": "Candidate must belong to target group.",
                        "operator": "AND",
                        "requirement_level": "required",
                        "confidence_policy": "trusted",
                        "source_usages": [{"source_ref": "src_1", "source_name": "Candidate A modernization"}],
                        "evidence_findings": [
                            {
                                "source_ref": "src_1",
                                "fact": "Candidate A belongs to target group.",
                                "excerpt": "Candidate A reports maintenance modernization.",
                                "why_it_matches_rule": "The source states the relevant relationship.",
                            }
                        ],
                        "cross_validation": {"required": False, "status": "not_required"},
                        "requirement_evaluation": {"requirement_level": "required", "satisfied": True},
                        "final_assessment": "matches",
                    }
                ],
                "signals": [
                    {
                        "signal_code": "S1",
                        "signal": "Maintenance modernization",
                        "status": "observed",
                        "score": 2,
                        "confidence": "high",
                        "summary": "Modernization is explicit.",
                        "evidence_refs": ["src_1"],
                        "source_usages": [{"source_ref": "src_1", "source_name": "Candidate A modernization"}],
                        "evidence_findings": [
                            {
                                "source_ref": "src_1",
                                "fact": "Modernization is active.",
                                "excerpt": "maintenance modernization",
                                "why_it_matches_signal": "Maintenance modernization matches S1.",
                                "why_score_applies": "Direct evidence supports max score.",
                            }
                        ],
                        "cross_validation": {"required": False, "status": "not_required"},
                        "score_evaluation": {
                            "scale": "0-2",
                            "applied_score": 2,
                            "max_score": 2,
                            "rule_snapshot": "2: direct evidence",
                            "explanation": "Direct source-backed signal.",
                        },
                    }
                ],
            }
        ],
        "contract_validation": [{"severity": "warning", "path": "signals.S1", "message": "Human review recommended."}],
    }
