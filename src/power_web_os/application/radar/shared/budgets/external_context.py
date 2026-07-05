"""Context-local helpers for Radar external-call budgets."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

from power_web_os.application.radar.shared.budgets.external_budget import (
    RadarExternalCallBudget,
)
from power_web_os.application.radar.shared.budgets.external_models import (
    ExternalCallKind,
    RadarExternalCallBudgetDecision,
    RadarExternalCallBudgetSettings,
)


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
    from power_web_os.application.radar.shared.budgets.external_settings import (
        external_budget_settings_from_context as build_settings,
    )

    return build_settings(context)
