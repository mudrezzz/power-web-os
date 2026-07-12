"""Bounded query revision after an evidence-quality checkpoint."""

from __future__ import annotations

from power_web_os.application.radar.signal_monitoring.contracts import (
    SignalMonitoringCheckpointDecision,
    SignalSearchTask,
)


class SignalMonitoringQueryRevisionService:
    """Create at most one explicit open-web revision per candidate/criterion."""

    def build(
        self,
        *,
        decisions: list[SignalMonitoringCheckpointDecision],
        tasks: list[SignalSearchTask],
        max_revisions_per_pair: int,
        allow_open_web: bool,
    ) -> list[SignalSearchTask]:
        if max_revisions_per_pair <= 0 or not allow_open_web:
            return []
        result: list[SignalSearchTask] = []
        for decision in decisions:
            if decision.action != "revise_query":
                continue
            pair = [
                task for task in tasks
                if task.candidate_id == decision.candidate_id
                and task.signal_code == decision.signal_code
            ]
            if any(task.revision_index >= max_revisions_per_pair for task in pair):
                continue
            base = next((task for task in pair if task.source_lane == "open_web"), pair[0] if pair else None)
            if base is None:
                continue
            revision_index = max((task.revision_index for task in pair), default=0) + 1
            result.append(base.model_copy(update={
                "task_id": f"{base.task_id}-revision-{revision_index}",
                "query": (
                    f"{base.query} exact company match exact signal criterion "
                    f"published between {base.window_start[:10]} and {base.window_end[:10]}"
                ),
                "source_lane": "open_web",
                "source_ids": [],
                "source_refs": [],
                "source_decision_ids": [],
                "source_contracts": [],
                "domain_restrictions": [],
                "required": False,
                "revision_index": revision_index,
            }))
        return result
