"""Typed task-context access for live Radar execution options."""

from __future__ import annotations

from typing import Any, Mapping


class LiveRadarTaskContextReader:
    """Reads provider-neutral live Radar execution options from task context."""

    _INT_EXECUTION_OPTION_KEYS = (
        "max_web_tasks_per_subject",
        "max_discovery_tasks_per_rule",
        "max_gate_tasks_per_candidate_rule",
        "max_signal_tasks_per_candidate_signal",
        "max_total_web_tasks_per_run",
        "min_useful_sources_per_discovery_task",
        "min_candidates_per_discovery_task",
        "max_discovery_retries_per_task",
        "max_checkpoint_revisions_per_run",
        "max_checkpoint_retries_per_stage",
        "max_openrouter_calls_per_run",
        "max_openrouter_planner_calls_per_run",
        "max_openrouter_web_task_calls_per_run",
        "max_recall_expansion_openrouter_calls_per_run",
        "max_openrouter_server_tool_web_searches_per_run",
        "max_dadata_lookups_per_run",
        "max_source_verification_requests_per_run",
        "max_provider_retries_per_task",
        "openrouter_web_max_results_per_call",
        "openrouter_web_max_total_results_per_call",
        "smoke_max_candidates",
        "smoke_max_signals",
    )
    _DICT_INT_EXECUTION_OPTION_KEYS = (
        "budget_reserve_limits",
        "semantic_task_reserve_limits",
    )
    _TEXT_EXECUTION_OPTION_KEYS = ("run_profile",)

    def __init__(self, context: Mapping[str, Any]) -> None:
        self._context = context

    def staged_execution_options(self, discovery_plan: Mapping[str, Any] | None) -> dict[str, Any]:
        options: dict[str, Any] = {key: self.optional_int(key) for key in self._INT_EXECUTION_OPTION_KEYS}
        options.update({key: self.optional_int_dict(key) for key in self._DICT_INT_EXECUTION_OPTION_KEYS})
        options.update({key: self.optional_text(key) for key in self._TEXT_EXECUTION_OPTION_KEYS})
        options["source_policy_decisions"] = self._source_policy_decisions(discovery_plan)
        return options

    def optional_int(self, key: str) -> int | None:
        value = self._context.get(key)
        if isinstance(value, bool):
            return None
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return None
        return parsed if parsed >= 0 else None

    def optional_int_dict(self, key: str) -> dict[str, int] | None:
        value = self._context.get(key)
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

    def optional_text(self, key: str) -> str | None:
        value = self._context.get(key)
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _source_policy_decisions(self, discovery_plan: Mapping[str, Any] | None) -> list[dict[str, Any]]:
        if discovery_plan is None:
            return []
        decisions = discovery_plan.get("source_policy_decisions", [])
        if not isinstance(decisions, list):
            return []
        return [dict(item) for item in decisions if isinstance(item, dict)]
