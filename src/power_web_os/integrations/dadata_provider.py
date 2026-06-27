"""DaData company registry provider adapter."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from time import perf_counter
from typing import Any
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError

from power_web_os.application.live_radar_external_budget import reserve_external_call
from power_web_os.application.radar_source_providers import (
    CompanyLookupRequest,
    CompanyLookupResult,
    CompanyRegistryObservation,
    CompanyRegistryProvider,
    CompanySourceOutcome,
    RadarSourceRegistry,
)
from power_web_os.application.radar_technical_trace import RadarRunTechnicalTraceCommand, append_current_trace
from power_web_os.integrations.dadata_lookup_terms import (
    attempt_payload,
    lookup_terms_for_execution,
    request_for_term,
    term_payload,
)
from power_web_os.integrations.dadata_recorded_fixtures import default_recorded_fixtures

DEFAULT_DADATA_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/party"


class RecordedDaDataCompanyRegistryProvider(CompanyRegistryProvider):
    provider_id = "dadata"

    def __init__(self, fixtures: list[dict[str, Any]] | None = None) -> None:
        self._fixtures = fixtures or default_recorded_fixtures()
        self.requests: list[CompanyLookupRequest] = []

    def lookup_companies(self, request: CompanyLookupRequest) -> CompanyLookupResult:
        self.requests.append(request)
        observations: list[CompanyRegistryObservation] = []
        outcomes: list[CompanySourceOutcome] = []
        attempts: list[dict[str, Any]] = []
        limited_budget_decision: dict[str, Any] | None = None
        for term in lookup_terms_for_execution(request):
            term_request = request_for_term(request, term)
            budget_decision = reserve_external_call("dadata", key=request.source_id or self.provider_id, task_id=request.task_id)
            if not budget_decision.accepted:
                limited = _budget_limited_lookup_result(
                    term_request,
                    provider_id=self.provider_id,
                    mode="recorded",
                    decision=budget_decision.to_payload(),
                )
                outcomes.extend(limited.outcomes)
                limited_budget_decision = dict(limited.provider_metadata.get("budget_decision") or {})
                attempts.append(attempt_payload(term=term, outcome=limited.outcomes[0], observation_count=0))
                break
            observations = [
                _with_match_metadata(_observation_from_fixture(item), request=term_request, matched_by=_matched_by_fixture(item, term_request))
                for item in self._fixtures
                if _matches_request(item, term_request)
            ][: request.limit]
            outcome = CompanySourceOutcome(
                source_id=request.source_id,
                provider_id=self.provider_id,
                outcome=_lookup_outcome(observations),
                reason=(
                    f"Recorded DaData fixture returned {len(observations)} company observations."
                    if observations
                    else "Recorded DaData fixture had no matching company observations."
                ),
                query=term,
                observation_count=len(observations),
            )
            outcomes.append(outcome)
            attempts.append(attempt_payload(term=term, outcome=outcome, observation_count=len(observations)))
            if observations:
                break
        _trace_dadata(
            trace_type="provider_response",
            title="DaData recorded lookup",
            summary=outcomes[-1].reason if outcomes else "Recorded DaData lookup did not execute.",
            payload={
                "mode": "recorded",
                "source_id": request.source_id,
                "lookup_terms": request.lookup_terms,
                "attempts": attempts,
                "observation_count": len(observations),
                "observations": [item.model_dump() for item in observations],
            },
        )
        return CompanyLookupResult(
            observations=observations,
            outcomes=outcomes,
            provider_metadata={
                "provider": "dadata",
                "dadata_mode": "recorded",
                "registry_lookup_terms": [term_payload(term) for term in lookup_terms_for_execution(request)],
                "registry_lookup_attempts": attempts,
                **({"budget_decision": limited_budget_decision} if limited_budget_decision else {}),
            },
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
            return _unavailable_result(request, provider_id=self.provider_id, reason="DaData live credentials are required for live company lookup.")
        observations: list[CompanyRegistryObservation] = []
        outcomes: list[CompanySourceOutcome] = []
        attempts: list[dict[str, Any]] = []
        status_code = 0
        limited_budget_decision: dict[str, Any] | None = None
        for query in lookup_terms_for_execution(request):
            term_request = request_for_term(request, query)
            budget_decision = reserve_external_call("dadata", key=request.source_id or self.provider_id, task_id=request.task_id)
            if not budget_decision.accepted:
                limited = _budget_limited_lookup_result(
                    term_request,
                    provider_id=self.provider_id,
                    mode="live",
                    decision=budget_decision.to_payload(),
                )
                outcomes.extend(limited.outcomes)
                limited_budget_decision = dict(limited.provider_metadata.get("budget_decision") or {})
                attempts.append(attempt_payload(term=query, outcome=limited.outcomes[0], observation_count=0))
                break
            result, status_code = self._lookup_single_term(request=term_request, query=query)
            outcomes.extend(result.outcomes)
            observations = result.observations
            if result.outcomes:
                attempts.append(attempt_payload(term=query, outcome=result.outcomes[0], observation_count=len(observations)))
            if observations or any(outcome.outcome in {"provider_unavailable", "invalid_credentials", "rate_limited", "schema_invalid"} for outcome in result.outcomes):
                break
        return CompanyLookupResult(
            observations=observations,
            outcomes=outcomes,
            provider_metadata={
                "provider": "dadata",
                "dadata_mode": "live",
                "dadata_status_code": status_code,
                "registry_lookup_terms": [term_payload(term) for term in lookup_terms_for_execution(request)],
                "registry_lookup_attempts": attempts,
                **({"budget_decision": limited_budget_decision} if limited_budget_decision else {}),
            },
        )

    def _lookup_single_term(self, *, request: CompanyLookupRequest, query: str) -> tuple[CompanyLookupResult, int]:
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
        except HTTPError as error:
            outcome = _http_error_outcome(error, request=request)
            _trace_dadata(
                trace_type="provider_error",
                title="DaData company lookup error",
                summary=outcome.reason,
                duration_ms=_duration_ms(started_at),
                payload={"error_type": error.__class__.__name__, "status_code": error.code, "message": outcome.reason, "source_id": request.source_id},
            )
            return CompanyLookupResult(outcomes=[outcome], provider_metadata={"provider": self.provider_id, "dadata_mode": "unavailable"}), 0
        except (URLError, TimeoutError) as error:
            _trace_dadata(
                trace_type="provider_error",
                title="DaData company lookup error",
                summary="DaData lookup request failed before a usable response was received.",
                duration_ms=_duration_ms(started_at),
                payload={"error_type": error.__class__.__name__, "message": str(error), "source_id": request.source_id},
            )
            return _unavailable_result(request, provider_id=self.provider_id, reason="DaData lookup request failed before a usable response was received."), 0
        try:
            payload_json = json.loads(body)
        except json.JSONDecodeError:
            return _schema_invalid_result(request, provider_id=self.provider_id, reason="DaData returned a non-JSON response."), status_code
        suggestions = payload_json.get("suggestions")
        if not isinstance(suggestions, list):
            return _schema_invalid_result(request, provider_id=self.provider_id, reason="DaData response does not contain a suggestions list."), status_code
        observations = [
            _with_match_metadata(_observation_from_dadata_suggestion(item), request=request, matched_by=_matched_by_dadata(item, request))
            for item in suggestions
            if isinstance(item, dict)
        ][: request.limit]
        outcome = CompanySourceOutcome(
            source_id=request.source_id,
            provider_id=self.provider_id,
            outcome=_lookup_outcome(observations),
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
        return CompanyLookupResult(observations=observations, outcomes=[outcome]), status_code


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


def _schema_invalid_result(request: CompanyLookupRequest, *, provider_id: str, reason: str) -> CompanyLookupResult:
    outcome = CompanySourceOutcome(
        source_id=request.source_id,
        provider_id=provider_id,
        outcome="schema_invalid",
        reason=reason,
        query=request.query,
        observation_count=0,
    )
    _trace_dadata(
        trace_type="provider_error",
        title="DaData response schema invalid",
        summary=reason,
        payload={"source_id": request.source_id, "query": request.query, "outcome": "schema_invalid"},
    )
    return CompanyLookupResult(outcomes=[outcome], provider_metadata={"provider": provider_id, "dadata_mode": "schema_invalid"})


def _budget_limited_lookup_result(
    request: CompanyLookupRequest,
    *,
    provider_id: str,
    mode: str,
    decision: dict[str, object],
) -> CompanyLookupResult:
    reason = str(decision.get("message") or "DaData external-call budget exhausted.")
    outcome = CompanySourceOutcome(
        source_id=request.source_id,
        provider_id=provider_id,
        outcome="not_executed_budget_limited",
        reason=reason,
        query=request.query,
        observation_count=0,
    )
    _trace_dadata(
        trace_type="provider_error",
        title="DaData lookup skipped by external budget",
        summary=reason,
        payload={"source_id": request.source_id, "query": request.query, "budget_decision": decision},
    )
    return CompanyLookupResult(
        outcomes=[outcome],
        provider_metadata={
            "provider": provider_id,
            "dadata_mode": mode,
            "budget_decision": {**decision, "state": "not_executed_budget_limited"},
        },
    )


def _observation_from_fixture(item: dict[str, Any]) -> CompanyRegistryObservation:
    return CompanyRegistryObservation(
        source_ref=str(item.get("source_ref") or f"dadata_{item.get('inn', item.get('legal_name', 'company'))}"),
        legal_name=str(item.get("legal_name") or item.get("value") or ""),
        normalized_legal_name=str(item.get("normalized_legal_name") or _normalize_company_name(str(item.get("legal_name") or item.get("value") or ""))),
        inn=str(item.get("inn") or ""),
        ogrn=str(item.get("ogrn") or ""),
        kpp=str(item.get("kpp") or ""),
        status=str(item.get("status") or ""),
        address=str(item.get("address") or ""),
        okved=str(item.get("okved") or ""),
        revenue=str(item.get("revenue") or ""),
        registry_url=str(item.get("registry_url") or ""),
        entity_type=str(item.get("entity_type") or "legal_entity"),
        match_quality=str(item.get("match_quality") or "medium"),
        matched_by=str(item.get("matched_by") or ""),
        lookup_query=str(item.get("lookup_query") or ""),
        provider_record_id=str(item.get("provider_record_id") or item.get("hid") or item.get("inn") or ""),
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
        normalized_legal_name=_normalize_company_name(legal_name),
        inn=inn,
        ogrn=str(data.get("ogrn") or ""),
        kpp=str(data.get("kpp") or ""),
        status=str(state.get("status") or ""),
        address=str(address.get("unrestricted_value") or item.get("unrestricted_value") or ""),
        okved=str(data.get("okved") or ""),
        entity_type="legal_entity",
        match_quality="medium",
        matched_by="",
        provider_record_id=str(data.get("hid") or inn or ""),
        facts={"dadata_hid": data.get("hid"), "opf": data.get("opf"), "management": data.get("management")},
    )


def _with_match_metadata(
    observation: CompanyRegistryObservation,
    *,
    request: CompanyLookupRequest,
    matched_by: str,
) -> CompanyRegistryObservation:
    quality = "high" if matched_by in {"inn", "ogrn"} else "medium" if matched_by else "low"
    return observation.model_copy(update={
        "lookup_query": observation.lookup_query or _best_query(request),
        "matched_by": observation.matched_by or matched_by or "query",
        "match_quality": observation.match_quality if observation.match_quality != "medium" or quality == "medium" else quality,
        "entity_type": observation.entity_type or "legal_entity",
        "normalized_legal_name": observation.normalized_legal_name or _normalize_company_name(observation.legal_name),
    })


def _matches_request(item: dict[str, Any], request: CompanyLookupRequest) -> bool:
    haystack = " ".join(str(value) for value in item.values()).lower()
    terms = [term.lower() for term in request.lookup_terms if len(term.strip()) >= 3]
    return not terms or any(term in haystack or haystack in term for term in terms)


def _matched_by_fixture(item: dict[str, Any], request: CompanyLookupRequest) -> str:
    return _matched_by_values(
        legal_name=str(item.get("legal_name") or item.get("value") or ""),
        inn=str(item.get("inn") or ""),
        ogrn=str(item.get("ogrn") or ""),
        request=request,
    )


def _matched_by_dadata(item: dict[str, Any], request: CompanyLookupRequest) -> str:
    data = item.get("data") if isinstance(item.get("data"), dict) else {}
    name = data.get("name") if isinstance(data.get("name"), dict) else {}
    return _matched_by_values(
        legal_name=str(name.get("short_with_opf") or name.get("full_with_opf") or item.get("value") or ""),
        inn=str(data.get("inn") or ""),
        ogrn=str(data.get("ogrn") or ""),
        request=request,
    )


def _matched_by_values(*, legal_name: str, inn: str, ogrn: str, request: CompanyLookupRequest) -> str:
    terms = [term.lower() for term in request.lookup_terms if str(term).strip()]
    if inn and inn.lower() in terms:
        return "inn"
    if ogrn and ogrn.lower() in terms:
        return "ogrn"
    normalized_name = _normalize_company_name(legal_name)
    if normalized_name and any(normalized_name in _normalize_company_name(term) or _normalize_company_name(term) in normalized_name for term in terms):
        return "legal_name"
    return "query"


def _lookup_outcome(observations: list[CompanyRegistryObservation]) -> str:
    if not observations:
        return "no_match"
    if len(observations) > 1 and not any(item.match_quality == "high" for item in observations):
        return "ambiguous_match"
    return "used"


def _http_error_outcome(error: HTTPError, *, request: CompanyLookupRequest) -> CompanySourceOutcome:
    if error.code in {401, 403}:
        outcome = "invalid_credentials"
        reason = f"DaData rejected the request with HTTP {error.code}."
    elif error.code == 429:
        outcome = "rate_limited"
        reason = "DaData rate limit was reached."
    else:
        outcome = "provider_unavailable"
        reason = f"DaData returned HTTP {error.code}."
    return CompanySourceOutcome(
        source_id=request.source_id,
        provider_id="dadata",
        outcome=outcome,
        reason=reason,
        query=request.query,
        observation_count=0,
    )


def _best_query(request: CompanyLookupRequest) -> str:
    for term in request.lookup_terms:
        if term.strip():
            return term.strip()
    return request.query


def _normalize_company_name(value: str) -> str:
    normalized = re.sub(r"[«»\"'.,]", " ", value.lower())
    normalized = re.sub(r"\b(ао|пао|оао|зао|ооо|нао|jsc|pjsc|llc)\b", " ", normalized, flags=re.IGNORECASE)
    return " ".join(normalized.split())


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
