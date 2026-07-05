"""Build accepted discovery and execution plans for a live Radar run."""

from __future__ import annotations

from typing import Any

from power_web_os.application.connector_profiles import ConnectorProfileRegistry
from power_web_os.application.radar.candidate_discovery.contracts import (
    LiveICPRadarRunState,
    LiveRadarPipelineEvent,
    RadarDiscoveryPlanner,
)
from power_web_os.application.radar.candidate_discovery.retrieval.definition import build_live_mini_radar_definition
from power_web_os.application.radar.candidate_discovery.planning.discovery_planning import (
    DeterministicRadarDiscoveryPlanner,
    RadarDiscoveryPlanValidator,
    build_discovery_planning_input,
    discovery_plan_to_execution_plan,
)
from power_web_os.application.radar.candidate_discovery.planning.execution_plan import execution_plan_to_search_plan
from power_web_os.application.radar.candidate_discovery.planning.plan_acceptance import RadarDiscoveryPlanAcceptanceService
from power_web_os.application.live_radar_pipeline_support import planned_event_type, trace_pipeline_step


def build_planned_state(
    *,
    state: LiveICPRadarRunState,
    planner: RadarDiscoveryPlanner,
    connector_profile_registry: ConnectorProfileRegistry | None = None,
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
        connector_profile_registry=connector_profile_registry,
    )
    trace_pipeline_step(
        state, "planning", "discovery_planner", "pipeline_input", "Discovery planner input",
        payload={"planning_input": planning_input.model_dump()},
    )
    acceptance_service = RadarDiscoveryPlanAcceptanceService(RadarDiscoveryPlanValidator())
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
    acceptance = acceptance_service.accept(planning_input=planning_input, plan=plan)
    validation = acceptance.validation
    accepted_plan = acceptance.accepted_plan
    events.extend(_plan_events(plan, accepted_plan=accepted_plan, validation=validation, revised=False))
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
        acceptance = acceptance_service.accept(planning_input=planning_input, plan=plan)
        validation = acceptance.validation
        accepted_plan = acceptance.accepted_plan
        events.extend(_plan_events(plan, accepted_plan=accepted_plan, validation=validation, revised=True))

    trace_pipeline_step(
        state, "planning", "discovery_planner", "validation_result", "Discovery plan validation",
        summary="Discovery plan validation completed.",
        payload={
            "original_plan": plan.model_dump(),
            "accepted_plan": accepted_plan.model_dump(),
            "validation": validation.model_dump(),
            "corrections": acceptance.corrections,
        },
    )
    if not validation.accepted:
        fallback_planner = DeterministicRadarDiscoveryPlanner()
        fallback_plan = fallback_planner.propose_plan(planning_input=planning_input)
        fallback_acceptance = acceptance_service.accept(planning_input=planning_input, plan=fallback_plan, fallback_used=True)
        fallback_plan = fallback_acceptance.accepted_plan
        fallback_validation = fallback_acceptance.validation
        events.append(LiveRadarPipelineEvent(
            event_type="discovery_plan_fallback_used",
            phase="planning",
            actor="application",
            node_name="discovery_plan_validator",
            visibility="operator",
            summary="LLM discovery plan stayed invalid; backend deterministic fallback plan will be used.",
            payload={
                "llm_validation": validation.model_dump(),
                "fallback_validation": fallback_validation.model_dump(),
                "fallback_corrections": fallback_acceptance.corrections,
            },
        ))
        trace_pipeline_step(
            state,
            "planning",
            "discovery_plan_validator",
            "validation_result",
            "Discovery plan fallback",
            summary="LLM discovery plan stayed invalid; backend deterministic fallback plan will be used.",
            payload={
                "invalid_plan": plan.model_dump(),
                "invalid_accepted_plan": accepted_plan.model_dump(),
                "validation": validation.model_dump(),
                "fallback_plan": fallback_plan.model_dump(),
                "fallback_validation": fallback_validation.model_dump(),
            },
        )
        plan = fallback_plan
        validation = fallback_validation
        acceptance = fallback_acceptance
        accepted_plan = fallback_plan
    if not validation.accepted:
        raise RuntimeError(f"Discovery plan validation failed: {'; '.join(validation.errors)}")

    plan = accepted_plan
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


def _plan_events(plan, *, accepted_plan, validation, revised: bool) -> list[LiveRadarPipelineEvent]:
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
    events.insert(1, LiveRadarPipelineEvent(
        event_type="criterion_roles_inferred",
        phase="planning",
        actor="validator",
        node_name="discovery_plan_acceptance",
        visibility="operator",
        summary=f"{len(accepted_plan.criterion_role_decisions)} qualification criterion roles are available for execution planning.",
        payload={"criterion_role_decisions": [item.model_dump() for item in accepted_plan.criterion_role_decisions]},
    ))
    for correction in validation.corrections:
        correction_type = str(correction.get("type") or "discovery_plan_corrected")
        if correction_type in {"source_capability_matched", "source_capability_rejected", "source_use_projected"}:
            event_type = correction_type
        elif correction_type == "source_scope_corrected":
            event_type = "source_scope_corrected"
        else:
            event_type = "discovery_plan_corrected"
        events.append(LiveRadarPipelineEvent(
            event_type=event_type,
            phase="planning",
            actor="validator",
            node_name="discovery_plan_acceptance",
            visibility="operator",
            summary=str(correction.get("reason") or correction_type),
            payload=correction,
        ))
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
