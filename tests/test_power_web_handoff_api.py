from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from power_web_os.api import create_app
from power_web_os.api.config import ApiSettings
from power_web_os.application.radar.lifecycle.records import (
    RadarRecord,
    RadarRunOutputRecord,
    RadarRunRecord,
    RadarRunStatus,
)
from power_web_os.persistence import (
    Base,
    SqlAlchemyRadarRepository,
    SqlAlchemyRadarRunOutputRepository,
    SqlAlchemyRadarRunRepository,
    create_database_engine,
    create_session_factory,
    session_scope,
)
from power_web_os.persistence.models import RadarRunModel


def _database_url(tmp_path: Path) -> str:
    return f"sqlite:///{(tmp_path / 'handoff-api.db').as_posix()}"


def _client(url: str) -> TestClient:
    Base.metadata.create_all(create_database_engine(database_url=url))
    return TestClient(create_app(ApiSettings(database_url=url, environment="test")))


def _seed_candidate(url: str, *, review: bool = False) -> None:
    engine = create_database_engine(database_url=url)
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    row = {
        "candidate_id": "candidate-a",
        "legal_name": "Example Plant",
        "entity_type": "legal_entity",
        "inn": "7700000000",
        "evidence_refs": ["source-a"],
        "candidate_surface_status": "review_needed_candidate" if review else "accepted_product_candidate",
        "product_acceptance_status": "review_required" if review else "product_candidate",
    }
    with session_scope(factory) as session:
        SqlAlchemyRadarRepository(session).upsert(
            RadarRecord(radar_id="radar-a", name="Radar A", status="active", owner="ABM")
        )
        runs = SqlAlchemyRadarRunRepository(session)
        runs.create(RadarRunRecord(run_id="radar-run-a", radar_id="radar-a"))
        runs.update_status("radar-run-a", RadarRunStatus.COMPLETED)
        SqlAlchemyRadarRunOutputRepository(session).upsert(RadarRunOutputRecord(
            run_id="radar-run-a",
            artifact_version="test",
            radar_payload={"radar_id": "radar-a"},
            search_plan_payload={},
            sources_payload=[{"evidence_ref": "source-a"}],
            candidates_payload=[row],
            artifact_payload={
                "artifact_type": "icp_radar_live_run",
                "run_metadata": {"execution_results": {"user_visible_candidates": [row]}},
            },
        ))


def _published_product(client: TestClient, *, code: str, role_count: int) -> str:
    product_id = client.post("/api/products", json={"product_code": code, "name": code.title()}).json()["product_id"]
    draft = client.get(f"/api/products/{product_id}/draft").json()
    draft["product"].update({
        "short_description": "Description",
        "customer_problem": "Problem",
        "value_proposition": "Value",
        "use_contexts": ["Context"],
    })
    roles = [{
        "role_code": f"role_{index}",
        "display_name": f"Role {index}",
        "business_responsibility": f"Responsibility {index}",
        "required": index == 0,
        "scope": "account",
    } for index in range(role_count)]
    response = client.put(f"/api/products/{product_id}/draft", json={
        "expected_revision": draft["draft_revision"],
        "updated_by": "test",
        "product": draft["product"],
        "buying_roles": roles,
    })
    assert response.status_code == 200
    assert client.post(f"/api/products/{product_id}/publish", json={"requester": "test"}).status_code == 200
    return product_id


def test_power_web_policy_and_handoff_round_trip(tmp_path: Path) -> None:
    url = _database_url(tmp_path)
    _seed_candidate(url)
    client = _client(url)
    first = _published_product(client, code="first", role_count=2)
    second = _published_product(client, code="second", role_count=1)

    policy = client.put("/api/radars/radar-a/power-web-policy", json={
        "expected_policy_version_id": None,
        "product_ids": [first, second],
        "requester": "tester",
    })
    assert policy.status_code == 200
    assert [item["product_id"] for item in policy.json()["product_bindings"]] == [first, second]

    preflight = client.get("/api/radars/radar-a/power-web-handoff/preflight", params={
        "source_candidate_run_id": "radar-run-a", "candidate_id": "candidate-a"
    })
    assert preflight.status_code == 200
    assert preflight.json()["ready"] is True
    assert preflight.json()["role_demand_count"] == 3

    created = client.post("/api/radars/radar-a/power-web-handoffs", json={
        "source_candidate_run_id": "radar-run-a",
        "candidate_id": "candidate-a",
        "product_ids": [first],
        "include_latest_signal_context": True,
        "idempotency_key": "api-handoff",
        "requester": "tester",
    })
    assert created.status_code == 201
    payload = created.json()
    assert payload["account"]["account_id"] == "account-inn-7700000000"
    assert len(payload["product_role_demand_sets"][0]["role_demands"]) == 2
    assert payload["source_signal_run_id"] is None

    repeated = client.post("/api/radars/radar-a/power-web-handoffs", json={
        "source_candidate_run_id": "radar-run-a",
        "candidate_id": "candidate-a",
        "product_ids": [first],
        "include_latest_signal_context": True,
        "idempotency_key": "api-handoff",
        "requester": "tester",
    })
    assert repeated.status_code == 201
    assert repeated.json()["handoff_id"] == payload["handoff_id"]

    restarted = _client(url)
    assert restarted.get(f"/api/power-web-handoffs/{payload['handoff_id']}").json() == payload
    history = restarted.get("/api/radars/radar-a/power-web-handoffs", params={
        "source_candidate_run_id": "radar-run-a", "candidate_id": "candidate-a"
    }).json()
    assert len(history) == 1


def test_handoff_has_zero_provider_and_pipeline_calls(tmp_path: Path) -> None:
    url = _database_url(tmp_path)
    _seed_candidate(url)
    client = _client(url)
    product_id = _published_product(client, code="zero-network", role_count=1)
    client.put("/api/radars/radar-a/power-web-policy", json={
        "expected_policy_version_id": None, "product_ids": [product_id], "requester": "tester"
    })
    engine = create_database_engine(database_url=url)
    with engine.connect() as connection:
        before = connection.execute(select(func.count()).select_from(RadarRunModel)).scalar_one()
    response = client.post("/api/radars/radar-a/power-web-handoffs", json={
        "source_candidate_run_id": "radar-run-a",
        "candidate_id": "candidate-a",
        "idempotency_key": "zero-network-handoff",
        "requester": "tester",
    })
    assert response.status_code == 201
    with engine.connect() as connection:
        after = connection.execute(select(func.count()).select_from(RadarRunModel)).scalar_one()
    assert before == after == 1
    assert response.json()["run_kind"] == "initial"
    assert response.json()["previous_power_web_run_id"] is None
