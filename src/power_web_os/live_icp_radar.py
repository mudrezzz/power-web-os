from __future__ import annotations

import json
import os
import re
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

try:  # pragma: no cover - covered only when langgraph-dai is installed.
    from framework.workflows.base import BaseWorkflow, WorkflowExecutionContext, WorkflowNodeSpec

    FRAMEWORK_AVAILABLE = True
except Exception:  # pragma: no cover - normal path for base install.
    BaseWorkflow = object  # type: ignore[assignment,misc]
    WorkflowExecutionContext = Any  # type: ignore[misc,assignment]
    WorkflowNodeSpec = None  # type: ignore[assignment]
    FRAMEWORK_AVAILABLE = False


QualificationStatus = Literal["confirmed", "weak", "unknown", "rejected"]
SignalStatus = Literal["observed", "not_observed", "unclear"]


class RadarSearchQuery(BaseModel):
    query_id: str
    query: str
    purpose: str
    expected_evidence: list[str] = Field(default_factory=list)


class RadarSearchPlan(BaseModel):
    radar_id: str
    queries: list[RadarSearchQuery]


class RadarSourceEvidence(BaseModel):
    evidence_ref: str
    title: str
    url: str
    snippet: str
    query_id: str | None = None
    source_type: str = "web"


class LiveRadarQualificationResult(BaseModel):
    criterion_code: str
    criterion: str
    status: QualificationStatus
    confidence: str = "low"
    rationale: str
    evidence_refs: list[str] = Field(default_factory=list)


class LiveRadarSignalResult(BaseModel):
    signal_code: str
    signal: str
    status: SignalStatus
    score: int = Field(ge=0, le=2)
    confidence: str = "low"
    summary: str
    evidence_refs: list[str] = Field(default_factory=list)


class LiveRadarScore(BaseModel):
    fit_score: int
    intent_score: int
    tier: str


class LiveRadarCandidate(BaseModel):
    candidate_id: str
    legal_name: str
    description: str = ""
    qualification: list[LiveRadarQualificationResult]
    signals: list[LiveRadarSignalResult]
    score: LiveRadarScore
    review_flags: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


class WebSearchProviderResult(BaseModel):
    sources: list[RadarSourceEvidence] = Field(default_factory=list)
    candidate_observations: list[dict[str, Any]] = Field(default_factory=list)
    provider_metadata: dict[str, Any] = Field(default_factory=dict)


class LiveRadarRunArtifact(BaseModel):
    artifact_type: Literal["icp_radar_live_run"] = "icp_radar_live_run"
    artifact_version: Literal["0.6.3.1"] = "0.6.3.1"
    radar: dict[str, Any]
    run_metadata: dict[str, Any]
    search_plan: dict[str, Any]
    sources: list[dict[str, Any]]
    candidates: list[dict[str, Any]]


class LiveICPRadarRunState(BaseModel):
    task_context: dict[str, Any] = Field(default_factory=dict)
    radar: dict[str, Any] = Field(default_factory=dict)
    search_plan: dict[str, Any] | None = None
    sources: list[dict[str, Any]] = Field(default_factory=list)
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    artifact: dict[str, Any] | None = None
    workflow_metadata: dict[str, Any] = Field(default_factory=dict)
    live: bool = False
    error_message: str | None = None


class WebSearchProvider(ABC):
    runtime_name = "web_search_provider"

    @abstractmethod
    def run_search_plan(self, *, radar: dict[str, Any], search_plan: RadarSearchPlan) -> WebSearchProviderResult:
        raise NotImplementedError


class RecordedWebSearchProvider(WebSearchProvider):
    runtime_name = "recorded"

    def __init__(self, result: WebSearchProviderResult | dict[str, Any]) -> None:
        self._result = WebSearchProviderResult.model_validate(result)

    def run_search_plan(self, *, radar: dict[str, Any], search_plan: RadarSearchPlan) -> WebSearchProviderResult:
        _ = radar
        _ = search_plan
        return self._result


class OpenRouterWebSearchProvider(WebSearchProvider):
    runtime_name = "openrouter_live"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        web_mode: str | None = None,
        env_path: Path | None = None,
        timeout_seconds: float = 90,
    ) -> None:
        self._env = _load_env_file(env_path or Path.cwd() / ".env")
        # Local demo runs should be reproducible from the project `.env`.
        # Keep explicit constructor values strongest, then local `.env`, then
        # ambient OS env as a production/CI fallback.
        self._api_key = api_key or self._env.get("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")
        self._model = model or self._env.get("OPENROUTER_MODEL") or os.getenv("OPENROUTER_MODEL")
        self._web_mode = web_mode or self._env.get("OPENROUTER_WEB_MODE") or os.getenv("OPENROUTER_WEB_MODE") or "auto"
        self._timeout_seconds = timeout_seconds

    @property
    def model(self) -> str:
        return self._model or "openai/gpt-4.1-mini"

    @property
    def web_mode(self) -> str:
        return self._web_mode

    def run_search_plan(self, *, radar: dict[str, Any], search_plan: RadarSearchPlan) -> WebSearchProviderResult:
        if not self._api_key:
            raise RuntimeError("OPENROUTER_API_KEY is required for live ICP Radar runs")

        mode = self._web_mode
        if mode == "auto":
            try:
                result = self._request_with_mode(radar=radar, search_plan=search_plan, mode="server_tools")
                if result.sources:
                    return result
            except RuntimeError as error:
                if "unsupported" not in str(error).lower() and "400" not in str(error):
                    raise
            return self._request_with_mode(radar=radar, search_plan=search_plan, mode="plugin_web")
        return self._request_with_mode(radar=radar, search_plan=search_plan, mode=mode)

    def _request_with_mode(
        self,
        *,
        radar: dict[str, Any],
        search_plan: RadarSearchPlan,
        mode: str,
    ) -> WebSearchProviderResult:
        try:
            import httpx
        except ImportError as error:  # pragma: no cover - exercised by install shape, not unit tests.
            raise RuntimeError("Install the agent extra to run live OpenRouter searches: pip install -e .[agent]") from error

        payload = build_openrouter_request(
            radar=radar,
            search_plan=search_plan,
            model=self.model,
            web_mode=mode,
        )
        response = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/mudrezzz/power-web-os",
                "X-Title": "Power Web OS Live ICP Radar",
            },
            json=payload,
            timeout=self._timeout_seconds,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"OpenRouter web search request failed with {response.status_code}: {response.text[:240]}")

        result = normalize_openrouter_response(
            response.json(),
            fallback_metadata={"provider": "openrouter", "model": self.model, "web_mode": mode},
        )
        return _filter_result_to_verified_sources(result)


def build_live_mini_radar_definition() -> dict[str, Any]:
    return {
        "radar_id": "toir-quick-live",
        "name": "ТОиР Quick Live Radar",
        "description": "Мини-радар для живого поиска производственных активов СИБУР с сигналами по ТОиР, модернизации и цифровизации.",
        "qualification_criteria": [
            {
                "code": "Q1",
                "label": "Компания входит в группу СИБУР",
                "rule": "Найти подтверждение, что юридическое лицо или площадка относится к группе СИБУР.",
            },
            {
                "code": "Q2",
                "label": "Промышленный или нефтехимический производственный актив",
                "rule": "Найти признаки промышленного, нефтехимического или производственного актива, а не только сервисной структуры.",
            },
        ],
        "intent_signals": [
            {
                "code": "S1",
                "label": "ТОиР / ремонты / надежность",
                "rule": "Есть упоминание ремонтов, надежности, ТОиР, межремонтного интервала или maintenance-повестки.",
            },
            {
                "code": "S2",
                "label": "Модернизация оборудования / инвестиции / рост мощности",
                "rule": "Есть упоминание модернизации оборудования, инвестиций, расширения или роста мощности.",
            },
            {
                "code": "S3",
                "label": "Цифровизация производства / диагностика / предиктивная аналитика",
                "rule": "Есть упоминание цифровизации производства, диагностики, датчиков, предиктивной аналитики или автоматизации.",
            },
        ],
        "source_policy": {
            "preferred_domains": ["sibur.ru"],
            "allow_open_web": True,
            "human_review_required": True,
        },
    }


def build_live_mini_radar_search_plan(radar: dict[str, Any] | None = None) -> RadarSearchPlan:
    radar_payload = radar or build_live_mini_radar_definition()
    return RadarSearchPlan(
        radar_id=str(radar_payload["radar_id"]),
        queries=[
            RadarSearchQuery(
                query_id="q1-toir-reliability",
                query="СИБУР ТОиР ремонты надежность межремонтный интервал производственная площадка",
                purpose="Найти активы СИБУР и сигналы по ТОиР, ремонту и надежности.",
                expected_evidence=["Q1", "Q2", "S1"],
            ),
            RadarSearchQuery(
                query_id="q2-modernization-investment",
                query="СИБУР модернизация оборудование инвестиции рост мощности нефтехимия",
                purpose="Найти сигналы модернизации, инвестиций и роста мощности.",
                expected_evidence=["Q1", "Q2", "S2"],
            ),
            RadarSearchQuery(
                query_id="q3-digital-diagnostics",
                query="СИБУР цифровизация производство диагностика предиктивная аналитика датчики",
                purpose="Найти сигналы цифровизации, диагностики и предиктивной аналитики.",
                expected_evidence=["Q1", "Q2", "S3"],
            ),
        ],
    )


def build_live_mini_radar_search_plan_artifact() -> dict[str, Any]:
    radar = build_live_mini_radar_definition()
    plan = build_live_mini_radar_search_plan(radar)
    return {
        "artifact_type": "icp_radar_live_search_plan",
        "artifact_version": "0.6.3.1",
        "radar": radar,
        "search_plan": plan.model_dump(),
        "workflow_metadata": {
            "workflow_name": "LiveICPRadarRunWorkflow",
            "runtime": "dry_run_plan",
            "created_at": _now_iso(),
        },
    }


def build_openrouter_request(
    *,
    radar: dict[str, Any],
    search_plan: RadarSearchPlan,
    model: str,
    web_mode: str,
) -> dict[str, Any]:
    prompt = {
        "task": "Run a live ICP radar search. Use web search and return only JSON.",
        "radar": radar,
        "search_plan": search_plan.model_dump(),
        "output_schema": {
            "sources": [
                {
                    "evidence_ref": "stable short id",
                    "title": "source title",
                    "url": "https://...",
                    "snippet": "short evidence summary",
                    "query_id": "search query id",
                }
            ],
            "candidates": [
                {
                    "legal_name": "candidate legal name",
                    "description": "short account description",
                    "qualification": [
                        {
                            "criterion_code": "Q1 or Q2",
                            "status": "confirmed|weak|unknown|rejected",
                            "confidence": "high|medium|low",
                            "rationale": "why this status",
                            "evidence_refs": ["source ids"],
                        }
                    ],
                    "signals": [
                        {
                            "signal_code": "S1|S2|S3",
                            "status": "observed|not_observed|unclear",
                            "score": "0|1|2",
                            "confidence": "high|medium|low",
                            "summary": "short signal summary",
                            "evidence_refs": ["source ids"],
                        }
                    ],
                    "review_flags": ["why human review is needed"],
                }
            ],
        },
        "rules": [
            "Do not invent candidates without source evidence.",
            "If evidence is weak, mark it weak/unclear and add a review flag.",
            "Do not include secrets, request headers, or raw tool dumps.",
        ],
    }
    request: dict[str, Any] = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are an ABM research agent. Return strict JSON only. Use Russian names and summaries when source content is Russian.",
            },
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    if web_mode == "server_tools":
        request["tools"] = [
            {
                "type": "openrouter:web_search",
                "parameters": {
                    "engine": "auto",
                    "max_results": 5,
                    "max_total_results": 12,
                    "search_context_size": "low",
                },
            }
        ]
    elif web_mode == "plugin_web":
        request["plugins"] = [{"id": "web"}]
    elif web_mode == "model_native":
        request["metadata"] = {"web_mode": "model_native"}
    else:
        raise ValueError(f"Unsupported OPENROUTER_WEB_MODE: {web_mode}")
    return request


def normalize_openrouter_response(payload: dict[str, Any], *, fallback_metadata: dict[str, Any]) -> WebSearchProviderResult:
    message = payload.get("choices", [{}])[0].get("message", {})
    content = message.get("content") or "{}"
    parsed = _parse_json_object(content)
    sources = [
        _source_from_payload(item, index=index)
        for index, item in enumerate(parsed.get("sources", []), start=1)
        if isinstance(item, dict)
    ]
    sources.extend(_sources_from_annotations(message.get("annotations", []), start_index=len(sources) + 1))
    return WebSearchProviderResult(
        sources=_dedupe_sources(sources),
        candidate_observations=[
            item for item in parsed.get("candidates", [])
            if isinstance(item, dict)
        ],
        provider_metadata={
            **fallback_metadata,
            "response_id": payload.get("id"),
            "usage": payload.get("usage", {}),
        },
    )


def _filter_result_to_verified_sources(result: WebSearchProviderResult) -> WebSearchProviderResult:
    verified_sources = [source for source in result.sources if _source_url_is_reachable(source.url)]
    verified_refs = {source.evidence_ref for source in verified_sources}
    verified_candidates = [
        _filter_candidate_evidence_refs(candidate, verified_refs)
        for candidate in result.candidate_observations
        if _collect_candidate_evidence_refs(candidate) & verified_refs
    ]
    return WebSearchProviderResult(
        sources=verified_sources,
        candidate_observations=verified_candidates,
        provider_metadata={
            **result.provider_metadata,
            "source_verification": "http_status",
            "discarded_source_count": len(result.sources) - len(verified_sources),
        },
    )


def _source_url_is_reachable(url: str) -> bool:
    if not url.startswith(("http://", "https://")):
        return False
    try:
        import httpx
    except ImportError:  # pragma: no cover - OpenRouter provider already requires httpx.
        return False

    headers = {"User-Agent": "PowerWebOS-LiveRadar/0.6.3.1"}
    try:
        with httpx.Client(follow_redirects=True, timeout=12, headers=headers) as client:
            response = client.head(url)
            if response.status_code in {405, 403}:
                response = client.get(url)
            return response.status_code < 400
    except httpx.HTTPError:
        return False


def _collect_candidate_evidence_refs(candidate: dict[str, Any]) -> set[str]:
    refs = set()
    for ref in candidate.get("evidence_refs", []):
        if str(ref).strip():
            refs.add(str(ref))
    for section_name in ("qualification", "signals"):
        section = candidate.get(section_name, [])
        if not isinstance(section, list):
            continue
        for item in section:
            if not isinstance(item, dict):
                continue
            for ref in item.get("evidence_refs", []):
                if str(ref).strip():
                    refs.add(str(ref))
    return refs


def _filter_candidate_evidence_refs(candidate: dict[str, Any], verified_refs: set[str]) -> dict[str, Any]:
    filtered = dict(candidate)
    if isinstance(filtered.get("evidence_refs"), list):
        filtered["evidence_refs"] = [ref for ref in filtered["evidence_refs"] if str(ref) in verified_refs]
    for section_name in ("qualification", "signals"):
        section = filtered.get(section_name, [])
        if not isinstance(section, list):
            continue
        filtered_section = []
        for item in section:
            if not isinstance(item, dict):
                continue
            next_item = dict(item)
            next_item["evidence_refs"] = [
                ref for ref in next_item.get("evidence_refs", [])
                if str(ref) in verified_refs
            ]
            filtered_section.append(next_item)
        filtered[section_name] = filtered_section
    return filtered


def build_live_mini_radar_artifact(
    *,
    provider: WebSearchProvider,
    live: bool,
    task_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    workflow = LiveICPRadarRunWorkflow(provider=provider)
    state = LiveICPRadarRunState(
        task_context=task_context or {
            "task_id": "live-mini-icp-radar",
            "correlation_id": "demo-slice-0.6.3.1",
            "requester": "demo",
        },
        radar=build_live_mini_radar_definition(),
        live=live,
    )
    result = workflow.invoke(state)
    if result.artifact is None:
        raise RuntimeError("LiveICPRadarRunWorkflow did not produce an artifact")
    return result.artifact


class _FallbackLiveICPRadarRunWorkflow:
    def __init__(self, provider: WebSearchProvider | None = None, **_: Any) -> None:
        self._provider = provider or RecordedWebSearchProvider({"sources": [], "candidate_observations": []})
        self._runtime_mode = "local_fallback"

    def compile(self) -> dict[str, Any]:
        return {
            "workflow": self.__class__.__name__,
            "runtime_mode": self._runtime_mode,
            "invoke_graph_ready": True,
            "resume_graph_ready": True,
            "invoke_node_count": 7,
            "resume_node_count": 7,
        }

    def invoke(self, payload: LiveICPRadarRunState | dict[str, Any]) -> LiveICPRadarRunState:
        state = LiveICPRadarRunState.model_validate(payload)
        return self._run(state=state, node_name="shape_artifact")

    def resume(self, payload: LiveICPRadarRunState | dict[str, Any]) -> LiveICPRadarRunState:
        return self.invoke(payload)

    def _runtime_metadata(self, *, state: LiveICPRadarRunState, node_name: str, provider_metadata: dict[str, Any]) -> dict[str, Any]:
        return {
            "workflow_name": "LiveICPRadarRunWorkflow",
            "runtime": getattr(self._provider, "runtime_name", "recorded") if state.live else "recorded",
            "framework_available": False,
            "runtime_mode": self._runtime_mode,
            "node_name": node_name,
            "task_id": state.task_context.get("task_id"),
            "correlation_id": state.task_context.get("correlation_id"),
            "model": provider_metadata.get("model"),
            "web_mode": provider_metadata.get("web_mode"),
            "query_count": len(state.search_plan["queries"]) if state.search_plan else 0,
            "source_count": len(state.sources),
            "candidate_count": len(state.candidates),
            "run_at": _now_iso(),
        }

    def _run(self, *, state: LiveICPRadarRunState, node_name: str) -> LiveICPRadarRunState:
        radar = state.radar or build_live_mini_radar_definition()
        plan = build_live_mini_radar_search_plan(radar)
        provider_result = self._provider.run_search_plan(radar=radar, search_plan=plan)
        sources = _dedupe_sources(provider_result.sources)
        candidates = _rank_candidates([
            normalize_live_candidate(item, radar=radar)
            for item in provider_result.candidate_observations
        ])
        metadata = self._runtime_metadata(
            state=state.model_copy(update={
                "search_plan": plan.model_dump(),
                "sources": [item.model_dump() for item in sources],
                "candidates": [item.model_dump() for item in candidates],
            }),
            node_name=node_name,
            provider_metadata=provider_result.provider_metadata,
        )
        artifact = LiveRadarRunArtifact(
            radar=radar,
            run_metadata=metadata,
            search_plan=plan.model_dump(),
            sources=[item.model_dump() for item in sources],
            candidates=[item.model_dump() for item in candidates],
        )
        return state.model_copy(
            update={
                "radar": radar,
                "search_plan": plan.model_dump(),
                "sources": [item.model_dump() for item in sources],
                "candidates": [item.model_dump() for item in candidates],
                "workflow_metadata": metadata,
                "artifact": artifact.model_dump(),
                "error_message": None,
            }
        )


if FRAMEWORK_AVAILABLE:

    class LiveICPRadarRunWorkflow(BaseWorkflow):  # type: ignore[misc,valid-type]
        def __init__(
            self,
            provider: WebSearchProvider | None = None,
            *,
            use_langgraph_runtime: bool = True,
            checkpointer: object | None = None,
            node_event_sink: object | None = None,
        ) -> None:
            super().__init__(
                use_langgraph_runtime=use_langgraph_runtime,
                checkpointer=checkpointer,
                node_event_sink=node_event_sink,
            )
            self._fallback = _FallbackLiveICPRadarRunWorkflow(provider=provider)
            self.compile()

        def state_schema(self) -> type[LiveICPRadarRunState]:
            return LiveICPRadarRunState

        def workflow_nodes(self, *, is_resume: bool) -> list[Any]:
            _ = is_resume
            return [
                WorkflowNodeSpec(name="build_search_plan", handler=self._run_node),  # type: ignore[misc,operator]
                WorkflowNodeSpec(name="run_web_search", handler=self._run_node),  # type: ignore[misc,operator]
                WorkflowNodeSpec(name="normalize_sources", handler=self._run_node),  # type: ignore[misc,operator]
                WorkflowNodeSpec(name="extract_candidates", handler=self._run_node),  # type: ignore[misc,operator]
                WorkflowNodeSpec(name="evaluate_qualification", handler=self._run_node),  # type: ignore[misc,operator]
                WorkflowNodeSpec(name="extract_signals", handler=self._run_node),  # type: ignore[misc,operator]
                WorkflowNodeSpec(name="rank_candidates", handler=self._run_node),  # type: ignore[misc,operator]
                WorkflowNodeSpec(name="shape_artifact", handler=self._run_node),  # type: ignore[misc,operator]
            ]

        def execute(self, state: LiveICPRadarRunState) -> LiveICPRadarRunState:
            return self._run_with_langgraph_metadata(state)

        def execute_resume(self, state: LiveICPRadarRunState) -> LiveICPRadarRunState:
            return self.execute(state)

        def _run_node(self, state: LiveICPRadarRunState, context: WorkflowExecutionContext) -> LiveICPRadarRunState:
            _ = context
            if state.artifact is not None:
                return state
            return self._run_with_langgraph_metadata(state)

        def _run_with_langgraph_metadata(self, state: LiveICPRadarRunState) -> LiveICPRadarRunState:
            result = self._fallback.invoke(state)
            metadata = {
                **result.workflow_metadata,
                "runtime_mode": "langgraph_dai",
                "framework_available": True,
            }
            artifact = {**(result.artifact or {}), "run_metadata": metadata}
            return result.model_copy(update={"workflow_metadata": metadata, "artifact": artifact})

else:
    LiveICPRadarRunWorkflow = _FallbackLiveICPRadarRunWorkflow


def normalize_live_candidate(payload: dict[str, Any], *, radar: dict[str, Any]) -> LiveRadarCandidate:
    legal_name = str(payload.get("legal_name") or payload.get("name") or "Unknown candidate").strip()
    qualification = _normalize_qualification(payload.get("qualification", []), radar)
    signals = _normalize_signals(payload.get("signals", []), radar)
    fit_score = sum(1 for item in qualification if item.status == "confirmed")
    intent_score = sum(item.score for item in signals if item.status == "observed")
    tier = "Tier 1" if fit_score == 2 and intent_score >= 3 else "Tier 2" if fit_score >= 1 and intent_score >= 1 else "Monitor"
    review_flags = [str(item) for item in payload.get("review_flags", []) if str(item).strip()]
    if any(item.status in {"weak", "unknown"} for item in qualification):
        review_flags.append("qualification_requires_human_review")
    if any(item.status == "unclear" for item in signals):
        review_flags.append("signal_requires_human_review")
    evidence_refs = sorted({
        ref
        for collection in [qualification, signals]
        for item in collection
        for ref in item.evidence_refs
    })
    return LiveRadarCandidate(
        candidate_id=_stable_id(legal_name),
        legal_name=legal_name,
        description=str(payload.get("description") or ""),
        qualification=qualification,
        signals=signals,
        score=LiveRadarScore(fit_score=fit_score, intent_score=intent_score, tier=tier),
        review_flags=sorted(set(review_flags)),
        evidence_refs=evidence_refs,
    )


def _normalize_qualification(payload: Any, radar: dict[str, Any]) -> list[LiveRadarQualificationResult]:
    by_code = {
        str(item.get("criterion_code", item.get("code", ""))): item
        for item in payload
        if isinstance(item, dict)
    } if isinstance(payload, list) else {}
    results = []
    for criterion in radar["qualification_criteria"]:
        raw = by_code.get(criterion["code"], {})
        status = _normalize_choice(str(raw.get("status", "unknown")), {"confirmed", "weak", "unknown", "rejected"}, "unknown")
        results.append(LiveRadarQualificationResult(
            criterion_code=criterion["code"],
            criterion=criterion["label"],
            status=status,  # type: ignore[arg-type]
            confidence=str(raw.get("confidence", "low")),
            rationale=str(raw.get("rationale") or raw.get("summary") or "No qualification evidence found."),
            evidence_refs=[str(ref) for ref in raw.get("evidence_refs", [])],
        ))
    return results


def _normalize_signals(payload: Any, radar: dict[str, Any]) -> list[LiveRadarSignalResult]:
    by_code = {
        str(item.get("signal_code", item.get("code", ""))): item
        for item in payload
        if isinstance(item, dict)
    } if isinstance(payload, list) else {}
    results = []
    for signal in radar["intent_signals"]:
        raw = by_code.get(signal["code"], {})
        status = _normalize_choice(str(raw.get("status", "not_observed")), {"observed", "not_observed", "unclear"}, "not_observed")
        raw_score = raw.get("score", 0)
        try:
            score = max(0, min(2, int(raw_score)))
        except (TypeError, ValueError):
            score = 0
        if status != "observed":
            score = 0
        results.append(LiveRadarSignalResult(
            signal_code=signal["code"],
            signal=signal["label"],
            status=status,  # type: ignore[arg-type]
            score=score,
            confidence=str(raw.get("confidence", "low")),
            summary=str(raw.get("summary") or "No signal evidence found."),
            evidence_refs=[str(ref) for ref in raw.get("evidence_refs", [])],
        ))
    return results


def _rank_candidates(candidates: list[LiveRadarCandidate]) -> list[LiveRadarCandidate]:
    return sorted(
        candidates,
        key=lambda item: (-item.score.fit_score, -item.score.intent_score, item.legal_name),
    )


def _source_from_payload(payload: dict[str, Any], *, index: int) -> RadarSourceEvidence:
    return RadarSourceEvidence(
        evidence_ref=str(payload.get("evidence_ref") or payload.get("id") or f"src_{index}"),
        title=str(payload.get("title") or payload.get("name") or "Untitled source"),
        url=str(payload.get("url") or payload.get("source_url") or ""),
        snippet=str(payload.get("snippet") or payload.get("summary") or payload.get("content") or ""),
        query_id=str(payload.get("query_id") or "") or None,
        source_type=str(payload.get("source_type") or "web"),
    )


def _sources_from_annotations(annotations: Any, *, start_index: int) -> list[RadarSourceEvidence]:
    sources = []
    if not isinstance(annotations, list):
        return sources
    for index, annotation in enumerate(annotations, start=start_index):
        if not isinstance(annotation, dict):
            continue
        url_info = annotation.get("url_citation") or annotation
        if not isinstance(url_info, dict) or not url_info.get("url"):
            continue
        sources.append(RadarSourceEvidence(
            evidence_ref=f"citation_{index}",
            title=str(url_info.get("title") or url_info.get("url")),
            url=str(url_info["url"]),
            snippet=str(url_info.get("content") or url_info.get("snippet") or ""),
        ))
    return sources


def _dedupe_sources(sources: list[RadarSourceEvidence]) -> list[RadarSourceEvidence]:
    seen: set[tuple[str, str]] = set()
    result = []
    for source in sources:
        key = (source.evidence_ref, source.url)
        if key in seen:
            continue
        seen.add(key)
        result.append(source)
    return result


def _parse_json_object(content: str) -> dict[str, Any]:
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?", "", stripped).strip()
        stripped = re.sub(r"```$", "", stripped).strip()
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
        if not match:
            return {}
        parsed = json.loads(match.group(0))
    return parsed if isinstance(parsed, dict) else {}


def _load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        from dotenv import dotenv_values
    except ImportError:
        values: dict[str, str] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line or line.lstrip().startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
        return values
    return {key: str(value) for key, value in dotenv_values(path).items() if value is not None}


def _normalize_choice(value: str, allowed: set[str], fallback: str) -> str:
    return value if value in allowed else fallback


def _stable_id(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9а-яА-ЯёЁ]+", "-", value.lower()).strip("-")
    return normalized or "candidate"


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()
