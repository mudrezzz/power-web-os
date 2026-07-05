"""Application contracts for the standalone Radar signal-monitoring pipeline.

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
    "review_needed",
]
SignalAttemptRole = Literal["primary", "primary_retry", "backup_retry"]
SignalEntityType = Literal["legal_entity", "branch", "production_site", "project", "asset", "unknown_entity"]
SignalMonitoringSourceLane = Literal["known_source", "official_company", "signal_specific", "open_web"]
SignalMonitoringSourceDecisionStatus = Literal["selected", "skipped", "rejected"]
SignalMonitoringDiagnosticSeverity = Literal["info", "warning", "blocking"]


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
    entity_type: SignalEntityType = "legal_entity"
    monitorable: bool = True
    review_flags: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)


class SignalMonitoringSignalRule(BaseModel):
    signal_code: str
    label: str
    description: str = ""
    expected_evidence: list[str] = Field(default_factory=list)
    query_template: str = "{candidate} {signal}"


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
    max_signal_source_verifications: int | None = None
    max_signal_lookback_queries: int | None = None


class SignalSourceRef(BaseModel):
    source_ref: str
    title: str = ""
    url: str = ""
    snippet: str = ""
    source_id: str = ""
    observed_at: str = ""
    lifecycle_state: Literal["used", "retrieved", "analyzed", "verified", "linked", "unknown"] = "unknown"
    candidate_id: str = ""


class SignalMonitoringSourceDecision(BaseModel):
    decision_id: str
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
    confidence: Literal["strong", "medium", "weak"] = "medium"


class SignalSearchTask(BaseModel):
    task_id: str
    candidate_id: str
    candidate_name: str
    signal_code: str
    signal_label: str
    query: str
    lookback_days: int
    known_source_refs: list[str] = Field(default_factory=list)
    source_lane: SignalMonitoringSourceLane = "open_web"
    source_ids: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    source_decision_ids: list[str] = Field(default_factory=list)


class SignalMonitoringPlan(BaseModel):
    radar_id: str
    tasks: list[SignalSearchTask] = Field(default_factory=list)


class SignalMonitoringDiagnostic(BaseModel):
    code: str
    message: str
    task_id: str = ""
    candidate_id: str = ""
    signal_code: str = ""
    path: str = ""
    details: dict[str, Any] = Field(default_factory=dict)


class SignalProviderAttemptRecord(BaseModel):
    task_id: str
    attempt_role: SignalAttemptRole
    outcome: str
    message: str = ""


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
    fingerprint: str = ""
    diagnostics: list[SignalMonitoringDiagnostic] = Field(default_factory=list)


class SignalMonitoringInput(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    run_id: str
    radar_id: str
    model_profile_id: str = "signal_monitoring_default"
    model_profile: RadarModelProfile | None = None
    candidates: list[SignalMonitoringCandidate] = Field(default_factory=list)
    signal_rules: list[SignalMonitoringSignalRule] = Field(default_factory=list)
    known_sources: list[SignalSourceRef] = Field(default_factory=list)
    source_policy: SignalMonitoringSourcePolicy = Field(default_factory=SignalMonitoringSourcePolicy)
    source_cards: list[RadarPlannerSourceCard] = Field(default_factory=list)
    budget: SignalMonitoringBudget = Field(default_factory=SignalMonitoringBudget)
    lookback_days: int = 7
    previous_signal_fingerprints: list[str] = Field(default_factory=list)


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
    model_profile_id: str = ""
    model_profile_summary: dict[str, Any] = Field(default_factory=dict)
    tasks: list[SignalSearchTask] = Field(default_factory=list)
    observations: list[SignalObservation] = Field(default_factory=list)
    diagnostics: list[SignalMonitoringDiagnostic] = Field(default_factory=list)
    source_strategy_decisions: list[SignalMonitoringSourceDecision] = Field(default_factory=list)
    source_strategy_diagnostics: list[SignalMonitoringDiagnostic] = Field(default_factory=list)
    provider_attempts: list[SignalProviderAttemptRecord] = Field(default_factory=list)
    budget_counters: dict[str, int] = Field(default_factory=dict)


class SignalMonitoringProviderResult(BaseModel):
    payload: Any


class SignalMonitoringEvidenceProvider(Protocol):
    runtime_name: str

    def run_signal_task(
        self,
        *,
        task: SignalSearchTask,
        attempt_role: SignalAttemptRole,
    ) -> SignalMonitoringProviderResult:
        """Return provider payload for one bounded signal-monitoring task."""
