"""Execution option contract for candidate-discovery staged runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from power_web_os.application.radar.candidate_discovery.execution.signal_modes import (
    CandidateDiscoverySignalExecutionMode,
    _normalize_signal_execution_mode,
)
from power_web_os.application.radar.candidate_discovery.execution.task_budget import (
    RadarExecutionBudgetSettings,
    budget_settings_from_context,
)
from power_web_os.application.radar.shared.budgets import RadarExternalCallBudgetSettings
from power_web_os.application.radar.shared.budgets.external_context import external_budget_settings_from_context
from power_web_os.application.radar.candidate_discovery.execution.useful_budget import UsefulResultBudget


@dataclass(frozen=True, slots=True)
class CandidateDiscoveryExecutionOptions:
    """Named execution options for one candidate-discovery staged run.

    Owns:
    - Provider-neutral task-context overrides, budget limits, useful-result
      retry limits, checkpoint limits, smoke caps, reserve maps, run profile,
      and source policy decisions for the compatibility staged execution entry.

    Does not own:
    - Provider ports, execution state, phase order, budget counters, checkpoint
      decisions, or final dossier projection.

    Architecture:
    docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md#candidatediscoveryexecutionoptions
    """

    task_context: dict[str, Any] = field(default_factory=dict)
    max_web_tasks_per_subject: int | None = None
    max_discovery_tasks_per_rule: int | None = None
    max_gate_tasks_per_candidate_rule: int | None = None
    max_signal_tasks_per_candidate_signal: int | None = None
    max_total_web_tasks_per_run: int | None = None
    min_useful_sources_per_discovery_task: int | None = None
    min_candidates_per_discovery_task: int | None = None
    max_discovery_retries_per_task: int | None = None
    max_checkpoint_revisions_per_run: int | None = None
    max_checkpoint_retries_per_stage: int | None = None
    run_profile: str | None = None
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
    budget_reserve_limits: dict[str, int] | None = None
    semantic_task_reserve_limits: dict[str, int] | None = None
    source_policy_decisions: list[dict[str, Any]] | None = None
    signal_execution_mode: CandidateDiscoverySignalExecutionMode = "handoff"

    @classmethod
    def from_task_context(
        cls,
        task_context: Mapping[str, Any] | None,
        discovery_plan: Mapping[str, Any] | None = None,
    ) -> "CandidateDiscoveryExecutionOptions":
        context = dict(task_context or {})
        return cls(
            task_context=context,
            max_web_tasks_per_subject=_optional_int(context, "max_web_tasks_per_subject"),
            max_discovery_tasks_per_rule=_optional_int(context, "max_discovery_tasks_per_rule"),
            max_gate_tasks_per_candidate_rule=_optional_int(context, "max_gate_tasks_per_candidate_rule"),
            max_signal_tasks_per_candidate_signal=_optional_int(context, "max_signal_tasks_per_candidate_signal"),
            max_total_web_tasks_per_run=_optional_int(context, "max_total_web_tasks_per_run"),
            min_useful_sources_per_discovery_task=_optional_int(context, "min_useful_sources_per_discovery_task"),
            min_candidates_per_discovery_task=_optional_int(context, "min_candidates_per_discovery_task"),
            max_discovery_retries_per_task=_optional_int(context, "max_discovery_retries_per_task"),
            max_checkpoint_revisions_per_run=_optional_int(context, "max_checkpoint_revisions_per_run"),
            max_checkpoint_retries_per_stage=_optional_int(context, "max_checkpoint_retries_per_stage"),
            run_profile=_optional_text(context, "run_profile"),
            max_openrouter_calls_per_run=_optional_int(context, "max_openrouter_calls_per_run"),
            max_openrouter_planner_calls_per_run=_optional_int(context, "max_openrouter_planner_calls_per_run"),
            max_openrouter_web_task_calls_per_run=_optional_int(context, "max_openrouter_web_task_calls_per_run"),
            max_recall_expansion_openrouter_calls_per_run=_optional_int(
                context, "max_recall_expansion_openrouter_calls_per_run"
            ),
            max_openrouter_server_tool_web_searches_per_run=_optional_int(
                context, "max_openrouter_server_tool_web_searches_per_run"
            ),
            max_dadata_lookups_per_run=_optional_int(context, "max_dadata_lookups_per_run"),
            max_source_verification_requests_per_run=_optional_int(
                context, "max_source_verification_requests_per_run"
            ),
            max_provider_retries_per_task=_optional_int(context, "max_provider_retries_per_task"),
            openrouter_web_max_results_per_call=_optional_int(context, "openrouter_web_max_results_per_call"),
            openrouter_web_max_total_results_per_call=_optional_int(
                context, "openrouter_web_max_total_results_per_call"
            ),
            smoke_max_candidates=_optional_int(context, "smoke_max_candidates"),
            smoke_max_signals=_optional_int(context, "smoke_max_signals"),
            budget_reserve_limits=_optional_int_dict(context, "budget_reserve_limits"),
            semantic_task_reserve_limits=_optional_int_dict(context, "semantic_task_reserve_limits"),
            source_policy_decisions=_source_policy_decisions(discovery_plan),
            signal_execution_mode=_normalize_signal_execution_mode(context.get("signal_execution_mode")),
        )

    @classmethod
    def from_legacy_kwargs(
        cls,
        *,
        task_context: dict[str, Any] | None = None,
        max_web_tasks_per_subject: int | None = None,
        max_discovery_tasks_per_rule: int | None = None,
        max_gate_tasks_per_candidate_rule: int | None = None,
        max_signal_tasks_per_candidate_signal: int | None = None,
        max_total_web_tasks_per_run: int | None = None,
        min_useful_sources_per_discovery_task: int | None = None,
        min_candidates_per_discovery_task: int | None = None,
        max_discovery_retries_per_task: int | None = None,
        max_checkpoint_revisions_per_run: int | None = None,
        max_checkpoint_retries_per_stage: int | None = None,
        run_profile: str | None = None,
        max_openrouter_calls_per_run: int | None = None,
        max_openrouter_planner_calls_per_run: int | None = None,
        max_openrouter_web_task_calls_per_run: int | None = None,
        max_recall_expansion_openrouter_calls_per_run: int | None = None,
        max_openrouter_server_tool_web_searches_per_run: int | None = None,
        max_dadata_lookups_per_run: int | None = None,
        max_source_verification_requests_per_run: int | None = None,
        max_provider_retries_per_task: int | None = None,
        openrouter_web_max_results_per_call: int | None = None,
        openrouter_web_max_total_results_per_call: int | None = None,
        smoke_max_candidates: int | None = None,
        smoke_max_signals: int | None = None,
        budget_reserve_limits: dict[str, int] | None = None,
        semantic_task_reserve_limits: dict[str, int] | None = None,
        source_policy_decisions: list[dict[str, Any]] | None = None,
        signal_execution_mode: str | None = None,
    ) -> "CandidateDiscoveryExecutionOptions":
        return cls(
            task_context=dict(task_context or {}),
            max_web_tasks_per_subject=max_web_tasks_per_subject,
            max_discovery_tasks_per_rule=max_discovery_tasks_per_rule,
            max_gate_tasks_per_candidate_rule=max_gate_tasks_per_candidate_rule,
            max_signal_tasks_per_candidate_signal=max_signal_tasks_per_candidate_signal,
            max_total_web_tasks_per_run=max_total_web_tasks_per_run,
            min_useful_sources_per_discovery_task=min_useful_sources_per_discovery_task,
            min_candidates_per_discovery_task=min_candidates_per_discovery_task,
            max_discovery_retries_per_task=max_discovery_retries_per_task,
            max_checkpoint_revisions_per_run=max_checkpoint_revisions_per_run,
            max_checkpoint_retries_per_stage=max_checkpoint_retries_per_stage,
            run_profile=run_profile,
            max_openrouter_calls_per_run=max_openrouter_calls_per_run,
            max_openrouter_planner_calls_per_run=max_openrouter_planner_calls_per_run,
            max_openrouter_web_task_calls_per_run=max_openrouter_web_task_calls_per_run,
            max_recall_expansion_openrouter_calls_per_run=max_recall_expansion_openrouter_calls_per_run,
            max_openrouter_server_tool_web_searches_per_run=max_openrouter_server_tool_web_searches_per_run,
            max_dadata_lookups_per_run=max_dadata_lookups_per_run,
            max_source_verification_requests_per_run=max_source_verification_requests_per_run,
            max_provider_retries_per_task=max_provider_retries_per_task,
            openrouter_web_max_results_per_call=openrouter_web_max_results_per_call,
            openrouter_web_max_total_results_per_call=openrouter_web_max_total_results_per_call,
            smoke_max_candidates=smoke_max_candidates,
            smoke_max_signals=smoke_max_signals,
            budget_reserve_limits=budget_reserve_limits,
            semantic_task_reserve_limits=semantic_task_reserve_limits,
            source_policy_decisions=source_policy_decisions,
            signal_execution_mode=_normalize_signal_execution_mode(signal_execution_mode),
        )

    def apply_task_context(self, radar: dict[str, Any]) -> dict[str, Any]:
        if not self.task_context:
            return radar
        return {
            **radar,
            "task_context": {
                **(radar.get("task_context") if isinstance(radar.get("task_context"), dict) else {}),
                **self.task_context,
            },
        }

    def to_task_budget_settings(self) -> RadarExecutionBudgetSettings:
        return budget_settings_from_context(
            max_web_tasks_per_subject=self.max_web_tasks_per_subject,
            max_discovery_tasks_per_rule=self.max_discovery_tasks_per_rule,
            max_gate_tasks_per_candidate_rule=self.max_gate_tasks_per_candidate_rule,
            max_signal_tasks_per_candidate_signal=self.max_signal_tasks_per_candidate_signal,
            max_total_web_tasks_per_run=self.max_total_web_tasks_per_run,
            semantic_task_reserve_limits=self.semantic_task_reserve_limits,
        )

    def to_external_budget_settings(self) -> RadarExternalCallBudgetSettings:
        return external_budget_settings_from_context(self._external_budget_context())

    def to_useful_budget(self) -> UsefulResultBudget:
        return UsefulResultBudget(
            min_sources=self.min_useful_sources_per_discovery_task,
            min_candidates=self.min_candidates_per_discovery_task,
            max_retries=self.max_discovery_retries_per_task,
        )

    def checkpoint_policy_kwargs(self) -> dict[str, int]:
        return {
            "max_revisions_per_run": (
                2 if self.max_checkpoint_revisions_per_run is None else self.max_checkpoint_revisions_per_run
            ),
            "max_retries_per_stage": (
                1 if self.max_checkpoint_retries_per_stage is None else self.max_checkpoint_retries_per_stage
            ),
        }

    def _external_budget_context(self) -> dict[str, Any]:
        return {
            "run_profile": self.run_profile,
            "max_openrouter_calls_per_run": self.max_openrouter_calls_per_run,
            "max_openrouter_planner_calls_per_run": self.max_openrouter_planner_calls_per_run,
            "max_openrouter_web_task_calls_per_run": self.max_openrouter_web_task_calls_per_run,
            "max_recall_expansion_openrouter_calls_per_run": self.max_recall_expansion_openrouter_calls_per_run,
            "max_openrouter_server_tool_web_searches_per_run": self.max_openrouter_server_tool_web_searches_per_run,
            "max_dadata_lookups_per_run": self.max_dadata_lookups_per_run,
            "max_source_verification_requests_per_run": self.max_source_verification_requests_per_run,
            "max_provider_retries_per_task": self.max_provider_retries_per_task,
            "openrouter_web_max_results_per_call": self.openrouter_web_max_results_per_call,
            "openrouter_web_max_total_results_per_call": self.openrouter_web_max_total_results_per_call,
            "smoke_max_candidates": self.smoke_max_candidates,
            "smoke_max_signals": self.smoke_max_signals,
            "budget_reserve_limits": self.budget_reserve_limits,
        }


def _optional_int(context: Mapping[str, Any], key: str) -> int | None:
    value = context.get(key)
    if isinstance(value, bool):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _optional_int_dict(context: Mapping[str, Any], key: str) -> dict[str, int] | None:
    value = context.get(key)
    if not isinstance(value, dict):
        return None
    result: dict[str, int] = {}
    for raw_key, raw_value in value.items():
        if not isinstance(raw_key, str) or isinstance(raw_value, bool):
            continue
        try:
            parsed = int(raw_value)
        except (TypeError, ValueError):
            continue
        if parsed >= 0:
            result[raw_key] = parsed
    return result or None


def _optional_text(context: Mapping[str, Any], key: str) -> str | None:
    value = context.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _source_policy_decisions(discovery_plan: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if discovery_plan is None:
        return []
    decisions = discovery_plan.get("source_policy_decisions", [])
    if not isinstance(decisions, list):
        return []
    return [dict(item) for item in decisions if isinstance(item, dict)]
