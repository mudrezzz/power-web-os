from fastapi.testclient import TestClient

from power_web_os.api import create_app
from power_web_os.api.config import ApiSettings


def test_health_endpoint_returns_backend_identity() -> None:
    app = create_app(ApiSettings(environment="test"))
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "Power Web OS API",
        "version": "0.7.0",
        "environment": "test",
    }


def test_api_health_alias_matches_root_health_contract() -> None:
    client = TestClient(create_app(ApiSettings(environment="test")))

    assert client.get("/api/health").json() == client.get("/health").json()


def test_openapi_contains_system_health_contract() -> None:
    client = TestClient(create_app(ApiSettings(environment="test")))

    schema = client.get("/openapi.json").json()

    assert schema["info"]["title"] == "Power Web OS API"
    assert schema["info"]["version"] == "0.7.0"
    assert "/health" in schema["paths"]
    assert "/api/health" in schema["paths"]
