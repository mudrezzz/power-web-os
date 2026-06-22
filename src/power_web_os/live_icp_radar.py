"""Compatibility facade for the extracted live ICP Radar backend modules.

New backend code should import from `application`, `integrations`, or `workflows`
directly. This facade preserves the historical public imports used by the demo
and tests while `live_icp_radar.py` is removed from the legacy-large allowlist.
"""

from __future__ import annotations

from power_web_os.application.live_radar_contracts import (
    LiveICPRadarRunState,
    LiveRadarCandidate,
    LiveRadarQualificationResult,
    LiveRadarRunArtifact,
    LiveRadarScore,
    LiveRadarSignalResult,
    QualificationContractIssue,
    QualificationCrossValidation,
    QualificationEvidenceFinding,
    QualificationRequirementEvaluation,
    QualificationReviewDecision,
    QualificationSourceUsage,
    RadarDiscoveryPlanner,
    RadarDiscoveryPlanningInput,
    RadarDiscoveryPlan,
    RadarDiscoveryPlanStep,
    RadarDiscoveryPlanValidationResult,
    RadarExecutionPlan,
    RadarExecutionTask,
    RadarSearchPlan,
    RadarSearchQuery,
    RadarSourceEvidence,
    SignalEvidenceFinding,
    SignalScoreEvaluation,
    WebSearchProvider,
    WebSearchProviderResult,
)
from power_web_os.application.live_radar_definition import (
    build_live_mini_radar_definition,
    build_live_mini_radar_search_plan,
    build_live_mini_radar_search_plan_artifact,
)
from power_web_os.application.live_radar_normalization import (
    _dedupe_sources,
    _rank_candidates,
    normalize_live_candidate,
    validate_live_radar_qualification_contract,
)
from power_web_os.application.live_radar_retrieval_plan import (
    RadarResponseContract,
    RadarRetrievalPlan,
    RadarRetrievalTask,
    RadarRetrievalTaskPrompt,
    retrieval_plan_from_execution_plan,
    retrieval_plan_to_search_plan,
)
from power_web_os.integrations.openrouter_discovery_planner import (
    OpenRouterDiscoveryPlanner,
    build_openrouter_discovery_planner_request,
)
from power_web_os.integrations.live_radar_openrouter import (
    OpenRouterWebSearchProvider,
    RecordedWebSearchProvider,
    build_openrouter_request,
    normalize_openrouter_response,
)
from power_web_os.integrations.live_radar_source_verification import check_source_url
from power_web_os.workflows.live_icp_radar_workflow import (
    FRAMEWORK_AVAILABLE,
    LiveICPRadarRunWorkflow,
    build_live_mini_radar_artifact,
)


def _source_url_is_reachable(url: str) -> bool:
    """Compatibility helper for legacy tests; production uses source verification metadata."""

    return check_source_url(url).state == "reachable"


def _filter_result_to_verified_sources(result: WebSearchProviderResult) -> WebSearchProviderResult:
    """Legacy strict filter kept for compatibility with earlier demo/tests."""

    reachable_sources = [
        source
        for source in result.sources
        if _source_url_is_reachable(source.url)
    ]
    reachable_refs = {source.evidence_ref for source in reachable_sources}
    candidates = [
        candidate
        for candidate in result.candidate_observations
        if _legacy_candidate_refs(candidate) & reachable_refs
    ]
    return WebSearchProviderResult(
        sources=reachable_sources,
        candidate_observations=candidates,
        provider_metadata={
            **result.provider_metadata,
            "source_verification": "legacy_strict",
            "discarded_source_count": len(result.sources) - len(reachable_sources),
        },
    )


def _legacy_candidate_refs(candidate: dict[str, object]) -> set[str]:
    refs = {str(ref) for ref in candidate.get("evidence_refs", []) if str(ref).strip()}
    for section_name in ("qualification", "signals"):
        section = candidate.get(section_name, [])
        if not isinstance(section, list):
            continue
        for item in section:
            if not isinstance(item, dict):
                continue
            refs.update(str(ref) for ref in item.get("evidence_refs", []) if str(ref).strip())
    return refs

__all__ = [
    "FRAMEWORK_AVAILABLE",
    "LiveICPRadarRunState",
    "LiveICPRadarRunWorkflow",
    "LiveRadarCandidate",
    "LiveRadarQualificationResult",
    "LiveRadarRunArtifact",
    "LiveRadarScore",
    "LiveRadarSignalResult",
    "OpenRouterWebSearchProvider",
    "OpenRouterDiscoveryPlanner",
    "QualificationContractIssue",
    "QualificationCrossValidation",
    "QualificationEvidenceFinding",
    "QualificationRequirementEvaluation",
    "QualificationReviewDecision",
    "QualificationSourceUsage",
    "RadarExecutionPlan",
    "RadarDiscoveryPlanner",
    "RadarDiscoveryPlanningInput",
    "RadarDiscoveryPlan",
    "RadarDiscoveryPlanStep",
    "RadarDiscoveryPlanValidationResult",
    "RadarExecutionTask",
    "RadarResponseContract",
    "RadarRetrievalPlan",
    "RadarRetrievalTask",
    "RadarRetrievalTaskPrompt",
    "RadarSearchPlan",
    "RadarSearchQuery",
    "RadarSourceEvidence",
    "RecordedWebSearchProvider",
    "SignalEvidenceFinding",
    "SignalScoreEvaluation",
    "WebSearchProvider",
    "WebSearchProviderResult",
    "_dedupe_sources",
    "_filter_result_to_verified_sources",
    "_rank_candidates",
    "_source_url_is_reachable",
    "build_live_mini_radar_artifact",
    "build_live_mini_radar_definition",
    "build_live_mini_radar_search_plan",
    "build_live_mini_radar_search_plan_artifact",
    "build_openrouter_request",
    "normalize_live_candidate",
    "normalize_openrouter_response",
    "retrieval_plan_from_execution_plan",
    "retrieval_plan_to_search_plan",
    "validate_live_radar_qualification_contract",
]
