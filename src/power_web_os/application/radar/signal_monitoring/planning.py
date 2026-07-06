"""Task planning for the Radar signal-monitoring executor."""

from __future__ import annotations

from power_web_os.application.radar.signal_monitoring.contracts import (
    SignalMonitoringInput,
    SignalMonitoringSourceStrategyResult,
    SignalSearchTask,
)


class SignalMonitoringTaskPlanner:
    """Build bounded provider tasks from monitoring input and source decisions."""

    def build_tasks(
        self,
        monitoring_input: SignalMonitoringInput,
        source_strategy_result: SignalMonitoringSourceStrategyResult,
    ) -> list[SignalSearchTask]:
        tasks = []
        selected_decisions = [decision for decision in source_strategy_result.decisions if decision.status == "selected"]
        if not selected_decisions:
            selected_decisions = []
        for candidate in monitoring_input.candidates:
            for rule in monitoring_input.signal_rules:
                decisions = selected_decisions or [None]
                for index, decision in enumerate(decisions, start=1):
                    query = rule.query_template.format(candidate=candidate.display_name, signal=rule.label)
                    suffix = f"-{decision.lane}-{index}" if decision else "-no-source"
                    tasks.append(SignalSearchTask(
                        task_id=f"signal-{candidate.candidate_id}-{rule.signal_code}{suffix}",
                        candidate_id=candidate.candidate_id,
                        candidate_name=candidate.display_name,
                        signal_code=rule.signal_code,
                        signal_label=rule.label,
                        query=" ".join(query.split()),
                        lookback_days=monitoring_input.lookback_days,
                        known_source_refs=list(candidate.source_refs),
                        source_lane=decision.lane if decision else "open_web",
                        source_ids=[decision.source_id] if decision and decision.source_id else [],
                        source_refs=list(decision.source_refs) if decision else [],
                        source_decision_ids=[decision.decision_id] if decision else [],
                    ))
        return tasks
