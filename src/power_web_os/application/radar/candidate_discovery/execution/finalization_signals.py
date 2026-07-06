"""Signal handoff metadata helpers for candidate-discovery finalization."""

from __future__ import annotations

from power_web_os.application.radar.candidate_discovery.execution.context import CandidateDiscoveryExecutionContext
from power_web_os.application.radar.candidate_discovery.execution.state import CandidateDiscoveryExecutionState


def _signal_projection_observations(
    context: CandidateDiscoveryExecutionContext,
    state: CandidateDiscoveryExecutionState,
    observations: list[dict],
) -> list[dict]:
    if context.signal_execution_mode == "inline_compatibility":
        return observations
    decision = _signal_handoff_decision(state)
    if not decision:
        return observations
    return [_observation_with_unsearched_signals(item, decision) for item in observations]


def _signal_monitoring_pending_count(state: CandidateDiscoveryExecutionState) -> int:
    return sum(
        1
        for item in state.signal_search_statuses
        if item.get("search_status") == "not_searched_pending_signal_monitoring"
    )


def _signal_handoff_status(
    context: CandidateDiscoveryExecutionContext,
    state: CandidateDiscoveryExecutionState,
) -> str:
    if context.signal_execution_mode == "inline_compatibility":
        return "inline_compatibility"
    if _signal_monitoring_pending_count(state) > 0:
        return "pending_signal_monitoring"
    if state.stopped_for_review_reason:
        return "blocked_before_signal_monitoring"
    return "not_applicable"


def _signal_handoff_decision(state: CandidateDiscoveryExecutionState) -> dict[str, str]:
    for item in state.signal_search_statuses:
        search_status = str(item.get("search_status") or "")
        if search_status.startswith("not_searched"):
            return {
                "search_status": search_status,
                "not_searched_reason": str(item.get("not_searched_reason") or "pending_signal_monitoring"),
                "message": str(item.get("message") or "Signal monitoring is pending a separate signal-monitoring run."),
            }
    return {}


def _observation_with_unsearched_signals(item: dict, decision: dict[str, str]) -> dict:
    signals = item.get("signals")
    if not isinstance(signals, list):
        return item
    projected = dict(item)
    projected["signals"] = [_signal_with_unsearched_status(signal, decision) for signal in signals]
    return projected


def _signal_with_unsearched_status(signal: object, decision: dict[str, str]) -> object:
    if not isinstance(signal, dict):
        return signal
    search_status = str(signal.get("search_status") or "")
    if search_status.startswith("not_searched"):
        return signal
    projected = dict(signal)
    projected["status"] = "unclear"
    projected["score"] = 0
    projected["search_status"] = decision["search_status"]
    projected["not_searched_reason"] = decision["not_searched_reason"]
    projected["summary"] = decision["message"]
    review_flags = [str(item) for item in projected.get("review_flags", []) if str(item).strip()]
    projected["review_flags"] = sorted({*review_flags, decision["search_status"]})
    return projected
