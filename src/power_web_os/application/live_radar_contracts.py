"""Application contracts for live ICP Radar execution.

These Pydantic models and provider ports describe live Radar inputs and outputs
without depending on OpenRouter, HTTP clients, persistence, or workflow runtime.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator
from power_web_os.application.live_radar_source_cards import RadarPlannerSourceCard, RadarPlannerSourceUse

QualificationStatus = Literal["confirmed", "weak", "unknown", "rejected"]
SignalStatus = Literal["observed", "not_observed", "unclear"]
QualificationAssessment = Literal["matches", "partially_matches", "does_not_match", "unknown"]
QualificationOperator = Literal["AND", "OR", "AND_NOT", "OR_NOT"]
QualificationRequirement = Literal["required", "recommended"]
QualificationSourceOrigin = Literal["global", "local", "additional"]
QualificationTrustPolicy = Literal["trusted", "cross_checked", "hitl_required"]
QualificationCrossValidationStatus = Literal["passed", "weak", "failed", "not_required"]
RadarExecutionStage = Literal["qualification_discovery", "qualification_gate", "coverage_check", "signal_search", "evaluation", "validation"]
RadarExecutionSubjectType = Literal["radar", "qualification", "signal"]
RadarDiscoveryPlanStepStage = Literal["candidate_universe_discovery", "source_probe", "qualification_gate", "coverage_check"]
RadarDiscoverySourceScope = Literal["global", "local", "additional", "system"]
RadarCriterionRole = Literal["upstream_discovery", "downstream_gate", "attribute_enrichment", "exclusion"]
RadarSourceBase = Literal["global_configured", "rule_local", "additional", "system"]
RadarSourceApplicationScope = Literal["whole_universe", "rule_scope", "candidate_scope"]
RadarSourceUsageObligation = Literal["required", "preferred", "optional", "fallback", "disabled", "required_for_identity", "required_for_coverage", "required_for_signal"]
RadarEntityType = Literal["legal_entity", "branch", "production_site", "project", "asset", "unknown_entity"]
RadarEntityResolutionStatus = Literal["resolved", "linked_to_legal_entity", "unresolved_gap", "rejected_as_account", "review_needed"]


class RadarSearchQuery(BaseModel):
    query_id: str
    query: str
    purpose: str
    expected_evidence: list[str] = Field(default_factory=list)
    stage: RadarExecutionStage | None = None
    subject_type: RadarExecutionSubjectType | None = None
    subject_id: str | None = None
    rule_snapshot: str = ""
    source_scope: RadarDiscoverySourceScope = "additional"
    source_base: RadarSourceBase | None = None
    application_scope: RadarSourceApplicationScope | None = None
    source_ids: list[str] = Field(default_factory=list)
    external_source_hints: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    candidate_scope: list[str] = Field(default_factory=list)


class RadarSearchPlan(BaseModel):
    radar_id: str
    queries: list[RadarSearchQuery]


class RadarExecutionTask(BaseModel):
    task_id: str
    stage: RadarExecutionStage
    subject_type: RadarExecutionSubjectType
    subject_id: str
    rule_snapshot: str = ""
    query: str
    purpose: str
    expected_evidence: list[str] = Field(default_factory=list)
    source_scope: RadarDiscoverySourceScope = "additional"
    source_base: RadarSourceBase | None = None
    application_scope: RadarSourceApplicationScope | None = None
    source_ids: list[str] = Field(default_factory=list)
    external_source_hints: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    candidate_scope: list[str] = Field(default_factory=list)


class RadarExecutionPlan(BaseModel):
    radar_id: str
    tasks: list[RadarExecutionTask]


RadarCandidateUniverseStatus = Literal["discovered", "qualified", "rejected", "unknown_review_needed", "gap"]


class RadarCandidateUniverseEntry(BaseModel):
    candidate_id: str
    legal_name: str
    status: RadarCandidateUniverseStatus
    origin_task_id: str = ""
    source_refs: list[str] = Field(default_factory=list)
    gate_results: list[dict[str, Any]] = Field(default_factory=list)
    rejection_reasons: list[str] = Field(default_factory=list)
    coverage_flags: list[str] = Field(default_factory=list)


class RadarCoverageCheckRecord(BaseModel):
    task_id: str
    iteration: int
    source_count: int = 0
    candidate_observation_count: int = 0
    new_candidate_count: int = 0
    gap_count: int = 0
    completeness_risk: Literal["low", "medium", "high"] = "medium"
    warnings: list[str] = Field(default_factory=list)


class RadarDiscoveryPlanStep(BaseModel):
    step_id: str
    stage: RadarDiscoveryPlanStepStage
    subject_rule_ids: list[str] = Field(default_factory=list)
    source_scope: RadarDiscoverySourceScope = "additional"
    source_base: RadarSourceBase | None = None
    application_scope: RadarSourceApplicationScope | None = None
    source_ids: list[str] = Field(default_factory=list)
    external_source_hints: list[str] = Field(default_factory=list)
    query: str
    purpose: str
    expected_evidence: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    skip_rationale: str = ""
    depends_on: list[str] = Field(default_factory=list)
    candidate_scope: list[str] = Field(default_factory=list)
    source_use: list[RadarPlannerSourceUse] = Field(default_factory=list)

    @field_validator("query", "purpose", "skip_rationale", mode="before")
    @classmethod
    def _empty_string_for_null(cls, value: Any) -> Any:
        return "" if value is None else value

    @field_validator(
        "subject_rule_ids",
        "source_ids",
        "external_source_hints",
        "expected_evidence",
        "acceptance_criteria",
        "depends_on",
        "candidate_scope",
        "source_use",
        mode="before",
    )
    @classmethod
    def _empty_list_for_null(cls, value: Any) -> Any:
        return [] if value is None else value


class RadarCriterionRoleDecision(BaseModel):
    rule_id: str
    role: RadarCriterionRole
    depends_on: list[str] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"] = "medium"
    reason: str = ""
    warnings: list[str] = Field(default_factory=list)

    @field_validator("depends_on", "warnings", mode="before")
    @classmethod
    def _empty_list_for_null(cls, value: Any) -> Any:
        return [] if value is None else value

    @field_validator("reason", mode="before")
    @classmethod
    def _empty_string_for_null(cls, value: Any) -> Any:
        return "" if value is None else value


class RadarDiscoverySourcePolicyDecision(BaseModel):
    source_id: str
    source_label: str = ""
    decision: Literal["selected", "skipped"]
    reason: str
    rule_ids: list[str] = Field(default_factory=list)
    usage_obligation: RadarSourceUsageObligation = "preferred"
    obligation_status: str = ""

    @field_validator("rule_ids", mode="before")
    @classmethod
    def _empty_list_for_null(cls, value: Any) -> Any:
        return [] if value is None else value

    @field_validator("reason", "obligation_status", mode="before")
    @classmethod
    def _empty_string_for_null(cls, value: Any) -> Any:
        return "" if value is None else value


class RadarDiscoveryCoverageHypothesis(BaseModel):
    summary: str
    expected_candidate_count: str = ""
    completeness_risk: Literal["low", "medium", "high"] = "medium"


class RadarDiscoveryPlan(BaseModel):
    plan_summary: str
    criterion_role_decisions: list[RadarCriterionRoleDecision] = Field(default_factory=list)
    steps: list[RadarDiscoveryPlanStep] = Field(default_factory=list)
    source_policy_decisions: list[RadarDiscoverySourcePolicyDecision] = Field(default_factory=list)
    coverage_hypotheses: list[RadarDiscoveryCoverageHypothesis] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    acceptance_metadata: dict[str, Any] = Field(default_factory=dict)


class RadarDiscoveryPlanningInput(BaseModel):
    radar_id: str
    name: str
    description: str = ""
    qualification_rules: list[dict[str, Any]] = Field(default_factory=list)
    global_search_policy: dict[str, Any] = Field(default_factory=dict)
    source_cards: list[RadarPlannerSourceCard] = Field(default_factory=list)
    task_context: dict[str, Any] = Field(default_factory=dict)
    requester: str = ""
    live: bool = False
    model: str | None = None
    web_mode: str | None = None
    max_steps: int = 8
    max_iterations: int = 2
    source_visibility_policy: str = "used_sources_product"


class RadarDiscoveryPlanValidationResult(BaseModel):
    accepted: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    corrections: list[dict[str, Any]] = Field(default_factory=list)


SourceVerificationState = Literal["reachable", "blocked", "timeout", "unverified_url", "invalid_url", "not_checked"]
SourceVerificationMode = Literal["strict", "soft", "off"]


class RadarSourceEvidence(BaseModel):
    evidence_ref: str
    title: str
    url: str
    snippet: str
    query_id: str | None = None
    source_type: str = "web"
    verification_state: SourceVerificationState = "reachable"
    verification_mode: SourceVerificationMode = "strict"
    verification_reason: str = ""
    verification_status_code: int | None = None


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
    search_status: str = "searched"
    not_searched_reason: str | None = None
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
    discovery_plan: dict[str, Any] | None = None
    execution_plan: dict[str, Any] | None = None
    execution_results: dict[str, Any] = Field(default_factory=dict)
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


class RadarDiscoveryPlanner(ABC):
    runtime_name = "discovery_planner"

    @abstractmethod
    def propose_plan(
        self,
        *,
        planning_input: RadarDiscoveryPlanningInput,
        previous_validation: RadarDiscoveryPlanValidationResult | None = None,
    ) -> RadarDiscoveryPlan:
        raise NotImplementedError
