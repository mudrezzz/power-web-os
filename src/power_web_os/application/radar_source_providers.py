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
    inn: str = ""
    ogrn: str = ""
    kpp: str = ""
    status: str = ""
    address: str = ""
    okved: str = ""
    revenue: str = ""
    registry_url: str = ""
    facts: dict[str, Any] = Field(default_factory=dict)


class CompanySourceOutcome(BaseModel):
    source_ref: str = ""
    source_id: str
    provider_id: str
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

    def __init__(self, *, company_registry_providers: dict[str, CompanyRegistryProvider] | None = None) -> None:
        self._company_registry_providers = company_registry_providers or {}

    def lookup_for_task(self, *, radar: dict[str, Any], task: RadarExecutionTask) -> WebSearchProviderResult:
        if task.stage == "signal_search":
            return WebSearchProviderResult()
        sources = _selected_company_registry_sources(radar, task)
        if not sources:
            return WebSearchProviderResult()

        evidence: list[RadarSourceEvidence] = []
        observations: list[dict[str, Any]] = []
        outcomes: list[dict[str, Any]] = []
        metadata: dict[str, Any] = {"provider": "source_registry"}
        for source in sources:
            provider_id = _provider_id(source)
            provider = self._company_registry_providers.get(provider_id)
            request = _lookup_request(radar=radar, task=task, source=source)
            if provider is None:
                outcomes.append(CompanySourceOutcome(
                    source_id=request.source_id,
                    provider_id=provider_id,
                    outcome="provider_unavailable",
                    reason=f"No company registry provider is configured for {provider_id}.",
                    query=request.query,
                ).model_dump())
                continue
            result = provider.lookup_companies(request)
            evidence.extend(_source_evidence_from_observations(result.observations, request=request, provider_id=provider_id))
            observations.extend(_candidate_observations_from_registry(result.observations, task=task))
            outcomes.extend([item.model_dump() for item in result.outcomes])
            metadata = merge_provider_metadata(metadata, result.provider_metadata)

        return WebSearchProviderResult(
            sources=evidence,
            candidate_observations=observations,
            provider_metadata={
                **metadata,
                "source_provider_outcomes": outcomes,
                "source_outcomes": outcomes,
            },
        )


class SourceRegistryWebSearchProvider(WebSearchProvider):
    """Composite provider that augments web retrieval with structured sources."""

    runtime_name = "web_search_with_source_registry"

    def __init__(self, web_provider: WebSearchProvider, source_registry: RadarSourceRegistry) -> None:
        self._web_provider = web_provider
        self._source_registry = source_registry

    def run_search_plan(self, *, radar: dict[str, Any], search_plan: RadarSearchPlan) -> WebSearchProviderResult:
        web_result = self._web_provider.run_search_plan(radar=radar, search_plan=search_plan)
        registry_result = WebSearchProviderResult()
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
            registry_result = _combine_results(
                registry_result,
                self._source_registry.lookup_for_task(radar=radar, task=task),
            )
        return _combine_results(registry_result, web_result)


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
    terms = [*task.candidate_scope, task.query]
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


def _registry_snippet(observation: CompanyRegistryObservation) -> str:
    parts = [
        observation.status,
        f"INN {observation.inn}" if observation.inn else "",
        f"OGRN {observation.ogrn}" if observation.ogrn else "",
        observation.address,
        f"OKVED {observation.okved}" if observation.okved else "",
    ]
    return "; ".join(part for part in parts if part) or "Structured company registry observation."


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
