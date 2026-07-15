"""Small mapping helpers for structured company registry observations."""

from __future__ import annotations

from typing import Any

from power_web_os.application.radar.candidate_discovery.contracts import WebSearchProviderResult


def radar_with_structured_observations(radar: dict[str, Any], result: WebSearchProviderResult) -> dict[str, Any]:
    observations = [
        dict(item)
        for item in result.provider_metadata.get("structured_company_observations", [])
        if isinstance(item, dict)
    ]
    if not observations:
        return radar
    existing = [
        dict(item)
        for item in radar.get("structured_company_observations", [])
        if isinstance(item, dict)
    ]
    return {**radar, "structured_company_observations": dedupe_observations([*existing, *observations])}


def registry_snippet(observation: Any) -> str:
    parts = [
        getattr(observation, "status", ""),
        f"INN {getattr(observation, 'inn', '')}" if getattr(observation, "inn", "") else "",
        f"OGRN {getattr(observation, 'ogrn', '')}" if getattr(observation, "ogrn", "") else "",
        getattr(observation, "address", ""),
        f"OKVED {getattr(observation, 'okved', '')}" if getattr(observation, "okved", "") else "",
    ]
    return "; ".join(part for part in parts if part) or "Structured company registry observation."


def dedupe_observations(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for item in values:
        key = str(item.get("inn") or item.get("ogrn") or item.get("normalized_legal_name") or item.get("legal_name") or "").lower()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def dedupe_text(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = " ".join(str(value).split())
        key = text.lower()
        if text and key not in seen:
            result.append(text)
            seen.add(key)
    return result
