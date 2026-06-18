"""Application contracts for live ICP Radar execution.

These Pydantic models and provider ports describe live Radar inputs and outputs
without depending on OpenRouter, HTTP clients, persistence, or workflow runtime.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Literal

from pydantic import BaseModel, Field

QualificationStatus = Literal["confirmed", "weak", "unknown", "rejected"]
SignalStatus = Literal["observed", "not_observed", "unclear"]
QualificationAssessment = Literal["matches", "partially_matches", "does_not_match", "unknown"]
QualificationOperator = Literal["AND", "OR", "AND_NOT", "OR_NOT"]
QualificationRequirement = Literal["required", "recommended"]
QualificationSourceOrigin = Literal["global", "local", "additional"]
QualificationTrustPolicy = Literal["trusted", "cross_checked", "hitl_required"]
QualificationCrossValidationStatus = Literal["passed", "weak", "failed", "not_required"]


class RadarSearchQuery(BaseModel):
    query_id: str
    query: str
    purpose: str
    expected_evidence: list[str] = Field(default_factory=list)


class RadarSearchPlan(BaseModel):
    radar_id: str
    queries: list[RadarSearchQuery]


class RadarSourceEvidence(BaseModel):
    evidence_ref: str
    title: str
    url: str
    snippet: str
    query_id: str | None = None
    source_type: str = "web"


class QualificationSourceUsage(BaseModel):
    source_ref: str
    source_name: str
    source_origin: QualificationSourceOrigin = "additional"
    trust_policy: QualificationTrustPolicy = "hitl_required"
    used_for: str = "verification"
    url: str = ""


class QualificationEvidenceFinding(BaseModel):
    source_ref: str
    fact: str
    excerpt: str = ""
    excerpt_type: Literal["quote", "paraphrase", "not_available"] = "not_available"
    why_it_matches_rule: str
    evidence_strength: Literal["strong", "medium", "weak"] = "weak"
    contradicts_rule: bool = False


class QualificationCrossValidation(BaseModel):
    required: bool = False
    status: QualificationCrossValidationStatus = "not_required"
    source_count: int = 0
    notes: str = ""


class QualificationRequirementEvaluation(BaseModel):
    requirement_level: QualificationRequirement
    satisfied: bool | None = None
    explanation: str = ""


class QualificationReviewDecision(BaseModel):
    status: Literal["approved", "rejected", "corrected"]
    corrected_assessment: QualificationAssessment | None = None
    comment: str
    reviewed_at: str


class LiveRadarQualificationResult(BaseModel):
    criterion_code: str
    criterion: str
    status: QualificationStatus
    confidence: str = "low"
    rationale: str
    evidence_refs: list[str] = Field(default_factory=list)
    rule_id: str
    rule_text_snapshot: str
    operator: QualificationOperator = "AND"
    requirement_level: QualificationRequirement = "required"
    confidence_policy: QualificationTrustPolicy = "hitl_required"
    source_usages: list[QualificationSourceUsage] = Field(default_factory=list)
    evidence_findings: list[QualificationEvidenceFinding] = Field(default_factory=list)
    cross_validation: QualificationCrossValidation = Field(default_factory=QualificationCrossValidation)
    requirement_evaluation: QualificationRequirementEvaluation
    final_assessment: QualificationAssessment = "unknown"
    review_decision: QualificationReviewDecision | None = None


class QualificationContractIssue(BaseModel):
    severity: Literal["error", "warning"]
    path: str
    message: str


class LiveRadarSignalResult(BaseModel):
    signal_code: str
    signal: str
    status: SignalStatus
    score: int = Field(ge=0, le=2)
    confidence: str = "low"
    summary: str
    evidence_refs: list[str] = Field(default_factory=list)
    source_usages: list[QualificationSourceUsage] = Field(default_factory=list)
    evidence_findings: list["SignalEvidenceFinding"] = Field(default_factory=list)
    cross_validation: QualificationCrossValidation = Field(default_factory=QualificationCrossValidation)
    score_evaluation: "SignalScoreEvaluation | None" = None


class SignalEvidenceFinding(BaseModel):
    source_ref: str
    fact: str
    excerpt: str = ""
    excerpt_type: Literal["quote", "paraphrase", "not_available"] = "not_available"
    why_it_matches_signal: str
    why_score_applies: str
    evidence_strength: Literal["strong", "medium", "weak"] = "weak"
    contradicts_signal: bool = False


class SignalScoreEvaluation(BaseModel):
    scale: str = "0-2"
    applied_score: int = Field(default=0, ge=0, le=2)
    max_score: int = 2
    rule_snapshot: str
    explanation: str


class LiveRadarScore(BaseModel):
    fit_score: int
    intent_score: int
    tier: str


class LiveRadarCandidate(BaseModel):
    candidate_id: str
    legal_name: str
    description: str = ""
    qualification: list[LiveRadarQualificationResult]
    signals: list[LiveRadarSignalResult]
    score: LiveRadarScore
    review_flags: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


class WebSearchProviderResult(BaseModel):
    sources: list[RadarSourceEvidence] = Field(default_factory=list)
    candidate_observations: list[dict[str, Any]] = Field(default_factory=list)
    provider_metadata: dict[str, Any] = Field(default_factory=dict)


class LiveRadarPipelineEvent(BaseModel):
    """Provider-neutral event emitted by one live Radar pipeline step."""

    event_type: str
    phase: str
    actor: str
    node_name: str
    summary: str
    visibility: Literal["user", "operator", "debug"] = "user"
    payload: dict[str, Any] = Field(default_factory=dict)
    source_refs: list[str] = Field(default_factory=list)
    candidate_refs: list[str] = Field(default_factory=list)


class LiveRadarPlanningResult(BaseModel):
    radar: dict[str, Any]
    search_plan: RadarSearchPlan
    events: list[LiveRadarPipelineEvent] = Field(default_factory=list)


class LiveRadarCollectionResult(BaseModel):
    sources: list[RadarSourceEvidence] = Field(default_factory=list)
    candidate_observations: list[dict[str, Any]] = Field(default_factory=list)
    provider_metadata: dict[str, Any] = Field(default_factory=dict)
    events: list[LiveRadarPipelineEvent] = Field(default_factory=list)


class LiveRadarExtractionResult(BaseModel):
    sources: list[RadarSourceEvidence] = Field(default_factory=list)
    candidates: list[LiveRadarCandidate] = Field(default_factory=list)
    events: list[LiveRadarPipelineEvent] = Field(default_factory=list)


class LiveRadarEvaluationResult(BaseModel):
    candidates: list[LiveRadarCandidate] = Field(default_factory=list)
    events: list[LiveRadarPipelineEvent] = Field(default_factory=list)


class LiveRadarValidationResult(BaseModel):
    issues: list[QualificationContractIssue] = Field(default_factory=list)
    events: list[LiveRadarPipelineEvent] = Field(default_factory=list)


class LiveRadarRunArtifact(BaseModel):
    artifact_type: Literal["icp_radar_live_run"] = "icp_radar_live_run"
    artifact_version: Literal["0.6.3.4"] = "0.6.3.4"
    radar: dict[str, Any]
    run_metadata: dict[str, Any]
    search_plan: dict[str, Any]
    sources: list[dict[str, Any]]
    candidates: list[dict[str, Any]]
    contract_validation: list[dict[str, Any]] = Field(default_factory=list)


class LiveICPRadarRunState(BaseModel):
    task_context: dict[str, Any] = Field(default_factory=dict)
    radar: dict[str, Any] = Field(default_factory=dict)
    search_plan: dict[str, Any] | None = None
    sources: list[dict[str, Any]] = Field(default_factory=list)
    candidate_observations: list[dict[str, Any]] = Field(default_factory=list)
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    contract_validation: list[dict[str, Any]] = Field(default_factory=list)
    provider_metadata: dict[str, Any] = Field(default_factory=dict)
    pipeline_events: list[dict[str, Any]] = Field(default_factory=list)
    artifact: dict[str, Any] | None = None
    workflow_metadata: dict[str, Any] = Field(default_factory=dict)
    live: bool = False
    error_message: str | None = None


class WebSearchProvider(ABC):
    runtime_name = "web_search_provider"

    @abstractmethod
    def run_search_plan(self, *, radar: dict[str, Any], search_plan: RadarSearchPlan) -> WebSearchProviderResult:
        raise NotImplementedError
