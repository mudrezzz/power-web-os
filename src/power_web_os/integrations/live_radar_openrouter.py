"""OpenRouter and recorded-provider adapters for live Radar search."""

from __future__ import annotations

import json
import os
from pathlib import Path
from time import perf_counter
from typing import Any

from power_web_os.application.live_radar_contracts import (
    RadarSearchPlan,
    RadarSourceEvidence,
    WebSearchProvider,
    WebSearchProviderResult,
)
from power_web_os.application.live_radar_normalization import _dedupe_sources
from power_web_os.application.live_radar_extraction_contract import extraction_validation_state, validate_and_repair_extraction_payload
from power_web_os.application.live_radar_external_budget import (
    current_external_call_budget,
    record_openrouter_server_tool_usage,
    reserve_openrouter_http_call,
)
from power_web_os.application.radar_technical_trace import RadarRunTechnicalTraceCommand, append_current_trace
from power_web_os.application.live_radar_web_retrieval import retrieval_request_from_search_plan
from power_web_os.integrations.openrouter_request_builder import build_openrouter_request, openrouter_compiled_prompt_summary
from power_web_os.integrations.openrouter_retrieval import retrieval_result_from_openrouter_response
from power_web_os.integrations.openrouter_trace import (
    duration_ms as _duration_ms,
    parse_json_object as _parse_json_object,
    provider_response_trace_payload as _provider_response_trace_payload,
    trace_provider as _trace_provider,
)
from power_web_os.integrations.live_radar_source_verification import (
    normalize_verification_mode,
    supports_product_evidence,
    verify_sources,
)


class RecordedWebSearchProvider(WebSearchProvider):
    runtime_name = "recorded"

    def __init__(self, result: WebSearchProviderResult | dict[str, Any]) -> None:
        self._result = WebSearchProviderResult.model_validate(result)
        self.calls: list[RadarSearchPlan] = []

    def run_search_plan(self, *, radar: dict[str, Any], search_plan: RadarSearchPlan) -> WebSearchProviderResult:
        _ = radar
        self.calls.append(search_plan)
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
        self._advanced_model = self._env.get("OPENROUTER_ADVANCED_MODEL") or os.getenv("OPENROUTER_ADVANCED_MODEL")
        self._extractor_model = (
            self._env.get("OPENROUTER_EXTRACTOR_MODEL")
            or os.getenv("OPENROUTER_EXTRACTOR_MODEL")
            or self._advanced_model
            or self._model
        )
        self._web_mode = web_mode or self._env.get("OPENROUTER_WEB_MODE") or os.getenv("OPENROUTER_WEB_MODE") or "auto"
        self._retrieval_provider = (
            self._env.get("POWER_WEB_OS_RADAR_WEB_RETRIEVAL_PROVIDER")
            or os.getenv("POWER_WEB_OS_RADAR_WEB_RETRIEVAL_PROVIDER")
            or "openrouter"
        )
        self._web_search_engine = (
            self._env.get("POWER_WEB_OS_OPENROUTER_WEB_SEARCH_ENGINE")
            or os.getenv("POWER_WEB_OS_OPENROUTER_WEB_SEARCH_ENGINE")
            or ("perplexity" if self._retrieval_provider == "openrouter_perplexity" else "auto")
        )
        self._source_verification_mode = normalize_verification_mode(
            self._env.get("POWER_WEB_OS_RADAR_SOURCE_VERIFICATION_MODE")
            or os.getenv("POWER_WEB_OS_RADAR_SOURCE_VERIFICATION_MODE")
        )
        self._timeout_seconds = timeout_seconds

    @property
    def model(self) -> str:
        return self._model or "openai/gpt-4.1-mini"

    @property
    def extractor_model(self) -> str:
        return self._extractor_model or self.model

    @property
    def web_mode(self) -> str:
        return self._web_mode

    @property
    def retrieval_provider(self) -> str:
        return self._retrieval_provider

    @property
    def web_search_engine(self) -> str:
        return self._web_search_engine

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

        selected_model = self._model_for_search_plan(search_plan)
        payload = build_openrouter_request(
            radar=radar,
            search_plan=search_plan,
            model=selected_model,
            web_mode=mode,
            web_search_engine=self.web_search_engine,
            web_max_results=_current_web_max_results(),
            web_max_total_results=_current_web_max_total_results(),
        )
        compiled_prompt = openrouter_compiled_prompt_summary(payload)
        retrieval_request = retrieval_request_from_search_plan(
            search_plan=search_plan,
            provider_id=self.retrieval_provider,
            engine=self.web_search_engine,
            source_policy=compiled_prompt.get("task_card", {}).get("source_policy", {}),
        )
        _trace_provider(
            trace_type="provider_request",
            title="OpenRouter retrieval request",
            summary=f"OpenRouter retrieval request using {self.retrieval_provider}/{self.web_search_engine}.",
            payload={
                "url": "https://openrouter.ai/api/v1/chat/completions",
                "model": selected_model,
                "web_mode": mode,
                "retrieval_request": retrieval_request.model_dump(),
                "task_card": compiled_prompt.get("task_card", {}),
                "compiled_prompt": compiled_prompt,
                "request": payload,
            },
        )
        budget_key = _search_plan_budget_key(search_plan)
        budget_decision = reserve_openrouter_http_call(role="web_task", task_id=budget_key)
        if not budget_decision.accepted:
            _trace_provider(
                trace_type="provider_error",
                title="OpenRouter call skipped by external budget",
                summary=budget_decision.message,
                payload={
                    "model": selected_model,
                    "web_mode": mode,
                    "retrieval_provider": self.retrieval_provider,
                    "retrieval_engine": self.web_search_engine,
                    "budget_decision": budget_decision.to_payload(),
                },
            )
            return _budget_limited_result(
                model=selected_model,
                default_model=self.model,
                extractor_model=self.extractor_model,
                web_mode=mode,
                retrieval_provider=self.retrieval_provider,
                retrieval_engine=self.web_search_engine,
                budget_decision=budget_decision.to_payload(),
            )
        started_at = perf_counter()
        try:
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
        except Exception as error:
            _trace_provider(
                trace_type="provider_error",
                title="OpenRouter request error",
                summary=str(error),
                duration_ms=_duration_ms(started_at),
                payload={"error_type": error.__class__.__name__, "message": str(error), "model": selected_model, "web_mode": mode},
            )
            raise
        if response.status_code >= 400:
            _trace_provider(
                trace_type="provider_error",
                title="OpenRouter response error",
                summary=f"OpenRouter returned HTTP {response.status_code}.",
                duration_ms=_duration_ms(started_at),
                payload={"status_code": response.status_code, "body": response.text[:2000], "model": selected_model, "web_mode": mode},
            )
            raise RuntimeError(f"OpenRouter web search request failed with {response.status_code}: {response.text[:240]}")

        try:
            response_payload = response.json()
        except json.JSONDecodeError as error:
            error_payload = {
                "error_type": error.__class__.__name__,
                "message": str(error),
                "status_code": response.status_code,
                "body_excerpt": response.text[:2000],
                "model": selected_model,
                "web_mode": mode,
            }
            _trace_provider(
                trace_type="provider_error",
                title="OpenRouter non-JSON response",
                summary="OpenRouter returned HTTP 200 with a response body that is not valid JSON.",
                duration_ms=_duration_ms(started_at),
                payload=error_payload,
            )
            return WebSearchProviderResult(
                sources=[],
                candidate_observations=[],
                provider_metadata={
                    "provider": "openrouter",
                    "model": selected_model,
                    "default_model": self.model,
                    "extractor_model": self.extractor_model,
                    "web_mode": mode,
                    "retrieval_provider": self.retrieval_provider,
                    "retrieval_engine": self.web_search_engine,
                    "provider_error": error_payload,
                },
            )
        retrieval_result = retrieval_result_from_openrouter_response(
            response_payload,
            provider_id=self.retrieval_provider,
            engine=self.web_search_engine,
            query=retrieval_request.query,
        )
        server_tool_usage = _server_tool_web_search_count(response_payload)
        server_tool_budget_decision = record_openrouter_server_tool_usage(count=server_tool_usage, task_id=budget_key)
        if server_tool_usage:
            _trace_provider(
                trace_type="normalization_result",
                title="OpenRouter server-tool usage",
                summary=f"OpenRouter reported {server_tool_usage} server-tool web searches.",
                duration_ms=_duration_ms(started_at),
                payload={
                    "task_id": budget_key,
                    "web_search_requests": server_tool_usage,
                    "budget_decision": server_tool_budget_decision.to_payload(),
                },
            )
        _trace_provider(
            trace_type="provider_response",
            title="OpenRouter retrieval response",
            summary=f"OpenRouter returned {len(retrieval_result.retrieved_sources)} retrieved sources.",
            duration_ms=_duration_ms(started_at),
            payload={
                "retrieval_request": retrieval_request.model_dump(),
                "retrieval_result": retrieval_result.model_dump(),
            },
        )
        _trace_provider(
            trace_type="normalization_result",
            title="OpenRouter extraction result",
            summary="OpenRouter response was parsed into Radar extraction observations.",
            duration_ms=_duration_ms(started_at),
            payload=_provider_response_trace_payload(response_payload, model=selected_model, web_mode=mode),
        )
        result = normalize_openrouter_response(
            response_payload,
            fallback_metadata={
                "provider": "openrouter",
                "model": selected_model,
                "default_model": self.model,
                "extractor_model": self.extractor_model,
                "web_mode": mode,
                "retrieval_provider": self.retrieval_provider,
                "retrieval_engine": self.web_search_engine,
                "retrieved_sources": [item.model_dump() for item in retrieval_result.retrieved_sources],
                "retrieval_source_outcomes": [item.model_dump() for item in retrieval_result.source_outcomes],
                "retrieved_source_count": len(retrieval_result.retrieved_sources),
                "openrouter_server_tool_usage": {
                    "web_search_requests": server_tool_usage,
                    "budget_decision": server_tool_budget_decision.to_payload(),
                },
            },
        )
        return _apply_source_verification(result, mode=self._source_verification_mode)

    def _model_for_search_plan(self, search_plan: RadarSearchPlan) -> str:
        stages = {query.stage for query in search_plan.queries}
        if stages & {"qualification_discovery", "qualification_gate", "coverage_check"}:
            return self.extractor_model
        return self.model


def normalize_openrouter_response(payload: dict[str, Any], *, fallback_metadata: dict[str, Any]) -> WebSearchProviderResult:
    message = payload.get("choices", [{}])[0].get("message", {})
    content = message.get("content") or "{}"
    parsed = _parse_json_object(content)
    content_repair = validate_and_repair_extraction_payload(content if content else parsed)
    parsed = content_repair.payload
    sources = [
        _source_from_payload(item, index=index)
        for index, item in enumerate(parsed.get("sources", []), start=1)
        if isinstance(item, dict)
    ]
    sources.extend(_sources_from_annotations(message.get("annotations", []), start_index=len(sources) + 1))
    repair = validate_and_repair_extraction_payload({**parsed, "sources": [source.model_dump() for source in sources]})
    parsed = repair.payload
    issues = [*content_repair.issues, *repair.issues]
    repair_actions = [*content_repair.repair_actions, *repair.repair_actions]
    validation_metadata = {
        **repair.to_metadata(),
        "issues": [issue.to_payload() for issue in issues],
        "repair_actions": list(repair_actions),
        "repaired": bool(repair_actions),
    }
    validation_metadata["state"] = extraction_validation_state(validation_metadata["issues"], repaired=bool(repair_actions))
    validation_metadata["valid"] = not any(issue.get("severity") == "error" for issue in validation_metadata["issues"])
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
            "extraction_validation_results": [validation_metadata],
            "extraction_validation_issues": [issue.to_payload() for issue in issues],
            "extraction_repair_results": list(repair_actions),
            "candidate_universe_gaps": [item for item in parsed.get("candidate_universe_gaps", []) if isinstance(item, dict)],
            "coverage_findings": [item for item in parsed.get("coverage_findings", []) if isinstance(item, dict)],
            "source_outcomes": [item for item in parsed.get("source_outcomes", []) if isinstance(item, dict)],
        },
    )


def _apply_source_verification(result: WebSearchProviderResult, *, mode: str) -> WebSearchProviderResult:
    verification_mode = normalize_verification_mode(mode)
    verified_sources = verify_sources(result.sources, mode=verification_mode)
    usable_sources = [
        source for source in verified_sources
        if supports_product_evidence(source, mode=verification_mode)
    ]
    usable_refs = {source.evidence_ref for source in usable_sources}
    if verification_mode == "strict":
        verified_candidates = [
            _filter_candidate_evidence_refs(candidate, usable_refs)
            for candidate in result.candidate_observations
            if _collect_candidate_evidence_refs(candidate) & usable_refs
        ]
        sources = usable_sources
    else:
        verified_candidates = [
            _filter_candidate_evidence_refs(candidate, usable_refs)
            for candidate in result.candidate_observations
            if _collect_candidate_evidence_refs(candidate) & usable_refs
        ]
        sources = usable_sources
    verification_results = [
        {
            "evidence_ref": source.evidence_ref,
            "title": source.title,
            "url": source.url,
            "query_id": source.query_id,
            "source_type": source.source_type,
            "verification_state": source.verification_state,
            "verification_mode": source.verification_mode,
            "verification_reason": source.verification_reason,
            "verification_status_code": source.verification_status_code,
        }
        for source in verified_sources
    ]
    _trace_provider(
        trace_type="normalization_result",
        title="Source verification result",
        summary=f"Verified {len(verified_sources)} sources in {verification_mode} mode.",
        payload={
            "verification_mode": verification_mode,
            "source_count": len(verified_sources),
            "usable_source_count": len(usable_sources),
            "discarded_source_count": len(verified_sources) - len(usable_sources),
            "sources": verification_results,
        },
    )
    verified_candidates = [
        _mark_candidate_verification_risk(candidate, sources_by_ref={source.evidence_ref: source for source in sources})
        for candidate in verified_candidates
    ]
    return WebSearchProviderResult(
        sources=sources,
        candidate_observations=verified_candidates,
        provider_metadata={
            **result.provider_metadata,
            "source_verification": "http_status",
            "source_verification_mode": verification_mode,
            "source_verification_results": verification_results,
            "discarded_source_count": len(verified_sources) - len(usable_sources),
        },
    )


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


def _mark_candidate_verification_risk(candidate: dict[str, Any], *, sources_by_ref: dict[str, RadarSourceEvidence]) -> dict[str, Any]:
    risky_refs = {
        ref for ref in _collect_candidate_evidence_refs(candidate)
        if sources_by_ref.get(ref) is not None and sources_by_ref[ref].verification_state != "reachable"
    }
    if not risky_refs:
        return candidate
    flags = [str(item) for item in candidate.get("review_flags", []) if str(item).strip()]
    flags.append("source_verification_review")
    marked = dict(candidate)
    marked["review_flags"] = sorted(set(flags))
    marked["source_verification_risks"] = sorted(risky_refs)
    return marked


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


def _search_plan_budget_key(search_plan: RadarSearchPlan) -> str:
    if search_plan.queries:
        return search_plan.queries[0].query_id or search_plan.radar_id
    return search_plan.radar_id


def _server_tool_web_search_count(payload: dict[str, Any]) -> int:
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        return 0
    details = usage.get("server_tool_use_details")
    if not isinstance(details, dict):
        return 0
    try:
        return max(0, int(details.get("web_search_requests") or 0))
    except (TypeError, ValueError):
        return 0


def _current_web_max_results() -> int | None:
    budget = current_external_call_budget()
    return None if budget is None else budget.settings.openrouter_web_max_results_per_call


def _current_web_max_total_results() -> int | None:
    budget = current_external_call_budget()
    return None if budget is None else budget.settings.openrouter_web_max_total_results_per_call


def _budget_limited_result(
    *,
    model: str,
    default_model: str,
    extractor_model: str,
    web_mode: str,
    retrieval_provider: str,
    retrieval_engine: str,
    budget_decision: dict[str, object],
) -> WebSearchProviderResult:
    return WebSearchProviderResult(
        sources=[],
        candidate_observations=[],
        provider_metadata={
            "provider": "openrouter",
            "model": model,
            "default_model": default_model,
            "extractor_model": extractor_model,
            "web_mode": web_mode,
            "retrieval_provider": retrieval_provider,
            "retrieval_engine": retrieval_engine,
            "budget_decision": {
                **budget_decision,
                "state": "not_executed_budget_limited",
            },
            "coverage_findings": [{
                "summary": budget_decision.get("message", "OpenRouter external-call budget exhausted."),
                "completeness_risk": "medium",
                "warnings": [str(budget_decision.get("message", "OpenRouter external-call budget exhausted."))],
            }],
        },
    )


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
