"""Application service for one live Radar execution pass.

The service owns provider-neutral orchestration: build a plan, call a provider
port, normalize observations, validate contracts, and shape the live run artifact.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from power_web_os.application.live_radar_contracts import (
    LiveRadarCollectionResult,
    LiveRadarEvaluationResult,
    LiveRadarExtractionResult,
    LiveICPRadarRunState,
    LiveRadarPipelineEvent,
    LiveRadarPlanningResult,
    RadarExecutionPlan,
    LiveRadarRunArtifact,
    LiveRadarValidationResult,
    RadarSearchPlan,
    RadarSourceEvidence,
    WebSearchProvider,
)
from power_web_os.application.live_radar_definition import build_live_mini_radar_definition, build_live_mini_radar_search_plan
from power_web_os.application.live_radar_execution_plan import (
    compile_radar_execution_plan,
    execution_plan_to_search_plan,
)
from power_web_os.application.live_radar_normalization import (
    _dedupe_sources,
    _rank_candidates,
    normalize_live_candidate,
    validate_live_radar_qualification_contract,
)
from power_web_os.application.live_radar_pipeline_support import (
    candidate_rejected as _candidate_rejected,
    planned_event_type as _planned_event_type,
    rejected_candidate_payload as _rejected_candidate_payload,
    trace_pipeline_step as _trace,
)
from power_web_os.application.live_radar_staged_execution import run_staged_radar_execution


class LiveRadarRunService:
    """Provider-neutral planner/executor/evaluator pipeline for live Radar."""

    def __init__(self, provider: WebSearchProvider) -> None:
        self._provider = provider

    def run(
        self,
        *,
        state: LiveICPRadarRunState,
        node_name: str,
        runtime_mode: str,
        framework_available: bool,
    ) -> LiveICPRadarRunState:
        for step in [
            self.build_search_plan,
            self.run_web_search,
            self.normalize_sources,
            self.extract_candidates,
            self.evaluate_candidates,
            self.validate_artifact,
        ]:
            state = step(state)
        return self.shape_artifact(
            state=state,
            node_name=node_name,
            runtime_mode=runtime_mode,
            framework_available=framework_available,
        )

    def build_search_plan(self, state: LiveICPRadarRunState) -> LiveICPRadarRunState:
        _trace(
            state, "planning", "build_search_plan", "pipeline_input", "Build search plan input",
            payload={"task_context": state.task_context, "has_existing_radar": state.radar is not None},
        )
        radar = state.radar or build_live_mini_radar_definition()
        execution_plan = compile_radar_execution_plan(radar)
        plan = execution_plan_to_search_plan(execution_plan)
        result = LiveRadarPlanningResult(
            radar=radar,
            search_plan=plan,
            events=[
                LiveRadarPipelineEvent(
                    event_type="plan_created",
                    phase="planning",
                    actor="workflow",
                    node_name="build_search_plan",
                    summary=f"Qualification-first Radar plan prepared with {len(execution_plan.tasks)} tasks.",
                    payload={
                        "query_count": len(plan.queries),
                        "task_count": len(execution_plan.tasks),
                        "radar_id": plan.radar_id,
                        "execution_plan": execution_plan.model_dump(),
                    },
                ),
                *[
                    LiveRadarPipelineEvent(
                        event_type=_planned_event_type(query.stage),
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
                    for query in plan.queries
                ],
            ],
        )
        next_state = state.model_copy(update={
            "radar": result.radar,
            "search_plan": result.search_plan.model_dump(),
            "execution_plan": execution_plan.model_dump(),
            "pipeline_events": _append_events(state, result.events),
        })
        _trace(
            next_state, "planning", "build_search_plan", "pipeline_output", "Build search plan output",
            summary=f"Built {len(execution_plan.tasks)} staged search tasks.",
            payload={
                "radar_id": plan.radar_id,
                "execution_plan": execution_plan.model_dump(),
                "queries": [query.model_dump() for query in plan.queries],
            },
        )
        return next_state

    def run_web_search(self, state: LiveICPRadarRunState) -> LiveICPRadarRunState:
        radar = state.radar or build_live_mini_radar_definition()
        execution_plan = RadarExecutionPlan.model_validate(state.execution_plan or compile_radar_execution_plan(radar))
        plan = execution_plan_to_search_plan(execution_plan)
        _trace(
            state, "collection", "run_web_search", "pipeline_input", "Web search input",
            payload={"radar_id": plan.radar_id, "execution_plan": execution_plan.model_dump()},
        )
        provider_result, task_events, execution_results = run_staged_radar_execution(
            radar=radar,
            execution_plan=execution_plan,
            provider=self._provider,
        )
        result = LiveRadarCollectionResult(
            sources=provider_result.sources,
            candidate_observations=provider_result.candidate_observations,
            provider_metadata=provider_result.provider_metadata,
            events=[
                *task_events,
                LiveRadarPipelineEvent(
                    event_type="source_collected",
                    phase="collection",
                    actor="provider",
                    node_name="run_web_search",
                    visibility="operator",
                    summary=f"Provider returned {len(provider_result.sources)} sources across {execution_results['executed_task_count']} staged tasks.",
                    payload={
                        "source_count": len(provider_result.sources),
                        "candidate_observation_count": len(provider_result.candidate_observations),
                        "executed_task_count": execution_results["executed_task_count"],
                        "provider": str(provider_result.provider_metadata.get("provider", "")),
                        "model": str(provider_result.provider_metadata.get("model", "")),
                        "web_mode": str(provider_result.provider_metadata.get("web_mode", "")),
                    },
                    source_refs=[source.evidence_ref for source in provider_result.sources if source.evidence_ref],
                )
            ],
        )
        next_state = state.model_copy(update={
            "sources": [item.model_dump() for item in result.sources],
            "candidate_observations": [dict(item) for item in result.candidate_observations],
            "provider_metadata": dict(result.provider_metadata),
            "execution_results": execution_results,
            "pipeline_events": _append_events(state, result.events),
        })
        _trace(
            next_state, "collection", "run_web_search", "pipeline_output", "Web search output",
            summary=f"Provider returned {len(result.sources)} sources from qualification-first execution.",
            payload={
                "provider_metadata": dict(result.provider_metadata),
                "source_count": len(result.sources),
                "candidate_observation_count": len(result.candidate_observations),
                "execution_results": execution_results,
                "source_refs": [source.evidence_ref for source in result.sources],
            },
        )
        return next_state

    def normalize_sources(self, state: LiveICPRadarRunState) -> LiveICPRadarRunState:
        _trace(
            state, "normalization", "normalize_sources", "pipeline_input", "Source normalization input",
            payload={"source_count": len(state.sources)},
        )
        sources = _dedupe_sources([RadarSourceEvidence.model_validate(item) for item in state.sources])
        result = LiveRadarExtractionResult(
            sources=sources,
            candidates=[],
            events=[
                LiveRadarPipelineEvent(
                    event_type="source_collected",
                    phase="collection",
                    actor="workflow",
                    node_name="normalize_sources",
                    summary=f"Normalized {len(sources)} unique sources.",
                    payload={"source_count": len(sources)},
                    source_refs=[source.evidence_ref for source in sources if source.evidence_ref],
                )
            ],
        )
        next_state = state.model_copy(update={
            "sources": [item.model_dump() for item in result.sources],
            "pipeline_events": _append_events(state, result.events),
        })
        _trace(
            next_state, "normalization", "normalize_sources", "normalization_result", "Source normalization result",
            summary=f"Normalized {len(sources)} unique sources.",
            payload={"source_count": len(sources), "source_refs": [source.evidence_ref for source in sources]},
        )
        return next_state

    def extract_candidates(self, state: LiveICPRadarRunState) -> LiveICPRadarRunState:
        radar = state.radar or build_live_mini_radar_definition()
        sources = [RadarSourceEvidence.model_validate(item) for item in state.sources]
        _trace(
            state, "extraction", "extract_candidates", "pipeline_input", "Candidate extraction input",
            payload={
                "candidate_observation_count": len(state.candidate_observations),
                "source_count": len(sources),
            },
        )
        candidates = _rank_candidates([
            normalize_live_candidate(item, radar=radar, sources=sources)
            for item in state.candidate_observations
        ])
        visible_candidates = [candidate for candidate in candidates if not _candidate_rejected(candidate)]
        rejected_candidates = [_rejected_candidate_payload(candidate) for candidate in candidates if _candidate_rejected(candidate)]
        result = LiveRadarExtractionResult(
            sources=sources,
            candidates=visible_candidates,
            events=[
                LiveRadarPipelineEvent(
                    event_type="candidate_extracted",
                    phase="extraction",
                    actor="workflow",
                    node_name="extract_candidates",
                    summary=f"Extracted {len(visible_candidates)} visible candidates and filtered {len(rejected_candidates)} rejected candidates.",
                    payload={"candidate_count": len(visible_candidates), "rejected_candidate_count": len(rejected_candidates)},
                    candidate_refs=[candidate.candidate_id for candidate in visible_candidates],
                )
            ],
        )
        execution_results = {
            **state.execution_results,
            "rejected_candidates": rejected_candidates or state.execution_results.get("rejected_candidates", []),
        }
        next_state = state.model_copy(update={
            "candidates": [item.model_dump() for item in result.candidates],
            "execution_results": execution_results,
            "pipeline_events": _append_events(state, result.events),
        })
        _trace(
            next_state, "extraction", "extract_candidates", "normalization_result", "Candidate extraction result",
            summary=f"Extracted {len(candidates)} normalized candidates.",
            payload={
                "candidate_count": len(visible_candidates),
                "rejected_candidate_count": len(rejected_candidates),
                "candidates": [
                    {"candidate_id": item.candidate_id, "legal_name": item.legal_name, "evidence_refs": list(item.evidence_refs)}
                    for item in visible_candidates
                ],
                "rejected_candidates": rejected_candidates,
            },
        )
        return next_state

    def evaluate_candidates(self, state: LiveICPRadarRunState) -> LiveICPRadarRunState:
        _trace(
            state, "evaluation", "evaluate_candidates", "pipeline_input", "Candidate evaluation input",
            payload={"candidate_count": len(state.candidates), "source_count": len(state.sources)},
        )
        candidates = [
            normalize_live_candidate(item, radar=state.radar or build_live_mini_radar_definition(), sources=[
                RadarSourceEvidence.model_validate(source)
                for source in state.sources
            ])
            for item in state.candidates
        ]
        result = LiveRadarEvaluationResult(
            candidates=candidates,
            events=[
                *[
                    LiveRadarPipelineEvent(
                        event_type="signal_evaluated",
                        phase="evaluation",
                        actor="workflow",
                        node_name="evaluate_candidates",
                        summary=f"Evaluated {candidate.legal_name}: {candidate.score.tier}.",
                        payload={
                            "fit_score": candidate.score.fit_score,
                            "intent_score": candidate.score.intent_score,
                            "tier": candidate.score.tier,
                            "qualification_count": len(candidate.qualification),
                            "signal_count": len(candidate.signals),
                            "review_flags": list(candidate.review_flags),
                        },
                        source_refs=list(candidate.evidence_refs),
                        candidate_refs=[candidate.candidate_id],
                    )
                    for candidate in candidates
                ],
                *[
                    LiveRadarPipelineEvent(
                        event_type="score_explained",
                        phase="evaluation",
                        actor="workflow",
                        node_name="evaluate_candidates",
                        summary=f"Candidate scored as {candidate.score.tier}.",
                        payload=candidate.score.model_dump(),
                        candidate_refs=[candidate.candidate_id],
                    )
                    for candidate in candidates
                ],
            ],
        )
        next_state = state.model_copy(update={
            "candidates": [item.model_dump() for item in result.candidates],
            "pipeline_events": _append_events(state, result.events),
        })
        _trace(
            next_state, "evaluation", "evaluate_candidates", "pipeline_output", "Candidate evaluation output",
            summary=f"Evaluated {len(candidates)} candidates.",
            payload={
                "candidates": [
                    {
                        "candidate_id": item.candidate_id,
                        "tier": item.score.tier,
                        "fit_score": item.score.fit_score,
                        "intent_score": item.score.intent_score,
                        "qualification_count": len(item.qualification),
                        "signal_count": len(item.signals),
                    }
                    for item in candidates
                ],
            },
        )
        return next_state

    def validate_artifact(self, state: LiveICPRadarRunState) -> LiveICPRadarRunState:
        radar = state.radar or build_live_mini_radar_definition()
        sources = [RadarSourceEvidence.model_validate(item) for item in state.sources]
        candidates = [
            normalize_live_candidate(item, radar=radar, sources=sources)
            for item in state.candidates
        ]
        issues = validate_live_radar_qualification_contract(
            candidates=candidates,
            sources=sources,
            radar=radar,
        )
        result = LiveRadarValidationResult(
            issues=issues,
            events=[
                *[
                    LiveRadarPipelineEvent(
                        event_type="validation_warning",
                        phase="validation",
                        actor="validator",
                        node_name="validate_artifact",
                        visibility="operator",
                        summary=issue.message,
                        payload={"severity": issue.severity, "path": issue.path},
                    )
                    for issue in issues
                ],
                LiveRadarPipelineEvent(
                    event_type="self_check_completed",
                    phase="validation",
                    actor="validator",
                    node_name="validate_artifact",
                    summary=f"Artifact self-check completed with {len(issues)} validation issues.",
                    payload={
                        "validation_issue_count": len(issues),
                        "candidate_count": len(candidates),
                        "source_count": len(sources),
                    },
                ),
            ],
        )
        next_state = state.model_copy(update={
            "contract_validation": [item.model_dump() for item in result.issues],
            "pipeline_events": _append_events(state, result.events),
        })
        _trace(
            next_state, "validation", "validate_artifact", "validation_result", "Artifact validation result",
            summary=f"Validation completed with {len(issues)} issues.",
            payload={"issues": [item.model_dump() for item in issues]},
        )
        return next_state

    def shape_artifact(
        self,
        *,
        state: LiveICPRadarRunState,
        node_name: str,
        runtime_mode: str,
        framework_available: bool,
    ) -> LiveICPRadarRunState:
        radar = state.radar or build_live_mini_radar_definition()
        sources = [RadarSourceEvidence.model_validate(item) for item in state.sources]
        candidates = [
            normalize_live_candidate(item, radar=radar, sources=sources)
            for item in state.candidates
        ]
        plan = RadarSearchPlan.model_validate(state.search_plan or build_live_mini_radar_search_plan(radar))
        state_for_metadata = state.model_copy(update={
            "search_plan": plan.model_dump(),
            "sources": [item.model_dump() for item in sources],
            "candidates": [item.model_dump() for item in candidates],
        })
        metadata = self._runtime_metadata(
            state=state_for_metadata,
            node_name=node_name,
            provider_metadata=state.provider_metadata,
            runtime_mode=runtime_mode,
            framework_available=framework_available,
        )
        metadata["pipeline_events"] = list(state.pipeline_events)
        artifact = LiveRadarRunArtifact(
            radar=radar,
            run_metadata=metadata,
            search_plan=plan.model_dump(),
            sources=[item.model_dump() for item in sources],
            candidates=[item.model_dump() for item in candidates],
            contract_validation=list(state.contract_validation),
        )
        next_state = state.model_copy(update={
            "radar": radar,
            "search_plan": plan.model_dump(),
            "sources": [item.model_dump() for item in sources],
            "candidates": [item.model_dump() for item in candidates],
            "workflow_metadata": metadata,
            "artifact": artifact.model_dump(),
            "error_message": None,
        })
        _trace(
            next_state, "artifact", "shape_artifact", "pipeline_output", "Artifact shaping output",
            summary=f"Shaped artifact with {len(candidates)} candidates and {len(sources)} sources.",
            payload={
                "artifact_version": artifact.run_metadata.get("artifact_version"),
                "source_count": len(sources),
                "candidate_count": len(candidates),
                "validation_issue_count": len(state.contract_validation),
            },
        )
        return next_state

    def _runtime_metadata(
        self,
        *,
        state: LiveICPRadarRunState,
        node_name: str,
        provider_metadata: dict[str, Any],
        runtime_mode: str,
        framework_available: bool,
    ) -> dict[str, Any]:
        return {
            "workflow_name": "LiveICPRadarRunWorkflow",
            "runtime": getattr(self._provider, "runtime_name", "recorded") if state.live else "recorded",
            "framework_available": framework_available,
            "runtime_mode": runtime_mode,
            "node_name": node_name,
            "task_id": state.task_context.get("task_id"),
            "correlation_id": state.task_context.get("correlation_id"),
            "model": provider_metadata.get("model"),
            "web_mode": provider_metadata.get("web_mode"),
            "query_count": len(state.search_plan["queries"]) if state.search_plan else 0,
            "source_count": len(state.sources),
            "candidate_count": len(state.candidates),
            "execution_plan": state.execution_plan or {},
            "execution_results": dict(state.execution_results),
            "run_at": _now_iso(),
        }


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _append_events(state: LiveICPRadarRunState, events: list[LiveRadarPipelineEvent]) -> list[dict[str, Any]]:
    return [*state.pipeline_events, *[event.model_dump() for event in events]]
