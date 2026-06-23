"""Summary helpers for Radar run dossier API projection."""

from __future__ import annotations

from typing import Any


def coverage_summary(discovery_plan: dict[str, Any], execution_results: dict[str, Any]) -> dict[str, Any]:
    hypotheses = _list(discovery_plan.get("coverage_hypotheses"))
    warnings = [str(value) for value in discovery_plan.get("warnings", []) if isinstance(value, str) and value.strip()]
    analyzed_sources = _list(execution_results.get("analyzed_sources"))
    rejected_candidates = _list(execution_results.get("rejected_candidates"))
    coverage_checks = _list(execution_results.get("coverage_checks"))
    coverage_warnings = [str(value) for value in execution_results.get("coverage_warnings", []) if isinstance(value, str)]
    unresolved_candidate_gaps = _list(execution_results.get("unresolved_candidate_gaps"))
    entity_resolution_results = _list(execution_results.get("entity_resolution_results"))
    linked_entity_facts = _list(execution_results.get("linked_entity_facts"))
    return {
        "hypotheses": hypotheses,
        "warnings": [*warnings, *coverage_warnings],
        "analyzed_source_count": _int(execution_results.get("analyzed_source_count"), default=len(analyzed_sources)),
        "used_source_count": _int(execution_results.get("used_source_count"), default=0),
        "rejected_candidate_count": len(rejected_candidates),
        "coverage_check_count": len(coverage_checks),
        "unresolved_candidate_gap_count": len(unresolved_candidate_gaps),
        "entity_resolution_count": len(entity_resolution_results),
        "linked_entity_fact_count": len(linked_entity_facts),
        "discovery_iteration_count": _int(execution_results.get("discovery_iteration_count"), default=0),
        "analyzed_source_reasons": sorted({
            str(item.get("reason"))
            for item in analyzed_sources
            if str(item.get("reason", "")).strip()
        }),
    }


def budget_summary(execution_results: dict[str, Any]) -> dict[str, Any]:
    counters = _dict(execution_results.get("budget_counters"))
    settings = _dict(execution_results.get("budget_settings"))
    exhaustion_events = _list(execution_results.get("budget_exhaustion_events"))
    signal_statuses = _list(execution_results.get("signal_search_statuses"))
    return {
        "settings": settings,
        "counters": counters,
        "exhausted_count": len(exhaustion_events),
        "signal_searched_count": sum(1 for item in signal_statuses if str(item.get("search_status")) == "searched"),
        "signal_not_searched_count": sum(1 for item in signal_statuses if str(item.get("search_status", "")).startswith("not_searched")),
        "not_searched_reasons": sorted({
            str(item.get("not_searched_reason"))
            for item in signal_statuses
            if str(item.get("not_searched_reason", "")).strip()
        }),
    }


def _list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _dict(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _int(value: object, *, default: int) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else default
