"""OpenRouter and recorded-provider adapters for live Radar search."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from power_web_os.application.live_radar_contracts import (
    RadarSearchPlan,
    RadarSourceEvidence,
    WebSearchProvider,
    WebSearchProviderResult,
)
from power_web_os.application.live_radar_normalization import _dedupe_sources


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
                            "operator": "AND|OR|AND_NOT|OR_NOT",
                            "requirement_level": "required|recommended",
                            "status": "confirmed|weak|unknown|rejected",
                            "confidence": "high|medium|low",
                            "rationale": "why this status",
                            "evidence_refs": ["source ids"],
                            "evidence_findings": [
                                {
                                    "source_ref": "source id",
                                    "fact": "what exactly was found",
                                    "excerpt": "short source excerpt or paraphrased fragment, not a long quote",
                                    "excerpt_type": "quote|paraphrase|not_available",
                                    "why_it_matches_rule": "why this fact satisfies or fails the rule",
                                    "evidence_strength": "strong|medium|weak",
                                    "contradicts_rule": False,
                                }
                            ],
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
                            "evidence_findings": [
                                {
                                    "source_ref": "source id",
                                    "fact": "what exactly was found",
                                    "excerpt": "short source excerpt or paraphrased fragment, not a long quote",
                                    "excerpt_type": "quote|paraphrase|not_available",
                                    "why_it_matches_signal": "why this fact is an intent signal",
                                    "why_score_applies": "why score 0, 1, or 2 applies",
                                    "evidence_strength": "strong|medium|weak",
                                    "contradicts_signal": False,
                                }
                            ],
                            "score_evaluation": {
                                "scale": "0-2",
                                "applied_score": 0,
                                "max_score": 2,
                                "rule_snapshot": "rubric rule used for the score",
                                "explanation": "short score rationale",
                            },
                        }
                    ],
                    "review_flags": ["why human review is needed"],
                }
            ],
        },
        "rules": [
            "Do not invent candidates without source evidence.",
            "If evidence is weak, mark it weak/unclear and add a review flag.",
            "For each qualification item, explain used sources, exact facts, a short reviewable excerpt or paraphrase, and why they match the rule.",
            "For each signal, explain source-linked facts, a short reviewable excerpt or paraphrase, why it matches the signal, and why the 0-2 score applies.",
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
