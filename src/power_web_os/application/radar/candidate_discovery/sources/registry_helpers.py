from __future__ import annotations

import re
from typing import Any


def promotable_registry_observations(result: Any) -> list[Any]:
    """Avoid promoting every medium suggestion from an ambiguous registry lookup."""

    ambiguous = any(outcome.outcome == "ambiguous_match" for outcome in result.outcomes)
    if not ambiguous:
        return list(result.observations)
    return [
        observation
        for observation in result.observations
        if observation.match_quality == "high" or observation.matched_by in {"inn", "ogrn"}
    ]


def registry_ambiguity_fanout_limit(radar: dict[str, Any]) -> int:
    context = radar.get("task_context") if isinstance(radar.get("task_context"), dict) else {}
    value = context.get("max_registry_ambiguity_fanout") if isinstance(context, dict) else None
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 3
    return parsed if parsed >= 0 else 3


def structured_observations_from_registry(
    observations: list[Any],
    *,
    request: Any,
    provider_id: str,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for observation in observations:
        result.append({
            "source_ref": observation.source_ref or _stable_source_ref(provider_id, observation.legal_name),
            "source_id": request.source_id,
            "provider_id": provider_id,
            "entity_type": observation.entity_type or "legal_entity",
            "legal_name": observation.legal_name,
            "normalized_legal_name": observation.normalized_legal_name or normalize_company_name(observation.legal_name),
            "inn": observation.inn,
            "ogrn": observation.ogrn,
            "kpp": observation.kpp,
            "status": observation.status,
            "address": observation.address,
            "okved": observation.okved,
            "match_quality": observation.match_quality,
            "matched_by": observation.matched_by,
            "lookup_query": observation.lookup_query or request.query,
            "provider_record_id": observation.provider_record_id,
            "facts": dict(observation.facts),
        })
    return result


def normalize_company_name(value: str) -> str:
    normalized = re.sub(r"[«»\"'.,]", " ", value.lower())
    normalized = re.sub(r"\b(??|???|???|???|???|???|jsc|pjsc|llc)\b", " ", normalized, flags=re.IGNORECASE)
    return " ".join(normalized.split())


def _stable_source_ref(provider_id: str, value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", str(value).lower()).strip("_")
    return f"{provider_id}_{normalized or 'company'}"[:80]
