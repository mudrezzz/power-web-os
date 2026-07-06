"""Provider payload parsing and repair for signal monitoring."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from power_web_os.application.radar.signal_monitoring.contracts import SignalSourceRef


@dataclass(frozen=True)
class ParsedSignalPayload:
    sources: list[SignalSourceRef]
    observations: list[dict[str, Any]]
    repaired: bool = False


@dataclass(frozen=True)
class SignalPayloadParseFailure:
    code: str
    message: str
    path: str = "$"


def parse_payload(payload: Any) -> ParsedSignalPayload | SignalPayloadParseFailure:
    payload, repaired_json = _payload_object(payload)
    if not isinstance(payload, dict):
        return SignalPayloadParseFailure("schema_invalid", "Provider payload must be a JSON object.")
    sources, sources_repaired = _list_field(payload, "sources", SignalSourceRef)
    if isinstance(sources, SignalPayloadParseFailure):
        return sources
    raw_observations = _raw_list_field(payload, "observations")
    if isinstance(raw_observations, SignalPayloadParseFailure):
        return raw_observations
    observations, observations_repaired = raw_observations
    return ParsedSignalPayload(
        sources=sources,
        observations=observations,
        repaired=repaired_json or sources_repaired or observations_repaired,
    )


def _payload_object(payload: Any) -> tuple[Any, bool]:
    if not isinstance(payload, str):
        return payload, False
    stripped = payload.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?", "", stripped).strip()
        stripped = re.sub(r"```$", "", stripped).strip()
    try:
        return json.loads(stripped), True
    except json.JSONDecodeError:
        return payload, False


def _list_field(
    payload: dict[str, Any],
    field_name: str,
    model_type: type[SignalSourceRef],
) -> tuple[list[SignalSourceRef], bool] | SignalPayloadParseFailure:
    raw = payload.get(field_name, [])
    if isinstance(raw, dict):
        raw = [raw]
        repaired = True
    else:
        repaired = False
    if not isinstance(raw, list):
        return SignalPayloadParseFailure("schema_invalid", f"{field_name} must be a list.", f"$.{field_name}")
    try:
        return [model_type.model_validate(item) for item in raw if isinstance(item, dict)], repaired
    except Exception as exc:  # pragma: no cover - pydantic message is not stable enough for exact assertions
        return SignalPayloadParseFailure("schema_invalid", f"{field_name} item is invalid: {exc}", f"$.{field_name}")


def _raw_list_field(payload: dict[str, Any], field_name: str) -> tuple[list[dict[str, Any]], bool] | SignalPayloadParseFailure:
    raw = payload.get(field_name, [])
    if isinstance(raw, dict):
        raw = [raw]
        repaired = True
    else:
        repaired = False
    if not isinstance(raw, list):
        return SignalPayloadParseFailure("schema_invalid", f"{field_name} must be a list.", f"$.{field_name}")
    if not all(isinstance(item, dict) for item in raw):
        return SignalPayloadParseFailure("schema_invalid", f"{field_name} items must be objects.", f"$.{field_name}")
    return raw, repaired
