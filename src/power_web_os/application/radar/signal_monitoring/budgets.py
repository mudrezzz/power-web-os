"""Budget counters and limit checks for signal monitoring."""

from __future__ import annotations

from power_web_os.application.radar.signal_monitoring.contracts import SignalMonitoringInput


class SignalMonitoringBudgetTracker:
    """Track signal-specific task, provider, retry, and lookback counters."""

    def __init__(self, monitoring_input: SignalMonitoringInput, *, task_count: int) -> None:
        self.monitoring_input = monitoring_input
        self.counters = {
            "tasks_built": task_count,
            "tasks_executed": 0,
            "provider_calls": 0,
            "retries": 0,
            "backup_retries": 0,
            "signal_tasks_built": task_count,
            "signal_tasks_executed": 0,
            "signal_provider_calls": 0,
            "signal_extraction_retries": 0,
            "signal_backup_retries": 0,
            "signal_source_verifications": 0,
            "signal_lookback_queries": 0,
        }
        self.exhaustion_events: list[dict[str, str | int]] = []
        self._retries_by_task: dict[str, int] = {}

    def task_budget_exhausted(self) -> bool:
        return self.counters["signal_tasks_executed"] >= self.max_signal_tasks()

    def provider_budget_exhausted(self) -> bool:
        return self.counters["signal_provider_calls"] >= self.max_signal_provider_calls()

    def retry_budget_available(self, task_id: str = "") -> bool:
        per_task = self._retries_by_task.get(task_id, 0)
        return (
            per_task < self.monitoring_input.budget.max_retries_per_task
            and self.counters["signal_extraction_retries"] < self.max_signal_extraction_retries()
        )

    def backup_retry_budget_available(self) -> bool:
        limit = self.monitoring_input.budget.max_signal_backup_retries
        return limit is None or self.counters["signal_backup_retries"] < limit

    def lookback_budget_exhausted(self) -> bool:
        limit = self.monitoring_input.budget.max_signal_lookback_queries
        return limit is not None and self.counters["signal_lookback_queries"] >= limit

    def source_verification_budget_available(self, count: int) -> bool:
        limit = self.monitoring_input.budget.max_signal_source_verifications
        return limit is None or self.counters["signal_source_verifications"] + count <= limit

    def record_lookback_query(self) -> None:
        self.counters["signal_lookback_queries"] += 1

    def record_source_verifications(self, count: int) -> None:
        self.counters["signal_source_verifications"] += max(0, count)

    def record_searched_task(self) -> None:
        self.counters["tasks_executed"] += 1
        self.counters["signal_tasks_executed"] += 1

    def record_provider_call(self) -> None:
        self.counters["provider_calls"] += 1
        self.counters["signal_provider_calls"] += 1

    def record_primary_retry(self, task_id: str = "") -> None:
        self.counters["retries"] += 1
        self.counters["signal_extraction_retries"] += 1
        self._retries_by_task[task_id] = self._retries_by_task.get(task_id, 0) + 1

    def record_backup_retry(self) -> None:
        self.counters["backup_retries"] += 1
        self.counters["signal_backup_retries"] += 1

    def record_exhaustion(self, *, budget: str, task_id: str, limit: int) -> None:
        event = {"budget": budget, "task_id": task_id, "limit": limit}
        if event not in self.exhaustion_events:
            self.exhaustion_events.append(event)

    def settings_payload(self) -> dict[str, int | bool | None]:
        budget = self.monitoring_input.budget
        return {
            "max_signal_tasks": self.max_signal_tasks(),
            "max_signal_provider_calls": self.max_signal_provider_calls(),
            "max_retries_per_task": budget.max_retries_per_task,
            "max_signal_extraction_retries": self.max_signal_extraction_retries(),
            "max_signal_backup_retries": budget.max_signal_backup_retries,
            "max_signal_source_verifications": budget.max_signal_source_verifications,
            "max_signal_lookback_queries": budget.max_signal_lookback_queries,
            "allow_backup_retry": budget.allow_backup_retry,
        }

    def max_signal_tasks(self) -> int:
        budget = self.monitoring_input.budget
        return budget.max_signal_tasks if budget.max_signal_tasks is not None else budget.max_tasks

    def max_signal_provider_calls(self) -> int:
        budget = self.monitoring_input.budget
        return (
            budget.max_signal_provider_calls
            if budget.max_signal_provider_calls is not None
            else budget.max_provider_calls
        )

    def max_signal_extraction_retries(self) -> int:
        budget = self.monitoring_input.budget
        return (
            budget.max_signal_extraction_retries
            if budget.max_signal_extraction_retries is not None
            else budget.max_retries_per_task
        )
