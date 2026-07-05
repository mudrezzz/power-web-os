"""Product-safe live Radar artifact projection for candidate discovery.

This module is the package-owned home for the artifact shaping steps that used
to live in the root-level live Radar service facade. It does not execute
provider tasks or change checkpoint decisions.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from power_web_os.application.live_radar_extraction_contract import (
    qualification_contract_issues_from_extraction_results,
)
from power_web_os.application.radar.candidate_discovery.retrieval.definition import (
    build_live_mini_radar_definition,
    build_live_mini_radar_search_plan,
)
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
from power_web_os.application.radar.candidate_discovery.contracts import (
    LiveICPRadarRunState,
    LiveRadarEvaluationResult,
    LiveRadarExtractionResult,
    LiveRadarPipelineEvent,
    LiveRadarRunArtifact,
    LiveRadarValidationResult,
    RadarSearchPlan,
    RadarSourceEvidence,
    WebSearchProvider,
)
from power_web_os.application.radar.candidate_discovery.retrieval.product_sources import (
    product_sources_for_candidates,
)


class LiveRadarRunArtifactProjector:
    """Projects candidate-discovery run state into the legacy live artifact.

    Owns:
    - Source normalization, candidate extraction/evaluation projection,
      qualification contract validation, runtime metadata, and artifact shape.

    Does not own:
    - Planning, provider task execution, checkpoint policy, budget admission, or
      candidate-discovery phase order.

    Architecture:
    docs/architecture/RADAR_BACKEND_ARCHITECTURE.md#radarcandidate_discovery
    """

    def __init__(self, provider: WebSearchProvider) -> None:
        self._provider = provider

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
            next_state,
            "normalization",
            "normalize_sources",
            "normalization_result",
            "Source normalization result",
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
        rejected_candidates = [
            _rejected_candidate_payload(candidate)
            for candidate in candidates
            if _candidate_rejected(candidate)
        ]
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
                    summary=(
                        f"Extracted {len(visible_candidates)} visible candidates and filtered "
                        f"{len(rejected_candidates)} rejected candidates."
                    ),
                    payload={
                        "candidate_count": len(visible_candidates),
                        "rejected_candidate_count": len(rejected_candidates),
                    },
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
            next_state,
            "extraction",
            "extract_candidates",
            "normalization_result",
            "Candidate extraction result",
            summary=f"Extracted {len(candidates)} normalized candidates.",
            payload={
                "candidate_count": len(visible_candidates),
                "rejected_candidate_count": len(rejected_candidates),
                "used_source_count": len(product_sources),
                "analyzed_source_count": len(analyzed_sources),
                "candidates": [
                    {
                        "candidate_id": item.candidate_id,
                        "legal_name": item.legal_name,
                        "evidence_refs": list(item.evidence_refs),
                    }
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
            normalize_live_candidate(
                item,
                radar=state.radar or build_live_mini_radar_definition(),
                sources=[RadarSourceEvidence.model_validate(source) for source in state.sources],
            )
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
            next_state,
            "evaluation",
            "evaluate_candidates",
            "pipeline_output",
            "Candidate evaluation output",
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
        issues = [*issues, *qualification_contract_issues_from_extraction_results(state.execution_results)]
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
            next_state,
            "validation",
            "validate_artifact",
            "validation_result",
            "Artifact validation result",
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
            next_state,
            "artifact",
            "shape_artifact",
            "pipeline_output",
            "Artifact shaping output",
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
