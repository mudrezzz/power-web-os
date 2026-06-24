"""Application ports for structured Radar source providers.

These contracts keep registry-style company data behind provider-neutral
interfaces. Integrations such as DaData implement the ports; Radar execution
only consumes structured observations and source outcomes.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any, Literal

from pydantic import BaseModel, Field

from power_web_os.application.connector_profiles import (
    ConnectorCapabilityCard,
    ConnectorProfileRegistry,
    default_connector_profile_registry,
)
from power_web_os.application.live_radar_contracts import (
    RadarExecutionTask,
    RadarSearchPlan,
    RadarSourceEvidence,
    WebSearchProvider,
    WebSearchProviderResult,
)
from power_web_os.application.live_radar_universe import merge_provider_metadata

RadarProviderType = Literal["company_registry"]


class CompanyLookupRequest(BaseModel):
    radar_id: str
    task_id: str
    stage: str
    subject_id: str
    query: str
    source_id: str
    source_label: str = ""
    source_reference: str = ""
    lookup_terms: list[str] = Field(default_factory=list)
    candidate_scope: list[str] = Field(default_factory=list)
    limit: int = 10


class CompanyRegistryObservation(BaseModel):
    source_ref: str = ""
    legal_name: str
    normalized_legal_name: str = ""
    inn: str = ""
    ogrn: str = ""
    kpp: str = ""
    status: str = ""
    address: str = ""
    okved: str = ""
    revenue: str = ""
    registry_url: str = ""
    entity_type: str = "legal_entity"
    match_quality: str = "medium"
    matched_by: str = ""
    lookup_query: str = ""
    provider_record_id: str = ""
    facts: dict[str, Any] = Field(default_factory=dict)


class CompanySourceOutcome(BaseModel):
    source_ref: str = ""
    source_id: str
    provider_id: str
    connector_profile_id: str = ""
    source_type: str = "company_registry"
    outcome: str
    reason: str
    query: str = ""
    observation_count: int = 0


class CompanyLookupResult(BaseModel):
    observations: list[CompanyRegistryObservation] = Field(default_factory=list)
    outcomes: list[CompanySourceOutcome] = Field(default_factory=list)
    provider_metadata: dict[str, Any] = Field(default_factory=dict)


class RadarSourceProvider(ABC):
    provider_id: str
    provider_type: RadarProviderType


class CompanyRegistryProvider(RadarSourceProvider):
    provider_type: RadarProviderType = "company_registry"

    @abstractmethod
    def lookup_companies(self, request: CompanyLookupRequest) -> CompanyLookupResult:
        raise NotImplementedError


class RadarSourceRegistry:
    """Select structured source providers from Radar source policy."""

    def __init__(
        self,
        *,
        company_registry_providers: dict[str, CompanyRegistryProvider] | None = None,
        connector_profile_registry: ConnectorProfileRegistry | None = None,
    ) -> None:
        self._company_registry_providers = company_registry_providers or {}
        self._connector_profile_registry = connector_profile_registry or default_connector_profile_registry()

    def lookup_for_task(self, *, radar: dict[str, Any], task: RadarExecutionTask) -> WebSearchProviderResult:
        if task.stage == "signal_search":
            return WebSearchProviderResult()
        sources = _selected_company_registry_sources(radar, task)
        if not sources:
            return WebSearchProviderResult()

        evidence: list[RadarSourceEvidence] = []
        observations: list[dict[str, Any]] = []
        outcomes: list[dict[str, Any]] = []
        structured_observations: list[dict[str, Any]] = []
        metadata: dict[str, Any] = {"provider": "source_registry"}
        for source in sources:
            provider_id = _provider_id(source)
            capability = self._connector_profile_registry.capability_for_source(source)
            connector_profile_id = capability.profile_id if capability else ""
            provider = self._company_registry_providers.get(provider_id)
            request = _lookup_request(radar=radar, task=task, source=source)
            if provider is None:
                outcomes.append(CompanySourceOutcome(
                    source_id=request.source_id,
                    provider_id=provider_id,
                    connector_profile_id=connector_profile_id,
                    outcome="provider_unavailable",
                    reason=f"No company registry provider is configured for {provider_id}.",
                    query=request.query,
                ).model_dump())
                continue
            if not request.lookup_terms or _lookup_is_insufficient_for_capability(task, request=request, capability=capability):
                outcomes.append(CompanySourceOutcome(
                    source_id=request.source_id,
                    provider_id=provider_id,
                    connector_profile_id=connector_profile_id,
                    outcome="registry_lookup_insufficient",
                    reason=(
                        "Connector capability requires concrete legal name, INN, OGRN, or candidate scope; "
                        "broad universe enumeration should use a source that supports broad discovery."
                    ),
                    query=request.query,
                    observation_count=0,
                ).model_dump())
                continue
            result = provider.lookup_companies(request)
            evidence.extend(_source_evidence_from_observations(result.observations, request=request, provider_id=provider_id))
            observations.extend(_candidate_observations_from_registry(result.observations, task=task))
            structured_observations.extend(_structured_observations_from_registry(result.observations, request=request, provider_id=provider_id))
            outcomes.extend([item.model_dump() for item in result.outcomes])
            metadata = merge_provider_metadata(metadata, result.provider_metadata)
            metadata.setdefault("compiled_source_capabilities", [])
            if capability:
                metadata["compiled_source_capabilities"].append(_safe_capability_payload(capability))

        return WebSearchProviderResult(
            sources=evidence,
            candidate_observations=observations,
            provider_metadata={
                **metadata,
                "source_provider_outcomes": outcomes,
                "source_outcomes": outcomes,
                "structured_company_observations": structured_observations,
            },
        )


class SourceRegistryWebSearchProvider(WebSearchProvider):
    """Composite provider that augments web retrieval with structured sources."""

    runtime_name = "web_search_with_source_registry"

    def __init__(self, web_provider: WebSearchProvider, source_registry: RadarSourceRegistry) -> None:
        self._web_provider = web_provider
        self._source_registry = source_registry

    def run_search_plan(self, *, radar: dict[str, Any], search_plan: RadarSearchPlan) -> WebSearchProviderResult:
        combined_result = WebSearchProviderResult()
        for query in search_plan.queries:
            task = RadarExecutionTask(
                task_id=query.query_id,
                stage=query.stage or "qualification_discovery",
                subject_type=query.subject_type or "qualification",
                subject_id=query.subject_id or query.query_id,
                rule_snapshot=query.rule_snapshot,
                query=query.query,
                purpose=query.purpose,
                expected_evidence=list(query.expected_evidence),
                source_scope=query.source_scope,
                source_base=query.source_base,
                application_scope=query.application_scope,
                source_ids=list(query.source_ids),
                external_source_hints=list(query.external_source_hints),
                depends_on=list(query.depends_on),
                candidate_scope=list(query.candidate_scope),
            )
            single_query_plan = RadarSearchPlan(radar_id=search_plan.radar_id, queries=[query])
            registry_result = self._source_registry.lookup_for_task(radar=radar, task=task)
            web_result = self._web_provider.run_search_plan(
                radar=_radar_with_structured_observations(radar, registry_result),
                search_plan=single_query_plan,
            )
            combined_result = _combine_results(combined_result, _combine_results(registry_result, web_result))
        return combined_result


def _combine_results(first: WebSearchProviderResult, second: WebSearchProviderResult) -> WebSearchProviderResult:
    return WebSearchProviderResult(
        sources=[*first.sources, *second.sources],
        candidate_observations=[*first.candidate_observations, *second.candidate_observations],
        provider_metadata=merge_provider_metadata(first.provider_metadata, second.provider_metadata),
    )


def _selected_company_registry_sources(radar: dict[str, Any], task: RadarExecutionTask) -> list[dict[str, Any]]:
    policy = radar.get("global_search_policy")
    if not isinstance(policy, dict):
        return []
    selected_ids = set(task.source_ids)
    result: list[dict[str, Any]] = []
    for source in policy.get("sources", []):
        if not isinstance(source, dict) or str(source.get("source_type")) != "company_registry":
            continue
        source_id = str(source.get("source_id") or source.get("reference") or "")
        if selected_ids and source_id not in selected_ids:
            continue
        result.append(dict(source))
    return result


def _provider_id(source: dict[str, Any]) -> str:
    if source.get("provider_id"):
        return str(source["provider_id"])
    reference = str(source.get("reference") or "")
    if ":" in reference:
        return reference.split(":")[-1]
    source_id = str(source.get("source_id") or "")
    return "dadata" if "dadata" in source_id.lower() else source_id


def _lookup_request(*, radar: dict[str, Any], task: RadarExecutionTask, source: dict[str, Any]) -> CompanyLookupRequest:
    terms = [*task.candidate_scope, *_safe_lookup_terms_from_text(task.query)]
    terms.extend(str(item) for item in source.get("keywords", []) if isinstance(item, str))
    return CompanyLookupRequest(
        radar_id=str(radar.get("radar_id") or ""),
        task_id=task.task_id,
        stage=task.stage,
        subject_id=task.subject_id,
        query=task.query,
        source_id=str(source.get("source_id") or source.get("reference") or "company_registry"),
        source_label=str(source.get("label") or source.get("source_id") or "Company registry"),
        source_reference=str(source.get("reference") or ""),
        lookup_terms=[item for item in _dedupe_text(terms) if item],
        candidate_scope=list(task.candidate_scope),
    )


def _safe_lookup_is_too_broad(task: RadarExecutionTask, *, request: CompanyLookupRequest | None = None) -> bool:
    if task.candidate_scope:
        return False
    terms = list(request.lookup_terms) if request is not None else _safe_lookup_terms_from_text(task.query)
    if any(_safe_is_concrete_lookup_term(term) for term in terms):
        return False
    return task.stage in {"qualification_discovery", "coverage_check"} and _safe_looks_like_broad_discovery(task.query)


def _lookup_is_insufficient_for_capability(
    task: RadarExecutionTask,
    *,
    request: CompanyLookupRequest,
    capability: ConnectorCapabilityCard | None,
) -> bool:
    if capability is None:
        return _safe_lookup_is_too_broad(task, request=request)
    if capability.supports_broad_discovery:
        return False
    if capability.requires_concrete_input:
        return _safe_lookup_is_too_broad(task, request=request)
    return False


def _safe_capability_payload(capability: ConnectorCapabilityCard) -> dict[str, Any]:
    payload = capability.to_payload()
    payload.pop("credential_env_vars", None)
    payload["credential_count"] = len(capability.credential_env_vars)
    return payload


def _safe_lookup_terms_from_text(text: str) -> list[str]:
    normalized = " ".join(str(text).split())
    if not normalized:
        return []
    identifiers = re.findall(r"\b\d{10}\b|\b\d{13}\b|\b\d{15}\b", normalized)
    quoted = re.findall(r"[\"«]([^\"»]{3,120})[\"»]", normalized)
    legal_patterns = re.findall(
        r"\b(?:АО|ПАО|ОАО|ЗАО|ООО|НАО|JSC|PJSC|LLC)\s+[\"«]?[A-Za-zА-Яа-яЁё0-9 .,\-]{3,90}",
        normalized,
        flags=re.IGNORECASE,
    )
    terms = [*identifiers, *quoted, *legal_patterns]
    if _safe_is_concrete_lookup_term(normalized):
        terms.append(normalized)
    return _dedupe_text(terms)


def _safe_is_concrete_lookup_term(term: str) -> bool:
    value = " ".join(str(term).split())
    if re.fullmatch(r"\d{10}|\d{13}|\d{15}", value):
        return True
    if re.search(r"\b(АО|ПАО|ОАО|ЗАО|ООО|НАО|JSC|PJSC|LLC)\b", value, flags=re.IGNORECASE):
        return True
    return 3 <= len(value) <= 90 and not _safe_looks_like_broad_discovery(value)


def _safe_looks_like_broad_discovery(text: str) -> bool:
    lowered = str(text).lower()
    return any(marker in lowered for marker in (
        "find ",
        "all ",
        "candidate universe",
        "holding",
        "contour",
        "universe",
        "найд",
        "все ",
        "контур",
        "периметр",
        "холдинг",
        "групп",
        "юр лиц",
        "юридическ",
    ))


def _source_evidence_from_observations(
    observations: list[CompanyRegistryObservation],
    *,
    request: CompanyLookupRequest,
    provider_id: str,
) -> list[RadarSourceEvidence]:
    return [
        RadarSourceEvidence(
            evidence_ref=observation.source_ref or _stable_source_ref(provider_id, observation.legal_name),
            title=f"{request.source_label}: {observation.legal_name}",
            url=observation.registry_url,
            snippet=_registry_snippet(observation),
            query_id=request.task_id,
            source_type="company_registry",
            verification_state="not_checked",
            verification_mode="off",
            verification_reason="structured_company_registry_provider",
        )
        for observation in observations
    ]


def _candidate_observations_from_registry(
    observations: list[CompanyRegistryObservation],
    *,
    task: RadarExecutionTask,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for observation in observations:
        source_ref = observation.source_ref or _stable_source_ref("company_registry", observation.legal_name)
        result.append({
            "legal_name": observation.legal_name,
            "description": _registry_snippet(observation),
            "evidence_refs": [source_ref],
            "review_flags": ["company_registry_fact_requires_review"],
            "entity_type": observation.entity_type or "legal_entity",
            "entity_resolution_status": "resolved",
            "inn": observation.inn,
            "ogrn": observation.ogrn,
            "okved": observation.okved,
            "normalized_legal_name": observation.normalized_legal_name,
            "match_quality": observation.match_quality,
            "matched_by": observation.matched_by,
            "lookup_query": observation.lookup_query,
            "registry_facts": observation.facts,
            "qualification": [{
                "criterion_code": task.subject_id,
                "criterion": task.rule_snapshot or task.subject_id,
                "status": "weak",
                "confidence": "medium",
                "rationale": "Structured company registry returned a source-backed company observation.",
                "evidence_refs": [source_ref],
            }],
        })
    return result


def _structured_observations_from_registry(
    observations: list[CompanyRegistryObservation],
    *,
    request: CompanyLookupRequest,
    provider_id: str,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for observation in observations:
        result.append({
            "source_ref": observation.source_ref or _stable_source_ref(provider_id, observation.legal_name),
            "source_id": request.source_id,
            "provider_id": provider_id,
            "entity_type": observation.entity_type or "legal_entity",
            "legal_name": observation.legal_name,
            "normalized_legal_name": observation.normalized_legal_name or _normalize_company_name(observation.legal_name),
            "inn": observation.inn,
            "ogrn": observation.ogrn,
            "kpp": observation.kpp,
            "status": observation.status,
            "address": observation.address,
            "okved": observation.okved,
            "match_quality": observation.match_quality,
            "matched_by": observation.matched_by,
            "lookup_query": observation.lookup_query or request.query,
            "provider_record_id": observation.provider_record_id,
            "facts": dict(observation.facts),
        })
    return result


def _radar_with_structured_observations(radar: dict[str, Any], result: WebSearchProviderResult) -> dict[str, Any]:
    observations = [
        dict(item)
        for item in result.provider_metadata.get("structured_company_observations", [])
        if isinstance(item, dict)
    ]
    if not observations:
        return radar
    existing = [
        dict(item)
        for item in radar.get("structured_company_observations", [])
        if isinstance(item, dict)
    ]
    return {**radar, "structured_company_observations": _dedupe_observations([*existing, *observations])}


def _registry_snippet(observation: CompanyRegistryObservation) -> str:
    parts = [
        observation.status,
        f"INN {observation.inn}" if observation.inn else "",
        f"OGRN {observation.ogrn}" if observation.ogrn else "",
        observation.address,
        f"OKVED {observation.okved}" if observation.okved else "",
    ]
    return "; ".join(part for part in parts if part) or "Structured company registry observation."


def _dedupe_observations(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for item in values:
        key = str(item.get("inn") or item.get("ogrn") or item.get("normalized_legal_name") or item.get("legal_name") or "").lower()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _normalize_company_name(value: str) -> str:
    normalized = re.sub(r"[«»\"'.,]", " ", value.lower())
    normalized = re.sub(r"\b(ао|пао|оао|зао|ооо|нао|jsc|pjsc|llc)\b", " ", normalized, flags=re.IGNORECASE)
    return " ".join(normalized.split())


def _dedupe_text(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = " ".join(str(value).split())
        key = text.lower()
        if text and key not in seen:
            result.append(text)
            seen.add(key)
    return result


def _stable_source_ref(provider_id: str, value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", value.lower()).strip("_")
    return f"{provider_id}_{normalized or 'company'}"[:80]
