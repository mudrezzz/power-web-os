"""Runtime budgets for bounded live Radar execution tasks."""

from __future__ import annotations

from dataclasses import dataclass, field

from power_web_os.application.radar.candidate_discovery.contracts import RadarExecutionTask


@dataclass(frozen=True, slots=True)
class RadarExecutionBudgetSettings:
    max_total_tasks_per_run: int | None = None
    max_discovery_tasks_per_rule: int | None = None
    max_gate_tasks_per_candidate_rule: int | None = None
    max_signal_tasks_per_candidate_signal: int | None = None
    compatibility_max_web_tasks_per_subject: int | None = None
    semantic_task_reserve_limits: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RadarBudgetDecision:
    accepted: bool
    key: str
    limit: int | None = None
    current: int = 0
    state: str = "searched"
    reason: str = ""
    message: str = ""
    reserve_key: str = ""
    used_semantic_reserve: bool = False


class RadarExecutionBudget:
    """Count backend-controlled provider calls with Radar semantic keys."""

    def __init__(self, settings: RadarExecutionBudgetSettings) -> None:
        self.settings = settings
        self.counts: dict[str, int] = {}
        self.total_count = 0
        self.semantic_reserve_counts: dict[str, int] = {}
        self.warnings: list[str] = []
        self.exhaustion_events: list[dict[str, object]] = []
        self.last_decision = RadarBudgetDecision(accepted=True, key="run")

    def reserve(self, task: RadarExecutionTask, *, semantic_reserve_key: str | None = None) -> bool:
        decision = self.reserve_decision(task, semantic_reserve_key=semantic_reserve_key)
        self.last_decision = decision
        if not decision.accepted and decision.message not in self.warnings:
            self.warnings.append(decision.message)
        if not decision.accepted:
            self.exhaustion_events.append(_event_payload(task, decision))
        return decision.accepted

    def reserve_decision(
        self,
        task: RadarExecutionTask,
        *,
        semantic_reserve_key: str | None = None,
    ) -> RadarBudgetDecision:
        regular_block = self._regular_blocking_decision(task)
        if regular_block is not None:
            reserve_decision = self._try_semantic_reserve(task, semantic_reserve_key)
            if reserve_decision is not None:
                return reserve_decision
            return regular_block

        key = budget_key(task)
        limit = self._limit_for(task)
        current = self.counts.get(key, 0)
        self.counts[key] = current + 1
        self.total_count += 1
        return RadarBudgetDecision(accepted=True, key=key, limit=limit, current=current + 1)

    def _regular_blocking_decision(self, task: RadarExecutionTask) -> RadarBudgetDecision | None:
        total_limit = _positive(self.settings.max_total_tasks_per_run)
        if total_limit is not None and self.total_count >= total_limit:
            return RadarBudgetDecision(
                accepted=False,
                key="run",
                limit=total_limit,
                current=self.total_count,
                state="not_searched_budget_limited",
                reason="total_run_budget_exhausted",
                message=f"Total Radar web task budget reached: {total_limit} tasks.",
            )

        key = budget_key(task)
        limit = self._limit_for(task)
        current = self.counts.get(key, 0)
        if limit is not None and current >= limit:
            return RadarBudgetDecision(
                accepted=False,
                key=key,
                limit=limit,
                current=current,
                state="not_searched_budget_limited",
                reason="semantic_budget_exhausted",
                message=f"Web task budget reached for {key}: {limit} tasks.",
            )
        return None

    def _try_semantic_reserve(self, task: RadarExecutionTask, semantic_reserve_key: str | None) -> RadarBudgetDecision | None:
        reserve_key = (semantic_reserve_key or "").strip()
        if not reserve_key:
            return None
        limit = _positive(self.settings.semantic_task_reserve_limits.get(reserve_key))
        if limit is None:
            return None
        key = f"semantic_reserve:{reserve_key}"
        current = self.semantic_reserve_counts.get(key, 0)
        if current >= limit:
            return RadarBudgetDecision(
                accepted=False,
                key=key,
                limit=limit,
                current=current,
                state="not_searched_budget_limited",
                reason="semantic_task_reserve_exhausted",
                message=f"Semantic Radar task reserve {reserve_key} reached: {current}/{limit}.",
                reserve_key=reserve_key,
            )
        self.semantic_reserve_counts[key] = current + 1
        self.total_count += 1
        return RadarBudgetDecision(
            accepted=True,
            key=key,
            limit=limit,
            current=current + 1,
            reserve_key=reserve_key,
            used_semantic_reserve=True,
        )

    def to_metadata(self) -> dict[str, object]:
        return {
            "semantic_task_budget_settings": {
                "semantic_task_reserve_limits": dict(self.settings.semantic_task_reserve_limits),
            },
            "semantic_task_budget_counters": dict(self.semantic_reserve_counts),
            "semantic_task_budget_exhaustion_events": [
                event for event in self.exhaustion_events if str(event.get("reason") or "") == "semantic_task_reserve_exhausted"
            ],
        }

    def _limit_for(self, task: RadarExecutionTask) -> int | None:
        alias = _positive(self.settings.compatibility_max_web_tasks_per_subject)
        if task.stage == "qualification_discovery":
            return _positive(self.settings.max_discovery_tasks_per_rule) or alias
        if task.stage == "qualification_gate":
            return _positive(self.settings.max_gate_tasks_per_candidate_rule) or alias
        if task.stage == "signal_search":
            return _positive(self.settings.max_signal_tasks_per_candidate_signal) or alias
        return alias


def budget_key(task: RadarExecutionTask) -> str:
    subject_id = task.subject_id.strip() if task.subject_id else task.stage
    if task.stage == "qualification_discovery":
        return f"discovery:{subject_id}"
    if task.stage == "qualification_gate":
        candidate = _candidate_key(task)
        return f"gate:{subject_id}:{candidate}" if candidate else f"gate:{subject_id}"
    if task.stage == "signal_search":
        candidate = _candidate_key(task)
        return f"signal:{subject_id}:{candidate}" if candidate else f"signal:{subject_id}"
    return f"{task.stage}:{subject_id}"


def _event_payload(task: RadarExecutionTask, decision: RadarBudgetDecision) -> dict[str, object]:
    return {
        "task_id": task.task_id,
        "stage": task.stage,
        "subject_type": task.subject_type,
        "subject_id": task.subject_id,
        "candidate_scope": list(task.candidate_scope),
        "budget_key": decision.key,
        "limit": decision.limit,
        "current": decision.current,
        "state": decision.state,
        "reason": decision.reason,
        "message": decision.message,
        "reserve_key": decision.reserve_key,
        "used_semantic_reserve": decision.used_semantic_reserve,
    }


def _candidate_key(task: RadarExecutionTask) -> str:
    if not task.candidate_scope:
        return ""
    return task.candidate_scope[0].strip()


def _positive(value: int | None) -> int | None:
    return value if value and value > 0 else None


# Backward-compatible alias used by older tests/imports.
class SubjectTaskBudget(RadarExecutionBudget):
    """Compatibility wrapper for the pre-0.7.6.1.9 subject budget."""

    def __init__(self, limit: int | None) -> None:
        super().__init__(RadarExecutionBudgetSettings(compatibility_max_web_tasks_per_subject=limit))

    @property
    def limit(self) -> int | None:
        return self.settings.compatibility_max_web_tasks_per_subject

    @property
    def last_warning(self) -> str:
        return self.last_decision.message


def budget_settings_from_context(
    *,
    max_web_tasks_per_subject: int | None = None,
    max_discovery_tasks_per_rule: int | None = None,
    max_gate_tasks_per_candidate_rule: int | None = None,
    max_signal_tasks_per_candidate_signal: int | None = None,
    max_total_web_tasks_per_run: int | None = None,
    semantic_task_reserve_limits: dict[str, int] | None = None,
) -> RadarExecutionBudgetSettings:
    return RadarExecutionBudgetSettings(
        max_total_tasks_per_run=_positive(max_total_web_tasks_per_run),
        max_discovery_tasks_per_rule=_positive(max_discovery_tasks_per_rule),
        max_gate_tasks_per_candidate_rule=_positive(max_gate_tasks_per_candidate_rule),
        max_signal_tasks_per_candidate_signal=_positive(max_signal_tasks_per_candidate_signal),
        compatibility_max_web_tasks_per_subject=_positive(max_web_tasks_per_subject),
        semantic_task_reserve_limits=_positive_int_dict(semantic_task_reserve_limits),
    )


def _positive_int_dict(value: dict[str, int] | None) -> dict[str, int]:
    result: dict[str, int] = {}
    for key, raw in (value or {}).items():
        try:
            parsed = int(raw)
        except (TypeError, ValueError):
            continue
        if parsed > 0:
            result[str(key)] = parsed
    return result
