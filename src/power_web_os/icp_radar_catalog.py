from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from power_web_os.icp_radar import RadarDefinition, SignalCriterion, radar_definition_to_payload


@dataclass(frozen=True, slots=True)
class ICPRadarCatalogItem:
    radar_id: str
    name: str
    status: str
    owner: str
    profile: dict[str, Any]
    summary: dict[str, Any]
    definition: RadarDefinition
    artifact_path: str | None


@dataclass(frozen=True, slots=True)
class ICPRadarCatalogArtifact:
    radars: tuple[ICPRadarCatalogItem, ...]
    workflow_metadata: dict[str, Any]


def build_icp_radar_catalog(active_radar_payload: dict[str, Any]) -> dict[str, Any]:
    active_definition = active_radar_payload["radar"]["definition"]
    active_criteria = tuple(
        SignalCriterion(
            code=item["code"],
            name=item["name"],
            description=item["description"],
            scoring_guidance=item["scoring_guidance"],
        )
        for item in active_definition["criteria"]
    )
    active_definition_model = _definition_from_payload(active_definition, criteria=active_criteria)
    active_candidates = active_radar_payload.get("candidates", [])
    radars = (
        ICPRadarCatalogItem(
            radar_id="toir-sibur",
            name="ТОиР / SIBUR",
            status="active",
            owner="ABM Research",
            profile={
                "icp_profile": active_radar_payload["radar"]["profile"]["name"],
                "product": active_definition_model.product,
                "segment": active_definition_model.segment,
                "scope": active_definition_model.market_scope,
            },
            summary={
                "cadence": active_definition_model.cadence,
                "last_run": "2026-06-11",
                "candidate_count": len(active_candidates),
                "needs_review_count": len(active_candidates),
                "accepted_count": 0,
                "run_mode": active_definition_model.run_mode,
            },
            definition=active_definition_model,
            artifact_path="/demo/icp_radar.json",
        ),
        ICPRadarCatalogItem(
            radar_id="mining-toir",
            name="ТОиР / Горнодобыча",
            status="configured",
            owner="Industrial ABM",
            profile={
                "icp_profile": "ТОиР для горнодобывающих активов",
                "product": "Автоматизация ремонтов и надежности",
                "segment": "Горнодобывающие предприятия",
                "scope": "Крупные производственные площадки с карьерной, обогатительной или транспортной инфраструктурой.",
            },
            summary={
                "cadence": "monthly",
                "last_run": "not_run",
                "candidate_count": 0,
                "needs_review_count": 0,
                "accepted_count": 0,
                "run_mode": "configured_not_generated",
            },
            definition=_planned_definition(
                definition_id="radar-def-mining-toir",
                product="Автоматизация ремонтов и надежности",
                segment="Горнодобывающие предприятия",
                holding="Рынок РФ / горнодобыча",
                market_scope="Юрлица с производственными активами, тяжелым оборудованием и публичными сигналами по ремонтам.",
                criteria=(
                    ("C1", "ТОиР / EAM", "Упоминание ремонтов, надежности, EAM или планирования ТОиР"),
                    ("C2", "Тяжелое оборудование", "Парк карьерной, дробильной, конвейерной или энергетической техники"),
                    ("C3", "Простои и надежность", "Сигналы о снижении простоев, OEE или повышении надежности"),
                    ("C4", "Цифровизация производства", "Программы цифровизации промышленных процессов"),
                    ("C5", "Закупочная активность", "Тендеры или закупки по диагностике, ремонтам, датчикам или аналитике"),
                ),
            ),
            artifact_path=None,
        ),
        ICPRadarCatalogItem(
            radar_id="retail-energy-efficiency",
            name="Энергоэффективность / Ритейл",
            status="planned",
            owner="Growth Team",
            profile={
                "icp_profile": "Энергоэффективность распределенной сети",
                "product": "Энергомониторинг и управление объектами",
                "segment": "Федеральный ритейл и склады",
                "scope": "Компании с распределенной сетью магазинов, складов или холодильной инфраструктуры.",
            },
            summary={
                "cadence": "weekly",
                "last_run": "not_scheduled",
                "candidate_count": 0,
                "needs_review_count": 0,
                "accepted_count": 0,
                "run_mode": "planned",
            },
            definition=_planned_definition(
                definition_id="radar-def-retail-energy",
                product="Энергомониторинг и управление объектами",
                segment="Федеральный ритейл и склады",
                holding="Рынок РФ / ритейл",
                market_scope="Операторы сетей с большим количеством объектов и затратами на энергоресурсы.",
                criteria=(
                    ("C1", "Распределенная сеть", "Большое число торговых, складских или холодильных объектов"),
                    ("C2", "Энергозатраты", "Публичные сигналы об оптимизации энергопотребления"),
                    ("C3", "ESG / устойчивость", "Заявленные программы устойчивого развития или снижения выбросов"),
                    ("C4", "IoT / диспетчеризация", "Интерес к удаленному мониторингу инженерной инфраструктуры"),
                    ("C5", "Бюджетный триггер", "Открытые закупки или проекты по энергоэффективности"),
                ),
            ),
            artifact_path=None,
        ),
    )
    return icp_radar_catalog_to_payload(
        ICPRadarCatalogArtifact(
            radars=radars,
            workflow_metadata={
                "workflow_name": "ICPRadarCatalog",
                "artifact_version": "0.6.2.5",
                "active_fixture_radar_id": "toir-sibur",
                "radar_count": len(radars),
            },
        )
    )


def icp_radar_catalog_to_payload(artifact: ICPRadarCatalogArtifact) -> dict[str, Any]:
    return {
        "artifact_type": "icp_radar_catalog",
        "artifact_version": "0.6.2.5",
        "radars": [catalog_item_to_payload(item) for item in artifact.radars],
        "workflow_metadata": artifact.workflow_metadata,
    }


def catalog_item_to_payload(item: ICPRadarCatalogItem) -> dict[str, Any]:
    return {
        "radar_id": item.radar_id,
        "name": item.name,
        "status": item.status,
        "owner": item.owner,
        "profile": item.profile,
        "summary": item.summary,
        "definition": radar_definition_to_payload(item.definition),
        "artifact_path": item.artifact_path,
    }


def _definition_from_payload(payload: dict[str, Any], *, criteria: tuple[SignalCriterion, ...]) -> RadarDefinition:
    return RadarDefinition(
        definition_id=payload["definition_id"],
        product=payload["product"],
        segment=payload["segment"],
        holding=payload["holding"],
        market_scope=payload["market_scope"],
        exclusions=tuple(payload["exclusions"]),
        assumptions=tuple(payload["assumptions"]),
        legal_entity_source=payload["legal_entity_source"],
        discovery_mode=payload["discovery_mode"],
        discovery_filters=tuple(payload["discovery_filters"]),
        monitoring_sources=tuple(payload["monitoring_sources"]),
        cadence=payload["cadence"],
        lookback_window=payload["lookback_window"],
        run_mode=payload["run_mode"],
        scoring_formula=dict(payload["scoring_formula"]),
        tier_thresholds=dict(payload["tier_thresholds"]),
        criteria=criteria,
        limitations=tuple(payload["limitations"]),
    )


def _planned_definition(
    *,
    definition_id: str,
    product: str,
    segment: str,
    holding: str,
    market_scope: str,
    criteria: tuple[tuple[str, str, str], ...],
) -> RadarDefinition:
    return RadarDefinition(
        definition_id=definition_id,
        product=product,
        segment=segment,
        holding=holding,
        market_scope=market_scope,
        exclusions=("Компании без публично наблюдаемых сигналов", "Малые объекты без enterprise-повестки"),
        assumptions=("Радар настроен как демонстрационный пример без generated shortlist.",),
        legal_entity_source="Manual ICP seed list",
        discovery_mode="configured_seed",
        discovery_filters=("Enterprise сегмент", "Публичные источники доступны", "Решение может приниматься на уровне юрлица"),
        monitoring_sources=("procurement", "company_site", "news", "hiring"),
        cadence="monthly",
        lookback_window="90 days",
        run_mode="configured_not_generated",
        scoring_formula={
            "fit_score": "profile criteria sum",
            "intent_score": "intent criteria sum",
            "trigger_score": "trigger criteria sum",
            "total_score": "fit + intent + trigger",
        },
        tier_thresholds={
            "Tier 1": ">=38",
            "Tier 2": ">=25",
            "Tier 3": ">=15",
            "Monitor": "<15",
        },
        criteria=tuple(
            SignalCriterion(
                code=code,
                name=name,
                description=description,
                scoring_guidance="0 = не наблюдается, 1 = слабый сигнал, 2 = средний сигнал, 3 = сильный сигнал",
            )
            for code, name, description in criteria
        ),
        limitations=(
            "Read-only configured example in Slice 0.6.2.5",
            "Candidate generation, live connectors, and schedule execution are not enabled yet",
            "Editable radar configuration is planned for Slice 0.6.5",
        ),
    )
