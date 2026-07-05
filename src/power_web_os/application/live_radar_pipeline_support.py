"""Small shared helpers for the live Radar application pipeline."""

from __future__ import annotations

from typing import Any

from power_web_os.application.radar.candidate_discovery.contracts import LiveICPRadarRunState, LiveRadarCandidate
from power_web_os.application.radar_technical_trace import RadarRunTechnicalTraceCommand, append_current_trace


def planned_event_type(stage: str | None) -> str:
    if stage == "qualification_discovery":
        return "qualification_discovery_planned"
    if stage == "qualification_gate":
        return "qualification_gate_applied"
    if stage == "signal_search":
        return "signal_search_planned"
    return "search_query_planned"


def candidate_rejected(candidate: LiveRadarCandidate) -> bool:
    return any(item.requirement_level == "required" and item.final_assessment == "does_not_match" for item in candidate.qualification)


def rejected_candidate_payload(candidate: LiveRadarCandidate) -> dict[str, Any]:
    return {
        "candidate_id": candidate.candidate_id,
        "legal_name": candidate.legal_name,
        "failed_rules": [
            item.criterion_code
            for item in candidate.qualification
            if item.requirement_level == "required" and item.final_assessment == "does_not_match"
        ],
    }


def trace_pipeline_step(
    state: LiveICPRadarRunState,
    phase: str,
    node_name: str,
    trace_type: str,
    title: str,
    payload: dict[str, Any],
    summary: str = "",
) -> None:
    run_id = state.task_context.get("run_id")
    if not run_id:
        return
    append_current_trace(
        RadarRunTechnicalTraceCommand(
            run_id=str(run_id),
            phase=phase,
            node_name=node_name,
            trace_type=trace_type,
            title=title,
            summary=summary,
            payload=payload,
        )
    )
