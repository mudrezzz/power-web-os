"""Provider-neutral web retrieval contracts for live Radar.

Retrieval is intentionally separate from candidate extraction and scoring:
providers return ranked source material, while application services keep source
policy, budgets, verification, candidate lifecycle, and score semantics.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Literal

from pydantic import BaseModel, Field

from power_web_os.application.radar.candidate_discovery.contracts import RadarSearchPlan

RadarRetrievalStatus = Literal["retrieved", "empty", "provider_error"]


class RadarWebRetrievalRequest(BaseModel):
    radar_id: str
    task_id: str
    query: str
    stage: str = ""
    subject_id: str = ""
    candidate_scope: list[str] = Field(default_factory=list)
    source_policy: dict[str, Any] = Field(default_factory=dict)
    provider_id: str = "openrouter"
    engine: str = "auto"


class RadarRetrievedSource(BaseModel):
    source_ref: str
    title: str = ""
    url: str = ""
    snippet: str = ""
    rank: int = 0
    citation_index: int | None = None
    provider_id: str = "openrouter"
    engine: str = "auto"
    raw_metadata: dict[str, Any] = Field(default_factory=dict)


class RadarRetrievalSourceOutcome(BaseModel):
    source_ref: str
    outcome: str
    reason: str = ""
    provider_id: str = "openrouter"
    engine: str = "auto"


class RadarWebRetrievalResult(BaseModel):
    provider_id: str
    engine: str
    status: RadarRetrievalStatus = "retrieved"
    query: str = ""
    retrieved_sources: list[RadarRetrievedSource] = Field(default_factory=list)
    source_outcomes: list[RadarRetrievalSourceOutcome] = Field(default_factory=list)
    provider_metadata: dict[str, Any] = Field(default_factory=dict)


class RadarWebRetrievalProvider(ABC):
    provider_id = "web_retrieval_provider"

    @abstractmethod
    def retrieve(self, *, request: RadarWebRetrievalRequest) -> RadarWebRetrievalResult:
        raise NotImplementedError


class RecordedRadarWebRetrievalProvider(RadarWebRetrievalProvider):
    """Recorded retrieval provider used by contract tests and fixtures."""

    def __init__(self, result: RadarWebRetrievalResult | dict[str, Any]) -> None:
        self._result = RadarWebRetrievalResult.model_validate(result)
        self.requests: list[RadarWebRetrievalRequest] = []

    def retrieve(self, *, request: RadarWebRetrievalRequest) -> RadarWebRetrievalResult:
        self.requests.append(request)
        return self._result


def retrieval_request_from_search_plan(
    *,
    search_plan: RadarSearchPlan,
    provider_id: str,
    engine: str,
    source_policy: dict[str, Any] | None = None,
) -> RadarWebRetrievalRequest:
    query = search_plan.queries[0] if search_plan.queries else None
    return RadarWebRetrievalRequest(
        radar_id=search_plan.radar_id,
        task_id=query.query_id if query else "multi-task-plan",
        query=query.query if query else " ".join(item.query for item in search_plan.queries),
        stage=str(query.stage or "") if query else "",
        subject_id=str(query.subject_id or "") if query else "",
        candidate_scope=list(query.candidate_scope) if query else [],
        source_policy=dict(source_policy or {}),
        provider_id=provider_id,
        engine=engine,
    )
