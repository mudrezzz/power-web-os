"""Transport DTOs for persisted Radar catalog, run, and candidate APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RadarSummaryResponse(BaseModel):
    radar_id: str
    name: str
    status: str
    owner: str
    profile: dict[str, Any]
    summary: dict[str, Any]
    artifact_path: str | None = None
    run_count: int = 0
    latest_run: "RadarRunSummaryResponse | None" = None


class RadarDefinitionResponse(BaseModel):
    definition_id: str
    radar_id: str
    definition_version: str
    definition_payload: dict[str, Any]
    is_active: bool
    updated_at: datetime | None = None


class RadarDefinitionUpdateRequest(BaseModel):
    definition_payload: dict[str, Any]
    definition_version: str | None = None
    is_active: bool = True


class RadarDetailResponse(RadarSummaryResponse):
    active_definition: RadarDefinitionResponse | None = None
    runs: list["RadarRunSummaryResponse"] = Field(default_factory=list)


class RadarPreflightResponse(BaseModel):
    artifact_type: str = "radar_execution_preflight_report"
    radar_id: str
    definition_id: str | None = None
    definition_version: str | None = None
    ready_for_live_run: bool
    summary: dict[str, Any] = Field(default_factory=dict)
    checks: list[dict[str, Any]] = Field(default_factory=list)
    runtime_config: dict[str, Any] = Field(default_factory=dict)


class RadarRunRequest(BaseModel):
    live: bool = True
    idempotency_key: str | None = None
    correlation_id: str | None = None
    requester: str = "api"
    task_context: dict[str, Any] = Field(default_factory=dict)


class RadarRunSummaryResponse(BaseModel):
    run_id: str
    radar_id: str
    status: str
    queued_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    idempotency_key: str | None = None
    correlation_id: str | None = None
    error_message: str | None = None
    error_metadata: dict[str, Any] = Field(default_factory=dict)
    run_metadata: dict[str, Any] = Field(default_factory=dict)
    output: "RadarRunOutputSummaryResponse | None" = None


class RadarRunOutputSummaryResponse(BaseModel):
    artifact_version: str
    source_count: int
    candidate_count: int
    contract_issue_count: int
    updated_at: datetime | None = None


class SourceUsageResponse(BaseModel):
    source_ref: str
    source_name: str = ""
    source_origin: str = "additional"
    trust_policy: str = "hitl_required"
    used_for: str = "verification"
    url: str = ""


class EvidenceFindingResponse(BaseModel):
    source_ref: str
    fact: str = ""
    excerpt: str = ""
    excerpt_type: str = "not_available"
    evidence_strength: str = "weak"
    contradicts_rule: bool | None = None
    contradicts_signal: bool | None = None
    why_it_matches_rule: str | None = None
    why_it_matches_signal: str | None = None
    why_score_applies: str | None = None


class QualificationResponse(BaseModel):
    criterion_code: str
    criterion: str = ""
    status: str
    confidence: str = "low"
    rationale: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    rule_id: str = ""
    rule_text_snapshot: str = ""
    operator: str = "AND"
    requirement_level: str = "required"
    confidence_policy: str = "hitl_required"
    source_usages: list[SourceUsageResponse] = Field(default_factory=list)
    evidence_findings: list[EvidenceFindingResponse] = Field(default_factory=list)
    cross_validation: dict[str, Any] = Field(default_factory=dict)
    requirement_evaluation: dict[str, Any] = Field(default_factory=dict)
    final_assessment: str = "unknown"
    review_decision: dict[str, Any] | None = None


class SignalResponse(BaseModel):
    signal_code: str
    signal: str = ""
    status: str
    search_status: str = "searched"
    not_searched_reason: str | None = None
    score: int = 0
    confidence: str = "low"
    summary: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    source_usages: list[SourceUsageResponse] = Field(default_factory=list)
    evidence_findings: list[EvidenceFindingResponse] = Field(default_factory=list)
    cross_validation: dict[str, Any] = Field(default_factory=dict)
    score_evaluation: dict[str, Any] | None = None
    review_decision: dict[str, Any] | None = None


class CandidateScoreResponse(BaseModel):
    fit_score: int | None = None
    intent_score: int | None = None
    tier: str | None = None


class RadarCandidateResponse(BaseModel):
    candidate_id: str
    legal_name: str
    description: str = ""
    score: CandidateScoreResponse
    review_flags: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    qualification: list[QualificationResponse] = Field(default_factory=list)
    signals: list[SignalResponse] = Field(default_factory=list)


class RadarSourceResponse(BaseModel):
    evidence_ref: str
    title: str = ""
    url: str = ""
    snippet: str = ""
    query_id: str | None = None
    source_type: str = "web"


class RadarRunCandidatesResponse(BaseModel):
    run_id: str
    radar_id: str
    candidates: list[RadarCandidateResponse]
    sources: list[RadarSourceResponse]
    contract_validation: list[dict[str, Any]] = Field(default_factory=list)


class RadarReviewDecisionRequest(BaseModel):
    status: str
    reviewer: str = "api"
    comment: str = ""
    corrected_assessment: str | None = None
    adjusted_score: int | None = None
    confidence: str | None = None
    corrected_summary: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    reviewed_at: datetime | None = None


class RadarReviewDecisionResponse(BaseModel):
    decision_id: str
    run_id: str
    radar_id: str
    candidate_id: str
    subject_type: str
    subject_id: str
    status: str
    reviewer: str
    comment: str
    decision_payload: dict[str, Any] = Field(default_factory=dict)
    score_impact: dict[str, Any] = Field(default_factory=dict)
    reviewed_at: datetime | None = None
    updated_at: datetime | None = None


class RadarRunReviewsResponse(BaseModel):
    run_id: str
    radar_id: str
    decisions: list[RadarReviewDecisionResponse] = Field(default_factory=list)


class RadarRunJournalEventResponse(BaseModel):
    event_id: str
    run_id: str
    sequence: int
    event_type: str
    phase: str
    actor: str
    node_name: str = ""
    visibility: str = "user"
    summary: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)
    source_refs: list[str] = Field(default_factory=list)
    candidate_refs: list[str] = Field(default_factory=list)
    created_at: datetime | None = None


class RadarRunJournalResponse(BaseModel):
    run_id: str
    radar_id: str
    events: list[RadarRunJournalEventResponse] = Field(default_factory=list)


class RadarRunTechnicalTraceItemResponse(BaseModel):
    trace_id: str
    run_id: str
    sequence: int
    phase: str
    node_name: str
    trace_type: str
    title: str
    summary: str = ""
    duration_ms: int | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    redaction_report: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class RadarRunTechnicalTraceResponse(BaseModel):
    run_id: str
    radar_id: str
    traces: list[RadarRunTechnicalTraceItemResponse] = Field(default_factory=list)


class RadarRunDossierContextResponse(BaseModel):
    run_id: str
    radar_id: str
    status: str
    live: bool
    requester: str = ""
    correlation_id: str | None = None
    idempotency_key: str | None = None
    queued_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    model: str | None = None
    web_mode: str | None = None
    runtime: str = ""
    task_context: dict[str, Any] = Field(default_factory=dict)


class RadarRunDossierDefinitionResponse(BaseModel):
    definition_id: str | None = None
    definition_version: str | None = None
    is_active: bool | None = None
    payload_summary: dict[str, Any] = Field(default_factory=dict)


class RadarRunDossierQueryResponse(BaseModel):
    query_id: str
    query: str
    purpose: str = ""
    expected_evidence: list[str] = Field(default_factory=list)
    stage: str | None = None
    subject_type: str | None = None
    subject_id: str | None = None
    rule_snapshot: str = ""
    source_scope: str = "additional"
    source_base: str | None = None
    application_scope: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    external_source_hints: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    candidate_scope: list[str] = Field(default_factory=list)
    source_count: int = 0
    source_refs: list[str] = Field(default_factory=list)
    candidate_refs: list[str] = Field(default_factory=list)


class RadarRunDossierSourceUsageResponse(BaseModel):
    candidate_id: str
    candidate_name: str = ""
    subject_type: str
    subject_id: str
    subject_label: str = ""


class RadarRunDossierSourceResponse(BaseModel):
    evidence_ref: str
    title: str = ""
    url: str = ""
    snippet: str = ""
    query_id: str | None = None
    source_type: str = "web"
    usage_status: str = "collected_not_used"
    usages: list[RadarRunDossierSourceUsageResponse] = Field(default_factory=list)


class RadarRunDossierSourceLifecycleItemResponse(BaseModel):
    evidence_ref: str
    title: str = ""
    url: str = ""
    query_id: str | None = None
    source_type: str = "web"
    state: str
    reason: str = "unknown"
    origin: str = "unknown"
    verification_state: str | None = None
    verification_mode: str | None = None
    verification_reason: str | None = None
    verification_status_code: int | None = None
    usages: list[RadarRunDossierSourceUsageResponse] = Field(default_factory=list)


class RadarRunDossierSourceLifecycleSummaryResponse(BaseModel):
    total_count: int = 0
    by_state: dict[str, int] = Field(default_factory=dict)
    by_reason: dict[str, int] = Field(default_factory=dict)


class RadarRunDossierSummaryResponse(BaseModel):
    output_state: str
    execution_outcome: str = ""
    execution_outcome_reason: str = ""
    query_count: int = 0
    source_count: int = 0
    used_source_count: int = 0
    retrieved_source_count: int = 0
    linked_source_count: int = 0
    linking_failed_source_count: int = 0
    schema_rejected_source_count: int = 0
    analyzed_source_count: int = 0
    analyzed_only_source_count: int = 0
    diagnostic_source_count: int = 0
    skipped_source_count: int = 0
    candidate_count: int = 0
    smoke_candidate_cap: int | None = None
    promoted_candidate_count: int = 0
    diagnostic_candidate_count: int = 0
    review_needed_universe_count: int = 0
    linked_branch_or_site_count: int = 0
    source_cards_count: int = 0
    source_capability_decision_count: int = 0
    connector_profile_loaded_count: int = 0
    validation_issue_count: int = 0
    review_flag_count: int = 0
    coverage_warning_count: int = 0


class RadarRunDossierResponse(BaseModel):
    run_context: RadarRunDossierContextResponse
    runtime_config: dict[str, Any] = Field(default_factory=dict)
    runtime_config_warnings: list[dict[str, Any]] = Field(default_factory=list)
    radar_snapshot: dict[str, Any] = Field(default_factory=dict)
    definition_snapshot: RadarRunDossierDefinitionResponse | None = None
    discovery_plan: dict[str, Any] = Field(default_factory=dict)
    retrieval_plan: dict[str, Any] = Field(default_factory=dict)
    source_cards: list[dict[str, Any]] = Field(default_factory=list)
    source_capability_decisions: list[dict[str, Any]] = Field(default_factory=list)
    source_capability_validation: dict[str, Any] = Field(default_factory=dict)
    source_policy_decisions: list[dict[str, Any]] = Field(default_factory=list)
    source_obligations: list[dict[str, Any]] = Field(default_factory=list)
    source_obligation_decisions: list[dict[str, Any]] = Field(default_factory=list)
    source_obligation_summary: dict[str, Any] = Field(default_factory=dict)
    coverage_summary: dict[str, Any] = Field(default_factory=dict)
    budget_summary: dict[str, Any] = Field(default_factory=dict)
    budget_exhaustion_events: list[dict[str, Any]] = Field(default_factory=list)
    checkpoint_summary: dict[str, Any] = Field(default_factory=dict)
    checkpoint_decisions: list[dict[str, Any]] = Field(default_factory=list)
    adaptive_actions: list[dict[str, Any]] = Field(default_factory=list)
    checkpoint_warnings: list[str] = Field(default_factory=list)
    stopped_for_review_reason: str = ""
    signal_search_statuses: list[dict[str, Any]] = Field(default_factory=list)
    entity_resolution_results: list[dict[str, Any]] = Field(default_factory=list)
    linked_entity_facts: list[dict[str, Any]] = Field(default_factory=list)
    entity_resolution_warnings: list[dict[str, Any]] = Field(default_factory=list)
    candidate_universe: list[dict[str, Any]] = Field(default_factory=list)
    upstream_disambiguation_results: list[dict[str, Any]] = Field(default_factory=list)
    cross_source_disambiguation_tasks: list[dict[str, Any]] = Field(default_factory=list)
    cross_source_disambiguation_execution: list[dict[str, Any]] = Field(default_factory=list)
    extraction_recovery_records: list[dict[str, Any]] = Field(default_factory=list)
    coverage_checks: list[dict[str, Any]] = Field(default_factory=list)
    coverage_warnings: list[str] = Field(default_factory=list)
    unresolved_candidate_gaps: list[dict[str, Any]] = Field(default_factory=list)
    discovery_iteration_count: int = 0
    search_plan: list[RadarRunDossierQueryResponse] = Field(default_factory=list)
    sources: list[RadarRunDossierSourceResponse] = Field(default_factory=list)
    source_lifecycle: list[RadarRunDossierSourceLifecycleItemResponse] = Field(default_factory=list)
    source_lifecycle_summary: RadarRunDossierSourceLifecycleSummaryResponse = Field(default_factory=RadarRunDossierSourceLifecycleSummaryResponse)
    validation: list[dict[str, Any]] = Field(default_factory=list)
    timeline: list[RadarRunJournalEventResponse] = Field(default_factory=list)
    summary: RadarRunDossierSummaryResponse


RadarSummaryResponse.model_rebuild()
RadarDetailResponse.model_rebuild()
RadarRunSummaryResponse.model_rebuild()
