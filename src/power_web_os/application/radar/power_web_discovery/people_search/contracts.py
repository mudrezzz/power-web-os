"""Provider-neutral contracts for the bounded people-search stage."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import PowerWebContract, RoleDemand


PeopleSourceLane = Literal["official_company", "hh_public_web", "generic_web"]
LaneDecisionStatus = Literal[
    "scheduled",
    "executed",
    "not_executable",
    "unsupported",
    "policy_limited",
    "budget_limited",
]
SearchTerminalOutcome = Literal[
    "searched_results",
    "searched_no_results",
    "provider_error",
    "schema_error",
]
CoverageState = Literal[
    "complete_with_leads",
    "complete_no_leads",
    "incomplete_capability",
    "incomplete_provider",
    "incomplete_budget",
    "incomplete_policy",
]


class PowerWebPeopleSearchPlanningInput(PowerWebContract):
    handoff_id: str = Field(min_length=1)
    account_id: str = Field(min_length=1)
    account_legal_name: str = Field(min_length=1)
    account_aliases: tuple[str, ...] = ()
    official_domains: tuple[str, ...] = ()
    official_domain_evidence_refs: tuple[str, ...] = ()
    geography: str | None = None
    language: str = Field(min_length=2, max_length=8)
    source_candidate_run_id: str = Field(min_length=1)
    source_signal_run_id: str | None = None
    role_demands: tuple[RoleDemand, ...] = Field(min_length=1)
    as_of: datetime

    @model_validator(mode="after")
    def require_unique_demand_lineage(self) -> "PowerWebPeopleSearchPlanningInput":
        demand_ids = [item.demand_id for item in self.role_demands]
        if len(demand_ids) != len(set(demand_ids)):
            raise ValueError("people-search planning input contains duplicate demand ids")
        if self.official_domains and not self.official_domain_evidence_refs:
            raise ValueError("official domains require source evidence refs")
        return self


class AccountRoleTitleHypothesisProposal(PowerWebContract):
    proposal_id: str = Field(min_length=1)
    demand_id: str = Field(min_length=1)
    account_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    sales_playbook_version_id: str = Field(min_length=1)
    buying_role_policy_version_id: str = Field(min_length=1)
    semantic_role_code: str = Field(min_length=1)
    title_or_function: str = Field(min_length=1, max_length=180)
    rationale: str = Field(default="", max_length=500)
    language: str = Field(min_length=2, max_length=8)
    origin: Literal["provider", "deterministic_fallback"]


class AcceptedAccountRoleTitleHypothesis(PowerWebContract):
    hypothesis_id: str = Field(min_length=1)
    proposal_id: str = Field(min_length=1)
    demand_id: str = Field(min_length=1)
    account_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    sales_playbook_version_id: str = Field(min_length=1)
    buying_role_policy_version_id: str = Field(min_length=1)
    semantic_role_code: str = Field(min_length=1)
    title_or_function: str = Field(min_length=1, max_length=180)
    language: str = Field(min_length=2, max_length=8)
    origin: Literal["provider", "deterministic_fallback"]


class TitleHypothesisAcceptanceDecision(PowerWebContract):
    proposal_id: str = Field(min_length=1)
    demand_id: str = Field(min_length=1)
    accepted: bool
    reason_code: str = Field(min_length=1)
    hypothesis_id: str | None = None


class PeopleSourceLaneDecision(PowerWebContract):
    decision_id: str = Field(min_length=1)
    demand_id: str = Field(min_length=1)
    account_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    sales_playbook_version_id: str = Field(min_length=1)
    buying_role_policy_version_id: str = Field(min_length=1)
    semantic_role_code: str = Field(min_length=1)
    lane: PeopleSourceLane
    mandatory: bool = True
    status: LaneDecisionStatus
    reason_code: str = Field(min_length=1)
    domain_restrictions: tuple[str, ...] = ()


class PeopleSearchTask(PowerWebContract):
    task_id: str = Field(min_length=1)
    decision_id: str = Field(min_length=1)
    demand_id: str = Field(min_length=1)
    account_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    sales_playbook_version_id: str = Field(min_length=1)
    buying_role_policy_version_id: str = Field(min_length=1)
    semantic_role_code: str = Field(min_length=1)
    hypothesis_ids: tuple[str, ...] = Field(min_length=1)
    lane: PeopleSourceLane
    query: str = Field(min_length=1, max_length=1200)
    domain_restrictions: tuple[str, ...] = ()
    revision: int = Field(default=0, ge=0, le=1)

    @model_validator(mode="after")
    def enforce_hh_public_web_contract(self) -> "PeopleSearchTask":
        if self.lane == "hh_public_web" and self.domain_restrictions != ("hh.ru",):
            raise ValueError("HH public-web tasks require the hh.ru domain restriction")
        return self


class PeopleSearchProviderSource(PowerWebContract):
    source_ref: str = Field(min_length=1)
    url: str = Field(pattern=r"^https?://")
    title: str = Field(min_length=1, max_length=500)
    excerpt: str = Field(default="", max_length=1200)
    rank: int = Field(ge=1)
    page_access_limited: bool = False


class PeopleSearchProviderResult(PowerWebContract):
    outcome: Literal["searched_results", "searched_no_results"]
    sources: tuple[PeopleSearchProviderSource, ...] = ()
    engine: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    server_tool_searches: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def align_outcome_and_sources(self) -> "PeopleSearchProviderResult":
        if self.outcome == "searched_results" and not self.sources:
            raise ValueError("searched_results requires at least one source")
        if self.outcome == "searched_no_results" and self.sources:
            raise ValueError("searched_no_results cannot contain sources")
        return self


class PeopleSearchProviderAttempt(PowerWebContract):
    attempt_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    attempt_number: int = Field(ge=1, le=2)
    started_at: datetime
    completed_at: datetime
    outcome: SearchTerminalOutcome
    engine: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    error_code: str | None = None
    server_tool_searches: int = Field(default=0, ge=0)


class PeopleSearchExecutionReceipt(PowerWebContract):
    receipt_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    decision_id: str = Field(min_length=1)
    demand_id: str = Field(min_length=1)
    account_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    semantic_role_code: str = Field(min_length=1)
    lane: PeopleSourceLane
    query: str = Field(min_length=1)
    domain_restrictions: tuple[str, ...] = ()
    started_at: datetime
    completed_at: datetime
    terminal_outcome: SearchTerminalOutcome
    result_count: int = Field(ge=0)
    source_refs: tuple[str, ...] = ()
    attempts: tuple[PeopleSearchProviderAttempt, ...] = Field(min_length=1)


class PeopleSourceLead(PowerWebContract):
    lead_id: str = Field(min_length=1)
    source_ref: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    receipt_id: str = Field(min_length=1)
    demand_id: str = Field(min_length=1)
    account_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    semantic_role_code: str = Field(min_length=1)
    lane: PeopleSourceLane
    url: str = Field(pattern=r"^https?://")
    title: str = Field(min_length=1, max_length=500)
    excerpt: str = Field(default="", max_length=1200)
    page_access_limited: bool = False
    relevance: Literal["account_role_relevant", "account_only", "role_only", "unclear"]
    retained: bool = True
    retained_reason: str = Field(min_length=1)


class RoleCoverageCheckpoint(PowerWebContract):
    checkpoint_id: str = Field(min_length=1)
    demand_id: str = Field(min_length=1)
    account_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    semantic_role_code: str = Field(min_length=1)
    required_lanes: tuple[PeopleSourceLane, ...]
    completed_lanes: tuple[PeopleSourceLane, ...]
    lead_ids: tuple[str, ...] = ()
    state: CoverageState
    reason_code: str = Field(min_length=1)


class PeopleSearchBudgetSettings(PowerWebContract):
    profile_id: Literal["people_search_quality"] = "people_search_quality"
    max_role_demands: int = 8
    max_hypothesis_provider_calls: int = 2
    max_proposed_hypotheses_per_role: int = 5
    max_accepted_hypotheses_per_role: int = 3
    max_initial_tasks: int = 24
    max_people_search_tasks: int = 40
    max_provider_calls: int = 48
    max_source_verifications: int = 80
    max_query_revisions_per_role_lane: int = 1
    max_provider_retries_per_task: int = 1
    hh_reserve: int = 8
    official_reserve: int = 8
    generic_reserve: int = 8
    recovery_reserve: int = 16


class PeopleSearchBudgetReport(PowerWebContract):
    settings: PeopleSearchBudgetSettings
    hypothesis_provider_calls: int = Field(ge=0)
    people_search_tasks: int = Field(ge=0)
    provider_calls: int = Field(ge=0)
    source_verifications: int = Field(ge=0)
    retries: int = Field(ge=0)
    query_revisions: int = Field(default=0, ge=0)
    exhaustion_events: tuple[str, ...] = ()


class PeopleSearchStageArtifact(PowerWebContract):
    schema_version: Literal["people_search_stage.v1"] = "people_search_stage.v1"
    stage_id: str = Field(min_length=1)
    pipeline_id: Literal["power_web_discovery"] = "power_web_discovery"
    handoff_id: str = Field(min_length=1)
    account_id: str = Field(min_length=1)
    source_candidate_run_id: str = Field(min_length=1)
    source_signal_run_id: str | None = None
    run_profile: Literal["people_search_quality"] = "people_search_quality"
    model_profile_id: str = Field(min_length=1)
    provider_runtime: str = Field(min_length=1)
    planning_input: PowerWebPeopleSearchPlanningInput
    proposed_hypotheses: tuple[AccountRoleTitleHypothesisProposal, ...]
    accepted_hypotheses: tuple[AcceptedAccountRoleTitleHypothesis, ...]
    hypothesis_acceptance: tuple[TitleHypothesisAcceptanceDecision, ...]
    lane_decisions: tuple[PeopleSourceLaneDecision, ...]
    tasks: tuple[PeopleSearchTask, ...]
    receipts: tuple[PeopleSearchExecutionReceipt, ...]
    source_leads: tuple[PeopleSourceLead, ...]
    checkpoints: tuple[RoleCoverageCheckpoint, ...]
    budgets: PeopleSearchBudgetReport
    completion_state: Literal["completed", "completed_with_limits"]
    diagnostics: tuple[str, ...] = ()
    controls_in_planning_count: Literal[0] = 0
    hh_api_calls: Literal[0] = 0
    raw_provider_payload_retained: Literal[False] = False
    raw_html_retained: Literal[False] = False
    credentials_retained: Literal[False] = False
    private_contacts_retained: Literal[False] = False
    hidden_reasoning_retained: Literal[False] = False

    @model_validator(mode="after")
    def enforce_audit_completeness(self) -> "PeopleSearchStageArtifact":
        decision_ids = {item.decision_id for item in self.lane_decisions}
        task_decisions = {item.decision_id for item in self.tasks}
        receipt_tasks = {item.task_id for item in self.receipts}
        missing_tasks = {
            item.decision_id for item in self.lane_decisions if item.status == "executed"
        } - task_decisions
        executed_decisions = {
            item.decision_id for item in self.lane_decisions if item.status == "executed"
        }
        missing_receipts = {
            item.task_id for item in self.tasks if item.decision_id in executed_decisions
        } - receipt_tasks
        if missing_tasks:
            raise ValueError(f"executed lane decisions without tasks: {sorted(missing_tasks)}")
        if missing_receipts:
            raise ValueError(f"executed tasks without receipts: {sorted(missing_receipts)}")
        if task_decisions - decision_ids:
            raise ValueError("people-search tasks contain orphan lane decisions")
        return self
