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
    max_dadata_lookups_per_run: int | None = None
    max_source_verification_requests_per_run: int | None = None
    max_provider_retries_per_task: int | None = None
    smoke_max_candidates: int | None = None
    smoke_max_signals: int | None = None


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

    def record_retry(self, *, task_id: str, reason: str, attempt: int, decision: RadarExternalCallBudgetDecision) -> None:
        self.retry_records.append({
            "task_id": task_id,
            "reason": reason,
            "attempt": attempt,
            "budget_decision": decision.to_payload(),
        })

    def to_metadata(self) -> dict[str, object]:
        return {
            "run_profile": self.settings.run_profile,
            "external_call_budget_settings": {
                "max_openrouter_calls_per_run": self.settings.max_openrouter_calls_per_run,
                "max_dadata_lookups_per_run": self.settings.max_dadata_lookups_per_run,
                "max_source_verification_requests_per_run": self.settings.max_source_verification_requests_per_run,
                "max_provider_retries_per_task": self.settings.max_provider_retries_per_task,
                "smoke_max_candidates": self.settings.smoke_max_candidates,
                "smoke_max_signals": self.settings.smoke_max_signals,
            },
            "external_call_budget_counters": dict(self.counts),
            "external_call_budget_exhaustion_events": list(self.exhaustion_events),
            "provider_retry_records": list(self.retry_records),
        }

    def _limit_for(self, kind: ExternalCallKind) -> int | None:
        if kind == "openrouter":
            return _non_negative(self.settings.max_openrouter_calls_per_run)
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


def external_budget_settings_from_context(context: dict[str, object]) -> RadarExternalCallBudgetSettings:
    profile = str(context.get("run_profile") or "live").strip().lower()
    if profile not in {"live", "smoke"}:
        profile = "live"
    smoke = profile == "smoke"
    return RadarExternalCallBudgetSettings(
        run_profile=profile,
        max_openrouter_calls_per_run=_context_int_or_default(context, "max_openrouter_calls_per_run", 8 if smoke else None),
        max_dadata_lookups_per_run=_context_int_or_default(context, "max_dadata_lookups_per_run", 3 if smoke else None),
        max_source_verification_requests_per_run=_context_int_or_default(context, "max_source_verification_requests_per_run", 20 if smoke else None),
        max_provider_retries_per_task=_context_int(context, "max_provider_retries_per_task") if _context_int(context, "max_provider_retries_per_task") is not None else (1 if smoke else 0),
        smoke_max_candidates=_context_int_or_default(context, "smoke_max_candidates", 2 if smoke else None),
        smoke_max_signals=_context_int_or_default(context, "smoke_max_signals", 1 if smoke else None),
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
