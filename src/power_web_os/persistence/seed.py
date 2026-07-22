"""Deterministic Radar catalog and product-safe demo evidence seed helpers.

Seeding never executes a pipeline or provider. Fixed completed fixture records
exist only so the handoff UI can be exercised on an empty local database.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from power_web_os.application.radar.configuration.catalog_seed import records_from_catalog_payload
from power_web_os.application.radar.lifecycle.records import (
    RadarRunOutputRecord,
    RadarRunRecord,
    RadarRunStatus,
    SignalMonitoringRunOutputRecord,
)
from power_web_os.application.radar.power_web_discovery.handoff import next_policy_version
from power_web_os.persistence.repositories import (
    SqlAlchemyRadarDefinitionRepository,
    SqlAlchemyRadarRepository,
    SqlAlchemyRadarRunOutputRepository,
    SqlAlchemyRadarRunRepository,
)
from power_web_os.persistence.signal_monitoring_repositories import SqlAlchemySignalMonitoringRunOutputRepository
from power_web_os.application.sales_playbook.seed import (
    INDUSTRIAL_ENERGY_OPTIMIZATION_PRODUCT_ID,
    SMARTDIAGNOSTICS_PRODUCT_ID,
    seed_industrial_energy_optimization,
    seed_smartdiagnostics,
)
from power_web_os.application.sales_playbook.service import SalesPlaybookService
from power_web_os.persistence.power_web_handoff_repositories import SqlAlchemyRadarPowerWebPolicyRepository
from power_web_os.persistence.sales_playbook_repositories import SqlAlchemySalesPlaybookRepository


@dataclass(frozen=True, slots=True)
class RadarCatalogSeedResult:
    radar_count: int
    definition_count: int
    product_count: int = 0
    fixture_run_count: int = 0

    def to_payload(self) -> dict[str, Any]:
        return {
            "artifact_type": "radar_catalog_seed_result",
            "radar_count": self.radar_count,
            "definition_count": self.definition_count,
            "product_count": self.product_count,
            "fixture_run_count": self.fixture_run_count,
        }


def seed_radar_catalog(session: Session, catalog_payload: dict[str, Any]) -> RadarCatalogSeedResult:
    seed_records = records_from_catalog_payload(catalog_payload)
    radar_repository = SqlAlchemyRadarRepository(session)
    definition_repository = SqlAlchemyRadarDefinitionRepository(session)

    for radar in seed_records.radars:
        radar_repository.upsert(radar)
    for definition in seed_records.definitions:
        definition_repository.upsert(definition)

    playbook_service = SalesPlaybookService(SqlAlchemySalesPlaybookRepository(session))
    seed_smartdiagnostics(playbook_service)
    seed_industrial_energy_optimization(playbook_service)
    policy_repository = SqlAlchemyRadarPowerWebPolicyRepository(session)
    if policy_repository.get_active("benchmark-sibur-holding-contour") is None:
        policy_repository.save(next_policy_version(
            radar_id="benchmark-sibur-holding-contour",
            product_ids=(SMARTDIAGNOSTICS_PRODUCT_ID, INDUSTRIAL_ENERGY_OPTIMIZATION_PRODUCT_ID),
            created_by="demo-seed",
            previous=None,
        ))
    _seed_power_web_handoff_fixture(session)
    return RadarCatalogSeedResult(
        radar_count=len(seed_records.radars),
        definition_count=len(seed_records.definitions),
        product_count=2,
        fixture_run_count=2,
    )


def _seed_power_web_handoff_fixture(session: Session) -> None:
    radar_id = "benchmark-sibur-holding-contour"
    candidate_run_id = "radar-run-fixture-power-web-handoff"
    signal_run_id = "signal-run-fixture-power-web-handoff"
    accepted = _fixture_candidate(
        candidate_id="ao-sibur-him-prom-demo",
        legal_name='АО "СИБУР-Химпром"',
        inn="5905001527",
        evidence_ref="power-web-fixture-source-accepted",
        accepted=True,
    )
    review = _fixture_candidate(
        candidate_id="ao-permskie-poliefiry-demo",
        legal_name='АО "Пермские полиэфиры"',
        inn="5903005921",
        evidence_ref="power-web-fixture-source-review",
        accepted=False,
    )
    candidates = [accepted, review]
    sources = [
        {
            "evidence_ref": "power-web-fixture-source-accepted",
            "title": "Public company profile",
            "url": "https://www.sibur.ru/",
            "snippet": "Product-safe demo provenance for the accepted candidate.",
            "source_type": "official_company",
        },
        {
            "evidence_ref": "power-web-fixture-source-review",
            "title": "Public registry profile",
            "url": "https://egrul.nalog.ru/",
            "snippet": "Product-safe demo provenance for the review-needed candidate.",
            "source_type": "registry",
        },
    ]
    completed_at = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    runs = SqlAlchemyRadarRunRepository(session)
    if runs.get(candidate_run_id) is None:
        runs.create(RadarRunRecord(
            run_id=candidate_run_id,
            radar_id=radar_id,
            pipeline_id="candidate_discovery",
            queued_at=completed_at,
            run_metadata={"run_profile": "fixture_import", "requester": "demo-seed"},
        ))
        runs.update_status(candidate_run_id, RadarRunStatus.COMPLETED, completed_at=completed_at)
    SqlAlchemyRadarRunOutputRepository(session).upsert(RadarRunOutputRecord(
        run_id=candidate_run_id,
        artifact_version="power_web_handoff_fixture.v1",
        radar_payload={"radar_id": radar_id},
        search_plan_payload={"mode": "fixture_import", "provider_calls": 0},
        sources_payload=sources,
        candidates_payload=candidates,
        artifact_payload={
            "artifact_type": "icp_radar_live_run",
            "radar": {"radar_id": radar_id},
            "run_metadata": {
                "task_id": candidate_run_id,
                "run_at": completed_at.isoformat(),
                "execution_results": {
                    "user_visible_candidates": candidates,
                    "candidate_universe": [
                        {"candidate_id": item["candidate_id"], "legal_name": item["legal_name"], "status": "qualified", "source_refs": item["evidence_refs"]}
                        for item in candidates
                    ],
                },
            },
            "sources": sources,
            "candidates": candidates,
            "contract_validation": [],
        },
    ))
    if runs.get(signal_run_id) is None:
        runs.create(RadarRunRecord(
            run_id=signal_run_id,
            radar_id=radar_id,
            pipeline_id="signal_monitoring",
            source_run_id=candidate_run_id,
            queued_at=completed_at,
            run_metadata={"run_profile": "fixture_import", "provider_calls": 0},
        ))
        runs.update_status(signal_run_id, RadarRunStatus.COMPLETED, completed_at=completed_at)
    observation = {
        "candidate_id": accepted["candidate_id"],
        "signal_code": "S1",
        "observation_status": "unclear",
        "search_status": "review_needed_date_unknown",
        "temporal_status": "review_needed_date_unknown",
        "evidence_refs": [accepted["evidence_refs"][0]],
        "summary": "Relevant product-safe demo evidence requires date review.",
    }
    SqlAlchemySignalMonitoringRunOutputRepository(session).upsert(SignalMonitoringRunOutputRecord(
        run_id=signal_run_id,
        source_run_id=candidate_run_id,
        artifact_version="signal_monitoring.v2",
        input_snapshot_payload={"candidates": [{"candidate_id": item["candidate_id"]} for item in candidates]},
        plan_payload={"mode": "fixture_import", "provider_calls": 0},
        observations_payload=[observation],
        artifact_payload={
            "artifact_type": "radar_signal_monitoring_report",
            "artifact_version": "signal_monitoring.v2",
            "pipeline_id": "signal_monitoring",
            "run_id": signal_run_id,
            "source_candidate_run_id": candidate_run_id,
            "candidate_scope": [{"candidate_id": item["candidate_id"]} for item in candidates],
            "observations": [observation],
            "budgets": {"settings": {}, "counters": {"provider_calls": 0}, "exhaustion_events": []},
        },
    ))


def _fixture_candidate(*, candidate_id: str, legal_name: str, inn: str, evidence_ref: str, accepted: bool):
    return {
        "candidate_id": candidate_id,
        "legal_name": legal_name,
        "description": "Product-safe deterministic Power Web handoff fixture.",
        "entity_type": "legal_entity",
        "inn": inn,
        "score": {"fit_score": 2 if accepted else 0, "intent_score": 0, "tier": "Review"},
        "qualification": [],
        "signals": [],
        "review_flags": [] if accepted else ["review_needed_upstream_lead"],
        "evidence_refs": [evidence_ref],
        "upstream_source_refs": [evidence_ref],
        "candidate_surface_status": "accepted_product_candidate" if accepted else "review_needed_candidate",
        "product_acceptance_status": "product_candidate" if accepted else "review_required",
        "upstream_discovery_outcome": "qualified" if accepted else "review_needed_upstream_lead",
        "upstream_confidence": "high" if accepted else "review_required",
        "candidate_surface_reason": "Evidence-complete deterministic demo fixture.",
    }
