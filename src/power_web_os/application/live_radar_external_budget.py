"""External-call budgets for live Radar provider integrations."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Iterator


ExternalCallKind = str


@dataclass(frozen=True, slots=True)
class RadarExternalCallBudgetSettings:
    run_profile: str = "live"
    max_openrouter_calls_per_run: int | None = None
    max_openrouter_planner_calls_per_run: int | None = None
    max_openrouter_web_task_calls_per_run: int | None = None
    max_recall_expansion_openrouter_calls_per_run: int | None = None
    max_openrouter_server_tool_web_searches_per_run: int | None = None
    max_dadata_lookups_per_run: int | None = None
    max_source_verification_requests_per_run: int | None = None
    max_provider_retries_per_task: int | None = None
    openrouter_web_max_results_per_call: int | None = None
    openrouter_web_max_total_results_per_call: int | None = None
    smoke_max_candidates: int | None = None
    smoke_max_signals: int | None = None
    budget_reserve_limits: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RadarExternalCallBudgetDecision:
    accepted: bool
    kind: ExternalCallKind
    key: str
    limit: int | None = None
    current: int = 0
    reason: str = ""
    message: str = ""

    def to_payload(self) -> dict[str, object]:
        return {
            "accepted": self.accepted,
            "kind": self.kind,
            "key": self.key,
            "limit": self.limit,
            "current": self.current,
            "reason": self.reason,
            "message": self.message,
        }


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

    def protect_recall_expansion_openrouter_task(self, *, task_id: str, reserve_key: str) -> None:
        if not task_id:
            return
        self.protected_recall_expansion_tasks[task_id] = reserve_key or "recall_expansion"

    def _reserve_protected_recall_expansion_openrouter_call(
        self,
        *,
        task_id: str,
    ) -> tuple[RadarExternalCallBudgetDecision, RadarExternalCallBudgetDecision]:
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
        total_decision = self.reserve("openrouter", key="run", task_id=task_id)
        return total_decision, protected_decision

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


_current_budget: ContextVar[RadarExternalCallBudget | None] = ContextVar("radar_external_call_budget", default=None)


@contextmanager
def external_call_budget_context(budget: RadarExternalCallBudget | None) -> Iterator[None]:
    token = _current_budget.set(budget)
    try:
        yield
    finally:
        _current_budget.reset(token)


def current_external_call_budget() -> RadarExternalCallBudget | None:
    return _current_budget.get()


def reserve_external_call(kind: ExternalCallKind, *, key: str = "run", task_id: str = "") -> RadarExternalCallBudgetDecision:
    budget = current_external_call_budget()
    if budget is None:
        return RadarExternalCallBudgetDecision(accepted=True, kind=kind, key=f"{kind}:{key or 'run'}")
    return budget.reserve(kind, key=key, task_id=task_id)


def reserve_openrouter_http_call(*, role: str, task_id: str = "") -> RadarExternalCallBudgetDecision:
    budget = current_external_call_budget()
    if budget is None:
        return RadarExternalCallBudgetDecision(accepted=True, kind=f"openrouter_{role}", key=f"openrouter_{role}:run")
    _, role_decision = budget.reserve_openrouter_http_call(role=role, task_id=task_id)
    return role_decision


def record_openrouter_server_tool_usage(*, count: int, task_id: str = "") -> RadarExternalCallBudgetDecision:
    budget = current_external_call_budget()
    if budget is None:
        return RadarExternalCallBudgetDecision(
            accepted=True,
            kind="openrouter_server_tool_web_search",
            key="openrouter_server_tool_web_search:run",
            current=count,
        )
    return budget.record_server_tool_web_search_usage(count=count, task_id=task_id)


def protect_recall_expansion_openrouter_task(*, task_id: str, reserve_key: str) -> None:
    budget = current_external_call_budget()
    if budget is None:
        return
    budget.protect_recall_expansion_openrouter_task(task_id=task_id, reserve_key=reserve_key)


def reserve_budget_slice(
    reserve_key: str,
    *,
    units: int = 1,
    task_id: str = "",
    reason: str = "",
) -> RadarExternalCallBudgetDecision:
    budget = current_external_call_budget()
    if budget is None:
        return RadarExternalCallBudgetDecision(accepted=True, kind="budget_reserve", key=f"budget_reserve:{reserve_key}")
    return budget.reserve_budget_slice(reserve_key, units=units, task_id=task_id, reason=reason)


def external_budget_settings_from_context(context: dict[str, object]) -> RadarExternalCallBudgetSettings:
    profile = str(context.get("run_profile") or "live").strip().lower()
    if profile not in {"live", "smoke"}:
        profile = "live"
    smoke = profile == "smoke"
    return RadarExternalCallBudgetSettings(
        run_profile=profile,
        max_openrouter_calls_per_run=_context_int_or_default(context, "max_openrouter_calls_per_run", 8 if smoke else None),
        max_openrouter_planner_calls_per_run=_context_int_or_default(
            context, "max_openrouter_planner_calls_per_run", 2 if smoke else None
        ),
        max_openrouter_web_task_calls_per_run=_context_int_or_default(
            context, "max_openrouter_web_task_calls_per_run", 6 if smoke else None
        ),
        max_recall_expansion_openrouter_calls_per_run=_context_int_or_default(
            context, "max_recall_expansion_openrouter_calls_per_run", 2 if smoke else None
        ),
        max_openrouter_server_tool_web_searches_per_run=_context_int_or_default(
            context, "max_openrouter_server_tool_web_searches_per_run", 24 if smoke else None
        ),
        max_dadata_lookups_per_run=_context_int_or_default(context, "max_dadata_lookups_per_run", 3 if smoke else None),
        max_source_verification_requests_per_run=_context_int_or_default(context, "max_source_verification_requests_per_run", 20 if smoke else None),
        max_provider_retries_per_task=_context_int(context, "max_provider_retries_per_task") if _context_int(context, "max_provider_retries_per_task") is not None else (1 if smoke else 0),
        openrouter_web_max_results_per_call=_context_int_or_default(
            context, "openrouter_web_max_results_per_call", 3 if smoke else None
        ),
        openrouter_web_max_total_results_per_call=_context_int_or_default(
            context, "openrouter_web_max_total_results_per_call", 6 if smoke else None
        ),
        smoke_max_candidates=_context_int_or_default(context, "smoke_max_candidates", 2 if smoke else None),
        smoke_max_signals=_context_int_or_default(context, "smoke_max_signals", 1 if smoke else None),
        budget_reserve_limits=_budget_reserve_limits(context, smoke=smoke),
    )


def _context_int(context: dict[str, object], key: str) -> int | None:
    value = context.get(key)
    if isinstance(value, bool):
        return None
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _context_int_or_default(context: dict[str, object], key: str, default: int | None) -> int | None:
    parsed = _context_int(context, key)
    return default if parsed is None else parsed


def _non_negative(value: int | None) -> int | None:
    return value if value is not None and value >= 0 else None


def _counts_by_role(counts: dict[str, int]) -> dict[str, int]:
    roles: dict[str, int] = {}
    for key, value in counts.items():
        role = key.split(":", 1)[0]
        roles[role] = roles.get(role, 0) + value
    return roles


def _budget_reserve_limits(context: dict[str, object], *, smoke: bool) -> dict[str, int]:
    defaults = _default_budget_reserve_limits(smoke=smoke)
    configured = context.get("budget_reserve_limits")
    if isinstance(configured, dict):
        parsed = {
            str(key): parsed
            for key, value in configured.items()
            if (parsed := _parse_non_negative_int(value)) is not None
        }
        return {**defaults, **parsed}
    return defaults


def _default_budget_reserve_limits(*, smoke: bool) -> dict[str, int]:
    if not smoke:
        return {}
    return {
        "primary_discovery": 3,
        "registry_identity": 2,
        "recall_expansion": 3,
        "official_coverage_probe": 2,
        "open_web_coverage_probe": 3,
        "production_site_coverage_probe": 2,
        "extraction_recovery": 2,
        "signal_search": 1,
    }


def _parse_non_negative_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None
