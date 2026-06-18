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
    LiveRadarRunArtifact,
    LiveRadarValidationResult,
    RadarSearchPlan,
    RadarSourceEvidence,
    WebSearchProvider,
)
from power_web_os.application.live_radar_definition import build_live_mini_radar_definition, build_live_mini_radar_search_plan
from power_web_os.application.live_radar_normalization import (
    _dedupe_sources,
    _rank_candidates,
    normalize_live_candidate,
    validate_live_radar_qualification_contract,
)


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
        radar = state.radar or build_live_mini_radar_definition()
        plan = build_live_mini_radar_search_plan(radar)
        result = LiveRadarPlanningResult(
            radar=radar,
            search_plan=plan,
            events=[
                LiveRadarPipelineEvent(
                    event_type="plan_created",
                    phase="planning",
                    actor="workflow",
                    node_name="build_search_plan",
                    summary=f"Live Radar plan prepared with {len(plan.queries)} search queries.",
                    payload={"query_count": len(plan.queries), "radar_id": plan.radar_id},
                ),
                *[
                    LiveRadarPipelineEvent(
                        event_type="search_query_planned",
                        phase="planning",
                        actor="workflow",
                        node_name=query.query_id,
                        summary=query.query,
                        payload={
                            "purpose": query.purpose,
                            "expected_evidence": list(query.expected_evidence),
                        },
                    )
                    for query in plan.queries
                ],
            ],
        )
        return state.model_copy(update={
            "radar": result.radar,
            "search_plan": result.search_plan.model_dump(),
            "pipeline_events": _append_events(state, result.events),
        })

    def run_web_search(self, state: LiveICPRadarRunState) -> LiveICPRadarRunState:
        radar = state.radar or build_live_mini_radar_definition()
        plan = RadarSearchPlan.model_validate(state.search_plan or build_live_mini_radar_search_plan(radar))
        provider_result = self._provider.run_search_plan(radar=radar, search_plan=plan)
        result = LiveRadarCollectionResult(
            sources=provider_result.sources,
            candidate_observations=provider_result.candidate_observations,
            provider_metadata=provider_result.provider_metadata,
            events=[
                LiveRadarPipelineEvent(
                    event_type="source_collected",
                    phase="collection",
                    actor="provider",
                    node_name="run_web_search",
                    visibility="operator",
                    summary=f"Provider returned {len(provider_result.sources)} sources and {len(provider_result.candidate_observations)} candidate observations.",
                    payload={
                        "source_count": len(provider_result.sources),
                        "candidate_observation_count": len(provider_result.candidate_observations),
                        "provider": str(provider_result.provider_metadata.get("provider", "")),
                        "model": str(provider_result.provider_metadata.get("model", "")),
                        "web_mode": str(provider_result.provider_metadata.get("web_mode", "")),
                    },
                    source_refs=[source.evidence_ref for source in provider_result.sources if source.evidence_ref],
                )
            ],
        )
        return state.model_copy(update={
            "sources": [item.model_dump() for item in result.sources],
            "candidate_observations": [dict(item) for item in result.candidate_observations],
            "provider_metadata": dict(result.provider_metadata),
            "pipeline_events": _append_events(state, result.events),
        })

    def normalize_sources(self, state: LiveICPRadarRunState) -> LiveICPRadarRunState:
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
        return state.model_copy(update={
            "sources": [item.model_dump() for item in result.sources],
            "pipeline_events": _append_events(state, result.events),
        })

    def extract_candidates(self, state: LiveICPRadarRunState) -> LiveICPRadarRunState:
        radar = state.radar or build_live_mini_radar_definition()
        sources = [RadarSourceEvidence.model_validate(item) for item in state.sources]
        candidates = _rank_candidates([
            normalize_live_candidate(item, radar=radar, sources=sources)
            for item in state.candidate_observations
        ])
        result = LiveRadarExtractionResult(
            sources=sources,
            candidates=candidates,
            events=[
                LiveRadarPipelineEvent(
                    event_type="candidate_extracted",
                    phase="extraction",
                    actor="workflow",
                    node_name="extract_candidates",
                    summary=f"Extracted {len(candidates)} normalized candidates.",
                    payload={"candidate_count": len(candidates)},
                    candidate_refs=[candidate.candidate_id for candidate in candidates],
                )
            ],
        )
        return state.model_copy(update={
            "candidates": [item.model_dump() for item in result.candidates],
            "pipeline_events": _append_events(state, result.events),
        })

    def evaluate_candidates(self, state: LiveICPRadarRunState) -> LiveICPRadarRunState:
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
        return state.model_copy(update={
            "candidates": [item.model_dump() for item in result.candidates],
            "pipeline_events": _append_events(state, result.events),
        })

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
        return state.model_copy(update={
            "contract_validation": [item.model_dump() for item in result.issues],
            "pipeline_events": _append_events(state, result.events),
        })

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
        return state.model_copy(update={
            "radar": radar,
            "search_plan": plan.model_dump(),
            "sources": [item.model_dump() for item in sources],
            "candidates": [item.model_dump() for item in candidates],
            "workflow_metadata": metadata,
            "artifact": artifact.model_dump(),
            "error_message": None,
        })

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
            "run_at": _now_iso(),
        }


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _append_events(state: LiveICPRadarRunState, events: list[LiveRadarPipelineEvent]) -> list[dict[str, Any]]:
    return [*state.pipeline_events, *[event.model_dump() for event in events]]
