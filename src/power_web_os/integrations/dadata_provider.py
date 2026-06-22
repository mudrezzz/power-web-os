"""DaData company registry provider adapter.

DaData is used as structured company data, not as open web retrieval. The
adapter maps DaData party suggestions into application-level registry
observations and keeps credentials out of traces and artifacts.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from time import perf_counter
from typing import Any
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError

from power_web_os.application.radar_source_providers import (
    CompanyLookupRequest,
    CompanyLookupResult,
    CompanyRegistryObservation,
    CompanyRegistryProvider,
    CompanySourceOutcome,
    RadarSourceRegistry,
)
from power_web_os.application.radar_technical_trace import RadarRunTechnicalTraceCommand, append_current_trace

DEFAULT_DADATA_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/party"


class RecordedDaDataCompanyRegistryProvider(CompanyRegistryProvider):
    provider_id = "dadata"

    def __init__(self, fixtures: list[dict[str, Any]] | None = None) -> None:
        self._fixtures = fixtures or _default_recorded_fixtures()
        self.requests: list[CompanyLookupRequest] = []

    def lookup_companies(self, request: CompanyLookupRequest) -> CompanyLookupResult:
        self.requests.append(request)
        observations = [
            _observation_from_fixture(item)
            for item in self._fixtures
            if _matches_request(item, request)
        ][: request.limit]
        outcome = CompanySourceOutcome(
            source_id=request.source_id,
            provider_id=self.provider_id,
            outcome="used" if observations else "provider_recorded_empty",
            reason=(
                f"Recorded DaData fixture returned {len(observations)} company observations."
                if observations
                else "Recorded DaData fixture had no matching company observations."
            ),
            query=request.query,
            observation_count=len(observations),
        )
        _trace_dadata(
            trace_type="provider_response",
            title="DaData recorded lookup",
            summary=outcome.reason,
            payload={
                "mode": "recorded",
                "source_id": request.source_id,
                "lookup_terms": request.lookup_terms,
                "observation_count": len(observations),
                "observations": [item.model_dump() for item in observations],
            },
        )
        return CompanyLookupResult(
            observations=observations,
            outcomes=[outcome],
            provider_metadata={"provider": "dadata", "dadata_mode": "recorded"},
        )


class DaDataCompanyRegistryProvider(CompanyRegistryProvider):
    provider_id = "dadata"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        secret_key: str | None = None,
        base_url: str | None = None,
        env_path: Path | None = None,
        timeout_seconds: float = 20,
    ) -> None:
        env = _load_env_file(env_path or Path.cwd() / ".env")
        self._api_key = api_key or env.get("DADATA_API_KEY") or os.getenv("DADATA_API_KEY")
        self._secret_key = secret_key or env.get("DADATA_SECRET_KEY") or os.getenv("DADATA_SECRET_KEY")
        self._base_url = base_url or env.get("POWER_WEB_OS_DADATA_BASE_URL") or os.getenv("POWER_WEB_OS_DADATA_BASE_URL") or DEFAULT_DADATA_URL
        self._timeout_seconds = timeout_seconds

    def lookup_companies(self, request: CompanyLookupRequest) -> CompanyLookupResult:
        if not self._api_key or not self._secret_key:
            return _unavailable_result(request, provider_id=self.provider_id, reason="DADATA_API_KEY and DADATA_SECRET_KEY are required for live DaData lookup.")
        query = _best_query(request)
        payload = {"query": query, "count": request.limit}
        _trace_dadata(
            trace_type="provider_request",
            title="DaData company lookup request",
            summary="DaData party suggestions lookup.",
            payload={"url": self._base_url, "request": payload, "source_id": request.source_id},
        )
        started_at = perf_counter()
        http_request = urllib_request.Request(
            self._base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Token {self._api_key}",
                "X-Secret": self._secret_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urllib_request.urlopen(http_request, timeout=self._timeout_seconds) as response:
                body = response.read().decode("utf-8")
                status_code = int(getattr(response, "status", 200))
        except (HTTPError, URLError, TimeoutError) as error:
            _trace_dadata(
                trace_type="provider_error",
                title="DaData company lookup error",
                summary=str(error),
                duration_ms=_duration_ms(started_at),
                payload={"error_type": error.__class__.__name__, "message": str(error), "source_id": request.source_id},
            )
            return _unavailable_result(request, provider_id=self.provider_id, reason=str(error))
        payload_json = json.loads(body)
        observations = [_observation_from_dadata_suggestion(item) for item in payload_json.get("suggestions", []) if isinstance(item, dict)]
        outcome = CompanySourceOutcome(
            source_id=request.source_id,
            provider_id=self.provider_id,
            outcome="used" if observations else "provider_empty",
            reason=f"DaData returned {len(observations)} company observations.",
            query=query,
            observation_count=len(observations),
        )
        _trace_dadata(
            trace_type="provider_response",
            title="DaData company lookup response",
            summary=outcome.reason,
            duration_ms=_duration_ms(started_at),
            payload={
                "status_code": status_code,
                "source_id": request.source_id,
                "observation_count": len(observations),
                "observations": [item.model_dump() for item in observations[:10]],
            },
        )
        return CompanyLookupResult(
            observations=observations,
            outcomes=[outcome],
            provider_metadata={"provider": "dadata", "dadata_mode": "live", "dadata_status_code": status_code},
        )


def dadata_source_registry_from_env(*, env_path: Path | None = None) -> RadarSourceRegistry:
    env = _load_env_file(env_path or Path.cwd() / ".env")
    mode = (env.get("POWER_WEB_OS_DADATA_MODE") or os.getenv("POWER_WEB_OS_DADATA_MODE") or "recorded").strip().lower()
    provider: CompanyRegistryProvider
    if mode == "live":
        provider = DaDataCompanyRegistryProvider(env_path=env_path)
    else:
        provider = RecordedDaDataCompanyRegistryProvider()
    return RadarSourceRegistry(company_registry_providers={"dadata": provider})


def _unavailable_result(request: CompanyLookupRequest, *, provider_id: str, reason: str) -> CompanyLookupResult:
    outcome = CompanySourceOutcome(
        source_id=request.source_id,
        provider_id=provider_id,
        outcome="provider_unavailable",
        reason=reason,
        query=request.query,
        observation_count=0,
    )
    return CompanyLookupResult(
        outcomes=[outcome],
        provider_metadata={"provider": provider_id, "dadata_mode": "unavailable"},
    )


def _observation_from_fixture(item: dict[str, Any]) -> CompanyRegistryObservation:
    return CompanyRegistryObservation(
        source_ref=str(item.get("source_ref") or f"dadata_{item.get('inn', item.get('legal_name', 'company'))}"),
        legal_name=str(item.get("legal_name") or item.get("value") or ""),
        inn=str(item.get("inn") or ""),
        ogrn=str(item.get("ogrn") or ""),
        kpp=str(item.get("kpp") or ""),
        status=str(item.get("status") or ""),
        address=str(item.get("address") or ""),
        okved=str(item.get("okved") or ""),
        revenue=str(item.get("revenue") or ""),
        registry_url=str(item.get("registry_url") or ""),
        facts={key: value for key, value in item.items() if key not in {"source_ref", "legal_name", "value"}},
    )


def _observation_from_dadata_suggestion(item: dict[str, Any]) -> CompanyRegistryObservation:
    data = item.get("data") if isinstance(item.get("data"), dict) else {}
    name = data.get("name") if isinstance(data.get("name"), dict) else {}
    address = data.get("address") if isinstance(data.get("address"), dict) else {}
    state = data.get("state") if isinstance(data.get("state"), dict) else {}
    legal_name = str(name.get("short_with_opf") or name.get("full_with_opf") or item.get("value") or "")
    inn = str(data.get("inn") or "")
    return CompanyRegistryObservation(
        source_ref=f"dadata_{inn or legal_name}".replace(" ", "_")[:80],
        legal_name=legal_name,
        inn=inn,
        ogrn=str(data.get("ogrn") or ""),
        kpp=str(data.get("kpp") or ""),
        status=str(state.get("status") or ""),
        address=str(address.get("unrestricted_value") or item.get("unrestricted_value") or ""),
        okved=str(data.get("okved") or ""),
        facts={"dadata_hid": data.get("hid"), "opf": data.get("opf"), "management": data.get("management")},
    )


def _matches_request(item: dict[str, Any], request: CompanyLookupRequest) -> bool:
    haystack = " ".join(str(value) for value in item.values()).lower()
    terms = [term.lower() for term in request.lookup_terms if len(term.strip()) >= 3]
    return not terms or any(term in haystack or haystack in term for term in terms)


def _best_query(request: CompanyLookupRequest) -> str:
    for term in request.lookup_terms:
        if term.strip():
            return term.strip()
    return request.query


def _default_recorded_fixtures() -> list[dict[str, Any]]:
    return [
        {
            "source_ref": "dadata_1651025328",
            "legal_name": "ПАО «Нижнекамскнефтехим»",
            "inn": "1651025328",
            "ogrn": "1021602502316",
            "status": "ACTIVE",
            "address": "Республика Татарстан, Нижнекамск",
            "okved": "20.17",
            "registry_url": "https://dadata.ru/suggestions/",
        },
        {
            "source_ref": "dadata_2465014500",
            "legal_name": "АО «Красноярский завод синтетического каучука»",
            "inn": "2465014500",
            "status": "ACTIVE",
            "address": "Красноярский край, Красноярск",
            "okved": "20.17",
            "registry_url": "https://dadata.ru/suggestions/",
        },
    ]


def _trace_dadata(
    *,
    trace_type: str,
    title: str,
    summary: str,
    payload: dict[str, Any],
    duration_ms: int | None = None,
) -> None:
    append_current_trace(RadarRunTechnicalTraceCommand(
        run_id="",
        phase="collection",
        node_name="dadata_company_registry",
        trace_type=trace_type,
        title=title,
        summary=summary,
        duration_ms=duration_ms,
        payload=payload,
    ))


def _duration_ms(started_at: float) -> int:
    return int((perf_counter() - started_at) * 1000)


def _load_env_file(path: Path) -> dict[str, str]:
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
