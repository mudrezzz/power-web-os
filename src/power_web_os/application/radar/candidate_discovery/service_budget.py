"""Budget metadata projection services for live Radar runs."""

from __future__ import annotations

from typing import Any


class ExternalBudgetMetadataMerger:
    """Merges planner-node and staged-execution external-call budget snapshots."""

    _COUNTER_KEYS = (
        "external_call_budget_counters",
        "external_call_budget_counters_by_role",
        "budget_reserve_counters",
    )
    _LIST_KEYS = (
        "external_call_budget_exhaustion_events",
        "provider_retry_records",
        "post_call_budget_overruns",
        "budget_reserve_exhaustion_events",
    )

    def merge(self, base: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
        if not base:
            return dict(current)
        merged = dict(current)
        for key in self._COUNTER_KEYS:
            merged[key] = self._merge_counter_dicts(base.get(key), current.get(key))
        for key in self._LIST_KEYS:
            merged[key] = [*self._list_payload(base.get(key)), *self._list_payload(current.get(key))]
        server_usage = dict(current.get("openrouter_server_tool_usage") or {})
        if not server_usage:
            server_usage = dict(base.get("openrouter_server_tool_usage") or {})
        if server_usage:
            server_usage["web_search_requests"] = merged.get("external_call_budget_counters", {}).get(
                "openrouter_server_tool_web_search:run",
                server_usage.get("web_search_requests", 0),
            )
            merged["openrouter_server_tool_usage"] = server_usage
        if "external_call_budget_settings" not in merged and base.get("external_call_budget_settings"):
            merged["external_call_budget_settings"] = base["external_call_budget_settings"]
        if "run_profile" not in merged and base.get("run_profile"):
            merged["run_profile"] = base["run_profile"]
        return merged

    def _merge_counter_dicts(self, left: Any, right: Any) -> dict[str, int]:
        result: dict[str, int] = {}
        for payload in (left, right):
            if not isinstance(payload, dict):
                continue
            for key, value in payload.items():
                try:
                    parsed = int(value)
                except (TypeError, ValueError):
                    continue
                result[str(key)] = result.get(str(key), 0) + parsed
        return result

    def _list_payload(self, value: Any) -> list[Any]:
        return list(value) if isinstance(value, list) else []
