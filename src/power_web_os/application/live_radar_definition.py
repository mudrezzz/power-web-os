"""Deterministic live mini Radar definition and search plan builders."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from power_web_os.application.radar.candidate_discovery.contracts import RadarSearchPlan
from power_web_os.application.radar.candidate_discovery.planning.execution_plan import compile_radar_execution_plan, execution_plan_to_search_plan

def build_live_mini_radar_definition() -> dict[str, Any]:
    return {
        "radar_id": "toir-quick-live",
        "name": "ТОиР Quick Live Radar",
        "description": "Мини-радар для живого поиска производственных активов СИБУР с сигналами по ТОиР, модернизации и цифровизации.",
        "qualification_criteria": [
            {
                "code": "Q1",
                "label": "Компания входит в группу СИБУР",
                "rule": "Найти подтверждение, что юридическое лицо или площадка относится к группе СИБУР.",
                "operator": "AND",
                "requirement_level": "required",
                "cross_validation_required": False,
            },
            {
                "code": "Q2",
                "label": "Промышленный или нефтехимический производственный актив",
                "rule": "Найти признаки промышленного, нефтехимического или производственного актива, а не только сервисной структуры.",
                "operator": "AND",
                "requirement_level": "required",
                "cross_validation_required": False,
            },
        ],
        "intent_signals": [
            {
                "code": "S1",
                "label": "ТОиР / ремонты / надежность",
                "rule": "Есть упоминание ремонтов, надежности, ТОиР, межремонтного интервала или maintenance-повестки.",
            },
            {
                "code": "S2",
                "label": "Модернизация оборудования / инвестиции / рост мощности",
                "rule": "Есть упоминание модернизации оборудования, инвестиций, расширения или роста мощности.",
            },
            {
                "code": "S3",
                "label": "Цифровизация производства / диагностика / предиктивная аналитика",
                "rule": "Есть упоминание цифровизации производства, диагностики, датчиков, предиктивной аналитики или автоматизации.",
            },
        ],
        "source_policy": {
            "preferred_domains": ["sibur.ru"],
            "allow_open_web": True,
            "human_review_required": True,
        },
    }


def build_live_mini_radar_search_plan(radar: dict[str, Any] | None = None) -> RadarSearchPlan:
    radar_payload = radar or build_live_mini_radar_definition()
    return execution_plan_to_search_plan(compile_radar_execution_plan(radar_payload))


def build_live_mini_radar_search_plan_artifact() -> dict[str, Any]:
    radar = build_live_mini_radar_definition()
    plan = build_live_mini_radar_search_plan(radar)
    return {
        "artifact_type": "icp_radar_live_search_plan",
        "artifact_version": "0.6.3.4",
        "radar": radar,
        "search_plan": plan.model_dump(),
        "workflow_metadata": {
            "workflow_name": "LiveICPRadarRunWorkflow",
            "runtime": "dry_run_plan",
            "created_at": _now_iso(),
        },
    }


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()
