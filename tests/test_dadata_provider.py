from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

import power_web_os.integrations.dadata_provider as dadata_module
from power_web_os.application.radar_source_providers import CompanyLookupRequest
from power_web_os.integrations.dadata_provider import (
    DaDataCompanyRegistryProvider,
    RecordedDaDataCompanyRegistryProvider,
)


def test_recorded_dadata_lookup_maps_company_observation() -> None:
    provider = RecordedDaDataCompanyRegistryProvider(fixtures=[{
        "source_ref": "dadata_test_company",
        "legal_name": "АО Тестовый завод",
        "inn": "1234567890",
        "ogrn": "1020000000000",
        "status": "ACTIVE",
        "address": "Москва",
        "okved": "20.17",
    }])

    result = provider.lookup_companies(_request(query="Тестовый завод", lookup_terms=["Тестовый завод"]))

    assert result.observations[0].source_ref == "dadata_test_company"
    assert result.observations[0].entity_type == "legal_entity"
    assert result.observations[0].normalized_legal_name
    assert result.observations[0].matched_by == "legal_name"
    assert result.observations[0].legal_name == "АО Тестовый завод"
    assert result.outcomes[0].outcome == "used"
    assert result.provider_metadata["provider"] == "dadata"
    assert result.provider_metadata["dadata_mode"] == "recorded"
    assert result.provider_metadata["registry_lookup_terms"][0]["value"] == "Тестовый завод"
    assert result.provider_metadata["registry_lookup_attempts"][0]["outcome"] == "used"


def test_recorded_dadata_lookup_by_inn_has_high_match_quality() -> None:
    provider = RecordedDaDataCompanyRegistryProvider(fixtures=[{
        "legal_name": "AO Test Plant",
        "inn": "1234567890",
        "ogrn": "1020000000000",
        "status": "ACTIVE",
    }])

    result = provider.lookup_companies(_request(query="1234567890", lookup_terms=["1234567890"]))

    assert result.outcomes[0].outcome == "used"
    assert result.observations[0].matched_by == "inn"
    assert result.observations[0].match_quality == "high"


def test_recorded_dadata_empty_result_is_no_match() -> None:
    provider = RecordedDaDataCompanyRegistryProvider(fixtures=[{"legal_name": "AO Other Plant", "inn": "1234567890"}])

    result = provider.lookup_companies(_request(query="Missing Plant", lookup_terms=["Missing Plant"]))

    assert result.observations == []
    assert result.outcomes[0].outcome == "no_match"


def test_recorded_dadata_ambiguous_result_is_not_auto_accepted() -> None:
    provider = RecordedDaDataCompanyRegistryProvider(fixtures=[
        {"legal_name": "AO Test Plant North", "status": "ACTIVE"},
        {"legal_name": "AO Test Plant South", "status": "ACTIVE"},
    ])

    result = provider.lookup_companies(_request(query="Test Plant", lookup_terms=["Test Plant"]))

    assert len(result.observations) == 2
    assert result.outcomes[0].outcome == "ambiguous_match"


def test_live_dadata_provider_reports_unavailable_without_credentials(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DADATA_API_KEY", raising=False)
    monkeypatch.delenv("DADATA_SECRET_KEY", raising=False)
    provider = DaDataCompanyRegistryProvider(env_path=tmp_path / "missing.env", timeout_seconds=1)

    result = provider.lookup_companies(_request(query="1651025328", lookup_terms=["1651025328"]))

    assert result.observations == []
    assert result.outcomes[0].outcome == "provider_unavailable"
    assert "credentials" in result.outcomes[0].reason.lower()


def test_live_dadata_provider_reports_schema_invalid_for_malformed_response(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def read(self) -> bytes:
            return b'{"unexpected": []}'

    monkeypatch.setattr(dadata_module.urllib_request, "urlopen", lambda *args, **kwargs: FakeResponse())
    provider = DaDataCompanyRegistryProvider(api_key="key", secret_key="secret", timeout_seconds=1)

    result = provider.lookup_companies(_request(query="1234567890", lookup_terms=["1234567890"]))

    assert result.observations == []
    assert result.outcomes[0].outcome == "schema_invalid"


@pytest.mark.live_dadata
def test_live_dadata_lookup_returns_company_observation() -> None:
    """Opt-in live smoke for one bounded DaData lookup, not a full Radar run."""

    if os.getenv("POWER_WEB_OS_RUN_LIVE_DADATA_TESTS", "").lower() not in {"1", "true", "yes"}:
        pytest.skip("Set POWER_WEB_OS_RUN_LIVE_DADATA_TESTS=1 to run live DaData probe.")
    env = _load_env(Path(".env"))
    if not (env.get("DADATA_API_KEY") or os.getenv("DADATA_API_KEY")):
        pytest.skip("DADATA_API_KEY is required for live DaData probe.")
    if not (env.get("DADATA_SECRET_KEY") or os.getenv("DADATA_SECRET_KEY")):
        pytest.skip("DADATA_SECRET_KEY is required for live DaData probe.")

    query = env.get("POWER_WEB_OS_DADATA_TEST_QUERY") or os.getenv("POWER_WEB_OS_DADATA_TEST_QUERY") or "1651025328"
    provider = DaDataCompanyRegistryProvider(env_path=Path(".env"), timeout_seconds=8)

    result = provider.lookup_companies(_request(query=query, lookup_terms=[query]))

    assert result.provider_metadata["provider"] == "dadata"
    assert result.provider_metadata["dadata_mode"] == "live"
    assert result.provider_metadata["dadata_status_code"] == 200
    assert result.outcomes[0].outcome == "used"
    assert result.outcomes[0].observation_count >= 1
    assert result.observations
    assert any(observation.legal_name for observation in result.observations)
    assert any(observation.inn for observation in result.observations)
    _assert_no_secret_markers(result.model_dump() if hasattr(result, "model_dump") else {})


def _request(*, query: str, lookup_terms: list[str]) -> CompanyLookupRequest:
    return CompanyLookupRequest(
        radar_id="toir-quick-live",
        task_id="live-dadata-probe",
        stage="qualification_discovery",
        subject_id="q1-sibur-group",
        query=query,
        source_id="dadata_registry",
        source_label="DaData company registry",
        source_reference="company_registry:dadata",
        lookup_terms=lookup_terms,
        limit=3,
    )


def _load_env(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _assert_no_secret_markers(payload: dict[str, object]) -> None:
    serialized = json.dumps(payload, ensure_ascii=False)
    forbidden = ("DADATA_API_KEY", "DADATA_SECRET_KEY", "Authorization", "Bearer", "Token ")
    assert not any(marker in serialized for marker in forbidden)
