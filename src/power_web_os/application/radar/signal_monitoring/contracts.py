"""Contracts for the standalone Radar signal-monitoring pipeline.

These models describe the no-network signal-monitoring harness introduced
before live providers, persistence, workers, or UI controls. They intentionally
separate the product signal state from the search execution state so
``not_observed`` can only mean "searched and no signal found".
"""

from __future__ import annotations

from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field

from power_web_os.application.radar.shared.source_cards import RadarPlannerSourceCard
from power_web_os.application.radar_model_profiles import RadarModelProfile


SignalObservationStatus = Literal["observed", "not_observed", "unclear"]
SignalSearchStatus = Literal[
    "searched",
    "not_searched_budget_limited",
    "not_searched_policy_limited",
    "not_searched_missing_candidate_scope",
    "schema_recovery_needed",
    "evidence_linking_failed",
    "duplicate_existing_signal",
    "duplicate_existing_review",
    "review_needed_date_unknown",
    "review_needed_date_conflict",
    "rejected_out_of_window",
    "review_needed",
]
SignalAttemptRole = Literal["primary", "primary_retry", "backup_retry"]
SignalEntityType = Literal["legal_entity", "branch", "production_site", "project", "asset", "unknown_entity"]
SignalMonitoringSourceLane = Literal["known_source", "official_company", "signal_specific", "open_web"]
SignalMonitoringSourceDecisionStatus = Literal["selected", "skipped", "rejected"]
SignalMonitoringDiagnosticSeverity = Literal["info", "warning", "blocking"]
SignalMonitoringCandidateScopeMode = Literal["accepted_and_review_needed", "accepted_only"]
SignalMonitoringCompletionState = Literal["completed", "completed_with_limits", "failed"]
SignalLaneExecutionStatus = Literal[
    "scheduled",
    "executed",
    "not_scheduled_budget_limited",
    "not_executable",
    "policy_limited",
]
SignalReceiptOutcome = Literal["retrieved", "no_results", "provider_error", "schema_invalid", "budget_limited"]
SignalTemporalStatus = Literal[
    "not_applicable",
    "confirmed_in_window",
    "review_needed_date_unknown",
    "review_needed_date_conflict",
    "rejected_out_of_window",
]
SignalDateBasis = Literal["json_ld", "open_graph", "html_time", "url", "title", "snippet", "provider_extracted", "none"]
SignalSourceCapability = Literal[
    "identity_only",
    "official_press",
    "event_feed",
    "project_or_asset_history",
    "registry",
    "generic_web",
    "unknown",
]
SignalSourceBindingStatus = Literal["matched_candidate", "group_only", "cross_entity", "unknown_owner", "no_url"]


class SignalMonitoringSourceHint(BaseModel):
    source_id: str
    label: str = ""
    connector_profile_id: str = ""
    source_type: str = ""
    query_template: str = ""


class SignalMonitoringCandidate(BaseModel):
    candidate_id: str
    display_name: str
    legal_name: str = ""
    aliases: list[str] = Field(default_factory=list)
    entity_type: SignalEntityType = "legal_entity"
    monitorable: bool = True
    review_flags: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    candidate_surface_status: str = "review_needed_candidate"
    product_acceptance_status: str = "review_required"


class SignalMonitoringSignalRule(BaseModel):
    signal_code: str
    label: str
    description: str = ""
    expected_evidence: list[str] = Field(default_factory=list)
    query_template: str = "{candidate} {signal}"
    initial_lookback_days: int | None = Field(default=None, ge=1, le=3650)
    source_ids: list[str] = Field(default_factory=list)


class SignalMonitoringSourcePolicy(BaseModel):
    enabled: bool = True
    allowed_source_ids: list[str] = Field(default_factory=list)
    preferred_source_ids: list[str] = Field(default_factory=list)
    required_source_ids: list[str] = Field(default_factory=list)
    fallback_source_ids: list[str] = Field(default_factory=list)
    official_source_ids: list[str] = Field(default_factory=list)
    signal_source_hints: list[SignalMonitoringSourceHint] = Field(default_factory=list)
    reuse_known_sources: bool = True
    allow_open_web: bool = True


class SignalMonitoringBudget(BaseModel):
    max_tasks: int = 20
    max_provider_calls: int = 20
    max_retries_per_task: int = 1
    allow_backup_retry: bool = True
    max_signal_tasks: int | None = None
    max_signal_provider_calls: int | None = None
    max_signal_extraction_retries: int | None = None
    max_signal_backup_retries: int | None = None
    max_signal_source_verifications: int | None = None
    max_signal_lookback_queries: int | None = None
    max_query_revisions_per_candidate_signal: int = 1


class SignalSourceRef(BaseModel):
    source_ref: str
    title: str = ""
    url: str = ""
    snippet: str = ""
    source_id: str = ""
    observed_at: str = ""
    retrieved_at: str = ""
    published_at: str = ""
    date_basis: SignalDateBasis = "none"
    date_confidence: Literal["strong", "medium", "weak"] = "weak"
    date_evidence: str = ""
    date_conflict: bool = False
    capability: SignalSourceCapability = "unknown"
    capability_basis: str = ""
    lifecycle_state: Literal["used", "retrieved", "analyzed", "verified", "linked", "unknown"] = "unknown"
    candidate_id: str = ""


class SignalMonitoringWatermark(BaseModel):
    candidate_id: str
    signal_code: str
    source_lane: SignalMonitoringSourceLane
    searched_through_at: str
    source_task_id: str = ""


class SignalMonitoringWindow(BaseModel):
    candidate_id: str
    signal_code: str
    source_lane: SignalMonitoringSourceLane
    window_start: str
    window_end: str
    basis: Literal["explicit_override", "criterion_policy", "radar_policy", "default_365", "incremental"]
    lookback_days: int
    overlap_days: int = 0
    previous_watermark: str = ""


class SignalMonitoringSourceDecision(BaseModel):
    decision_id: str
    candidate_id: str = ""
    lane: SignalMonitoringSourceLane
    status: SignalMonitoringSourceDecisionStatus
    reason: str
    source_id: str = ""
    source_ref: str = ""
    source_refs: list[str] = Field(default_factory=list)
    connector_profile_id: str = ""
    supports_signal_evidence: bool = False
    required: bool = False
    diagnostic_severity: SignalMonitoringDiagnosticSeverity = "info"


class SignalMonitoringSourceStrategyResult(BaseModel):
    decisions: list[SignalMonitoringSourceDecision] = Field(default_factory=list)
    diagnostics: list["SignalMonitoringDiagnostic"] = Field(default_factory=list)
    selected_decision_ids: list[str] = Field(default_factory=list)


class SignalEvidence(BaseModel):
    source_ref: str
    fact: str
    excerpt: str = ""
    observed_at: str = ""
    event_at: str = ""
    event_end_at: str = ""
    published_at: str = ""
    temporal_status: SignalTemporalStatus = "not_applicable"
    date_basis: SignalDateBasis = "none"
    date_confidence: Literal["strong", "medium", "weak"] = "weak"
    date_evidence: str = ""
    confidence: Literal["strong", "medium", "weak"] = "medium"


class SignalSearchTask(BaseModel):
    task_id: str
    candidate_id: str
    candidate_name: str
    candidate_aliases: list[str] = Field(default_factory=list)
    signal_code: str
    signal_label: str
    query: str
    alternate_query: str = ""
    lookback_days: int
    known_source_refs: list[str] = Field(default_factory=list)
    source_lane: SignalMonitoringSourceLane = "open_web"
    source_ids: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    source_decision_ids: list[str] = Field(default_factory=list)
    source_contracts: list[SignalSourceRef] = Field(default_factory=list)
    domain_restrictions: list[str] = Field(default_factory=list)
    required: bool = True
    window_start: str = ""
    window_end: str = ""
    window_basis: str = ""
    revision_index: int = 0


class SignalMonitoringPlan(BaseModel):
    radar_id: str
    tasks: list[SignalSearchTask] = Field(default_factory=list)


class SignalMonitoringPlanAcceptance(BaseModel):
    accepted: bool = True
    tasks: list[SignalSearchTask] = Field(default_factory=list)
    rejected_tasks: list[SignalSearchTask] = Field(default_factory=list)
    corrections: list[dict[str, Any]] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SignalSourceLaneLedgerEntry(BaseModel):
    task_id: str
    candidate_id: str
    signal_code: str
    source_lane: SignalMonitoringSourceLane
    required: bool
    status: SignalLaneExecutionStatus
    reason: str = ""
    source_decision_ids: list[str] = Field(default_factory=list)


class SignalSearchExecutionReceipt(BaseModel):
    task_id: str
    candidate_id: str
    signal_code: str
    source_lane: SignalMonitoringSourceLane
    query: str
    requested_urls: list[str] = Field(default_factory=list)
    requested_domains: list[str] = Field(default_factory=list)
    engine: str = ""
    window_start: str = ""
    window_end: str = ""
    started_at: str = ""
    completed_at: str = ""
    result_count: int = 0
    source_refs: list[str] = Field(default_factory=list)
    outcome: SignalReceiptOutcome


class SignalSourceLifecycleRecord(BaseModel):
    task_id: str
    source_ref: str = ""
    source_lane: SignalMonitoringSourceLane
    state: Literal["planned", "requested", "retrieved", "verified", "linked", "used", "no_results", "rejected", "failed"]
    reason: str = ""


class SignalEvidenceValidationRecord(BaseModel):
    task_id: str
    candidate_id: str
    signal_code: str
    accepted: bool
    reason: str
    source_refs: list[str] = Field(default_factory=list)
    temporal_status: SignalTemporalStatus = "not_applicable"
    details: dict[str, Any] = Field(default_factory=dict)


class SignalSourceBindingDecision(BaseModel):
    candidate_id: str
    source_ref: str
    status: SignalSourceBindingStatus
    capability: SignalSourceCapability
    reason: str
    basis: str = ""
    confidence: Literal["strong", "medium", "weak"] = "weak"
    scheduled_as_known_source: bool = False


class SignalSourceTemporalMetadata(BaseModel):
    source_ref: str
    published_at: str = ""
    date_basis: SignalDateBasis = "none"
    date_confidence: Literal["strong", "medium", "weak"] = "weak"
    date_evidence: str = ""
    conflicting: bool = False


class SignalMonitoringCheckpointDecision(BaseModel):
    candidate_id: str
    signal_code: str
    action: Literal["observed", "not_observed", "revise_query", "review_needed_coverage_incomplete"]
    reason: str
    required_task_count: int = 0
    completed_required_task_count: int = 0
    task_ids: list[str] = Field(default_factory=list)


class SignalMonitoringDiagnostic(BaseModel):
    code: str
    message: str
    task_id: str = ""
    candidate_id: str = ""
    signal_code: str = ""
    path: str = ""
    details: dict[str, Any] = Field(default_factory=dict)


class SignalProviderAttemptRecord(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    task_id: str
    attempt_role: SignalAttemptRole
    outcome: str
    message: str = ""
    provider_runtime: str = ""
    model_id: str = ""
    attempt_index: int = 1


class SignalObservation(BaseModel):
    task_id: str
    candidate_id: str
    signal_code: str
    observation_status: SignalObservationStatus
    search_status: SignalSearchStatus
    summary: str = ""
    score: int = 0
    evidence: list[SignalEvidence] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    sources: list[SignalSourceRef] = Field(default_factory=list)
    fingerprint: str = ""
    diagnostics: list[SignalMonitoringDiagnostic] = Field(default_factory=list)


class SignalMonitoringInput(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    run_id: str
    radar_id: str
    source_candidate_run_id: str = ""
    candidate_scope_mode: SignalMonitoringCandidateScopeMode = "accepted_and_review_needed"
    model_profile_id: str = "signal_monitoring_default"
    model_profile: RadarModelProfile | None = None
    candidates: list[SignalMonitoringCandidate] = Field(default_factory=list)
    signal_rules: list[SignalMonitoringSignalRule] = Field(default_factory=list)
    known_sources: list[SignalSourceRef] = Field(default_factory=list)
    configured_sources: list[SignalSourceRef] = Field(default_factory=list)
    source_policy: SignalMonitoringSourcePolicy = Field(default_factory=SignalMonitoringSourcePolicy)
    source_cards: list[RadarPlannerSourceCard] = Field(default_factory=list)
    budget: SignalMonitoringBudget = Field(default_factory=SignalMonitoringBudget)
    lookback_days: int = 365
    lookback_basis: Literal["explicit_override", "criterion_policy", "radar_policy", "default_365"] = "default_365"
    as_of: str = ""
    incremental_overlap_days: int = 2
    previous_signal_fingerprints: list[str] = Field(default_factory=list)
    previous_signal_source_keys: list[str] = Field(default_factory=list)
    previous_watermarks: list[SignalMonitoringWatermark] = Field(default_factory=list)
    source_binding_decisions: list[SignalSourceBindingDecision] = Field(default_factory=list)


class SignalMonitoringRun(BaseModel):
    run_id: str
    radar_id: str
    status: Literal["planned", "completed", "failed"] = "planned"
    monitoring_input: SignalMonitoringInput | None = None
    plan: SignalMonitoringPlan | None = None


class SignalMonitoringOutcome(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    run_id: str
    radar_id: str
    source_candidate_run_id: str = ""
    candidate_scope_mode: SignalMonitoringCandidateScopeMode = "accepted_and_review_needed"
    completion_state: SignalMonitoringCompletionState = "completed"
    model_profile_id: str = ""
    model_profile_summary: dict[str, Any] = Field(default_factory=dict)
    tasks: list[SignalSearchTask] = Field(default_factory=list)
    observations: list[SignalObservation] = Field(default_factory=list)
    sources: list[SignalSourceRef] = Field(default_factory=list)
    diagnostics: list[SignalMonitoringDiagnostic] = Field(default_factory=list)
    source_strategy_decisions: list[SignalMonitoringSourceDecision] = Field(default_factory=list)
    source_strategy_diagnostics: list[SignalMonitoringDiagnostic] = Field(default_factory=list)
    provider_attempts: list[SignalProviderAttemptRecord] = Field(default_factory=list)
    search_plan: SignalMonitoringPlan | None = None
    plan_acceptance: SignalMonitoringPlanAcceptance | None = None
    task_observations: list[SignalObservation] = Field(default_factory=list)
    source_lane_ledger: list[SignalSourceLaneLedgerEntry] = Field(default_factory=list)
    search_execution_receipts: list[SignalSearchExecutionReceipt] = Field(default_factory=list)
    source_lifecycle: list[SignalSourceLifecycleRecord] = Field(default_factory=list)
    effective_windows: list[SignalMonitoringWindow] = Field(default_factory=list)
    watermarks_before: list[SignalMonitoringWatermark] = Field(default_factory=list)
    watermarks_after: list[SignalMonitoringWatermark] = Field(default_factory=list)
    evidence_validation_records: list[SignalEvidenceValidationRecord] = Field(default_factory=list)
    checkpoint_decisions: list[SignalMonitoringCheckpointDecision] = Field(default_factory=list)
    source_binding_decisions: list[SignalSourceBindingDecision] = Field(default_factory=list)
    budget_counters: dict[str, int] = Field(default_factory=dict)
    budget_settings: dict[str, Any] = Field(default_factory=dict)
    budget_exhaustion_events: list[dict[str, Any]] = Field(default_factory=list)


class SignalMonitoringProviderResult(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    payload: Any
    runtime_name: str = ""
    model_id: str = ""
    execution_receipt: SignalSearchExecutionReceipt | None = None


class SignalMonitoringEvidenceProvider(Protocol):
    runtime_name: str

    def run_signal_task(
        self,
        *,
        task: SignalSearchTask,
        attempt_role: SignalAttemptRole,
    ) -> SignalMonitoringProviderResult:
        """Return provider payload for one bounded signal-monitoring task."""


class SignalSourceMetadataProvider(Protocol):
    def resolve(self, source: SignalSourceRef) -> SignalSourceTemporalMetadata:
        """Return product-safe publication metadata for one source URL."""
