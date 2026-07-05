"""External-call budgets for live Radar provider integrations."""

from __future__ import annotations

from dataclasses import dataclass, field

from power_web_os.application.radar.shared.budgets.external_models import (
    ExternalCallKind,
    RadarExternalCallBudgetDecision,
    RadarExternalCallBudgetSettings,
)
from power_web_os.application.radar.shared.budgets.external_reservations import (
    guaranteed_recall_expansion_reservation_metadata as guaranteed_reservation_metadata,
    openrouter_reserved_remaining_by_lane,
)


@dataclass
class RadarExternalCallBudget:
    """Count actual external operations below semantic Radar task budgets."""

    settings: RadarExternalCallBudgetSettings
    counts: dict[str, int] = field(default_factory=dict)
    exhaustion_events: list[dict[str, object]] = field(default_factory=list)
    retry_records: list[dict[str, object]] = field(default_factory=list)
    post_call_budget_overruns: list[dict[str, object]] = field(default_factory=list)
    reserve_counts: dict[str, int] = field(default_factory=dict)
    reserve_exhaustion_events: list[dict[str, object]] = field(default_factory=list)
    protected_recall_expansion_tasks: dict[str, str] = field(default_factory=dict)
    guaranteed_recall_expansion_tasks: dict[str, dict[str, object]] = field(default_factory=dict)
    guaranteed_recall_expansion_first_calls_used: set[str] = field(default_factory=set)
    openrouter_total_reservations: dict[str, dict[str, object]] = field(default_factory=dict)

    def reserve(self, kind: ExternalCallKind, *, key: str = "run", task_id: str = "") -> RadarExternalCallBudgetDecision:
        budget_key = f"{kind}:{key or 'run'}" if kind == "provider_retry" else f"{kind}:run"
        limit = self._limit_for(kind)
        current = self.counts.get(budget_key, 0)
        if limit is not None and current >= limit:
            decision = RadarExternalCallBudgetDecision(
                accepted=False,
                kind=kind,
                key=budget_key,
                limit=limit,
                current=current,
                reason="external_call_budget_exhausted",
                message=f"External {kind} budget reached for {key or 'run'}: {limit}.",
            )
            self.exhaustion_events.append({"task_id": task_id, **decision.to_payload()})
            return decision
        self.counts[budget_key] = current + 1
        return RadarExternalCallBudgetDecision(
            accepted=True,
            kind=kind,
            key=budget_key,
            limit=limit,
            current=current + 1,
        )

    def reserve_openrouter_http_call(
        self,
        *,
        role: str,
        task_id: str = "",
    ) -> tuple[RadarExternalCallBudgetDecision, RadarExternalCallBudgetDecision]:
        role_kind = "openrouter_planner" if role == "planner" else "openrouter_web_task"
        if role_kind == "openrouter_web_task" and task_id in self.protected_recall_expansion_tasks:
            return self._reserve_protected_recall_expansion_openrouter_call(task_id=task_id)
        reserved_capacity_block = self._reserved_openrouter_capacity_decision(role_kind=role_kind, task_id=task_id)
        if reserved_capacity_block is not None:
            return reserved_capacity_block, reserved_capacity_block
        total_block = self._exhausted_decision("openrouter", budget_key="openrouter:run", key="run", task_id=task_id)
        if total_block is not None:
            return total_block, total_block
        if role_kind == "openrouter_web_task":
            server_tool_block = self._exhausted_decision(
                "openrouter_server_tool_web_search",
                budget_key="openrouter_server_tool_web_search:run",
                key="run",
                task_id=task_id,
            )
            if server_tool_block is not None:
                return server_tool_block, server_tool_block
        role_block = self._exhausted_decision(role_kind, budget_key=f"{role_kind}:run", key="run", task_id=task_id)
        if role_block is not None:
            return role_block, role_block
        role_decision = self.reserve(role_kind, key="run", task_id=task_id)
        total_decision = self.reserve("openrouter", key="run", task_id=task_id)
        return total_decision, role_decision

    def protect_recall_expansion_openrouter_task(
        self,
        *,
        task_id: str,
        reserve_key: str,
        guaranteed: bool = False,
        lane: str = "",
        target_id: str = "",
        target_type: str = "",
    ) -> None:
        if not task_id:
            return
        self.protected_recall_expansion_tasks[task_id] = reserve_key or "recall_expansion"
        if guaranteed:
            self.guaranteed_recall_expansion_tasks[task_id] = {
                "task_id": task_id,
                "reserve_key": reserve_key or "recall_expansion",
                "lane": lane,
                "target_id": target_id,
                "target_type": target_type,
            }

    def configure_openrouter_total_reserve(self, *, lane: str, units: int, reason: str = "") -> None:
        if units <= 0:
            return
        self.openrouter_total_reservations[lane or "unclassified"] = {
            "lane": lane or "unclassified",
            "units": units,
            "reason": reason,
        }

    def openrouter_total_reservation_metadata(self) -> dict[str, object]:
        return {
            "reservations": {key: dict(value) for key, value in self.openrouter_total_reservations.items()},
            "reserved_remaining": self._openrouter_reserved_remaining_by_lane(),
            "guaranteed_recall_expansion": self.guaranteed_recall_expansion_reservation_metadata(),
        }

    def guaranteed_recall_expansion_reservation_metadata(self) -> dict[str, object]:
        return guaranteed_reservation_metadata(
            tasks=self.guaranteed_recall_expansion_tasks,
            used_task_ids=self.guaranteed_recall_expansion_first_calls_used,
        )

    def _reserve_protected_recall_expansion_openrouter_call(
        self,
        *,
        task_id: str,
    ) -> tuple[RadarExternalCallBudgetDecision, RadarExternalCallBudgetDecision]:
        reservation_block = self._protected_recall_expansion_reservation_decision(task_id=task_id)
        if reservation_block is not None:
            return reservation_block, reservation_block
        total_block = self._exhausted_decision("openrouter", budget_key="openrouter:run", key="run", task_id=task_id)
        if total_block is not None:
            return total_block, total_block
        server_tool_block = self._exhausted_decision(
            "openrouter_server_tool_web_search",
            budget_key="openrouter_server_tool_web_search:run",
            key="run",
            task_id=task_id,
        )
        if server_tool_block is not None:
            return server_tool_block, server_tool_block
        protected_block = self._exhausted_decision(
            "openrouter_recall_expansion",
            budget_key="openrouter_recall_expansion:run",
            key="run",
            task_id=task_id,
        )
        if protected_block is not None:
            return protected_block, protected_block
        protected_decision = self.reserve("openrouter_recall_expansion", key="run", task_id=task_id)
        if protected_decision.accepted and task_id in self.guaranteed_recall_expansion_tasks:
            self.guaranteed_recall_expansion_first_calls_used.add(task_id)
        total_decision = self.reserve("openrouter", key="run", task_id=task_id)
        return total_decision, protected_decision

    def _protected_recall_expansion_reservation_decision(
        self,
        *,
        task_id: str,
    ) -> RadarExternalCallBudgetDecision | None:
        """Prevent retries or optional work from spending guaranteed first-call slots."""

        if task_id in self.guaranteed_recall_expansion_tasks and task_id not in self.guaranteed_recall_expansion_first_calls_used:
            return None
        recall_limit = self._limit_for("openrouter_recall_expansion")
        if recall_limit is None:
            return None
        remaining_first_calls = int(
            self.guaranteed_recall_expansion_reservation_metadata().get("first_call_remaining_count", 0) or 0
        )
        if remaining_first_calls <= 0:
            return None
        current = self.counts.get("openrouter_recall_expansion:run", 0)
        allowed_before_reserved_slots = max(recall_limit - remaining_first_calls, 0)
        if current < allowed_before_reserved_slots:
            return None
        decision = RadarExternalCallBudgetDecision(
            accepted=False,
            kind="openrouter_recall_expansion",
            key="openrouter_recall_expansion:run",
            limit=recall_limit,
            current=current,
            reason="guaranteed_external_reservation_protected",
            message=(
                "Recall-expansion OpenRouter capacity is reserved for "
                f"{remaining_first_calls} guaranteed first calls."
            ),
        )
        self.exhaustion_events.append({"task_id": task_id, **decision.to_payload()})
        return decision

    def check_recall_expansion_openrouter_capacity(self, *, task_id: str = "") -> RadarExternalCallBudgetDecision:
        """Non-mutating scheduler preflight for protected recall-expansion calls."""
        for kind, budget_key in (
            ("openrouter", "openrouter:run"),
            ("openrouter_server_tool_web_search", "openrouter_server_tool_web_search:run"),
            ("openrouter_recall_expansion", "openrouter_recall_expansion:run"),
        ):
            limit = self._limit_for(kind)
            current = self.counts.get(budget_key, 0)
            if limit is not None and current >= limit:
                return RadarExternalCallBudgetDecision(
                    accepted=False,
                    kind=kind,
                    key=budget_key,
                    limit=limit,
                    current=current,
                    reason="external_call_budget_exhausted",
                    message=f"External {kind} budget reached for run: {limit}.",
                )
        return RadarExternalCallBudgetDecision(
            accepted=True,
            kind="openrouter_recall_expansion",
            key="openrouter_recall_expansion:run",
            limit=self._limit_for("openrouter_recall_expansion"),
            current=self.counts.get("openrouter_recall_expansion:run", 0),
        )

    def _exhausted_decision(
        self,
        kind: ExternalCallKind,
        *,
        budget_key: str,
        key: str,
        task_id: str,
    ) -> RadarExternalCallBudgetDecision | None:
        limit = self._limit_for(kind)
        current = self.counts.get(budget_key, 0)
        if limit is None or current < limit:
            return None
        decision = RadarExternalCallBudgetDecision(
            accepted=False,
            kind=kind,
            key=budget_key,
            limit=limit,
            current=current,
            reason="external_call_budget_exhausted",
            message=f"External {kind} budget reached for {key or 'run'}: {limit}.",
        )
        self.exhaustion_events.append({"task_id": task_id, **decision.to_payload()})
        return decision

    def _reserved_openrouter_capacity_decision(
        self,
        *,
        role_kind: str,
        task_id: str,
    ) -> RadarExternalCallBudgetDecision | None:
        if role_kind != "openrouter_web_task":
            return None
        total_limit = self._limit_for("openrouter")
        if total_limit is None:
            return None
        reserved_remaining = sum(self._openrouter_reserved_remaining_by_lane().values())
        if reserved_remaining <= 0:
            return None
        current_total = self.counts.get("openrouter:run", 0)
        allowed_regular_total = max(total_limit - reserved_remaining, 0)
        if current_total < allowed_regular_total:
            return None
        decision = RadarExternalCallBudgetDecision(
            accepted=False,
            kind="openrouter",
            key="openrouter:run",
            limit=total_limit,
            current=current_total,
            reason="work_admission_reserved_capacity",
            message=(
                "OpenRouter run capacity is reserved for guaranteed recall expansion "
                f"({reserved_remaining} calls remaining)."
            ),
        )
        self.exhaustion_events.append({"task_id": task_id, **decision.to_payload()})
        return decision

    def _openrouter_reserved_remaining_by_lane(self) -> dict[str, int]:
        return openrouter_reserved_remaining_by_lane(
            reservations=self.openrouter_total_reservations,
            guaranteed_tasks=self.guaranteed_recall_expansion_tasks,
            used_task_ids=self.guaranteed_recall_expansion_first_calls_used,
            protected_used=self.counts.get("openrouter_recall_expansion:run", 0),
        )

    def record_server_tool_web_search_usage(
        self,
        *,
        count: int,
        task_id: str = "",
    ) -> RadarExternalCallBudgetDecision:
        if count <= 0:
            return RadarExternalCallBudgetDecision(
                accepted=True,
                kind="openrouter_server_tool_web_search",
                key="openrouter_server_tool_web_search:run",
                limit=self._limit_for("openrouter_server_tool_web_search"),
                current=self.counts.get("openrouter_server_tool_web_search:run", 0),
            )
        budget_key = "openrouter_server_tool_web_search:run"
        limit = self._limit_for("openrouter_server_tool_web_search")
        current = self.counts.get(budget_key, 0)
        next_value = current + count
        self.counts[budget_key] = next_value
        decision = RadarExternalCallBudgetDecision(
            accepted=limit is None or next_value <= limit,
            kind="openrouter_server_tool_web_search",
            key=budget_key,
            limit=limit,
            current=next_value,
            reason="" if limit is None or next_value <= limit else "external_call_budget_overrun",
            message="" if limit is None or next_value <= limit else (
                f"OpenRouter server-tool web search usage exceeded run budget: {next_value}/{limit}."
            ),
        )
        if not decision.accepted:
            self.post_call_budget_overruns.append({"task_id": task_id, "usage_count": count, **decision.to_payload()})
        return decision

    def record_retry(self, *, task_id: str, reason: str, attempt: int, decision: RadarExternalCallBudgetDecision) -> None:
        self.retry_records.append({
            "task_id": task_id,
            "reason": reason,
            "attempt": attempt,
            "budget_decision": decision.to_payload(),
        })

    def reserve_budget_slice(
        self,
        reserve_key: str,
        *,
        units: int = 1,
        task_id: str = "",
        reason: str = "",
    ) -> RadarExternalCallBudgetDecision:
        key = f"budget_reserve:{reserve_key or 'unclassified'}"
        limit = _non_negative(self.settings.budget_reserve_limits.get(reserve_key or "unclassified"))
        current = self.reserve_counts.get(key, 0)
        if limit is not None and current + max(units, 1) > limit:
            decision = RadarExternalCallBudgetDecision(
                accepted=False,
                kind="budget_reserve",
                key=key,
                limit=limit,
                current=current,
                reason="budget_reserve_exhausted",
                message=f"Radar budget reserve {reserve_key} reached: {current}/{limit}.",
            )
            self.reserve_exhaustion_events.append({
                "task_id": task_id,
                "reserve_key": reserve_key,
                "reason_detail": reason,
                **decision.to_payload(),
            })
            return decision
        self.reserve_counts[key] = current + max(units, 1)
        return RadarExternalCallBudgetDecision(
            accepted=True,
            kind="budget_reserve",
            key=key,
            limit=limit,
            current=self.reserve_counts[key],
        )

    def to_metadata(self) -> dict[str, object]:
        return {
            "run_profile": self.settings.run_profile,
            "external_call_budget_settings": {
                "max_openrouter_calls_per_run": self.settings.max_openrouter_calls_per_run,
                "max_openrouter_planner_calls_per_run": self.settings.max_openrouter_planner_calls_per_run,
                "max_openrouter_web_task_calls_per_run": self.settings.max_openrouter_web_task_calls_per_run,
                "max_recall_expansion_openrouter_calls_per_run": (
                    self.settings.max_recall_expansion_openrouter_calls_per_run
                ),
                "max_openrouter_server_tool_web_searches_per_run": self.settings.max_openrouter_server_tool_web_searches_per_run,
                "max_dadata_lookups_per_run": self.settings.max_dadata_lookups_per_run,
                "max_source_verification_requests_per_run": self.settings.max_source_verification_requests_per_run,
                "max_provider_retries_per_task": self.settings.max_provider_retries_per_task,
                "openrouter_web_max_results_per_call": self.settings.openrouter_web_max_results_per_call,
                "openrouter_web_max_total_results_per_call": self.settings.openrouter_web_max_total_results_per_call,
                "smoke_max_candidates": self.settings.smoke_max_candidates,
                "smoke_max_signals": self.settings.smoke_max_signals,
                "budget_reserve_limits": dict(self.settings.budget_reserve_limits),
            },
            "external_call_budget_counters": dict(self.counts),
            "external_call_budget_counters_by_role": _counts_by_role(self.counts),
            "external_call_budget_exhaustion_events": list(self.exhaustion_events),
            "provider_retry_records": list(self.retry_records),
            "openrouter_server_tool_usage": {
                "web_search_requests": self.counts.get("openrouter_server_tool_web_search:run", 0),
                "limit": self.settings.max_openrouter_server_tool_web_searches_per_run,
            },
            "post_call_budget_overruns": list(self.post_call_budget_overruns),
            "budget_reserve_counters": dict(self.reserve_counts),
            "budget_reserve_exhaustion_events": list(self.reserve_exhaustion_events),
            "work_admission_reserved_capacity": self.openrouter_total_reservation_metadata(),
        }

    def _limit_for(self, kind: ExternalCallKind) -> int | None:
        if kind == "openrouter":
            return _non_negative(self.settings.max_openrouter_calls_per_run)
        if kind == "openrouter_planner":
            return _non_negative(self.settings.max_openrouter_planner_calls_per_run)
        if kind == "openrouter_web_task":
            return _non_negative(self.settings.max_openrouter_web_task_calls_per_run)
        if kind == "openrouter_recall_expansion":
            return _non_negative(self.settings.max_recall_expansion_openrouter_calls_per_run)
        if kind == "openrouter_server_tool_web_search":
            return _non_negative(self.settings.max_openrouter_server_tool_web_searches_per_run)
        if kind == "dadata":
            return _non_negative(self.settings.max_dadata_lookups_per_run)
        if kind == "source_verification":
            return _non_negative(self.settings.max_source_verification_requests_per_run)
        if kind == "provider_retry":
            return _non_negative(self.settings.max_provider_retries_per_task)
        return None

def _non_negative(value: int | None) -> int | None:
    return value if value is not None and value >= 0 else None


def _counts_by_role(counts: dict[str, int]) -> dict[str, int]:
    roles: dict[str, int] = {}
    for key, value in counts.items():
        role = key.split(":", 1)[0]
        roles[role] = roles.get(role, 0) + value
    return roles
