from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from power_web_os.api import create_app
from power_web_os.api.__main__ import _api_port_from_env
from power_web_os.api.config import ApiSettings
from power_web_os.application.radar_records import (
    RadarDefinitionRecord,
    RadarRecord,
    RadarRunOutputRecord,
    RadarRunRecord,
    RadarRunStatus,
    RadarRunTechnicalTraceRecord,
)
from power_web_os.jobs.radar_jobs import execute_radar_run_once
from power_web_os.persistence import (
    Base,
    SqlAlchemyRadarDefinitionRepository,
    SqlAlchemyRadarRepository,
    SqlAlchemyRadarRunOutputRepository,
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
            "version": "0.7.6.1.11.9",
        "environment": "test",
    }


def test_api_health_alias_matches_root_health_contract(tmp_path: Path) -> None:
    client = TestClient(_app(tmp_path))

    assert client.get("/api/health").json() == client.get("/health").json()


def test_manual_api_port_can_be_overridden(monkeypatch) -> None:
    monkeypatch.delenv("POWER_WEB_OS_API_PORT", raising=False)
    assert _api_port_from_env() == 8000

    monkeypatch.setenv("POWER_WEB_OS_API_PORT", "8010")
    assert _api_port_from_env() == 8010

    monkeypatch.setenv("POWER_WEB_OS_API_PORT", "not-a-port")
    try:
        _api_port_from_env()
    except SystemExit as exc:
        assert "integer" in str(exc)
    else:
        raise AssertionError("POWER_WEB_OS_API_PORT must reject non-integer values.")


def test_openapi_contains_system_and_radar_contracts(tmp_path: Path) -> None:
    client = TestClient(_app(tmp_path))

    schema = client.get("/openapi.json").json()

    assert schema["info"]["title"] == "Power Web OS API"
    assert schema["info"]["version"] == "0.7.6.1.11.9"
    for path in [
        "/health",
        "/api/health",
        "/api/runtime-config",
        "/api/radars",
        "/api/radars/{radar_id}",
        "/api/radars/{radar_id}/definition",
        "/api/radars/{radar_id}/preflight",
        "/api/radars/{radar_id}/runs",
        "/api/radars/{radar_id}/signal-monitoring/preflight",
        "/api/radars/{radar_id}/signal-monitoring-runs",
        "/api/signal-monitoring-runs/{run_id}",
        "/api/signal-monitoring-runs/{run_id}/report",
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


def test_runtime_config_endpoint_returns_redacted_api_config(tmp_path: Path) -> None:
    client = TestClient(_app(
        tmp_path,
        max_web_tasks_per_subject=7,
        max_signal_tasks_per_candidate_signal=3,
        max_total_web_tasks_per_run=25,
    ))

    response = client.get("/api/runtime-config")

    assert response.status_code == 200
    payload = response.json()
    assert payload["artifact_type"] == "radar_runtime_config_report"
    assert payload["component"] == "api"
    assert len(payload["fingerprint"]) == 16
    assert payload["config"]["radar"]["max_web_tasks_per_subject"] == 7
    assert payload["config"]["radar"]["max_signal_tasks_per_candidate_signal"] == 3
    assert payload["config"]["radar"]["max_total_web_tasks_per_run"] == 25
    serialized = json.dumps(payload)
    assert not any(marker in serialized for marker in [
        "OPENROUTER_API_KEY",
        "DADATA_API_KEY",
        "DADATA_SECRET_KEY",
        "Authorization",
        "Bearer",
        "sk-or-",
    ])


def test_radar_preflight_endpoint_returns_readable_report_without_creating_runs(tmp_path: Path) -> None:
    database_url = _create_seeded_database(tmp_path)
    client = TestClient(_app(tmp_path, database_url=database_url))

    response = client.get("/api/radars/toir-quick-live/preflight")

    assert response.status_code == 200
    payload = response.json()
    assert payload["artifact_type"] == "radar_execution_preflight_report"
    assert payload["radar_id"] == "toir-quick-live"
    assert payload["runtime_config"]["component"] == "api"
    assert isinstance(payload["ready_for_live_run"], bool)
    assert {check["code"] for check in payload["checks"]} >= {
        "active_definition_available",
        "definition_runtime_mismatch",
    }
    assert client.get("/api/radars/toir-quick-live").json()["run_count"] == 0
    serialized = json.dumps(payload)
    assert not any(marker in serialized for marker in [
        "OPENROUTER_API_KEY",
        "DADATA_API_KEY",
        "DADATA_SECRET_KEY",
        "Authorization",
        "Bearer",
        "sk-or-",
        "chain_of_thought",
        "hidden_reasoning",
        "internal_thoughts",
    ])


def test_radar_preflight_endpoint_returns_404_for_missing_radar(tmp_path: Path) -> None:
    database_url = _create_seeded_database(tmp_path)
    client = TestClient(_app(tmp_path, database_url=database_url))

    assert client.get("/api/radars/missing/preflight").status_code == 404


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


def test_radar_run_history_endpoint_returns_recent_runs_newest_first(tmp_path: Path) -> None:
    database_url = _create_seeded_database(tmp_path)
    engine = create_database_engine(database_url=database_url)
    session_factory = create_session_factory(engine)
    queued_at = datetime(2026, 7, 9, 10, 0, tzinfo=timezone.utc)
    with session_scope(session_factory) as session:
        run_repo = SqlAlchemyRadarRunRepository(session)
        output_repo = SqlAlchemyRadarRunOutputRepository(session)
        for index in range(3):
            run = run_repo.create(
                RadarRunRecord(
                    run_id=f"history-run-{index}",
                    radar_id="toir-quick-live",
                    status=RadarRunStatus.COMPLETED,
                    queued_at=queued_at + timedelta(minutes=index),
                    completed_at=queued_at + timedelta(minutes=index, seconds=30),
                    run_metadata={"benchmark_mode": "blind" if index == 1 else "smoke"},
                )
            )
            output_repo.upsert(
                RadarRunOutputRecord(
                    run_id=run.run_id,
                    artifact_version="0.7.6-test",
                    radar_payload={"radar_id": "toir-quick-live"},
                    search_plan_payload={},
                    sources_payload=[],
                    candidates_payload=[{"candidate_id": f"candidate-{index}"}],
                    contract_validation_payload=[],
                    artifact_payload={"artifact_type": "icp_radar_live_run"},
                )
            )

    client = TestClient(_app(tmp_path, database_url=database_url))

    response = client.get("/api/radars/toir-quick-live/runs?limit=2")

    assert response.status_code == 200
    runs = response.json()
    assert [item["run_id"] for item in runs] == ["history-run-2", "history-run-1"]
    assert runs[0]["output"]["candidate_count"] == 1
    assert runs[1]["run_metadata"]["benchmark_mode"] == "blind"
    assert client.get("/api/radars/missing/runs").status_code == 404


def test_radar_catalog_summary_uses_latest_visible_candidate_surface_counts(tmp_path: Path) -> None:
    database_url = _create_seeded_database(tmp_path)
    engine = create_database_engine(database_url=database_url)
    session_factory = create_session_factory(engine)
    with session_scope(session_factory) as session:
        radar_repo = SqlAlchemyRadarRepository(session)
        definition_repo = SqlAlchemyRadarDefinitionRepository(session)
        run_repo = SqlAlchemyRadarRunRepository(session)
        output_repo = SqlAlchemyRadarRunOutputRepository(session)
        radar_repo.upsert(
            RadarRecord(
                radar_id="benchmark-sibur-holding-contour",
                name="Benchmark / SIBUR holding contour",
                status="active",
                owner="ABM Research",
                profile={"icp_profile": "Benchmark / SIBUR holding contour"},
                summary={"run_mode": "benchmark", "candidate_count": 0, "accepted_count": 0, "needs_review_count": 0},
            )
        )
        definition_repo.upsert(
            RadarDefinitionRecord(
                definition_id="radar-def-benchmark",
                radar_id="benchmark-sibur-holding-contour",
                definition_payload={"definition_id": "radar-def-benchmark", "metadata": {"name": "Benchmark / SIBUR holding contour"}},
                definition_version="0.7.6-test",
            )
        )
        run_repo.create(RadarRunRecord(
            run_id="benchmark-run",
            radar_id="benchmark-sibur-holding-contour",
            run_metadata={"heavy": {"nested": ["payload"] * 100}},
        ))
        run_repo.update_status("benchmark-run", RadarRunStatus.COMPLETED)
        visible_candidates = [
            {
                "candidate_id": f"accepted-{index}",
                "legal_name": f"Accepted {index}",
                "candidate_surface_status": "accepted_product_candidate",
                "product_acceptance_status": "product_candidate",
            }
            for index in range(3)
        ] + [
            {
                "candidate_id": f"review-{index}",
                "legal_name": f"Review {index}",
                "candidate_surface_status": "review_needed_candidate",
                "product_acceptance_status": "review_required",
            }
            for index in range(10)
        ]
        output_repo.upsert(
            RadarRunOutputRecord(
                run_id="benchmark-run",
                artifact_version="0.7.6-test",
                radar_payload={"radar_id": "benchmark-sibur-holding-contour"},
                search_plan_payload={"queries": []},
                sources_payload=[],
                candidates_payload=visible_candidates,
                contract_validation_payload=[],
                artifact_payload={
                    "artifact_type": "icp_radar_live_run",
                    "run_metadata": {
                        "execution_results": {
                            "user_visible_candidates": visible_candidates,
                        },
                    },
                    "candidates": [],
                },
            )
        )

    client = TestClient(_app(tmp_path, database_url=database_url))
    payload = client.get("/api/radars").json()
    benchmark = next(item for item in payload if item["radar_id"] == "benchmark-sibur-holding-contour")

    assert benchmark["latest_run"]["run_id"] == "benchmark-run"
    assert benchmark["latest_run"]["run_metadata"] == {}
    assert benchmark["summary"]["candidate_count"] == 13
    assert benchmark["summary"]["accepted_count"] == 3
    assert benchmark["summary"]["needs_review_count"] == 10


def test_update_radar_definition_persists_source_usage_obligations_without_creating_runs(tmp_path: Path) -> None:
    database_url = _create_seeded_database(tmp_path)
    client = TestClient(_app(tmp_path, database_url=database_url))
    payload = {
        "definition_id": "radar-def-live",
        "metadata": {"name": "TOIR Quick Live Radar"},
        "global_search_policy": {
            "allow_system_sources": True,
            "keywords": [],
            "exclusions": [],
            "sources": [
                {
                    "source_id": "dadata_registry",
                    "source_type": "api",
                    "label": "DaData",
                    "reference": "company_registry:dadata",
                    "trust_level": "high",
                    "usage_obligation": "required_for_identity",
                },
                {
                    "source_id": "openrouter_web",
                    "source_type": "search_engine",
                    "label": "Open web",
                    "reference": "openrouter:web",
                    "trust_level": "cross_check",
                    "usage_obligation": "required_for_coverage",
                },
            ],
        },
    }

    response = client.put(
        "/api/radars/toir-quick-live/definition",
        json={"definition_payload": payload, "definition_version": "ui-test"},
    )

    assert response.status_code == 200
    detail = response.json()
    sources = detail["active_definition"]["definition_payload"]["global_search_policy"]["sources"]
    assert [source["usage_obligation"] for source in sources] == ["required_for_identity", "required_for_coverage"]
    assert detail["active_definition"]["definition_version"] == "ui-test"
    assert detail["run_count"] == 0
    preflight = client.get("/api/radars/toir-quick-live/preflight").json()
    assert any(
        check["code"] == "source_usage_obligation_valid" and check["status"] == "passed"
        for check in preflight["checks"]
    )

    invalid = dict(payload)
    invalid["global_search_policy"] = {
        **payload["global_search_policy"],
        "sources": [{**sources[0], "usage_obligation": "must_use_because_i_say_so"}],
    }
    assert client.put(
        "/api/radars/toir-quick-live/definition",
        json={"definition_payload": invalid},
    ).status_code == 422
    assert client.put(
        "/api/radars/missing/definition",
        json={"definition_payload": payload},
    ).status_code == 404


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
    assert queued_dossier["run_context"]["task_context"]["max_web_tasks_per_subject"] == 20
    assert queued_dossier["run_context"]["task_context"]["max_signal_tasks_per_candidate_signal"] is None
    assert queued_dossier["run_context"]["task_context"]["source_verification_mode"] == "soft"
    assert queued_dossier["run_context"]["task_context"]["min_useful_sources_per_discovery_task"] == 3
    assert queued_dossier["run_context"]["task_context"]["min_candidates_per_discovery_task"] == 5
    assert queued_dossier["run_context"]["task_context"]["max_discovery_retries_per_task"] == 2
    assert queued_dossier["run_context"]["task_context"]["run_profile"] == "live"
    assert queued_dossier["run_context"]["task_context"]["max_openrouter_calls_per_run"] is None
    assert queued_dossier["run_context"]["task_context"]["max_provider_retries_per_task"] is None

    assert queued_dossier["runtime_config"]["component"] == "api"
    assert queued_dossier["runtime_config_warnings"] == []
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
    assert candidate["entity_type"] == "legal_entity"
    assert candidate["upstream_discovery_outcome"] == "confirmed_upstream_lead"
    assert candidate["product_acceptance_status"] == "product_candidate"
    assert candidate["public_result_status"] == "public_candidate"
    assert candidate["candidate_surface_status"] == "accepted_product_candidate"
    assert candidates["candidates"][1]["legal_name"] == "Candidate B"
    assert candidates["candidates"][1]["product_acceptance_status"] == "review_required"
    assert candidates["candidates"][1]["candidate_surface_status"] == "review_needed_candidate"
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
    assert dossier["runtime_config"]["component"] == "worker"
    assert isinstance(dossier["runtime_config_warnings"], list)
    assert dossier["summary"]["output_state"] == "available"
    assert dossier["summary"]["query_count"] == 1
    assert dossier["summary"]["used_source_count"] == 1
    assert dossier["summary"]["analyzed_source_count"] == 1
    assert dossier["summary"]["skipped_source_count"] == 1
    assert dossier["source_lifecycle_summary"]["total_count"] == 2
    assert dossier["source_lifecycle_summary"]["by_state"] == {"analyzed_only": 1, "used": 1}
    assert dossier["source_lifecycle_summary"]["by_reason"]["used_by_candidate"] == 1
    assert dossier["source_lifecycle_summary"]["by_reason"]["not_used_by_candidate"] == 1
    assert dossier["source_lifecycle"][0]["evidence_ref"] == "src_1"
    assert dossier["source_lifecycle"][0]["state"] == "used"
    assert dossier["source_lifecycle"][1]["evidence_ref"] == "unused_src"
    assert dossier["source_lifecycle"][1]["state"] == "analyzed_only"
    assert dossier["source_lifecycle"][1]["reason"] == "not_used_by_candidate"
    assert dossier["summary"]["diagnostic_source_count"] == 2
    assert dossier["summary"]["analyzed_only_source_count"] == 1
    assert dossier["summary"]["linked_source_count"] == 1
    assert dossier["summary"]["smoke_candidate_cap"] == 2
    assert dossier["summary"]["promoted_candidate_count"] == 1
    assert dossier["summary"]["diagnostic_candidate_count"] == 3
    assert dossier["summary"]["source_cards_count"] == 1
    assert dossier["summary"]["source_capability_decision_count"] == 1
    assert dossier["summary"]["connector_profile_loaded_count"] == 1
    assert dossier["summary"]["review_needed_universe_count"] == 1
    assert dossier["summary"]["linked_branch_or_site_count"] == 0
    assert dossier["discovery_plan"]["plan_summary"] == "Test discovery plan."
    assert dossier["discovery_plan"]["steps"][0]["stage"] == "candidate_universe_discovery"
    assert dossier["source_cards"][0]["connector_profile_id"] == "generic_registry"
    assert dossier["source_capability_decisions"][0]["type"] == "source_capability_matched"
    assert dossier["source_capability_validation"]["accepted"] is True
    assert dossier["source_policy_decisions"][0]["decision"] == "selected"
    assert dossier["source_policy_decisions"][0]["usage_obligation"] == "required_for_identity"
    assert dossier["source_obligations"][0]["usage_obligation"] == "required_for_identity"
    assert dossier["source_obligation_decisions"][0]["status"] == "satisfied"
    assert dossier["source_obligation_summary"]["by_obligation"] == {"required_for_identity": 1}
    assert dossier["coverage_summary"]["analyzed_source_reasons"] == ["not_used_by_candidate"]
    assert dossier["candidate_universe"][0]["status"] == "qualified"
    assert dossier["candidate_universe"][0]["public_result_status"] == "public_candidate"
    assert dossier["candidate_universe"][0]["candidate_surface_status"] == "accepted_product_candidate"
    assert dossier["candidate_universe"][0]["entity_type"] == "legal_entity"
    assert dossier["candidate_universe"][0]["resolution_status"] == "resolved"
    assert dossier["candidate_universe"][0]["linked_fact_count"] == 1
    assert dossier["candidate_universe"][1]["entity_type"] == "legal_entity"
    assert dossier["candidate_universe"][1]["candidate_surface_status"] == "review_needed_candidate"
    assert dossier["candidate_universe"][2]["entity_type"] == "branch"
    assert dossier["candidate_universe"][2]["resolution_status"] == "review_needed"
    assert dossier["candidate_universe"][2]["not_candidate_reason"] == "not_standalone_legal_entity"
    assert dossier["candidate_universe"][2]["public_projection_reason"] == "review_entity_not_standalone_legal_entity"
    assert "registry_match_ambiguous" in dossier["candidate_universe"][2]["review_flags"]
    assert dossier["candidate_discovery_reconciliation"]["unexplained_drop_count"] == 0
    assert dossier["candidate_discovery_reconciliation"]["raw_upstream_lead_count"] == 3
    assert dossier["candidate_discovery_reconciliation"]["visible_candidate_count"] == 2
    assert dossier["candidate_discovery_reconciliation"]["accepted_product_candidate_count"] == 1
    assert dossier["candidate_discovery_reconciliation"]["review_needed_candidate_count"] == 1
    assert dossier["summary"]["candidate_count"] == 2
    assert dossier["summary"]["visible_candidate_count"] == 2
    assert dossier["summary"]["accepted_product_candidate_count"] == 1
    assert dossier["summary"]["review_needed_candidate_count"] == 1
    assert dossier["candidates"][0]["legal_name"] == "Candidate A"
    assert dossier["candidates"][0]["product_acceptance_status"] == "product_candidate"
    assert dossier["candidates"][0]["public_result_status"] == "public_candidate"
    assert dossier["candidates"][1]["legal_name"] == "Candidate B"
    assert dossier["candidates"][1]["candidate_surface_status"] == "review_needed_candidate"
    assert dossier["product_acceptance_ledger"][2]["public_result_status"] == "retained_in_candidate_universe"
    assert candidates["candidate_discovery_reconciliation"]["unexplained_drop_count"] == 0
    assert candidates["product_acceptance_ledger"][0]["legal_name"] == "Candidate A"
    assert dossier["entity_resolution_results"][1]["entity_type"] == "project"
    assert dossier["entity_resolution_results"][1]["resolution_status"] == "linked_to_legal_entity"
    assert dossier["linked_entity_facts"][0]["entity_name"] == "EP-600"
    assert dossier["coverage_summary"]["entity_resolution_count"] == 2
    assert dossier["coverage_summary"]["linked_entity_fact_count"] == 1
    assert dossier["upstream_disambiguation_results"][0]["entity_type"] == "branch"
    assert dossier["cross_source_disambiguation_tasks"][0]["source_ids"] == ["sibur_site"]
    assert dossier["cross_source_disambiguation_tasks"][0]["outcome"] == "confirmed_relation"
    assert dossier["cross_source_disambiguation_execution"][0]["status"] == "executed"
    assert dossier["extraction_recovery_records"][0]["action"] == "repair_extraction"
    assert dossier["coverage_checks"][0]["task_id"] == "coverage-q1"
    assert dossier["coverage_warnings"] == []
    assert dossier["unresolved_candidate_gaps"] == []
    assert dossier["discovery_iteration_count"] == 1
    assert dossier["retrieval_plan"]["tasks"][0]["task_id"] == "q1"
    assert dossier["retrieval_plan"]["tasks"][0]["response_contract"]["schema_id"] == "signal_finding_v1"
    assert dossier["budget_summary"]["counters"]["total"] == 4
    assert dossier["budget_summary"]["signal_not_searched_count"] == 1
    assert dossier["budget_exhaustion_events"][0]["state"] == "not_searched_budget_limited"
    assert dossier["checkpoint_summary"]["by_action"] == {"continue": 1}
    assert dossier["checkpoint_decisions"][0]["phase"] == "before_signal_search"
    assert dossier["adaptive_actions"] == []
    assert dossier["checkpoint_warnings"] == []
    assert dossier["stopped_for_review_reason"] == ""
    assert dossier["signal_search_statuses"][1]["search_status"] == "not_searched_budget_limited"
    assert dossier["search_plan"][0]["query_id"] == "q1"
    assert dossier["search_plan"][0]["source_refs"] == ["src_1"]
    assert dossier["search_plan"][0]["candidate_refs"] == ["candidate-a", "candidate-b"]
    assert dossier["sources"][0]["usage_status"] == "used"
    assert {usage["subject_type"] for usage in dossier["sources"][0]["usages"]} == {"candidate", "qualification", "signal"}
    assert [event["event_type"] for event in dossier["timeline"]][0] == "run_queued"
    assert not any(marker in json.dumps(dossier) for marker in ["chain_of_thought", "hidden_reasoning", "internal_thoughts"])
    assert trace_empty["traces"][0]["title"] == "Effective runtime config"
    assert trace_empty["traces"][0]["trace_type"] == "validation_result"

    with session_scope(app.state.session_factory) as session:
        trace_repository = SqlAlchemyRadarRunTechnicalTraceRepository(session)
        sequence = trace_repository.next_sequence(run["run_id"])
        trace_repository.append(
            RadarRunTechnicalTraceRecord(
                trace_id=f"{run['run_id']}:trace:{sequence:06d}",
                run_id=run["run_id"],
                sequence=sequence,
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
    assert any(item["trace_type"] == "provider_request" for item in trace["traces"])
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


def test_candidates_endpoint_exposes_registry_provenance_for_review_needed_candidate(tmp_path: Path) -> None:
    database_url = _create_seeded_database(tmp_path)
    engine = create_database_engine(database_url=database_url)
    session_factory = create_session_factory(engine)
    with session_scope(session_factory) as session:
        radar_repo = SqlAlchemyRadarRepository(session)
        run_repo = SqlAlchemyRadarRunRepository(session)
        output_repo = SqlAlchemyRadarRunOutputRepository(session)
        radar_repo.upsert(
            RadarRecord(
                radar_id="benchmark-sibur-holding-contour",
                name="Benchmark / SIBUR holding contour",
                status="active",
                owner="ABM Research",
                profile={"icp_profile": "Benchmark / SIBUR holding contour"},
                summary={"run_mode": "benchmark"},
            )
        )
        run = RadarRunRecord(
            run_id="radar-run-registry-provenance",
            radar_id="benchmark-sibur-holding-contour",
            status=RadarRunStatus.COMPLETED,
        )
        run_repo.create(run)
        output_repo.upsert(
            RadarRunOutputRecord(
                run_id=run.run_id,
                artifact_version="live_icp_radar.v1",
                radar_payload={},
                artifact_payload={
                    "sources": [],
                    "candidates": [],
                    "contract_validation": [],
                    "run_metadata": {
                        "execution_results": {
                            "user_visible_candidates": [
                                {
                                    "candidate_id": "ао-сибуртюменьгаз",
                                    "legal_name": 'АО "СИБУРТЮМЕНЬГАЗ"',
                                    "description": "",
                                    "entity_type": "legal_entity",
                                    "score": {"fit_score": 0, "intent_score": 0, "tier": "Review needed"},
                                    "review_flags": ["registry_match_ambiguous"],
                                    "evidence_refs": ["dadata_7202116628"],
                                    "qualification": [],
                                    "signals": [],
                                    "upstream_source_refs": ["dadata_7202116628"],
                                    "product_acceptance_status": "review_required",
                                    "candidate_surface_status": "review_needed_candidate",
                                    "candidate_surface_reason": "source_backed_legal_entity_requires_review",
                                },
                                {
                                    "candidate_id": "ао-сибуртюменьгаз",
                                    "legal_name": "АО «СибурТюменьГаз»",
                                    "description": "",
                                    "entity_type": "legal_entity",
                                    "score": {"fit_score": 0, "intent_score": 0, "tier": "Review needed"},
                                    "review_flags": ["benchmark_present_source_projection"],
                                    "evidence_refs": ["dadata_7202116628"],
                                    "qualification": [],
                                    "signals": [],
                                    "upstream_source_refs": ["dadata_7202116628"],
                                    "product_acceptance_status": "review_required",
                                    "candidate_surface_status": "review_needed_candidate",
                                    "candidate_surface_reason": "benchmark_present_source_projection_requires_review",
                                    "benchmark_id": "sibur-tyumen-gas",
                                },
                            ],
                            "review_needed_upstream_entities": [
                                {
                                    "entity_name": 'АО "СИБУРТЮМЕНЬГАЗ"',
                                    "legal_name": 'АО "СИБУРТЮМЕНЬГАЗ"',
                                    "entity_type": "legal_entity",
                                    "source_refs": ["dadata_7202116628"],
                                    "source_id": "dadata_registry",
                                    "provider_id": "dadata",
                                    "lookup_query": "АО СИБУР",
                                    "inn": "7202116628",
                                    "ogrn": "1037200611612",
                                    "match_quality": "medium",
                                    "review_flags": ["registry_match_ambiguous", "requires_human_review"],
                                    "reason": "Ambiguous registry observation retained for recall-first upstream discovery.",
                                }
                            ],
                        }
                    },
                },
                search_plan_payload={},
                sources_payload=[],
                candidates_payload=[],
                contract_validation_payload=[],
            )
        )

    client = TestClient(_app(tmp_path, database_url=database_url))
    candidates = client.get(f"/api/radar-runs/{run.run_id}/candidates").json()
    dossier = client.get(f"/api/radar-runs/{run.run_id}/dossier").json()
    sources_by_ref = {source["evidence_ref"]: source for source in candidates["sources"]}
    lifecycle_by_ref = {source["evidence_ref"]: source for source in dossier["source_lifecycle"]}

    assert len(candidates["candidates"]) == 1
    assert candidates["candidates"][0]["legal_name"] == "АО «СибурТюменьГаз»"
    assert candidates["candidates"][0]["evidence_refs"] == ["dadata_7202116628"]
    assert sources_by_ref["dadata_7202116628"]["source_type"] == "registry"
    assert "7202116628" in sources_by_ref["dadata_7202116628"]["snippet"]
    assert "1037200611612" in sources_by_ref["dadata_7202116628"]["snippet"]
    assert "dadata_7202116628" not in lifecycle_by_ref


def test_post_radar_run_commits_before_enqueue_so_worker_can_read_run(tmp_path: Path) -> None:
    database_path = tmp_path / "api-seeded.db"
    database_url = _create_seeded_database(tmp_path)
    queue = _ReadDuringEnqueueJobQueue(database_path)
    app = _app(tmp_path, database_url=database_url, job_queue=queue)
    client = TestClient(app)

    response = client.post("/api/radars/toir-quick-live/runs", json={"live": True, "requester": "test"})

    assert response.status_code == 202
    assert queue.visible_statuses == ["queued"]


def test_post_radar_run_preserves_explicit_smoke_task_context(tmp_path: Path) -> None:
    database_url = _create_seeded_database(tmp_path)
    queue = _RecordingJobQueue()
    app = _app(tmp_path, database_url=database_url, job_queue=queue)
    client = TestClient(app)

    response = client.post(
        "/api/radars/toir-quick-live/runs",
        json={
            "live": True,
            "requester": "test",
            "task_context": {
                "run_profile": "smoke",
                "max_web_tasks_per_subject": 4,
                "max_discovery_tasks_per_rule": 5,
                "max_gate_tasks_per_candidate_rule": 6,
                "max_signal_tasks_per_candidate_signal": 7,
                "max_total_web_tasks_per_run": 18,
                "source_verification_mode": "off",
                "min_useful_sources_per_discovery_task": 8,
                "min_candidates_per_discovery_task": 9,
                "max_discovery_retries_per_task": 10,
                "max_checkpoint_revisions_per_run": 11,
                "max_checkpoint_retries_per_stage": 12,
                "max_openrouter_calls_per_run": 0,
                "max_dadata_lookups_per_run": 1,
                "max_source_verification_requests_per_run": 2,
                "max_provider_retries_per_task": 0,
                "smoke_max_candidates": 1,
                "smoke_max_signals": 1,
            },
        },
    )

    assert response.status_code == 202
    run_id = response.json()["run_id"]
    task_context = client.get(f"/api/radar-runs/{run_id}/dossier").json()["run_context"]["task_context"]
    assert task_context["run_profile"] == "smoke"
    assert task_context["max_web_tasks_per_subject"] == 4
    assert task_context["max_discovery_tasks_per_rule"] == 5
    assert task_context["max_gate_tasks_per_candidate_rule"] == 6
    assert task_context["max_signal_tasks_per_candidate_signal"] == 7
    assert task_context["max_total_web_tasks_per_run"] == 18
    assert task_context["source_verification_mode"] == "off"
    assert task_context["min_useful_sources_per_discovery_task"] == 8
    assert task_context["min_candidates_per_discovery_task"] == 9
    assert task_context["max_discovery_retries_per_task"] == 10
    assert task_context["max_checkpoint_revisions_per_run"] == 11
    assert task_context["max_checkpoint_retries_per_stage"] == 12
    assert task_context["max_openrouter_calls_per_run"] == 0
    assert task_context["max_dadata_lookups_per_run"] == 1
    assert task_context["max_source_verification_requests_per_run"] == 2
    assert task_context["max_provider_retries_per_task"] == 0
    assert task_context["smoke_max_candidates"] == 1
    assert task_context["smoke_max_signals"] == 1


def test_radar_run_dossier_explains_zero_product_sources(tmp_path: Path) -> None:
    database_url = _create_seeded_database(tmp_path)
    app = _app(tmp_path, database_url=database_url)
    client = TestClient(app)

    run = client.post(
        "/api/radars/toir-quick-live/runs",
        json={"live": True, "requester": "test", "task_context": {"source": "zero-source-test"}},
    ).json()
    artifact = _artifact()
    artifact["sources"] = []
    artifact["candidates"][0]["evidence_refs"] = []
    artifact["candidates"][0]["qualification"][0]["evidence_refs"] = []
    artifact["candidates"][0]["signals"][0]["evidence_refs"] = []
    artifact["run_metadata"]["execution_results"]["used_source_count"] = 0
    artifact["run_metadata"]["execution_results"]["analyzed_source_count"] = 2
    artifact["run_metadata"]["execution_results"]["analyzed_sources"] = [
        {"evidence_ref": "blocked_src", "title": "Blocked source", "url": "https://example.test/blocked", "reason": "unreachable"},
        {"evidence_ref": "unlinked_src", "title": "Unlinked source", "url": "https://example.test/unlinked", "reason": "not_used_by_candidate"},
    ]
    artifact["run_metadata"]["execution_results"]["external_call_budget_settings"] = {
        "max_openrouter_calls_per_run": 14,
        "max_recall_expansion_openrouter_calls_per_run": 4,
    }
    artifact["run_metadata"]["execution_results"]["external_call_budget_counters"] = {
        "openrouter:run": 14,
        "openrouter_recall_expansion:run": 1,
    }
    artifact["run_metadata"]["execution_results"]["external_call_budget_counters_by_role"] = {
        "openrouter": 14,
        "openrouter_recall_expansion": 1,
    }
    artifact["run_metadata"]["execution_results"]["external_call_budget_exhaustion_events"] = [
        {"reason": "external_call_budget_exhausted", "key": "openrouter:run"}
    ]
    artifact["run_metadata"]["execution_results"]["work_admission_reserved_capacity"] = {
        "guaranteed_recall_expansion": {
            "reserved_task_count": 2,
            "first_call_used_count": 1,
            "first_call_remaining_count": 1,
        }
    }
    artifact["run_metadata"]["execution_results"]["semantic_task_budget_counters"] = {
        "semantic_reserve:production_site_coverage_probe": 2
    }
    artifact["run_metadata"]["execution_results"]["semantic_task_budget_exhaustion_events"] = [
        {"reason": "semantic_task_reserve_exhausted", "reserve_key": "production_site_coverage_probe"}
    ]
    artifact["run_metadata"]["execution_results"]["target_probe_guarantees"] = {
        "target_probe_minimums_satisfied": False
    }
    artifact["run_metadata"]["execution_results"]["target_probe_guarantee_failures"] = [
        {"target_type": "production_site_or_branch_target", "reason": "semantic_task_budget_limited"}
    ]
    artifact["run_metadata"]["execution_results"]["work_scheduler_plan"] = {"work_item_count": 2}
    artifact["run_metadata"]["execution_results"]["work_scheduler_ledger"] = {"accepted_count": 1, "rejected_count": 1}
    artifact["run_metadata"]["execution_results"]["search_expansion_selection_summary"] = {
        "selected_guaranteed_count": 1,
        "selected_optional_count": 0,
        "effective_max_variants": 5,
    }
    artifact["run_metadata"]["execution_results"]["search_expansion_selection_diagnostics"] = [
        {"target_type": "production_site_or_branch_target", "reason": "selection_below_minimum"}
    ]
    artifact["run_metadata"]["execution_results"]["search_expansion_target_coverage"] = [
        {
            "target_id": "site-1",
            "target_type": "production_site_or_branch_target",
            "coverage_state": "not_admitted",
            "not_searched_reason": "budget_reserve_exhausted",
        }
    ]
    artifact["run_metadata"]["execution_results"]["legal_subsidiary_completion_summary"] = {
        "target_type": "known_subsidiary_or_legal_entity_target",
        "generated_count": 3,
        "selected_variant_count": 2,
        "executed_count": 1,
        "not_searched_count": 1,
        "not_searched_by_reason": {"completion_cap_exhausted": 1},
    }
    artifact["run_metadata"]["execution_results"]["work_admission_decisions"] = [
        {"work_id": "work-1", "accepted": True},
        {"work_id": "work-2", "accepted": False, "reason": "budget_reserve_exhausted"},
    ]
    artifact["run_metadata"]["execution_results"]["work_lane_summary"] = {
        "recall_expansion_production_site_branch": {"planned": 2, "accepted": 1, "rejected": 1}
    }
    artifact["run_metadata"]["execution_results"]["work_guarantee_failures"] = [
        {"work_id": "work-2", "target_type": "production_site_or_branch_target", "reason": "budget_reserve_exhausted"}
    ]
    artifact["run_metadata"]["execution_results"]["work_execution_order"] = [{"work_id": "work-1"}]
    artifact["run_metadata"]["execution_results"]["rejected_work_items"] = [{"work_id": "work-2"}]
    artifact["run_metadata"]["execution_results"]["source_verification_cache_stats"] = {
        "source_verification_unique_request_count": 1,
        "source_verification_duplicate_skip_count": 2,
    }
    artifact["run_metadata"]["execution_results"]["source_verification_unique_request_count"] = 1
    artifact["run_metadata"]["execution_results"]["source_verification_duplicate_skip_count"] = 2

    execute_radar_run_once(
        run_id=run["run_id"],
        live_executor=_FakeExecutor(artifact),
        session_factory=app.state.session_factory,
    )

    dossier = client.get(f"/api/radar-runs/{run['run_id']}/dossier").json()
    assert dossier["summary"]["source_count"] == 0
    assert dossier["summary"]["used_source_count"] == 0
    assert dossier["summary"]["analyzed_source_count"] == 2
    assert dossier["sources"] == []
    assert dossier["source_lifecycle_summary"]["total_count"] == 2
    assert dossier["source_lifecycle_summary"]["by_state"] == {"analyzed_only": 1, "verification_failed": 1}
    assert dossier["source_lifecycle_summary"]["by_reason"] == {"not_used_by_candidate": 1, "unreachable": 1}
    assert {item["evidence_ref"] for item in dossier["source_lifecycle"]} == {"blocked_src", "unlinked_src"}
    assert dossier["summary"]["diagnostic_source_count"] == 2
    assert dossier["summary"]["analyzed_only_source_count"] == 1
    assert dossier["external_call_budget_settings"]["max_openrouter_calls_per_run"] == 14
    assert dossier["external_call_budget_counters"]["openrouter:run"] == 14
    assert dossier["external_call_budget_counters_by_role"]["openrouter_recall_expansion"] == 1
    assert dossier["external_call_budget_exhaustion_events"][0]["key"] == "openrouter:run"
    assert dossier["work_admission_reserved_capacity"]["guaranteed_recall_expansion"]["reserved_task_count"] == 2
    assert dossier["semantic_task_budget_counters"]["semantic_reserve:production_site_coverage_probe"] == 2
    assert dossier["semantic_task_budget_exhaustion_events"][0]["reason"] == "semantic_task_reserve_exhausted"
    assert dossier["target_probe_guarantees"]["target_probe_minimums_satisfied"] is False
    assert dossier["target_probe_guarantee_failures"][0]["reason"] == "semantic_task_budget_limited"
    assert dossier["search_expansion_selection_summary"]["selected_guaranteed_count"] == 1
    assert dossier["search_expansion_selection_diagnostics"][0]["reason"] == "selection_below_minimum"
    assert dossier["search_expansion_target_coverage"][0]["coverage_state"] == "not_admitted"
    assert dossier["legal_subsidiary_completion_summary"]["generated_count"] == 3
    assert dossier["legal_subsidiary_completion_summary"]["not_searched_by_reason"] == {"completion_cap_exhausted": 1}
    assert dossier["work_scheduler_ledger"]["rejected_count"] == 1
    assert dossier["work_admission_decisions"][1]["reason"] == "budget_reserve_exhausted"
    assert dossier["work_lane_summary"]["recall_expansion_production_site_branch"]["accepted"] == 1
    assert dossier["work_guarantee_failures"][0]["target_type"] == "production_site_or_branch_target"
    assert dossier["work_execution_order"][0]["work_id"] == "work-1"
    assert dossier["rejected_work_items"][0]["work_id"] == "work-2"
    assert dossier["source_verification_cache_stats"]["source_verification_duplicate_skip_count"] == 2
    assert dossier["source_verification_unique_request_count"] == 1
    assert dossier["source_verification_duplicate_skip_count"] == 2
    serialized = json.dumps(dossier)
    assert not any(marker in serialized for marker in ["chain_of_thought", "hidden_reasoning", "internal_thoughts"])


def test_radar_run_dossier_exposes_retrieved_sources_without_product_sources(tmp_path: Path) -> None:
    database_url = _create_seeded_database(tmp_path)
    app = _app(tmp_path, database_url=database_url)
    client = TestClient(app)
    run = client.post("/api/radars/toir-quick-live/runs", json={"live": True, "requester": "test"}).json()
    artifact = _artifact()
    artifact["sources"] = []
    artifact["candidates"] = []
    artifact["run_metadata"]["execution_results"].update({
        "used_source_count": 0,
        "analyzed_source_count": 0,
        "analyzed_sources": [],
        "retrieved_sources": [
            {"source_ref": "retrieved_1", "title": "Retrieved source", "url": "https://example.test/retrieved"}
        ],
    })

    execute_radar_run_once(
        run_id=run["run_id"],
        live_executor=_FakeExecutor(artifact),
        session_factory=app.state.session_factory,
    )

    dossier = client.get(f"/api/radar-runs/{run['run_id']}/dossier").json()
    assert dossier["summary"]["source_count"] == 0
    assert dossier["summary"]["retrieved_source_count"] == 1
    assert dossier["summary"]["diagnostic_source_count"] == 1
    assert dossier["source_lifecycle_summary"]["by_state"] == {"retrieved": 1}
    assert dossier["source_lifecycle"][0]["reason"] == "retrieved_not_extracted"


def test_radar_run_dossier_retrieved_source_count_uses_origin_metadata(tmp_path: Path) -> None:
    database_url = _create_seeded_database(tmp_path)
    app = _app(tmp_path, database_url=database_url)
    client = TestClient(app)
    run = client.post("/api/radars/toir-quick-live/runs", json={"live": True, "requester": "test"}).json()
    artifact = _artifact()
    artifact["sources"] = []
    artifact["candidates"] = []
    artifact["run_metadata"]["execution_results"].update({
        "retrieved_sources": [
            {"source_ref": "retrieved_1", "title": "Retrieved source", "url": "https://example.test/retrieved"}
        ],
        "analyzed_sources": [
            {"source_ref": "retrieved_1", "title": "Retrieved source", "url": "https://example.test/retrieved", "outcome": "not_used_by_candidate"}
        ],
    })

    execute_radar_run_once(
        run_id=run["run_id"],
        live_executor=_FakeExecutor(artifact),
        session_factory=app.state.session_factory,
    )

    dossier = client.get(f"/api/radar-runs/{run['run_id']}/dossier").json()
    assert dossier["summary"]["retrieved_source_count"] == 1
    assert dossier["summary"]["analyzed_only_source_count"] == 1
    assert dossier["source_lifecycle_summary"]["by_state"] == {"analyzed_only": 1}


def test_radar_run_dossier_marks_retrieved_sources_with_failed_evidence_linking(tmp_path: Path) -> None:
    database_url = _create_seeded_database(tmp_path)
    app = _app(tmp_path, database_url=database_url)
    client = TestClient(app)
    run = client.post("/api/radars/toir-quick-live/runs", json={"live": True, "requester": "test"}).json()
    artifact = _artifact()
    artifact["sources"] = []
    artifact["candidates"] = []
    artifact["run_metadata"]["execution_results"].update({
        "used_source_count": 0,
        "analyzed_source_count": 0,
        "analyzed_sources": [],
        "retrieved_sources": [
            {"source_ref": "unresolved_src", "title": "Unresolved source", "url": "https://example.test/unresolved"}
        ],
        "extraction_validation_results": [
            {"state": "evidence_linking_failed", "issues": [{"code": "evidence_linking_failed"}]},
        ],
    })

    execute_radar_run_once(
        run_id=run["run_id"],
        live_executor=_FakeExecutor(artifact),
        session_factory=app.state.session_factory,
    )

    dossier = client.get(f"/api/radar-runs/{run['run_id']}/dossier").json()
    assert dossier["sources"] == []
    assert dossier["summary"]["linking_failed_source_count"] == 1
    assert dossier["source_lifecycle"][0]["state"] == "linking_failed"
    assert dossier["source_lifecycle"][0]["reason"] == "evidence_linking_failed"


def test_radar_run_dossier_marks_retrieved_sources_rejected_by_extraction_schema(tmp_path: Path) -> None:
    database_url = _create_seeded_database(tmp_path)
    app = _app(tmp_path, database_url=database_url)
    client = TestClient(app)
    run = client.post("/api/radars/toir-quick-live/runs", json={"live": True, "requester": "test"}).json()
    artifact = _artifact()
    artifact["sources"] = []
    artifact["candidates"] = []
    artifact["run_metadata"]["execution_results"].update({
        "used_source_count": 0,
        "analyzed_source_count": 0,
        "analyzed_sources": [],
        "retrieved_sources": [
            {"source_ref": "schema_src", "title": "Schema rejected source", "url": "https://example.test/schema"}
        ],
        "extraction_validation_results": [
            {"state": "extraction_schema_invalid", "issues": [{"code": "extraction_schema_invalid"}]},
        ],
    })

    execute_radar_run_once(
        run_id=run["run_id"],
        live_executor=_FakeExecutor(artifact),
        session_factory=app.state.session_factory,
    )

    dossier = client.get(f"/api/radar-runs/{run['run_id']}/dossier").json()
    assert dossier["summary"]["schema_rejected_source_count"] == 1
    assert dossier["source_lifecycle"][0]["state"] == "schema_rejected"
    assert dossier["source_lifecycle"][0]["reason"] == "extraction_schema_invalid"


def test_radar_run_dossier_summary_exposes_stopped_for_review_outcome(tmp_path: Path) -> None:
    database_url = _create_seeded_database(tmp_path)
    app = _app(tmp_path, database_url=database_url)
    client = TestClient(app)
    run = client.post("/api/radars/toir-quick-live/runs", json={"live": True, "requester": "test"}).json()
    artifact = _artifact()
    artifact["sources"] = []
    artifact["candidates"] = []
    artifact["run_metadata"]["execution_results"].update({
        "stopped_for_review_reason": "No qualified candidate scope is available for signal search.",
        "checkpoint_summary": {
            "decision_count": 1,
            "by_action": {"stop_review_needed": 1},
            "by_reason": {"no_candidate_scope": 1},
            "blocking_count": 1,
            "stopped_for_review": True,
            "hard_failure_recommended": False,
        },
    })

    execute_radar_run_once(
        run_id=run["run_id"],
        live_executor=_FakeExecutor(artifact),
        session_factory=app.state.session_factory,
    )

    dossier = client.get(f"/api/radar-runs/{run['run_id']}/dossier").json()
    assert dossier["summary"]["execution_outcome"] == "stopped_for_review"
    assert dossier["summary"]["execution_outcome_reason"] == "No qualified candidate scope is available for signal search."


def test_radar_run_dossier_preserves_verification_limited_source_reason(tmp_path: Path) -> None:
    database_url = _create_seeded_database(tmp_path)
    app = _app(tmp_path, database_url=database_url)
    client = TestClient(app)
    run = client.post("/api/radars/toir-quick-live/runs", json={"live": True, "requester": "test"}).json()
    artifact = _artifact()
    artifact["sources"] = []
    artifact["candidates"] = []
    artifact["run_metadata"]["execution_results"].update({
        "used_source_count": 0,
        "analyzed_source_count": 0,
        "analyzed_sources": [],
        "source_verification_results": [
            {
                "evidence_ref": "timeout_src",
                "title": "Timeout source",
                "url": "https://example.test/timeout",
                "verification_state": "timeout",
                "verification_mode": "soft",
                "verification_reason": "request_timeout",
            }
        ],
    })

    execute_radar_run_once(
        run_id=run["run_id"],
        live_executor=_FakeExecutor(artifact),
        session_factory=app.state.session_factory,
    )

    dossier = client.get(f"/api/radar-runs/{run['run_id']}/dossier").json()
    assert dossier["source_lifecycle"][0]["state"] == "verification_failed"
    assert dossier["source_lifecycle"][0]["reason"] == "timeout"
    assert dossier["source_lifecycle"][0]["verification_state"] == "timeout"
    assert dossier["source_lifecycle"][0]["verification_reason"] == "request_timeout"


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


def test_post_radar_run_persists_configured_web_task_budget(tmp_path: Path) -> None:
    database_url = _create_seeded_database(tmp_path)
    queue = _RecordingJobQueue()
    client = TestClient(_app(
        tmp_path,
        database_url=database_url,
        job_queue=queue,
        max_web_tasks_per_subject=7,
        max_signal_tasks_per_candidate_signal=3,
        max_total_web_tasks_per_run=25,
    ))

    run = client.post("/api/radars/toir-quick-live/runs", json={"live": False}).json()
    dossier = client.get(f"/api/radar-runs/{run['run_id']}/dossier").json()

    assert dossier["run_context"]["task_context"]["max_web_tasks_per_subject"] == 7
    assert dossier["run_context"]["task_context"]["max_signal_tasks_per_candidate_signal"] == 3
    assert dossier["run_context"]["task_context"]["max_total_web_tasks_per_run"] == 25


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
    max_web_tasks_per_subject: int = 20,
    max_signal_tasks_per_candidate_signal: int | None = None,
    max_total_web_tasks_per_run: int | None = None,
):
    return create_app(
        ApiSettings(
            environment="test",
            database_url=database_url or sqlite_url(tmp_path / "api.db"),
            radar_max_web_tasks_per_subject=max_web_tasks_per_subject,
            radar_max_signal_tasks_per_candidate_signal=max_signal_tasks_per_candidate_signal,
            radar_max_total_web_tasks_per_run=max_total_web_tasks_per_run,
        ),
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


class _ReadDuringEnqueueJobQueue(_RecordingJobQueue):
    def __init__(self, database_path: Path) -> None:
        super().__init__()
        self._database_path = database_path
        self.visible_statuses: list[str] = []

    def enqueue_radar_run(self, run: RadarRunRecord) -> None:
        super().enqueue_radar_run(run)
        with sqlite3.connect(self._database_path) as connection:
            row = connection.execute(
                "select status from radar_runs where run_id = ?",
                (run.run_id,),
            ).fetchone()
        self.visible_statuses.append(str(row[0]) if row else "missing")


class _FakeExecutor:
    def __init__(self, artifact: dict[str, Any]) -> None:
        self._artifact = artifact

    def execute(
        self,
        *,
        live: bool,
        task_context: dict[str, object],
        radar_payload: dict[str, object] | None = None,
    ) -> dict[str, object]:
        _ = live, task_context, radar_payload
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
                "acceptance_metadata": {
                    "source_cards": [
                        {
                            "source_id": "registry",
                            "source_label": "Registry",
                            "connector_profile_id": "generic_registry",
                            "source_type": "company_registry",
                            "usage_obligation": "required_for_identity",
                            "best_for": ["legal entity identity"],
                            "not_for": ["broad natural-language universe discovery without concrete company input"],
                            "required_input_kinds": ["legal_name", "inn", "ogrn"],
                            "returned_fact_kinds": ["legal_identity"],
                            "useful_result_criteria": ["resolved legal entity identity"],
                            "supports_identity": True,
                            "requires_concrete_input": True,
                        }
                    ],
                    "source_capability_decisions": [
                        {
                            "type": "source_capability_matched",
                            "step_id": "discover-q1",
                            "source_id": "registry",
                            "connector_profile_id": "generic_registry",
                            "intended_use": "identity_lookup",
                            "input_shape": "candidate_scope",
                            "reason": "source use matches compiled connector capability",
                        }
                    ],
                    "source_capability_validation": {
                        "accepted": True,
                        "error_count": 0,
                        "decision_count": 1,
                    },
                },
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
                        "usage_obligation": "required_for_identity",
                        "obligation_status": "planned",
                    },
                    {
                        "source_id": "open-web",
                        "source_label": "Open web",
                        "decision": "skipped",
                        "reason": "Registry is sufficient for this fixture.",
                        "rule_ids": ["rule-q1"],
                        "usage_obligation": "preferred",
                        "obligation_status": "skipped_with_rationale",
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
                "candidate_universe": [
                    {
                        "candidate_id": "candidate-a",
                        "legal_name": "Candidate A",
                        "status": "qualified",
                        "origin_task_id": "discover-q1",
                        "source_refs": ["src_1"],
                        "gate_results": [{"criterion_code": "Q1", "final_assessment": "matches"}],
                        "rejection_reasons": [],
                        "coverage_flags": [],
                        "entity_type": "legal_entity",
                        "resolution_status": "resolved",
                        "linked_fact_count": 1,
                        "upstream_discovery_outcome": "confirmed_upstream_lead",
                        "product_acceptance_status": "product_candidate",
                        "upstream_confidence": "high",
                        "upstream_reason": "Source-backed qualification evidence satisfies the candidate-discovery rules.",
                        "product_acceptance_reason": "deterministic_qualification_and_upstream_evidence_passed",
                        "public_result_status": "public_candidate",
                        "public_projection_reason": "promoted_to_public_candidate_row",
                        "candidate_surface_status": "accepted_product_candidate",
                        "candidate_surface_reason": "accepted_by_product_candidate_rules",
                    },
                    {
                        "candidate_id": "candidate-b",
                        "legal_name": "Candidate B",
                        "status": "unknown_review_needed",
                        "origin_task_id": "discover-q1",
                        "source_refs": ["src_1"],
                        "gate_results": [],
                        "rejection_reasons": [],
                        "coverage_flags": [],
                        "entity_type": "legal_entity",
                        "resolution_status": "review_needed",
                        "linked_fact_count": 0,
                        "upstream_discovery_outcome": "review_needed_upstream_lead",
                        "product_acceptance_status": "review_required",
                        "upstream_confidence": "medium",
                        "upstream_reason": "Source-backed legal entity retained for user review.",
                        "product_acceptance_reason": "requires_human_review_before_product_acceptance",
                        "public_result_status": "review_needed_candidate",
                        "public_projection_reason": "source_backed_legal_entity_requires_review",
                        "candidate_surface_status": "review_needed_candidate",
                        "candidate_surface_reason": "source_backed_legal_entity_requires_review",
                    },
                    {
                        "candidate_id": "review-gubkin-plant",
                        "legal_name": "Gubkin gas processing plant",
                        "status": "unknown_review_needed",
                        "origin_task_id": "discover-q1",
                        "source_refs": ["registry_branch_src"],
                        "gate_results": [],
                        "rejection_reasons": [],
                        "coverage_flags": ["registry_match_ambiguous"],
                        "entity_type": "branch",
                        "resolution_status": "review_needed",
                        "linked_fact_count": 0,
                        "not_candidate_reason": "not_standalone_legal_entity",
                        "review_flags": [
                            "registry_match_ambiguous",
                            "not_standalone_legal_entity",
                            "requires_human_review",
                        ],
                        "upstream_discovery_outcome": "review_needed_upstream_lead",
                        "product_acceptance_status": "review_required",
                        "upstream_confidence": "medium",
                        "upstream_reason": "Review-needed upstream entity retained from source-backed diagnostics.",
                        "product_acceptance_reason": "review_entity_not_standalone_legal_entity",
                        "public_result_status": "retained_in_candidate_universe",
                        "public_projection_reason": "review_entity_not_standalone_legal_entity",
                    }
                ],
                "user_visible_candidates": [
                    {
                        "candidate_id": "candidate-a",
                        "legal_name": "Candidate A",
                        "description": "Industrial candidate with maintenance agenda.",
                        "entity_type": "legal_entity",
                        "score": {"fit_score": 2, "intent_score": 2, "tier": "Tier 1"},
                        "review_flags": ["signal_requires_human_review"],
                        "evidence_refs": ["src_1"],
                        "upstream_discovery_outcome": "confirmed_upstream_lead",
                        "product_acceptance_status": "product_candidate",
                        "upstream_confidence": "high",
                        "upstream_reason": "Source-backed qualification evidence satisfies the candidate-discovery rules.",
                        "upstream_source_refs": ["src_1"],
                        "product_acceptance_reason": "deterministic_qualification_and_upstream_evidence_passed",
                        "public_result_status": "public_candidate",
                        "public_projection_reason": "promoted_to_public_candidate_row",
                        "candidate_surface_status": "accepted_product_candidate",
                        "candidate_surface_reason": "accepted_by_product_candidate_rules",
                        "candidate_surface_rank": 1,
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
                    },
                    {
                        "candidate_id": "candidate-b",
                        "legal_name": "Candidate B",
                        "description": "",
                        "entity_type": "legal_entity",
                        "score": {"fit_score": 0, "intent_score": 0, "tier": "Review needed"},
                        "review_flags": ["review_needed_candidate"],
                        "evidence_refs": ["src_1"],
                        "qualification": [],
                        "signals": [],
                        "upstream_discovery_outcome": "review_needed_upstream_lead",
                        "product_acceptance_status": "review_required",
                        "upstream_confidence": "medium",
                        "upstream_reason": "Source-backed legal entity retained for user review.",
                        "upstream_source_refs": ["src_1"],
                        "product_acceptance_reason": "requires_human_review_before_product_acceptance",
                        "public_result_status": "review_needed_candidate",
                        "public_projection_reason": "source_backed_legal_entity_requires_review",
                        "candidate_surface_status": "review_needed_candidate",
                        "candidate_surface_reason": "source_backed_legal_entity_requires_review",
                        "candidate_surface_rank": 2,
                    },
                ],
                "candidate_discovery_reconciliation": {
                    "raw_upstream_lead_count": 3,
                    "public_candidate_count": 1,
                    "visible_candidate_count": 2,
                    "accepted_product_candidate_count": 1,
                    "review_needed_candidate_count": 1,
                    "candidate_universe_count": 3,
                    "unresolved_gap_count": 0,
                    "ledger_entry_count": 3,
                    "product_candidate_count": 1,
                    "universe_only_count": 1,
                    "not_promoted_count": 0,
                    "rejected_or_noise_count": 0,
                    "unexplained_drop_count": 0,
                    "product_candidate_zero_explained": False,
                },
                "product_acceptance_ledger": [
                    {
                        "candidate_id": "candidate-a",
                        "legal_name": "Candidate A",
                        "collection": "public_candidates",
                        "entity_type": "legal_entity",
                        "source_refs": ["src_1"],
                        "upstream_discovery_outcome": "confirmed_upstream_lead",
                        "product_acceptance_status": "product_candidate",
                        "product_acceptance_reason": "deterministic_qualification_and_upstream_evidence_passed",
                        "public_result_status": "public_candidate",
                        "public_projection_reason": "promoted_to_public_candidate_row",
                        "candidate_surface_status": "accepted_product_candidate",
                        "candidate_surface_reason": "accepted_by_product_candidate_rules",
                        "review_flags": ["signal_requires_human_review"],
                    },
                    {
                        "candidate_id": "candidate-b",
                        "legal_name": "Candidate B",
                        "collection": "candidate_universe",
                        "entity_type": "legal_entity",
                        "source_refs": ["src_1"],
                        "upstream_discovery_outcome": "review_needed_upstream_lead",
                        "product_acceptance_status": "review_required",
                        "product_acceptance_reason": "requires_human_review_before_product_acceptance",
                        "public_result_status": "review_needed_candidate",
                        "public_projection_reason": "source_backed_legal_entity_requires_review",
                        "candidate_surface_status": "review_needed_candidate",
                        "candidate_surface_reason": "source_backed_legal_entity_requires_review",
                        "review_flags": ["review_needed_candidate"],
                    },
                    {
                        "candidate_id": "review-gubkin-plant",
                        "legal_name": "Gubkin gas processing plant",
                        "collection": "candidate_universe",
                        "entity_type": "branch",
                        "source_refs": ["registry_branch_src"],
                        "upstream_discovery_outcome": "review_needed_upstream_lead",
                        "product_acceptance_status": "review_required",
                        "product_acceptance_reason": "review_entity_not_standalone_legal_entity",
                        "public_result_status": "retained_in_candidate_universe",
                        "public_projection_reason": "review_entity_not_standalone_legal_entity",
                        "review_flags": [
                            "registry_match_ambiguous",
                            "not_standalone_legal_entity",
                            "requires_human_review",
                        ],
                    },
                ],
                "entity_resolution_results": [
                    {
                        "entity_name": "Candidate A",
                        "entity_type": "legal_entity",
                        "resolution_status": "resolved",
                        "source_refs": ["src_1"],
                        "reason": "Legal entity identity was supported by registry facts.",
                    },
                    {
                        "entity_name": "EP-600",
                        "entity_type": "project",
                        "resolution_status": "linked_to_legal_entity",
                        "resolved_legal_name": "Candidate A",
                        "source_refs": ["src_1"],
                        "reason": "Non-account entity was linked to a resolved legal entity.",
                    },
                ],
                "linked_entity_facts": [
                    {
                        "entity_name": "EP-600",
                        "entity_type": "project",
                        "linked_legal_name": "Candidate A",
                        "source_refs": ["src_1"],
                        "reason": "Non-account entity was linked to a resolved legal entity.",
                    }
                ],
                "entity_resolution_warnings": [],
                "upstream_disambiguation_results": [
                    {
                        "entity_name": "Gubkin gas processing plant",
                        "entity_type": "branch",
                        "resolution_status": "review_needed",
                        "not_candidate_reason": "not_standalone_legal_entity",
                        "source_refs": ["registry_branch_src"],
                        "review_flags": [
                            "registry_match_ambiguous",
                            "not_standalone_legal_entity",
                            "requires_human_review",
                        ],
                        "reason": "Ambiguous registry observation retained for upstream review.",
                    }
                ],
                "cross_source_disambiguation_tasks": [
                    {
                        "task_id": "cross-check-registry-branch-src",
                        "entity_name": "Gubkin gas processing plant",
                        "entity_type": "branch",
                        "source_ids": ["sibur_site"],
                        "source_scope": "global",
                        "purpose": "Cross-check ambiguous registry observation using allowed official/web sources.",
                        "status": "executed",
                        "outcome": "confirmed_relation",
                    }
                ],
                "cross_source_disambiguation_execution": [
                    {
                        "task_id": "cross-check-registry-branch-src",
                        "entity_name": "Gubkin gas processing plant",
                        "entity_type": "branch",
                        "source_ids": ["sibur_site"],
                        "status": "executed",
                        "outcome": "confirmed_relation",
                        "reason": "Cross-source evidence was returned for the review-needed entity.",
                    }
                ],
                "extraction_recovery_records": [
                    {
                        "checkpoint_id": "after-discovery",
                        "phase": "after_discovery",
                        "action": "repair_extraction",
                        "attempt": 1,
                        "task_id": "discover-q1:repair_extraction-1",
                        "outcome": "recovered",
                    }
                ],
                "review_needed_universe_count": 1,
                "linked_branch_or_site_count": 0,
                "source_obligations": [
                    {
                        "source_id": "registry",
                        "source_label": "Registry",
                        "source_type": "company_registry",
                        "trust_level": "high",
                        "usage_obligation": "required_for_identity",
                        "required": True,
                    }
                ],
                "source_obligation_decisions": [
                    {
                        "source_id": "registry",
                        "source_label": "Registry",
                        "source_type": "company_registry",
                        "trust_level": "high",
                        "usage_obligation": "required_for_identity",
                        "required": True,
                        "status": "satisfied",
                        "stage_task_ids": ["discover-q1"],
                    }
                ],
                "source_obligation_summary": {
                    "decision_count": 1,
                    "by_status": {"satisfied": 1},
                    "by_obligation": {"required_for_identity": 1},
                    "blocking_count": 0,
                    "blocking_source_ids": [],
                },
                "coverage_checks": [
                    {
                        "task_id": "coverage-q1",
                        "iteration": 1,
                        "source_count": 1,
                        "candidate_observation_count": 0,
                        "new_candidate_count": 0,
                        "gap_count": 0,
                        "completeness_risk": "low",
                        "warnings": [],
                    }
                ],
                "coverage_warnings": [],
                "unresolved_candidate_gaps": [],
                "discovery_iteration_count": 1,
                "analyzed_source_count": 1,
                "used_source_count": 1,
                "smoke_candidate_cap": 2,
                "promoted_candidate_count": 1,
                "diagnostic_candidate_count": 3,
                "analyzed_sources": [
                    {
                        "evidence_ref": "unused_src",
                        "reason": "not_used_by_candidate",
                    }
                ],
                "retrieval_plan": {
                    "radar_id": "toir-quick-live",
                    "tasks": [
                        {
                            "task_id": "q1",
                            "stage": "signal_search",
                            "subject_type": "signal",
                            "subject_id": "S1",
                            "query": "Candidate A maintenance modernization SIBUR",
                            "purpose": "Find source-backed modernization evidence for Candidate A.",
                            "expected_evidence": ["maintenance modernization", "target group relationship"],
                            "source_scope": "additional",
                            "candidate_scope": ["Candidate A"],
                            "response_contract": {
                                "schema_id": "signal_finding_v1",
                                "expected_sections": ["sources", "candidates.signals", "source_outcomes"],
                                "required_fields": ["signal_code", "status", "score", "evidence_refs"],
                            },
                        }
                    ],
                },
                "budget_settings": {
                    "max_total_web_tasks_per_run": 4,
                    "max_discovery_tasks_per_rule": None,
                    "max_gate_tasks_per_candidate_rule": None,
                    "max_signal_tasks_per_candidate_signal": 1,
                    "compatibility_max_web_tasks_per_subject": 20,
                },
                "budget_counters": {
                    "total": 4,
                    "by_key": {
                        "discovery:Q1": 1,
                        "signal:S1:Candidate A": 1,
                    },
                },
                "budget_exhaustion_events": [
                    {
                        "task_id": "signal-search-s1",
                        "stage": "signal_search",
                        "subject_type": "signal",
                        "subject_id": "S1",
                        "candidate_scope": ["Candidate B"],
                        "budget_key": "run",
                        "limit": 4,
                        "current": 4,
                        "state": "not_searched_budget_limited",
                        "reason": "total_run_budget_exhausted",
                        "message": "Total Radar web task budget reached: 4 tasks.",
                    }
                ],
                "checkpoint_summary": {
                    "decision_count": 1,
                    "by_action": {"continue": 1},
                    "by_reason": {"quality_sufficient": 1},
                    "blocking_count": 0,
                    "stopped_for_review": False,
                    "hard_failure_recommended": False,
                },
                "checkpoint_decisions": [
                    {
                        "checkpoint_id": "before-signal-search",
                        "phase": "before_signal_search",
                        "action": "continue",
                        "reason_code": "quality_sufficient",
                        "severity": "info",
                        "message": "Checkpoint quality gates passed.",
                    }
                ],
                "adaptive_actions": [],
                "checkpoint_warnings": [],
                "stopped_for_review_reason": "",
                "signal_search_statuses": [
                    {
                        "candidate_name": "Candidate A",
                        "signal_id": "S1",
                        "task_id": "signal-search-s1",
                        "search_status": "searched",
                        "not_searched_reason": "",
                    },
                    {
                        "candidate_name": "Candidate B",
                        "signal_id": "S1",
                        "task_id": "signal-search-s1",
                        "search_status": "not_searched_budget_limited",
                        "not_searched_reason": "total_run_budget_exhausted",
                    },
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
                "upstream_discovery_outcome": "confirmed_upstream_lead",
                "product_acceptance_status": "product_candidate",
                "upstream_confidence": "high",
                "upstream_reason": "Source-backed qualification evidence satisfies the candidate-discovery rules.",
                "upstream_source_refs": ["src_1"],
                "product_acceptance_reason": "deterministic_qualification_and_upstream_evidence_passed",
                "public_result_status": "public_candidate",
                "public_projection_reason": "promoted_to_public_candidate_row",
                "candidate_surface_status": "accepted_product_candidate",
                "candidate_surface_reason": "accepted_by_product_candidate_rules",
                "candidate_surface_rank": 1,
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
