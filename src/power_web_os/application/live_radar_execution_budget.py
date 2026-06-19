"""Runtime budgets for bounded live Radar execution tasks."""

from __future__ import annotations

from power_web_os.application.live_radar_contracts import RadarExecutionTask


class SubjectTaskBudget:
    """Count backend-controlled provider calls by qualification rule or signal."""

    def __init__(self, limit: int | None) -> None:
        self.limit = limit if limit and limit > 0 else None
        self.counts: dict[str, int] = {}
        self.warnings: list[str] = []
        self.last_warning = ""

    def reserve(self, task: RadarExecutionTask) -> bool:
        if self.limit is None:
            return True
        key = _budget_key(task)
        current = self.counts.get(key, 0)
        if current >= self.limit:
            self.last_warning = f"Web task budget reached for {key}: {self.limit} tasks."
            if self.last_warning not in self.warnings:
                self.warnings.append(self.last_warning)
            return False
        self.counts[key] = current + 1
        return True


def _budget_key(task: RadarExecutionTask) -> str:
    subject_id = task.subject_id.strip() if task.subject_id else ""
    return subject_id or task.stage
