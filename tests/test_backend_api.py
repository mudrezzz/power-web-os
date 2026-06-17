from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from power_web_os.api import create_app
from power_web_os.api.config import ApiSettings
from power_web_os.application.radar_records import (
    RadarDefinitionRecord,
    RadarRecord,
    RadarRunRecord,
)
from power_web_os.persistence import (
    Base,
    SqlAlchemyRadarDefinitionRepository,
    SqlAlchemyRadarRepository,
    SqlAlchemyRadarRunRepository,
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
        "version": "0.7.3",
        "environment": "test",
    }


def test_api_health_alias_matches_root_health_contract(tmp_path: Path) -> None:
    client = TestClient(_app(tmp_path))

    assert client.get("/api/health").json() == client.get("/health").json()


def test_openapi_contains_system_and_radar_contracts(tmp_path: Path) -> None:
    client = TestClient(_app(tmp_path))

    schema = client.get("/openapi.json").json()

    assert schema["info"]["title"] == "Power Web OS API"
    assert schema["info"]["version"] == "0.7.3"
    for path in [
        "/health",
        "/api/health",
        "/api/radars",
        "/api/radars/{radar_id}",
        "/api/radars/{radar_id}/runs",
        "/api/radar-runs/{run_id}",
        "/api/radar-runs/{run_id}/candidates",
    ]:
        assert path in schema["paths"]


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


def test_post_radar_run_executes_inline_and_persists_output(tmp_path: Path) -> None:
    database_url = _create_seeded_database(tmp_path)
    client = TestClient(_app(tmp_path, database_url=database_url, artifact=_artifact()))

    response = client.post(
        "/api/radars/toir-quick-live/runs",
        json={
            "live": False,
            "idempotency_key": "radar:live:api",
            "correlation_id": "corr-api-1",
            "requester": "test",
        },
    )

    assert response.status_code == 200
    run = response.json()
    assert run["status"] == "completed"
    assert run["radar_id"] == "toir-quick-live"
    assert run["correlation_id"] == "corr-api-1"
    assert run["output"]["candidate_count"] == 1
    assert run["output"]["source_count"] == 1

    detail = client.get(f"/api/radar-runs/{run['run_id']}").json()
    assert detail["status"] == "completed"
    assert detail["output"]["candidate_count"] == 1

    candidates = client.get(f"/api/radar-runs/{run['run_id']}/candidates").json()
    assert candidates["radar_id"] == "toir-quick-live"
    assert candidates["sources"][0]["evidence_ref"] == "src_1"
    candidate = candidates["candidates"][0]
    assert candidate["legal_name"] == "Candidate A"
    assert candidate["score"]["tier"] == "Tier 1"
    assert candidate["qualification"][0]["source_usages"][0]["source_ref"] == "src_1"
    assert candidate["qualification"][0]["evidence_findings"][0]["why_it_matches_rule"]
    assert candidate["signals"][0]["score_evaluation"]["applied_score"] == 2


def test_post_radar_run_persists_failed_run_without_untracked_http_500(tmp_path: Path) -> None:
    database_url = _create_seeded_database(tmp_path)
    client = TestClient(_app(tmp_path, database_url=database_url, executor=_FailingExecutor()))

    response = client.post("/api/radars/toir-quick-live/runs", json={"live": True})

    assert response.status_code == 200
    run = response.json()
    assert run["status"] == "failed"
    assert run["error_message"] == "provider unavailable"
    assert run["error_metadata"]["exception_type"] == "RuntimeError"
    assert run["output"] is None


def test_api_missing_and_no_output_cases_return_explicit_statuses(tmp_path: Path) -> None:
    database_url = _create_seeded_database(tmp_path, queued_run=True)
    client = TestClient(_app(tmp_path, database_url=database_url))

    assert client.get("/api/radars/missing").status_code == 404
    assert client.post("/api/radars/missing/runs", json={"live": False}).status_code == 404
    assert client.get("/api/radar-runs/missing").status_code == 404
    assert client.get("/api/radar-runs/missing/candidates").status_code == 404
    assert client.get("/api/radar-runs/queued-run/candidates").status_code == 409


def _app(
    tmp_path: Path,
    *,
    database_url: str | None = None,
    artifact: dict[str, Any] | None = None,
    executor: object | None = None,
):
    return create_app(
        ApiSettings(environment="test", database_url=database_url or sqlite_url(tmp_path / "api.db")),
        live_executor_factory=lambda: executor or _FakeExecutor(artifact or _artifact()),
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


class _FakeExecutor:
    def __init__(self, artifact: dict[str, Any]) -> None:
        self._artifact = artifact

    def execute(self, *, live: bool, task_context: dict[str, object]) -> dict[str, object]:
        _ = live, task_context
        return self._artifact


class _FailingExecutor:
    def execute(self, *, live: bool, task_context: dict[str, object]) -> dict[str, object]:
        _ = live, task_context
        raise RuntimeError("provider unavailable")


def _artifact() -> dict[str, Any]:
    return {
        "artifact_type": "icp_radar_live_run",
        "artifact_version": "0.6.3.4",
        "radar": {"radar_id": "toir-quick-live", "name": "TOIR Quick Live Radar"},
        "run_metadata": {"runtime": "recorded", "candidate_count": 1, "source_count": 1},
        "search_plan": {"radar_id": "toir-quick-live", "queries": []},
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
        "contract_validation": [],
    }
