"""OpenRouter adapter for Power Web title planning and public-web retrieval."""

from __future__ import annotations

import json
from pathlib import Path
import re
from time import monotonic, sleep
from typing import Any
from urllib.parse import urlparse

from power_web_os.application.radar.configuration.runtime_settings import effective_runtime_env
from power_web_os.application.radar.power_web_discovery.people_search.contracts import (
    PeopleSearchProviderResult,
    PeopleSearchProviderSource,
    PeopleSearchTask,
    PowerWebPeopleSearchPlanningInput,
)
from power_web_os.integrations.openrouter_annotations import normalized_openrouter_annotations
from power_web_os.integrations.openrouter_trace import parse_json_object


class OpenRouterPeopleSearchProvider:
    runtime_name = "openrouter_people_search"

    def __init__(
        self,
        *,
        planner_model_id: str,
        search_model_id: str,
        api_key: str | None = None,
        env_path: Path | None = None,
        timeout_seconds: float = 120.0,
    ) -> None:
        env = effective_runtime_env(dotenv_path=env_path or Path.cwd() / ".env")
        self._api_key = api_key or env.get("OPENROUTER_API_KEY")
        self.planner_model_id = planner_model_id
        self.model_id = search_model_id
        self.timeout_seconds = timeout_seconds
        self.web_search_engine = env.get("POWER_WEB_OS_OPENROUTER_WEB_SEARCH_ENGINE") or "perplexity"
        self.web_max_results = _positive_int(env.get("POWER_WEB_OS_OPENROUTER_PEOPLE_WEB_MAX_RESULTS"), 6)
        self.web_max_total_results = _positive_int(env.get("POWER_WEB_OS_OPENROUTER_PEOPLE_WEB_MAX_TOTAL_RESULTS"), 10)
        self.min_request_interval_seconds = _non_negative_float(
            env.get("POWER_WEB_OS_OPENROUTER_PEOPLE_MIN_REQUEST_INTERVAL_SECONDS"), 1.5
        )
        self._last_request_at = 0.0

    @property
    def credentials_available(self) -> bool:
        return bool(self._api_key)

    def propose(self, planning_input: PowerWebPeopleSearchPlanningInput) -> dict[str, tuple[str, ...]]:
        payload = self._post(self._hypothesis_request(planning_input))
        message = _message(payload)
        parsed = parse_json_object(str(message.get("content") or ""))
        roles = parsed.get("roles") if isinstance(parsed, dict) else None
        if not isinstance(roles, list):
            raise ValueError("people title planner returned an invalid roles array")
        result: dict[str, tuple[str, ...]] = {}
        for item in roles:
            if not isinstance(item, dict):
                raise ValueError("people title planner returned an invalid role item")
            demand_id = str(item.get("demand_id") or "").strip()
            variants = item.get("variants")
            if not demand_id or not isinstance(variants, list):
                raise ValueError("people title planner omitted demand_id or variants")
            result[demand_id] = tuple(str(value).strip() for value in variants if str(value).strip())
        return result

    def search(self, task: PeopleSearchTask) -> PeopleSearchProviderResult:
        payload = self._post(self._search_request(task))
        message = _message(payload)
        parsed = parse_json_object(str(message.get("content") or ""))
        raw_sources = parsed.get("sources", []) if isinstance(parsed, dict) else []
        sources = [dict(item) for item in raw_sources if isinstance(item, dict)]
        sources.extend(normalized_openrouter_annotations(
            message.get("annotations", []), source_ref_prefix=f"{task.task_id}:citation"
        ))
        normalized: list[PeopleSearchProviderSource] = []
        seen_urls: set[str] = set()
        for rank, source in enumerate(sources, start=1):
            url = str(source.get("url") or "").strip()
            if not url or url in seen_urls or not _domain_allowed(url, task.domain_restrictions):
                continue
            seen_urls.add(url)
            normalized.append(PeopleSearchProviderSource(
                source_ref=f"{task.task_id}:source:{len(normalized) + 1}",
                url=url,
                title=_safe_text(source.get("title") or url, limit=500),
                excerpt=_safe_text(source.get("excerpt") or source.get("snippet") or "", limit=1200),
                rank=len(normalized) + 1,
                page_access_limited=bool(source.get("page_access_limited")) or task.lane == "hh_public_web",
            ))
        return PeopleSearchProviderResult(
            outcome="searched_results" if normalized else "searched_no_results",
            sources=tuple(normalized),
            engine=self.web_search_engine,
            model_id=self.model_id,
            server_tool_searches=_server_tool_search_count(payload),
        )

    def _post(self, request: dict[str, Any]) -> dict[str, Any]:
        if not self._api_key:
            raise RuntimeError("OPENROUTER_API_KEY is required for live people search")
        try:
            import httpx
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("Install the agent extra to run live people search") from exc
        elapsed = monotonic() - self._last_request_at
        if elapsed < self.min_request_interval_seconds:
            sleep(self.min_request_interval_seconds - elapsed)
        response = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/mudrezzz/power-web-os",
                "X-Title": "Power Web OS People Search",
            },
            json=request,
            timeout=self.timeout_seconds,
        )
        self._last_request_at = monotonic()
        if response.status_code >= 400:
            raise RuntimeError(f"OpenRouter people search failed with HTTP {response.status_code}")
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("OpenRouter people search returned a non-object response")
        return payload

    def _hypothesis_request(self, planning_input: PowerWebPeopleSearchPlanningInput) -> dict[str, Any]:
        role_demands = [{
            "demand_id": item.demand_id,
            "semantic_role_code": item.semantic_role_code,
            "display_name": item.display_name,
            "responsibility": item.responsibility,
            "scope": item.scope,
        } for item in planning_input.role_demands]
        task = {
            "account": {
                "legal_name": planning_input.account_legal_name,
                "aliases": planning_input.account_aliases,
                "geography": planning_input.geography,
                "language": planning_input.language,
            },
            "role_demands": role_demands,
            "response_contract": {"roles": [{"demand_id": "existing demand id", "variants": ["up to five role/title variants"]}]},
            "constraints": [
                "Return every supplied demand_id exactly once and do not create new demand ids.",
                "Suggest account-specific public role or function titles, not people.",
                "Do not return names, contacts, URLs, search queries, blind controls or explanations.",
                "Keep the source language; do not invent transliterations.",
                "Return strict JSON only.",
            ],
        }
        return {
            "model": self.planner_model_id,
            "messages": [
                {"role": "system", "content": "Map semantic buying roles to plausible account-specific functions. Return strict JSON only."},
                {"role": "user", "content": json.dumps(task, ensure_ascii=False)},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }

    def _search_request(self, task: PeopleSearchTask) -> dict[str, Any]:
        task_card = {
            "task_id": task.task_id,
            "account_id": task.account_id,
            "demand_id": task.demand_id,
            "semantic_role_code": task.semantic_role_code,
            "source_lane": task.lane,
            "query": task.query,
            "domain_restrictions": task.domain_restrictions,
            "response_contract": {"sources": ["url", "title", "excerpt", "page_access_limited"]},
            "constraints": [
                "Run the supplied public web search and return source leads only.",
                "Respect every domain restriction; do not use an API, authentication, crawling or bypass.",
                "A snippet does not prove identity or employment.",
                "Do not return private contacts, raw HTML, headers, credentials, tool dumps or hidden reasoning.",
                "Return searched sources as strict JSON; return an empty sources array when none were found.",
            ],
        }
        return {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": "Find public source leads for B2B people research. Return strict JSON only."},
                {"role": "user", "content": json.dumps(task_card, ensure_ascii=False)},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "tools": [{
                "type": "openrouter:web_search",
                "parameters": {
                    "engine": self.web_search_engine,
                    "max_results": self.web_max_results,
                    "max_total_results": self.web_max_total_results,
                    "search_context_size": "medium",
                },
            }],
        }


def _message(payload: dict[str, Any]) -> dict[str, Any]:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise ValueError("OpenRouter response omitted choices")
    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise ValueError("OpenRouter response omitted message")
    return message


def _domain_allowed(url: str, restrictions: tuple[str, ...]) -> bool:
    if not restrictions:
        return True
    host = (urlparse(url).hostname or "").casefold().removeprefix("www.")
    return any(host == domain.casefold() or host.endswith(f".{domain.casefold()}") for domain in restrictions)


def _safe_text(value: object, *, limit: int) -> str:
    text = " ".join(str(value or "").replace("<", " ").replace(">", " ").split())
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[redacted-contact]", text)
    text = re.sub(r"(?<!\w)\+?\d[\d\s()\-]{7,}\d", "[redacted-contact]", text)
    return text[:limit] or "Public source"


def _positive_int(value: str | None, default: int) -> int:
    try:
        parsed = int(str(value or ""))
    except ValueError:
        return default
    return parsed if parsed > 0 else default


def _non_negative_float(value: str | None, default: float) -> float:
    try:
        parsed = float(str(value or ""))
    except ValueError:
        return default
    return parsed if parsed >= 0 else default


def _server_tool_search_count(payload: dict[str, Any]) -> int:
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        return 0
    details = usage.get("server_tool_use_details") or usage.get("server_tool_usage")
    if not isinstance(details, dict):
        return 0
    try:
        return max(0, int(details.get("web_search_requests") or 0))
    except (TypeError, ValueError):
        return 0
