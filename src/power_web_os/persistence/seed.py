"""Deterministic Radar catalog seed helpers.

Seeding persists configured Radar definitions only. It does not run live
searches, create candidates, or create Radar run records.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from power_web_os.application.radar.configuration.catalog_seed import records_from_catalog_payload
from power_web_os.persistence.repositories import SqlAlchemyRadarDefinitionRepository, SqlAlchemyRadarRepository


@dataclass(frozen=True, slots=True)
class RadarCatalogSeedResult:
    radar_count: int
    definition_count: int

    def to_payload(self) -> dict[str, Any]:
        return {
            "artifact_type": "radar_catalog_seed_result",
            "radar_count": self.radar_count,
            "definition_count": self.definition_count,
        }


def seed_radar_catalog(session: Session, catalog_payload: dict[str, Any]) -> RadarCatalogSeedResult:
    seed_records = records_from_catalog_payload(catalog_payload)
    radar_repository = SqlAlchemyRadarRepository(session)
    definition_repository = SqlAlchemyRadarDefinitionRepository(session)

    for radar in seed_records.radars:
        radar_repository.upsert(radar)
    for definition in seed_records.definitions:
        definition_repository.upsert(definition)

    return RadarCatalogSeedResult(
        radar_count=len(seed_records.radars),
        definition_count=len(seed_records.definitions),
    )
