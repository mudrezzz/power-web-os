from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from power_web_os.api import create_app
from power_web_os.api.config import ApiSettings
from power_web_os.persistence import Base, create_database_engine
from power_web_os.demo import seed_icp_radar_catalog_database


def _database_url(tmp_path: Path) -> str:
    return f"sqlite:///{(tmp_path / 'api.db').as_posix()}"


def _client(tmp_path: Path, *, database_url: str | None = None) -> TestClient:
    url = database_url or _database_url(tmp_path)
    Base.metadata.create_all(create_database_engine(database_url=url))
    return TestClient(create_app(ApiSettings(database_url=url, environment="test")))


def test_sales_playbook_round_trip(tmp_path: Path) -> None:
    client = _client(tmp_path)
    created = client.post("/api/products", json={"product_code": "roundtrip", "name": "Roundtrip"})
    assert created.status_code == 201
    product_id = created.json()["product_id"]
    draft = client.get(f"/api/products/{product_id}/draft").json()
    draft["product"].update({
        "short_description": "Description",
        "customer_problem": "Problem",
        "value_proposition": "Value",
        "use_contexts": ["Context"],
    })
    draft["buying_roles"] = [{
        "role_code": "business_owner",
        "display_name": "Business owner",
        "business_responsibility": "Owns the business result.",
        "decision_rights": ["Approves the outcome."],
        "required": True,
        "priority": "critical",
        "scope": "account",
        "reason": "Required for a decision.",
        "expected_evidence": ["Public responsibility evidence."],
        "exclusions": [],
    }]
    draft["access_playbook"] = {"route_rules": [], "blocked_channels": [], "available_assets": [], "required_review_for": []}
    update = client.put(f"/api/products/{product_id}/draft", json={
        "expected_revision": draft["draft_revision"],
        "updated_by": "test",
        "product": draft["product"],
        "buying_roles": draft["buying_roles"],
        "access_playbook": draft["access_playbook"],
    })
    assert update.status_code == 200
    published = client.post(f"/api/products/{product_id}/publish", json={"requester": "test", "activate": True})
    assert published.status_code == 200
    assert published.json()["is_active"] is True
    assert published.json()["access_playbook_version_id"] is None
    assert published.json()["access_playbook"] is None

    restarted = _client(tmp_path, database_url=_database_url(tmp_path))
    assert restarted.get(f"/api/products/{product_id}").json()["active_version_number"] == 1
    assert len(restarted.get(f"/api/products/{product_id}/versions").json()) == 1


def test_simplified_playbook_round_trip(tmp_path: Path) -> None:
    client = _client(tmp_path)
    product_id = client.post("/api/products", json={"product_code": "simple", "name": "Simple"}).json()["product_id"]
    draft = client.get(f"/api/products/{product_id}/draft").json()
    draft["product"].update({
        "short_description": "Description",
        "customer_problem": "Problem",
        "value_proposition": "Value",
        "use_contexts": ["Context"],
    })
    role = {
        "role_code": "outcome_owner",
        "display_name": "Outcome owner",
        "business_responsibility": "Owns the outcome.",
        "required": True,
        "scope": "account",
    }
    updated = client.put(f"/api/products/{product_id}/draft", json={
        "expected_revision": draft["draft_revision"],
        "updated_by": "test",
        "product": draft["product"],
        "buying_roles": [role],
    })
    assert updated.status_code == 200
    assert updated.json()["buying_roles"][0]["priority"] == "high"
    assert client.post(f"/api/products/{product_id}/publish", json={"requester": "test"}).status_code == 200

    restarted = _client(tmp_path, database_url=_database_url(tmp_path))
    version = restarted.get(f"/api/products/{product_id}/versions").json()[0]
    assert version["access_playbook_version_id"] is None
    assert version["buying_roles"][0]["business_responsibility"] == "Owns the outcome."


def test_access_playbook_is_frozen_for_new_publications(tmp_path: Path) -> None:
    client = _client(tmp_path)
    product_id = client.post("/api/products", json={"product_code": "frozen", "name": "Frozen"}).json()["product_id"]
    draft = client.get(f"/api/products/{product_id}/draft").json()
    changed_access = dict(draft["access_playbook"])
    changed_access["blocked_channels"] = ["new-rule"]

    response = client.put(f"/api/products/{product_id}/draft", json={
        "expected_revision": draft["draft_revision"],
        "updated_by": "test",
        "product": draft["product"],
        "buying_roles": draft["buying_roles"],
        "access_playbook": changed_access,
    })

    assert response.status_code == 409
    assert response.json()["detail"] == "access_playbook_frozen"


def test_published_version_is_immutable_and_stale_draft_conflicts(tmp_path: Path) -> None:
    client = _client(tmp_path)
    product_id = client.post("/api/products", json={"product_code": "conflict", "name": "Conflict"}).json()["product_id"]
    draft = client.get(f"/api/products/{product_id}/draft").json()
    request = {
        "expected_revision": draft["draft_revision"],
        "updated_by": "first",
        "product": draft["product"],
        "buying_roles": draft["buying_roles"],
        "access_playbook": draft["access_playbook"],
    }
    assert client.put(f"/api/products/{product_id}/draft", json=request).status_code == 200
    assert client.put(f"/api/products/{product_id}/draft", json=request).status_code == 409
    assert "put" not in client.app.openapi()["paths"][f"/api/products/{{product_id}}/versions/{{version_id}}"]


def test_smartdiagnostics_seed_is_idempotent(tmp_path: Path) -> None:
    url = _database_url(tmp_path)
    seed_icp_radar_catalog_database(
        input_path=Path("demo/fixtures/icp_radar/sibur_icp_pass1.xlsx"),
        database_url=url,
    )
    seed_icp_radar_catalog_database(
        input_path=Path("demo/fixtures/icp_radar/sibur_icp_pass1.xlsx"),
        database_url=url,
    )
    client = _client(tmp_path, database_url=url)
    products = client.get("/api/products").json()
    assert [item["product_id"] for item in products].count("product-smartdiagnostics") == 1
    versions = client.get("/api/products/product-smartdiagnostics/versions").json()
    assert len(versions) == 1
    assert len(versions[0]["buying_roles"]) == 8
    energy = client.get("/api/products/product-industrial-energy-optimization/versions").json()
    assert len(energy) == 1
    assert len(energy[0]["buying_roles"]) == 6
    policy = client.get("/api/radars/benchmark-sibur-holding-contour/power-web-policy").json()
    assert [item["product_id"] for item in policy["product_bindings"]] == [
        "product-smartdiagnostics",
        "product-industrial-energy-optimization",
    ]
