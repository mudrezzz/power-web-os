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
from power_web_os.integrations.live_radar_openrouter import (
    OpenRouterWebSearchProvider,
    RecordedWebSearchProvider,
    _filter_result_to_verified_sources,
    _source_url_is_reachable,
    build_openrouter_request,
    normalize_openrouter_response,
)
from power_web_os.workflows.live_icp_radar_workflow import (
    FRAMEWORK_AVAILABLE,
    LiveICPRadarRunWorkflow,
    build_live_mini_radar_artifact,
)

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
    "QualificationContractIssue",
    "QualificationCrossValidation",
    "QualificationEvidenceFinding",
    "QualificationRequirementEvaluation",
    "QualificationReviewDecision",
    "QualificationSourceUsage",
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
    "validate_live_radar_qualification_contract",
]
