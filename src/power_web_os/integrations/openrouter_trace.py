"""Shared OpenRouter trace and response parsing helpers."""

from __future__ import annotations

import json
import re
from time import perf_counter
from typing import Any

from power_web_os.application.radar_technical_trace import RadarRunTechnicalTraceCommand, append_current_trace


def parse_json_object(content: str) -> dict[str, Any]:
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


def provider_response_trace_payload(payload: dict[str, Any], *, model: str, web_mode: str) -> dict[str, Any]:
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
        "parser_status": "json_object" if parse_json_object(str(content)) else "empty_or_unparseable",
    }


def duration_ms(started_at: float) -> int:
    return max(0, int((perf_counter() - started_at) * 1000))


def trace_provider(
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
