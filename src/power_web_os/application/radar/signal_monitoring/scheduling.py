"""Budget-aware scheduling and source-lane ledger projection."""

from __future__ import annotations

from dataclasses import dataclass

from power_web_os.application.radar.signal_monitoring.contracts import (
    SignalMonitoringPlan,
    SignalSourceLaneLedgerEntry,
    SignalSearchTask,
)


@dataclass(frozen=True, slots=True)
class SignalMonitoringSchedule:
    tasks: list[SignalSearchTask]
    ledger: list[SignalSourceLaneLedgerEntry]


class SignalMonitoringWorkScheduler:
    """Schedule accepted signal work while retaining every lane decision."""

    def schedule(self, plan: SignalMonitoringPlan, *, task_limit: int) -> SignalMonitoringSchedule:
        ordered = sorted(plan.tasks, key=_priority)
        selected_ids = {task.task_id for task in ordered[: max(task_limit, 0)]}
        tasks = [task for task in plan.tasks if task.task_id in selected_ids]
        ledger = [
            SignalSourceLaneLedgerEntry(
                task_id=task.task_id,
                candidate_id=task.candidate_id,
                signal_code=task.signal_code,
                source_lane=task.source_lane,
                required=task.required,
                status="scheduled" if task.task_id in selected_ids else "not_scheduled_budget_limited",
                reason="accepted_by_signal_task_budget" if task.task_id in selected_ids else "signal_task_budget_limited",
                source_decision_ids=list(task.source_decision_ids),
            )
            for task in plan.tasks
        ]
        return SignalMonitoringSchedule(tasks=tasks, ledger=ledger)


def _priority(task: SignalSearchTask) -> tuple[int, int, str, str]:
    lane_order = {"official_company": 0, "open_web": 1, "known_source": 2, "signal_specific": 3}
    return (0 if task.required else 1, lane_order.get(task.source_lane, 9), task.candidate_id, task.signal_code)
