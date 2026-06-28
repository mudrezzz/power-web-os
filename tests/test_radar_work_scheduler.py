from __future__ import annotations

from power_web_os.application.live_radar_contracts import RadarExecutionTask
from power_web_os.application.live_radar_external_budget import RadarExternalCallBudget, RadarExternalCallBudgetSettings
from power_web_os.application.radar_search_expansion_models import RadarSearchExpansionVariant
from power_web_os.application.radar_search_expansion_scheduler import schedule_guaranteed_expansion_variants
from power_web_os.application.radar_work_scheduler import RadarWorkScheduler, merge_work_scheduler_metadata


def test_scheduler_reserves_openrouter_total_capacity_for_recall_expansion() -> None:
    budget = RadarExternalCallBudget(
        RadarExternalCallBudgetSettings(
            max_openrouter_calls_per_run=3,
            max_openrouter_web_task_calls_per_run=3,
            max_recall_expansion_openrouter_calls_per_run=2,
        )
    )
    scheduler = RadarWorkScheduler()

    metadata = scheduler.configure_run_admission(
        radar={
            "task_context": {
                "benchmark_profile": "benchmark_smoke",
                "benchmark_target_probe_minimums": {
                    "holding_or_group_target": 1,
                    "production_site_or_branch_target": 1,
                },
            }
        },
        external_budget=budget,
    )

    first_regular, _ = budget.reserve_openrouter_http_call(role="web_task", task_id="regular-1")
    blocked_regular, _ = budget.reserve_openrouter_http_call(role="web_task", task_id="regular-2")
    budget.protect_recall_expansion_openrouter_task(task_id="expansion-1", reserve_key="recall_expansion")
    protected, protected_role = budget.reserve_openrouter_http_call(role="web_task", task_id="expansion-1")

    assert metadata["work_scheduler_plan"]["protected_capacity"]["openrouter_recall_expansion"] == 2
    assert first_regular.accepted
    assert not blocked_regular.accepted
    assert blocked_regular.reason == "work_admission_reserved_capacity"
    assert protected.accepted
    assert protected_role.kind == "openrouter_recall_expansion"
    assert budget.counts["openrouter:run"] == 2


def test_scheduler_admits_guaranteed_lanes_before_optional_expansion_work() -> None:
    budget = RadarExternalCallBudget(
        RadarExternalCallBudgetSettings(
            max_openrouter_calls_per_run=8,
            max_openrouter_web_task_calls_per_run=8,
            max_recall_expansion_openrouter_calls_per_run=5,
            budget_reserve_limits={
                "official_coverage_probe": 3,
                "production_site_coverage_probe": 2,
            },
        )
    )
    variants = [
        _variant("holding-1", "holding_or_group_target", "official_coverage_probe"),
        _variant("legal-1", "known_subsidiary_or_legal_entity_target", "official_coverage_probe"),
        _variant("site-1", "production_site_or_branch_target", "production_site_coverage_probe"),
        _variant("optional-1", "alias_or_language_variant_target", "official_coverage_probe"),
    ]
    schedule = schedule_guaranteed_expansion_variants(
        variants=variants,
        targets=[_target(item) for item in variants],
        minimums={
            "holding_or_group_target": 1,
            "known_subsidiary_or_legal_entity_target": 1,
            "production_site_or_branch_target": 1,
        },
    )

    portfolio = RadarWorkScheduler().build_recall_expansion_portfolio(
        tasks=[_task(index) for index, _ in enumerate(schedule.scheduled_variants, start=1)],
        scheduled_variants=list(schedule.scheduled_variants),
        external_budget=budget,
    )

    assert portfolio.ledger.accepted_count == 4
    assert [item.scheduled_variant.schedule_role for item in portfolio.accepted_items[:3] if item.scheduled_variant] == [
        "guaranteed",
        "guaranteed",
        "guaranteed",
    ]
    assert portfolio.to_metadata()["work_lane_summary"]["recall_expansion_production_site_branch"]["accepted"] == 1
    assert budget.reserve_counts["budget_reserve:production_site_coverage_probe"] == 1


def test_scheduler_rejects_work_before_provider_execution_when_lane_reserve_is_exhausted() -> None:
    budget = RadarExternalCallBudget(
        RadarExternalCallBudgetSettings(
            max_openrouter_calls_per_run=8,
            max_openrouter_web_task_calls_per_run=8,
            max_recall_expansion_openrouter_calls_per_run=5,
            budget_reserve_limits={"production_site_coverage_probe": 0},
        )
    )
    variant = _variant("site-1", "production_site_or_branch_target", "production_site_coverage_probe")
    schedule = schedule_guaranteed_expansion_variants(
        variants=[variant],
        targets=[_target(variant)],
        minimums={"production_site_or_branch_target": 1},
    )

    portfolio = RadarWorkScheduler().build_recall_expansion_portfolio(
        tasks=[_task(1)],
        scheduled_variants=list(schedule.scheduled_variants),
        external_budget=budget,
    )

    assert portfolio.ledger.accepted_count == 0
    assert portfolio.ledger.rejected_count == 1
    decision = portfolio.ledger.decisions[0]
    assert decision.reason == "budget_reserve_exhausted"
    assert decision.schedule_role == "guaranteed"
    assert portfolio.to_metadata()["work_guarantee_failures"][0]["target_type"] == "production_site_or_branch_target"


def test_scheduler_metadata_merges_multiple_portfolios() -> None:
    first = {
        "work_scheduler_plan": {"work_item_count": 1, "protected_capacity": {"first": 1}},
        "work_admission_decisions": [
            {"work_id": "w1", "lane": "recall_expansion_holding_group", "accepted": True},
        ],
        "work_scheduler_ledger": {"accepted_count": 1, "rejected_count": 0},
        "work_lane_summary": {"recall_expansion_holding_group": {"planned": 1, "accepted": 1, "rejected": 0}},
        "work_execution_order": [{"work_id": "w1"}],
    }
    second = {
        "work_scheduler_plan": {"work_item_count": 1, "protected_capacity": {"second": 2}},
        "work_admission_decisions": [
            {"work_id": "w2", "lane": "recall_expansion_production_site_branch", "accepted": False},
        ],
        "work_scheduler_ledger": {"accepted_count": 0, "rejected_count": 1},
        "work_lane_summary": {
            "recall_expansion_production_site_branch": {"planned": 1, "accepted": 0, "rejected": 1}
        },
        "rejected_work_items": [{"work_id": "w2"}],
        "work_guarantee_failures": [{"work_id": "w2", "reason": "server_tool_budget_limited"}],
    }

    merged = merge_work_scheduler_metadata(first, second)

    assert merged["work_scheduler_plan"]["work_item_count"] == 2
    assert merged["work_scheduler_ledger"]["accepted_count"] == 1
    assert merged["work_scheduler_ledger"]["rejected_count"] == 1
    assert len(merged["work_admission_decisions"]) == 2
    assert len(merged["work_execution_order"]) == 1
    assert len(merged["rejected_work_items"]) == 1
    assert len(merged["work_guarantee_failures"]) == 1
    assert merged["work_lane_summary"]["recall_expansion_holding_group"]["accepted"] == 1
    assert merged["work_lane_summary"]["recall_expansion_production_site_branch"]["rejected"] == 1


def _variant(target_id: str, target_type: str, reserve_key: str) -> RadarSearchExpansionVariant:
    return RadarSearchExpansionVariant(
        query=f"{target_id} SIBUR",
        source_ids=["openrouter_web"],
        source_scope="configured",
        reason="benchmark_target_probe",
        target_id=target_id,
        target_type=target_type,
        budget_reserve_key=reserve_key,
    )


def _target(variant: RadarSearchExpansionVariant) -> dict[str, str]:
    return {
        "target_id": variant.target_id,
        "target_label": variant.query,
        "target_type": variant.target_type,
        "budget_reserve_key": variant.budget_reserve_key,
    }


def _task(index: int) -> RadarExecutionTask:
    return RadarExecutionTask(
        task_id=f"expansion-{index}",
        stage="coverage_check",
        subject_type="qualification",
        subject_id="q1",
        query=f"expansion query {index}",
        purpose="Recall expansion.",
        source_ids=["openrouter_web"],
    )
