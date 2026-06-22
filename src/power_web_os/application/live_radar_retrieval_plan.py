"""Compact retrieval task contracts for live Radar provider execution."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from power_web_os.application.live_radar_contracts import (
    RadarExecutionPlan,
    RadarExecutionStage,
    RadarExecutionSubjectType,
    RadarExecutionTask,
    RadarSearchPlan,
    RadarSearchQuery,
)


class RadarResponseContract(BaseModel):
    """Short task-specific schema hint for provider prompts."""

    schema_id: str
    expected_sections: list[str] = Field(default_factory=list)
    required_fields: list[str] = Field(default_factory=list)


class RadarRetrievalTask(BaseModel):
    """Executable task card accepted by backend planning and sent to providers."""

    task_id: str
    stage: RadarExecutionStage
    subject_type: RadarExecutionSubjectType
    subject_id: str
    query: str
    purpose: str
    expected_evidence: list[str] = Field(default_factory=list)
    rule_snapshot: str = ""
    source_scope: str = "additional"
    source_base: str | None = None
    application_scope: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    external_source_hints: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    candidate_scope: list[str] = Field(default_factory=list)
    response_contract: RadarResponseContract


class RadarRetrievalPlan(BaseModel):
    """Accepted retrieval task list used for dossier and trace inspection."""

    radar_id: str
    tasks: list[RadarRetrievalTask]


class RadarRetrievalTaskPrompt(BaseModel):
    """Provider-neutral compact prompt payload before adapter-specific wrapping."""

    task_card: dict[str, Any]
    response_contract: dict[str, Any]
    constraints: list[str]


def retrieval_plan_from_execution_plan(plan: RadarExecutionPlan) -> RadarRetrievalPlan:
    return RadarRetrievalPlan(
        radar_id=plan.radar_id,
        tasks=[retrieval_task_from_execution_task(task) for task in plan.tasks],
    )


def retrieval_task_from_execution_task(task: RadarExecutionTask) -> RadarRetrievalTask:
    return RadarRetrievalTask(
        task_id=task.task_id,
        stage=task.stage,
        subject_type=task.subject_type,
        subject_id=task.subject_id,
        query=_query_with_scope(task.query, task.candidate_scope),
        purpose=task.purpose,
        expected_evidence=list(task.expected_evidence),
        rule_snapshot=task.rule_snapshot,
        source_scope=task.source_scope,
        source_base=task.source_base,
        application_scope=task.application_scope,
        source_ids=list(task.source_ids),
        external_source_hints=list(task.external_source_hints),
        depends_on=list(task.depends_on),
        candidate_scope=list(task.candidate_scope),
        response_contract=response_contract_for_stage(task.stage, task.subject_id),
    )


def retrieval_task_from_search_query(query: RadarSearchQuery) -> RadarRetrievalTask:
    return RadarRetrievalTask(
        task_id=query.query_id,
        stage=query.stage,
        subject_type=query.subject_type,
        subject_id=query.subject_id,
        query=query.query,
        purpose=query.purpose,
        expected_evidence=list(query.expected_evidence),
        rule_snapshot=query.rule_snapshot,
        source_scope=query.source_scope,
        source_base=query.source_base,
        application_scope=query.application_scope,
        source_ids=list(query.source_ids),
        external_source_hints=list(query.external_source_hints),
        depends_on=list(query.depends_on),
        candidate_scope=list(query.candidate_scope),
        response_contract=response_contract_for_stage(query.stage, query.subject_id),
    )


def retrieval_plan_to_search_plan(plan: RadarRetrievalPlan) -> RadarSearchPlan:
    return RadarSearchPlan(
        radar_id=plan.radar_id,
        queries=[retrieval_task_to_search_query(task) for task in plan.tasks],
    )


def retrieval_task_to_search_plan(task: RadarRetrievalTask, *, radar_id: str) -> RadarSearchPlan:
    return RadarSearchPlan(radar_id=radar_id, queries=[retrieval_task_to_search_query(task)])


def retrieval_task_to_search_query(task: RadarRetrievalTask) -> RadarSearchQuery:
    return RadarSearchQuery(
        query_id=task.task_id,
        query=task.query,
        purpose=task.purpose,
        expected_evidence=list(task.expected_evidence),
        stage=task.stage,
        subject_type=task.subject_type,
        subject_id=task.subject_id,
        rule_snapshot=task.rule_snapshot,
        source_scope=task.source_scope,
        source_base=task.source_base,
        application_scope=task.application_scope,
        source_ids=list(task.source_ids),
        external_source_hints=list(task.external_source_hints),
        depends_on=list(task.depends_on),
        candidate_scope=list(task.candidate_scope),
    )


def response_contract_for_stage(stage: RadarExecutionStage, subject_id: str) -> RadarResponseContract:
    if stage == "signal_search":
        return RadarResponseContract(
            schema_id="signal_finding_v1",
            expected_sections=["sources", "candidates.signals", "source_outcomes"],
            required_fields=["signal_code", "status", "score", "evidence_refs"],
        )
    if stage == "coverage_check":
        return RadarResponseContract(
            schema_id="coverage_check_v1",
            expected_sections=["sources", "candidate_universe_gaps", "coverage_findings", "source_outcomes"],
            required_fields=["legal_name", "source_refs", "completeness_risk"],
        )
    return RadarResponseContract(
        schema_id="qualification_finding_v1",
        expected_sections=["sources", "candidates.qualification", "source_outcomes"],
        required_fields=[subject_id, "status", "evidence_refs"],
    )


def stage_task_label(stage: RadarExecutionStage) -> str:
    labels: dict[str, str] = {
        "qualification_discovery": "Discover candidate accounts for this qualification rule only.",
        "qualification_gate": "Filter the candidate scope through this qualification rule only.",
        "coverage_check": "Check candidate universe coverage and return source-backed gaps.",
        "signal_search": "Search the candidate scope for this one intent signal only.",
    }
    return labels.get(stage, "Run this bounded Radar task.")


def _query_with_scope(query: str, candidate_scope: list[str]) -> str:
    if not candidate_scope:
        return query
    value = " ".join([query, "Candidate scope:", "; ".join(candidate_scope)])
    return " ".join(value.split())[:700]
