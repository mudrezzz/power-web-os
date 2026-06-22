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
    RadarDiscoveryPlanner,
    RadarExecutionPlan,
    LiveRadarRunArtifact,
    LiveRadarValidationResult,
    RadarSearchPlan,
    RadarSourceEvidence,
    WebSearchProvider,
)
from power_web_os.application.live_radar_definition import build_live_mini_radar_definition, build_live_mini_radar_search_plan
from power_web_os.application.live_radar_discovery_planning import DeterministicRadarDiscoveryPlanner, product_sources_for_candidates
from power_web_os.application.live_radar_execution_plan import compile_radar_execution_plan, execution_plan_to_search_plan
from power_web_os.application.live_radar_normalization import (
    _dedupe_sources,
    _rank_candidates,
    normalize_live_candidate,
    validate_live_radar_qualification_contract,
)
from power_web_os.application.live_radar_pipeline_support import (
    candidate_rejected as _candidate_rejected,
    rejected_candidate_payload as _rejected_candidate_payload,
    trace_pipeline_step as _trace,
)
from power_web_os.application.live_radar_planning_pipeline import build_planned_state
from power_web_os.application.radar_source_providers import RadarSourceRegistry, SourceRegistryWebSearchProvider
from power_web_os.application.live_radar_staged_execution import run_staged_radar_execution


class LiveRadarRunService:
    """Provider-neutral planner/executor/evaluator pipeline for live Radar."""

    def __init__(
        self,
        provider: WebSearchProvider,
        *,
        discovery_planner: RadarDiscoveryPlanner | None = None,
        source_registry: RadarSourceRegistry | None = None,
    ) -> None:
        self._provider = SourceRegistryWebSearchProvider(provider, source_registry) if source_registry is not None else provider
        self._discovery_planner = discovery_planner or DeterministicRadarDiscoveryPlanner()

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
        return build_planned_state(state=state, planner=self._discovery_planner)

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
            max_web_tasks_per_subject=_int_context_value(state.task_context, "max_web_tasks_per_subject"),
            max_discovery_tasks_per_rule=_int_context_value(state.task_context, "max_discovery_tasks_per_rule"),
            max_gate_tasks_per_candidate_rule=_int_context_value(state.task_context, "max_gate_tasks_per_candidate_rule"),
            max_signal_tasks_per_candidate_signal=_int_context_value(
                state.task_context,
                "max_signal_tasks_per_candidate_signal",
            ),
            max_total_web_tasks_per_run=_int_context_value(state.task_context, "max_total_web_tasks_per_run"),
            min_useful_sources_per_discovery_task=_int_context_value(
                state.task_context,
                "min_useful_sources_per_discovery_task",
            ),
            min_candidates_per_discovery_task=_int_context_value(
                state.task_context,
                "min_candidates_per_discovery_task",
            ),
            max_discovery_retries_per_task=_int_context_value(
                state.task_context,
                "max_discovery_retries_per_task",
            ),
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
        coverage_needs_review = bool(
            state.execution_results.get("coverage_warnings")
            or state.execution_results.get("unresolved_candidate_gaps")
        )
        if coverage_needs_review:
            visible_candidates = [
                candidate.model_copy(update={
                    "review_flags": sorted({*candidate.review_flags, "candidate_universe_coverage_requires_review"}),
                })
                for candidate in visible_candidates
            ]
        rejected_candidates = [_rejected_candidate_payload(candidate) for candidate in candidates if _candidate_rejected(candidate)]
        product_sources, analyzed_sources = product_sources_for_candidates(
            sources=sources,
            candidates=[candidate.model_dump() for candidate in visible_candidates],
        )
        result = LiveRadarExtractionResult(
            sources=product_sources,
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
            "analyzed_sources": analyzed_sources,
            "analyzed_source_count": len(analyzed_sources),
            "used_source_count": len(product_sources),
        }
        next_state = state.model_copy(update={
            "sources": [item.model_dump() for item in result.sources],
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
                "used_source_count": len(product_sources),
                "analyzed_source_count": len(analyzed_sources),
                "candidates": [
                    {"candidate_id": item.candidate_id, "legal_name": item.legal_name, "evidence_refs": list(item.evidence_refs)}
                    for item in visible_candidates
                ],
                "rejected_candidates": rejected_candidates,
                "analyzed_sources": analyzed_sources,
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
            "discovery_plan": state.discovery_plan or {},
            "execution_plan": state.execution_plan or {},
            "execution_results": dict(state.execution_results),
            "run_at": _now_iso(),
        }


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _append_events(state: LiveICPRadarRunState, events: list[LiveRadarPipelineEvent]) -> list[dict[str, Any]]:
    return [*state.pipeline_events, *[event.model_dump() for event in events]]


def _int_context_value(context: dict[str, Any], key: str) -> int | None:
    value = context.get(key)
    if isinstance(value, bool):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None
