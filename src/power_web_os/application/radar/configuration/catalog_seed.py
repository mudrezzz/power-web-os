"""Map deterministic Radar catalog artifacts into application records.

The seed path consumes the already-normalized catalog payload so persistence
does not need to know workbook import details or live provider behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from power_web_os.application.radar.lifecycle.records import RadarDefinitionRecord, RadarRecord


@dataclass(frozen=True, slots=True)
class RadarCatalogSeedRecords:
    radars: tuple[RadarRecord, ...]
    definitions: tuple[RadarDefinitionRecord, ...]


def records_from_catalog_payload(catalog: dict[str, Any]) -> RadarCatalogSeedRecords:
    artifact_version = str(catalog.get("artifact_version", "unknown"))
    radars: list[RadarRecord] = []
    definitions: list[RadarDefinitionRecord] = []

    for item in catalog.get("radars", []):
        radar_id = str(item["radar_id"])
        definition_payload = dict(item["definition"])
        radars.append(
            RadarRecord(
                radar_id=radar_id,
                name=str(item["name"]),
                status=str(item["status"]),
                owner=str(item["owner"]),
                profile=dict(item.get("profile", {})),
                summary=dict(item.get("summary", {})),
                artifact_path=item.get("artifact_path"),
            )
        )
        definitions.append(
            RadarDefinitionRecord(
                definition_id=str(definition_payload["definition_id"]),
                radar_id=radar_id,
                definition_payload=definition_payload,
                definition_version=artifact_version,
                is_active=True,
            )
        )

    return RadarCatalogSeedRecords(radars=tuple(radars), definitions=tuple(definitions))
