"""OpenRouter adapter for the standalone signal-monitoring provider port."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from time import sleep
from typing import Any

from power_web_os.application.radar.signal_monitoring.contracts import (
    SignalAttemptRole,
    SignalMonitoringProviderResult,
    SignalSearchExecutionReceipt,
    SignalSearchTask,
    SignalSourceRef,
)
from power_web_os.application.radar.configuration.runtime_settings import effective_runtime_env
from power_web_os.integrations.openrouter_trace import parse_json_object
from power_web_os.integrations.openrouter_annotations import normalized_openrouter_annotations


class OpenRouterSignalMonitoringProvider:
    """Execute bounded signal tasks without owning signal semantics."""

    runtime_name = "openrouter_signal_monitoring"

    def __init__(
        self,
        *,
        model_id: str,
        temperature: float = 0.0,
        api_key: str | None = None,
        env_path: Path | None = None,
        timeout_seconds: float = 90.0,
    ) -> None:
        env = effective_runtime_env(dotenv_path=env_path or Path.cwd() / ".env")
        self._api_key = api_key or env.get("OPENROUTER_API_KEY")
        self.model_id = model_id
        self.temperature = temperature
        self.timeout_seconds = timeout_seconds
        self.web_search_engine = env.get("POWER_WEB_OS_OPENROUTER_WEB_SEARCH_ENGINE") or "perplexity"
        self.web_max_results = _positive_int(
            env.get("POWER_WEB_OS_OPENROUTER_SIGNAL_WEB_MAX_RESULTS"),
            default=8,
        )
        self.web_max_total_results = _positive_int(
            env.get("POWER_WEB_OS_OPENROUTER_SIGNAL_WEB_MAX_TOTAL_RESULTS"),
            default=16,
        )
        self.web_search_context_size = (
            env.get("POWER_WEB_OS_OPENROUTER_SIGNAL_WEB_CONTEXT_SIZE") or "medium"
        )
        self.min_request_interval_seconds = _non_negative_float(
            env.get("POWER_WEB_OS_OPENROUTER_SIGNAL_MIN_REQUEST_INTERVAL_SECONDS"),
            default=2.0,
        )

    @property
    def credentials_available(self) -> bool:
        return bool(self._api_key)

    def run_signal_task(
        self,
        *,
        task: SignalSearchTask,
        attempt_role: SignalAttemptRole,
    ) -> SignalMonitoringProviderResult:
        if not self._api_key:
            raise RuntimeError("OPENROUTER_API_KEY is required for live signal monitoring")
        try:
            import httpx
        except ImportError as exc:  # pragma: no cover - installation shape
            raise RuntimeError("Install the agent extra to run live signal monitoring") from exc

        started_at = _now()
        _pace_openrouter_signal_request(self.min_request_interval_seconds)
        response = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/mudrezzz/power-web-os",
                "X-Title": "Power Web OS Signal Monitoring",
            },
            json=self._request(task=task, attempt_role=attempt_role),
            timeout=self.timeout_seconds,
        )
        if response.status_code >= 400:
            raise RuntimeError(
                "OpenRouter signal search failed with "
                f"HTTP {response.status_code}: {_safe_error_prefix(response.text)}"
            )
        payload = response.json()
        message = self._dict(self._first(self._list(payload.get("choices"))).get("message"))
        content = str(message.get("content") or "")
        parsed = parse_json_object(content)
        normalized = dict(parsed) if isinstance(parsed, dict) else {}
        sources = [dict(item) for item in normalized.get("sources", []) if isinstance(item, dict)]
        annotation_sources = normalized_openrouter_annotations(
            message.get("annotations", []), source_ref_prefix="signal_retrieved"
        )
        known_urls = {str(item.get("url") or "") for item in sources}
        sources.extend(item for item in annotation_sources if str(item.get("url") or "") not in known_urls)
        if normalized:
            normalized["sources"] = sources
            normalized = _task_scoped_signal_payload(normalized, task=task)
            sources = [dict(item) for item in normalized.get("sources", []) if isinstance(item, dict)]
        receipt_sources = _normalized_signal_sources(sources)
        if normalized:
            normalized["sources"] = [item.model_dump(mode="json") for item in receipt_sources]
        receipt = SignalSearchExecutionReceipt(
            task_id=task.task_id,
            candidate_id=task.candidate_id,
            signal_code=task.signal_code,
            source_lane=task.source_lane,
            query=task.query,
            requested_urls=[item.url for item in task.source_contracts if item.url],
            requested_domains=list(task.domain_restrictions),
            engine=self.web_search_engine,
            window_start=task.window_start,
            window_end=task.window_end,
            started_at=started_at,
            completed_at=_now(),
            result_count=len(receipt_sources),
            source_refs=[item.source_ref for item in receipt_sources],
            outcome="retrieved" if receipt_sources else "no_results",
        )
        return SignalMonitoringProviderResult(
            payload=normalized or content,
            runtime_name=self.runtime_name,
            model_id=self.model_id,
            execution_receipt=receipt,
        )

    def _request(self, *, task: SignalSearchTask, attempt_role: SignalAttemptRole) -> dict[str, Any]:
        task_card = {
            "task_id": task.task_id,
            "candidate_id": task.candidate_id,
            "candidate_name": task.candidate_name,
            "signal_code": task.signal_code,
            "signal_label": task.signal_label,
            "query": task.query,
            "lookback_days": task.lookback_days,
            "source_lane": task.source_lane,
            "source_ids": task.source_ids,
            "known_source_refs": task.known_source_refs,
            "source_contracts": [item.model_dump(mode="json") for item in task.source_contracts],
            "domain_restrictions": task.domain_restrictions,
            "window_start": task.window_start,
            "window_end": task.window_end,
            "attempt_role": attempt_role,
            "response_contract": {
                "sources": ["source_ref", "title", "url", "snippet", "source_id", "retrieved_at", "published_at"],
                "observations": [
                    "candidate_id", "signal_code", "status", "summary", "score",
                    "evidence_refs", "event_at", "event_end_at", "published_at", "confidence",
                ],
            },
            "constraints": [
                "Return one strict JSON object with sources and observations arrays.",
                "Do not add or rediscover candidates.",
                "Use retrieved_at only for retrieval audit; it never proves freshness.",
                "Use event_at when the event date is known and source.published_at when publication date is known.",
                "If relevant evidence has no reliable date, return status observed with evidence refs; backend will route it to human review.",
                "Use only event or publication evidence inside the requested lookback window for confirmed fresh signals.",
                "Use status not_observed only after a real search found no fresh evidence.",
                "Every observed item must link to returned source_ref values.",
                "Do not include secrets, headers, hidden reasoning, or raw tool output.",
            ],
        }
        return {
            "model": self.model_id,
            "messages": [
                {
                    "role": "system",
                    "content": "You monitor recent B2B account signals. Search the web and return strict JSON only.",
                },
                {"role": "user", "content": json.dumps(task_card, ensure_ascii=False)},
            ],
            "temperature": self.temperature,
            "response_format": {"type": "json_object"},
            "tools": [{
                "type": "openrouter:web_search",
                "parameters": {
                    "engine": self.web_search_engine,
                    "max_results": self.web_max_results,
                    "max_total_results": self.web_max_total_results,
                    "search_context_size": self.web_search_context_size,
                },
            }],
        }

    @staticmethod
    def _dict(value: Any) -> dict[str, Any]:
        return dict(value) if isinstance(value, dict) else {}

    @staticmethod
    def _list(value: Any) -> list[Any]:
        return list(value) if isinstance(value, list) else []

    @staticmethod
    def _first(value: list[Any]) -> dict[str, Any]:
        return dict(value[0]) if value and isinstance(value[0], dict) else {}


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


_LAST_OPENROUTER_SIGNAL_REQUEST_AT = 0.0


def _pace_openrouter_signal_request(min_interval_seconds: float) -> None:
    """Avoid tight OpenRouter web-search bursts during live quality validation."""

    if min_interval_seconds <= 0:
        return
    global _LAST_OPENROUTER_SIGNAL_REQUEST_AT
    # time.monotonic is intentionally imported lazily to keep the module's public
    # imports focused on product contracts and provider setup.
    from time import monotonic

    now = monotonic()
    wait_seconds = min_interval_seconds - (now - _LAST_OPENROUTER_SIGNAL_REQUEST_AT)
    if wait_seconds > 0:
        sleep(wait_seconds)
    _LAST_OPENROUTER_SIGNAL_REQUEST_AT = monotonic()


def _positive_int(value: str | None, *, default: int) -> int:
    try:
        parsed = int(str(value or "").strip())
    except ValueError:
        return default
    return parsed if parsed > 0 else default


def _non_negative_float(value: str | None, *, default: float) -> float:
    try:
        parsed = float(str(value or "").strip())
    except ValueError:
        return default
    return parsed if parsed >= 0 else default


def _safe_error_prefix(text: str) -> str:
    cleaned = " ".join(str(text or "").split())
    if not cleaned:
        return "empty response"
    return cleaned[:240]


def _normalized_signal_sources(sources: list[dict[str, Any]]) -> list[SignalSourceRef]:
    result: list[SignalSourceRef] = []
    for index, raw in enumerate(sources, start=1):
        payload = dict(raw)
        payload["source_ref"] = str(payload.get("source_ref") or f"signal_retrieved_{index}")
        for field in ("title", "url", "snippet", "source_id", "observed_at", "retrieved_at", "published_at", "date_evidence", "candidate_id"):
            payload[field] = str(payload.get(field) or "")
        payload["date_basis"] = str(payload.get("date_basis") or "none")
        payload["date_confidence"] = str(payload.get("date_confidence") or "weak")
        result.append(SignalSourceRef.model_validate(payload))
    return result


def _task_scoped_signal_payload(payload: dict[str, Any], *, task: SignalSearchTask) -> dict[str, Any]:
    """Make provider-local source refs unique before run-level aggregation."""

    result = dict(payload)
    known_refs = {item.source_ref for item in task.source_contracts if item.source_ref}
    ref_map: dict[str, str] = {}
    scoped_sources: list[dict[str, Any]] = []
    for index, raw in enumerate(result.get("sources", []), start=1):
        if not isinstance(raw, dict):
            continue
        source = dict(raw)
        original = str(source.get("source_ref") or f"signal_retrieved_{index}")
        scoped = original if original in known_refs else f"{task.task_id}:{original}"
        ref_map[original] = scoped
        source["source_ref"] = scoped
        scoped_sources.append(source)
    result["sources"] = scoped_sources

    scoped_observations: list[dict[str, Any]] = []
    for raw in result.get("observations", []):
        if not isinstance(raw, dict):
            continue
        observation = dict(raw)
        observation["evidence_refs"] = [
            ref_map.get(str(ref), str(ref) if str(ref) in known_refs else f"{task.task_id}:{ref}")
            for ref in observation.get("evidence_refs", [])
            if str(ref)
        ]
        scoped_observations.append(observation)
    result["observations"] = scoped_observations
    return result
