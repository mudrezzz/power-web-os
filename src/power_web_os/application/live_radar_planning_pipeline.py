"""Build accepted discovery and execution plans for a live Radar run."""

from __future__ import annotations

from typing import Any

from power_web_os.application.live_radar_contracts import (
    LiveICPRadarRunState,
    LiveRadarPipelineEvent,
    RadarDiscoveryPlanner,
)
from power_web_os.application.live_radar_definition import build_live_mini_radar_definition
from power_web_os.application.live_radar_discovery_planning import (
    RadarDiscoveryPlanValidator,
    build_discovery_planning_input,
    discovery_plan_to_execution_plan,
)
from power_web_os.application.live_radar_execution_plan import execution_plan_to_search_plan
from power_web_os.application.live_radar_pipeline_support import planned_event_type, trace_pipeline_step


def build_planned_state(
    *,
    state: LiveICPRadarRunState,
    planner: RadarDiscoveryPlanner,
) -> LiveICPRadarRunState:
    trace_pipeline_step(
        state, "planning", "build_search_plan", "pipeline_input", "Build search plan input",
        payload={"task_context": state.task_context, "has_existing_radar": state.radar is not None},
    )
    radar = state.radar or build_live_mini_radar_definition()
    planning_input = build_discovery_planning_input(
        radar=radar,
        task_context=state.task_context,
        live=state.live,
        provider_metadata=state.provider_metadata,
    )
    trace_pipeline_step(
        state, "planning", "discovery_planner", "pipeline_input", "Discovery planner input",
        payload={"planning_input": planning_input.model_dump()},
    )
    validator = RadarDiscoveryPlanValidator()
    events: list[LiveRadarPipelineEvent] = [
        LiveRadarPipelineEvent(
            event_type="discovery_plan_requested",
            phase="planning",
            actor="application",
            node_name="discovery_planner",
            visibility="operator",
            summary=f"Discovery plan requested for {planning_input.radar_id}.",
            payload={"max_steps": planning_input.max_steps, "max_iterations": planning_input.max_iterations},
        )
    ]

    plan = planner.propose_plan(planning_input=planning_input)
    validation = validator.validate(planning_input=planning_input, plan=plan)
    events.extend(_plan_events(plan, validation=validation, revised=False))
    if not validation.accepted and planning_input.max_iterations > 1:
        events.append(LiveRadarPipelineEvent(
            event_type="discovery_plan_revised",
            phase="planning",
            actor="application",
            node_name="discovery_planner",
            visibility="operator",
            summary="Discovery plan failed validation; requesting one revised plan.",
            payload=validation.model_dump(),
        ))
        plan = planner.propose_plan(planning_input=planning_input, previous_validation=validation)
        validation = validator.validate(planning_input=planning_input, plan=plan)
        events.extend(_plan_events(plan, validation=validation, revised=True))

    trace_pipeline_step(
        state, "planning", "discovery_planner", "validation_result", "Discovery plan validation",
        summary="Discovery plan validation completed.",
        payload={"plan": plan.model_dump(), "validation": validation.model_dump()},
    )
    if not validation.accepted:
        raise RuntimeError(f"Discovery plan validation failed: {'; '.join(validation.errors)}")

    execution_plan = discovery_plan_to_execution_plan(radar=radar, plan=plan)
    search_plan = execution_plan_to_search_plan(execution_plan)
    events.extend([
        LiveRadarPipelineEvent(
            event_type="plan_created",
            phase="planning",
            actor="workflow",
            node_name="build_search_plan",
            summary=f"LLM-planned discovery strategy accepted with {len(plan.steps)} discovery steps and {len(execution_plan.tasks)} execution tasks.",
            payload={
                "query_count": len(search_plan.queries),
                "task_count": len(execution_plan.tasks),
                "radar_id": search_plan.radar_id,
                "discovery_plan": plan.model_dump(),
                "execution_plan": execution_plan.model_dump(),
            },
        ),
        *[
            LiveRadarPipelineEvent(
                event_type=planned_event_type(query.stage),
                phase="planning",
                actor="workflow",
                node_name=query.query_id,
                summary=query.query,
                payload={
                    "stage": query.stage,
                    "subject_type": query.subject_type,
                    "subject_id": query.subject_id,
                    "purpose": query.purpose,
                    "expected_evidence": list(query.expected_evidence),
                    "depends_on": list(query.depends_on),
                },
            )
            for query in search_plan.queries
        ],
    ])
    next_state = state.model_copy(update={
        "radar": radar,
        "search_plan": search_plan.model_dump(),
        "discovery_plan": plan.model_dump(),
        "execution_plan": execution_plan.model_dump(),
        "pipeline_events": [*state.pipeline_events, *[event.model_dump() for event in events]],
    })
    trace_pipeline_step(
        next_state, "planning", "build_search_plan", "pipeline_output", "Build search plan output",
        summary=f"Built {len(execution_plan.tasks)} execution tasks from discovery plan.",
        payload={
            "radar_id": search_plan.radar_id,
            "discovery_plan": plan.model_dump(),
            "execution_plan": execution_plan.model_dump(),
            "queries": [query.model_dump() for query in search_plan.queries],
        },
    )
    return next_state


def _plan_events(plan, *, validation, revised: bool) -> list[LiveRadarPipelineEvent]:
    prefix = "Revised discovery plan" if revised else "Discovery plan"
    events = [
        LiveRadarPipelineEvent(
            event_type="discovery_plan_created",
            phase="planning",
            actor="planner",
            node_name="discovery_planner",
            visibility="operator",
            summary=f"{prefix} created with {len(plan.steps)} steps.",
            payload=plan.model_dump(),
        ),
        LiveRadarPipelineEvent(
            event_type="discovery_plan_validated",
            phase="planning",
            actor="validator",
            node_name="discovery_plan_validator",
            visibility="operator",
            summary="Discovery plan accepted." if validation.accepted else "Discovery plan validation failed.",
            payload=validation.model_dump(),
        ),
    ]
    for decision in plan.source_policy_decisions:
        events.append(LiveRadarPipelineEvent(
            event_type="source_base_selected" if decision.decision == "selected" else "source_base_skipped",
            phase="planning",
            actor="planner",
            node_name="discovery_planner",
            visibility="operator",
            summary=f"{decision.source_label or decision.source_id}: {decision.reason}",
            payload=decision.model_dump(),
        ))
    for warning in [*plan.warnings, *validation.warnings]:
        events.append(LiveRadarPipelineEvent(
            event_type="coverage_warning",
            phase="planning",
            actor="validator",
            node_name="discovery_plan_validator",
            visibility="operator",
            summary=warning,
            payload={},
        ))
    return events
