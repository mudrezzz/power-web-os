"""OpenRouter and recorded-provider adapters for live Radar search."""

from __future__ import annotations

import json
import os
import re
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
from power_web_os.application.radar_technical_trace import RadarRunTechnicalTraceCommand, append_current_trace
from power_web_os.integrations.openrouter_request_builder import build_openrouter_request
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
        )
        _trace_provider(
            trace_type="provider_request",
            title="OpenRouter request",
            summary=f"OpenRouter request using {mode}.",
            payload={
                "url": "https://openrouter.ai/api/v1/chat/completions",
                "model": selected_model,
                "web_mode": mode,
                "request": payload,
            },
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
                    "provider_error": error_payload,
                },
            )
        _trace_provider(
            trace_type="provider_response",
            title="OpenRouter response",
            summary="OpenRouter returned a structured response payload.",
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


def _parse_json_object(content: str) -> dict[str, Any]:
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?", "", stripped).strip()
        stripped = re.sub(r"```$", "", stripped).strip()
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        for index, char in enumerate(stripped):
            if char != "{":
                continue
            try:
                parsed, _ = decoder.raw_decode(stripped[index:])
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _provider_response_trace_payload(payload: dict[str, Any], *, model: str, web_mode: str) -> dict[str, Any]:
    message = payload.get("choices", [{}])[0].get("message", {})
    content = message.get("content") or ""
    return {
        "response_id": payload.get("id"),
        "model": model,
        "web_mode": web_mode,
        "usage": payload.get("usage", {}),
        "message": {
            "role": message.get("role"),
            "content": content,
            "annotations": message.get("annotations", []),
        },
        "parser_status": "json_object" if _parse_json_object(str(content)) else "empty_or_unparseable",
    }


def _duration_ms(started_at: float) -> int:
    return max(0, int((perf_counter() - started_at) * 1000))


def _trace_provider(
    *,
    trace_type: str,
    title: str,
    summary: str,
    payload: dict[str, Any],
    duration_ms: int | None = None,
) -> None:
    append_current_trace(
        RadarRunTechnicalTraceCommand(
            run_id="",
            phase="provider",
            node_name="openrouter_web_search",
            trace_type=trace_type,
            title=title,
            summary=summary,
            duration_ms=duration_ms,
            payload=payload,
        )
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
