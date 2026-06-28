"""Central work admission for bounded Radar execution.

The scheduler owns ordering and admission decisions for application-approved
work lanes. It does not execute provider calls; execution remains in staged
Radar helpers and integration adapters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from power_web_os.application.live_radar_contracts import RadarExecutionTask
from power_web_os.application.live_radar_external_budget import RadarExternalCallBudget, RadarExternalCallBudgetDecision
from power_web_os.application.radar_search_expansion_scheduler import RadarScheduledExpansionVariant


@dataclass(frozen=True, slots=True)
class RadarWorkCostEstimate:
    semantic_task_units: int = 1
    openrouter_calls: int = 1
    reserve_key: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "semantic_task_units": self.semantic_task_units,
            "openrouter_calls": self.openrouter_calls,
            "reserve_key": self.reserve_key,
        }


@dataclass(frozen=True, slots=True)
class RadarWorkItem:
    work_id: str
    task_id: str
    lane: str
    priority: int
    task: RadarExecutionTask
    scheduled_variant: RadarScheduledExpansionVariant | None = None
    cost: RadarWorkCostEstimate = field(default_factory=RadarWorkCostEstimate)
    optional: bool = False

    def to_payload(self) -> dict[str, Any]:
        variant_payload: dict[str, Any] = {}
        if self.scheduled_variant is not None:
            variant_payload = self.scheduled_variant.to_payload()
        return {
            "work_id": self.work_id,
            "task_id": self.task_id,
            "lane": self.lane,
            "priority": self.priority,
            "optional": self.optional,
            "source_ids": list(self.task.source_ids),
            "source_scope": self.task.source_scope,
            "query": self.task.query,
            "target_id": variant_payload.get("target_id", ""),
            "target_type": variant_payload.get("target_type", ""),
            "budget_reserve_key": self.cost.reserve_key,
            "schedule_role": variant_payload.get("schedule_role", ""),
            "cost": self.cost.to_payload(),
        }


@dataclass(frozen=True, slots=True)
class RadarWorkAdmissionDecision:
    work_id: str
    task_id: str
    lane: str
    accepted: bool
    reason: str = ""
    message: str = ""
    budget_decision: dict[str, Any] = field(default_factory=dict)
    schedule_role: str = ""
    target_id: str = ""
    target_type: str = ""
    reserve_key: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "work_id": self.work_id,
            "task_id": self.task_id,
            "lane": self.lane,
            "accepted": self.accepted,
            "reason": self.reason,
            "message": self.message,
            "budget_decision": dict(self.budget_decision),
            "schedule_role": self.schedule_role,
            "target_id": self.target_id,
            "target_type": self.target_type,
            "reserve_key": self.reserve_key,
        }


@dataclass(frozen=True, slots=True)
class RadarWorkLedger:
    decisions: list[RadarWorkAdmissionDecision] = field(default_factory=list)

    @property
    def accepted_count(self) -> int:
        return sum(1 for item in self.decisions if item.accepted)

    @property
    def rejected_count(self) -> int:
        return sum(1 for item in self.decisions if not item.accepted)

    def to_payload(self) -> dict[str, Any]:
        return {
            "accepted_count": self.accepted_count,
            "rejected_count": self.rejected_count,
            "decisions_by_lane": _count_by_lane(self.decisions),
        }


@dataclass(frozen=True, slots=True)
class RadarWorkPortfolio:
    work_items: list[RadarWorkItem] = field(default_factory=list)
    ledger: RadarWorkLedger = field(default_factory=RadarWorkLedger)
    protected_capacity: dict[str, Any] = field(default_factory=dict)

    @property
    def accepted_items(self) -> list[RadarWorkItem]:
        accepted = {decision.work_id for decision in self.ledger.decisions if decision.accepted}
        return [item for item in self.work_items if item.work_id in accepted]

    @property
    def rejected_items(self) -> list[RadarWorkItem]:
        rejected = {decision.work_id for decision in self.ledger.decisions if not decision.accepted}
        return [item for item in self.work_items if item.work_id in rejected]

    def decision_for(self, work_id: str) -> RadarWorkAdmissionDecision | None:
        for decision in self.ledger.decisions:
            if decision.work_id == work_id:
                return decision
        return None

    def to_metadata(self) -> dict[str, Any]:
        decisions = [item.to_payload() for item in self.ledger.decisions]
        return {
            "work_scheduler_plan": {
                "work_item_count": len(self.work_items),
                "protected_capacity": dict(self.protected_capacity),
            },
            "work_scheduler_ledger": self.ledger.to_payload(),
            "work_admission_decisions": decisions,
            "work_lane_summary": _lane_summary(self.work_items, self.ledger.decisions),
            "work_execution_order": [
                item.to_payload() for item in self.accepted_items
            ],
            "rejected_work_items": [
                {
                    **item.to_payload(),
                    "admission_decision": (self.decision_for(item.work_id).to_payload() if self.decision_for(item.work_id) else {}),
                }
                for item in self.rejected_items
            ],
            "deferred_work_items": [],
            "work_guarantee_failures": _guarantee_failures(self.ledger.decisions),
        }


class RadarWorkScheduler:
    """Admit Radar work before local executors can spend shared budgets."""

    def configure_run_admission(
        self,
        *,
        radar: dict[str, Any],
        external_budget: RadarExternalCallBudget,
    ) -> dict[str, Any]:
        task_context = radar.get("task_context") if isinstance(radar.get("task_context"), dict) else {}
        minimums = _positive_int_dict(task_context.get("benchmark_target_probe_minimums"))
        if not minimums or not task_context.get("benchmark_profile"):
            return {"work_scheduler_plan": {"protected_capacity": {}}}
        required_expansion_calls = sum(minimums.values())
        recall_limit = _positive(external_budget.settings.max_recall_expansion_openrouter_calls_per_run)
        total_limit = _positive(external_budget.settings.max_openrouter_calls_per_run)
        reserve_units = required_expansion_calls
        if recall_limit is not None:
            reserve_units = min(reserve_units, recall_limit)
        if total_limit is not None:
            reserve_units = min(reserve_units, total_limit)
        external_budget.configure_openrouter_total_reserve(
            lane="recall_expansion",
            units=reserve_units,
            reason="benchmark_target_probe_minimums",
        )
        return {
            "work_scheduler_plan": {
                "protected_capacity": {
                    "openrouter_recall_expansion": reserve_units,
                    "minimums": minimums,
                    "reason": "benchmark_target_probe_minimums",
                }
            }
        }

    def build_recall_expansion_portfolio(
        self,
        *,
        tasks: list[RadarExecutionTask],
        scheduled_variants: list[RadarScheduledExpansionVariant],
        external_budget: RadarExternalCallBudget | None,
    ) -> RadarWorkPortfolio:
        work_items = [
            _work_item_for(task=task, scheduled_variant=scheduled_variant, priority=index)
            for index, (task, scheduled_variant) in enumerate(zip(tasks, scheduled_variants), start=1)
        ]
        decisions: list[RadarWorkAdmissionDecision] = []
        for item in work_items:
            decision = self._admit_recall_expansion_item(item=item, external_budget=external_budget)
            decisions.append(decision)
        protected = {}
        if external_budget is not None:
            protected = external_budget.openrouter_total_reservation_metadata()
        return RadarWorkPortfolio(
            work_items=work_items,
            ledger=RadarWorkLedger(decisions=decisions),
            protected_capacity=protected,
        )

    def _admit_recall_expansion_item(
        self,
        *,
        item: RadarWorkItem,
        external_budget: RadarExternalCallBudget | None,
    ) -> RadarWorkAdmissionDecision:
        variant = item.scheduled_variant.variant if item.scheduled_variant is not None else None
        if external_budget is None:
            return _accepted(item, RadarExternalCallBudgetDecision(accepted=True, kind="none", key="none"))
        preflight = external_budget.check_recall_expansion_openrouter_capacity(task_id=item.task_id)
        if not preflight.accepted:
            return _rejected(item, preflight, reason=_reason_from_budget(preflight))
        reserve = external_budget.reserve_budget_slice(item.cost.reserve_key, task_id=item.task_id, reason=variant.reason if variant else "")
        if not reserve.accepted:
            return _rejected(item, reserve, reason="budget_reserve_exhausted")
        external_budget.protect_recall_expansion_openrouter_task(task_id=item.task_id, reserve_key=item.cost.reserve_key)
        return _accepted(item, reserve)


def merge_work_scheduler_metadata(existing: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    """Append scheduler portfolio metadata without losing earlier admissions."""

    if not update:
        return dict(existing)
    merged = dict(existing)
    existing_plan = _dict(existing.get("work_scheduler_plan"))
    update_plan = _dict(update.get("work_scheduler_plan"))
    if existing_plan or update_plan:
        merged["work_scheduler_plan"] = {
            **existing_plan,
            **update_plan,
            "work_item_count": _int(existing_plan.get("work_item_count")) + _int(update_plan.get("work_item_count")),
        }
    decisions = [
        *_dict_list(existing.get("work_admission_decisions")),
        *_dict_list(update.get("work_admission_decisions")),
    ]
    merged["work_admission_decisions"] = decisions
    merged["work_scheduler_ledger"] = _ledger_payload_from_decisions(decisions)
    merged["work_lane_summary"] = _merge_lane_summaries(
        _dict(existing.get("work_lane_summary")),
        _dict(update.get("work_lane_summary")),
    )
    merged["work_execution_order"] = [
        *_dict_list(existing.get("work_execution_order")),
        *_dict_list(update.get("work_execution_order")),
    ]
    merged["rejected_work_items"] = [
        *_dict_list(existing.get("rejected_work_items")),
        *_dict_list(update.get("rejected_work_items")),
    ]
    merged["deferred_work_items"] = [
        *_dict_list(existing.get("deferred_work_items")),
        *_dict_list(update.get("deferred_work_items")),
    ]
    merged["work_guarantee_failures"] = [
        *_dict_list(existing.get("work_guarantee_failures")),
        *_dict_list(update.get("work_guarantee_failures")),
    ]
    return merged


def _work_item_for(
    *,
    task: RadarExecutionTask,
    scheduled_variant: RadarScheduledExpansionVariant,
    priority: int,
) -> RadarWorkItem:
    variant = scheduled_variant.variant
    lane = _lane_for_target_type(variant.target_type)
    return RadarWorkItem(
        work_id=f"{task.task_id}:recall-expansion:{priority}",
        task_id=task.task_id,
        lane=lane,
        priority=priority,
        task=task,
        scheduled_variant=scheduled_variant,
        cost=RadarWorkCostEstimate(reserve_key=variant.budget_reserve_key),
        optional=scheduled_variant.schedule_role != "guaranteed",
    )


def _accepted(item: RadarWorkItem, budget_decision: RadarExternalCallBudgetDecision) -> RadarWorkAdmissionDecision:
    return _decision(item, accepted=True, budget_decision=budget_decision, reason="")


def _rejected(
    item: RadarWorkItem,
    budget_decision: RadarExternalCallBudgetDecision,
    *,
    reason: str,
) -> RadarWorkAdmissionDecision:
    return _decision(
        item,
        accepted=False,
        budget_decision=budget_decision,
        reason=reason,
        message=budget_decision.message or f"Rejected {item.work_id}: {reason}.",
    )


def _decision(
    item: RadarWorkItem,
    *,
    accepted: bool,
    budget_decision: RadarExternalCallBudgetDecision,
    reason: str,
    message: str = "",
) -> RadarWorkAdmissionDecision:
    variant = item.scheduled_variant.variant if item.scheduled_variant is not None else None
    return RadarWorkAdmissionDecision(
        work_id=item.work_id,
        task_id=item.task_id,
        lane=item.lane,
        accepted=accepted,
        reason=reason,
        message=message,
        budget_decision=budget_decision.to_payload(),
        schedule_role=item.scheduled_variant.schedule_role if item.scheduled_variant else "",
        target_id=variant.target_id if variant else "",
        target_type=variant.target_type if variant else "",
        reserve_key=item.cost.reserve_key,
    )


def _lane_for_target_type(target_type: str) -> str:
    if target_type == "holding_or_group_target":
        return "recall_expansion_holding_group"
    if target_type == "production_site_or_branch_target":
        return "recall_expansion_production_site_branch"
    if target_type == "known_subsidiary_or_legal_entity_target":
        return "recall_expansion_legal_subsidiary"
    return "recall_expansion_optional"


def _reason_from_budget(decision: RadarExternalCallBudgetDecision) -> str:
    if decision.kind == "openrouter":
        return "external_total_budget_limited"
    if decision.kind == "openrouter_recall_expansion":
        return "openrouter_recall_expansion_budget_limited"
    if decision.kind == "openrouter_server_tool_web_search":
        return "server_tool_budget_limited"
    return decision.reason or "work_admission_failed"


def _positive(value: int | None) -> int | None:
    return value if value is not None and value > 0 else None


def _positive_int_dict(value: object) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, int] = {}
    for key, raw in value.items():
        try:
            parsed = int(raw)
        except (TypeError, ValueError):
            continue
        if parsed > 0:
            result[str(key)] = parsed
    return result


def _count_by_lane(decisions: list[RadarWorkAdmissionDecision]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for item in decisions:
        bucket = result.setdefault(item.lane, {"accepted": 0, "rejected": 0})
        bucket["accepted" if item.accepted else "rejected"] += 1
    return result


def _count_payload_by_lane(decisions: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for item in decisions:
        lane = str(item.get("lane") or "unknown")
        bucket = result.setdefault(lane, {"accepted": 0, "rejected": 0})
        bucket["accepted" if item.get("accepted") else "rejected"] += 1
    return result


def _lane_summary(work_items: list[RadarWorkItem], decisions: list[RadarWorkAdmissionDecision]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for item in work_items:
        bucket = result.setdefault(item.lane, {"planned": 0, "accepted": 0, "rejected": 0})
        bucket["planned"] += 1
    for decision in decisions:
        bucket = result.setdefault(decision.lane, {"planned": 0, "accepted": 0, "rejected": 0})
        bucket["accepted" if decision.accepted else "rejected"] += 1
    return result


def _merge_lane_summaries(left: dict[str, Any], right: dict[str, Any]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for source in (left, right):
        for lane, values in source.items():
            if not isinstance(values, dict):
                continue
            bucket = result.setdefault(str(lane), {"planned": 0, "accepted": 0, "rejected": 0})
            bucket["planned"] += _int(values.get("planned"))
            bucket["accepted"] += _int(values.get("accepted"))
            bucket["rejected"] += _int(values.get("rejected"))
    return result


def _guarantee_failures(decisions: list[RadarWorkAdmissionDecision]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for decision in decisions:
        if decision.accepted or decision.schedule_role != "guaranteed":
            continue
        failures.append({
            "work_id": decision.work_id,
            "task_id": decision.task_id,
            "lane": decision.lane,
            "target_id": decision.target_id,
            "target_type": decision.target_type,
            "reason": decision.reason,
            "message": decision.message,
            "reserve_key": decision.reserve_key,
        })
    return failures


def _ledger_payload_from_decisions(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    accepted_count = sum(1 for item in decisions if item.get("accepted"))
    return {
        "accepted_count": accepted_count,
        "rejected_count": len(decisions) - accepted_count,
        "decisions_by_lane": _count_payload_by_lane(decisions),
    }


def _dict(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _dict_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
