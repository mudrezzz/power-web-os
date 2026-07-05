"""Provider-level external-call budget records shared by Radar pipelines."""

from __future__ import annotations

from dataclasses import dataclass, field


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
