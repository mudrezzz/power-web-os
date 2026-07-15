"""Application service for updating active Radar definition payloads.

API routes delegate definition edits here so transport code does not own
definition normalization, source usage-obligation validation, or repository
write semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from power_web_os.application.ports import RadarDefinitionRepository
from power_web_os.application.radar.candidate_discovery.sources.obligations import SOURCE_USAGE_OBLIGATIONS
from power_web_os.application.radar.lifecycle.records import RadarDefinitionRecord


class RadarDefinitionUpdateError(ValueError):
    """Raised when a definition update cannot be accepted."""


@dataclass(frozen=True, slots=True)
class RadarDefinitionUpdateCommand:
    radar_id: str
    definition_payload: dict[str, Any]
    definition_version: str | None = None
    is_active: bool = True


class RadarDefinitionUpdateService:
    """Updates the active definition while preserving application-layer rules."""

    def __init__(self, repository: RadarDefinitionRepository) -> None:
        self._repository = repository

    def update_active(self, command: RadarDefinitionUpdateCommand) -> RadarDefinitionRecord:
        active = self._repository.get_active(command.radar_id)
        if active is None and not str(command.definition_payload.get("definition_id") or "").strip():
            raise RadarDefinitionUpdateError(f"Active Radar definition not found: {command.radar_id}")

        fallback_definition_id = active.definition_id if active is not None else ""
        definition_id = str(command.definition_payload.get("definition_id") or fallback_definition_id).strip()
        if not definition_id:
            raise RadarDefinitionUpdateError("Definition id is required.")
        payload = _normalized_definition_payload(
            command.definition_payload,
            radar_id=command.radar_id,
            definition_id=definition_id,
        )
        version = command.definition_version or (active.definition_version if active else str(payload.get("definition_version") or "ui-update"))
        return self._repository.upsert(
            RadarDefinitionRecord(
                definition_id=definition_id,
                radar_id=command.radar_id,
                definition_payload=payload,
                definition_version=version,
                is_active=command.is_active,
            )
        )


def _normalized_definition_payload(payload: dict[str, Any], *, radar_id: str, definition_id: str) -> dict[str, Any]:
    normalized = dict(payload)
    normalized["definition_id"] = definition_id
    normalized["radar_id"] = radar_id
    global_policy = dict(normalized.get("global_search_policy") or {})
    global_policy["sources"] = [_normalized_source(source) for source in _source_list(global_policy.get("sources"))]
    normalized["global_search_policy"] = global_policy
    return normalized


def _normalized_source(source: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(source)
    obligation = str(normalized.get("usage_obligation") or "preferred").strip().lower()
    if obligation not in SOURCE_USAGE_OBLIGATIONS:
        raise RadarDefinitionUpdateError(f"Unsupported source usage obligation: {obligation}")
    normalized["usage_obligation"] = obligation
    return normalized


def _source_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]
