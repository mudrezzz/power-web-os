"""Executable cross-source disambiguation for review-needed Radar entities."""

from __future__ import annotations

from typing import Any

from power_web_os.application.radar.candidate_discovery.contracts import (
    LiveRadarPipelineEvent,
    RadarExecutionPlan,
    RadarExecutionTask,
    RadarSourceEvidence,
    WebSearchProvider,
)
from power_web_os.application.radar.candidate_discovery.execution.task_budget import RadarExecutionBudget
from power_web_os.application.radar.shared.budgets import RadarExternalCallBudget
from power_web_os.application.radar.candidate_discovery.execution.task_runner import TaskExecutionService


def execute_cross_source_disambiguation(
    *,
    radar: dict[str, Any],
    execution_plan: RadarExecutionPlan,
    provider: WebSearchProvider,
    sources: list[RadarSourceEvidence],
    observations: list[dict[str, Any]],
    provider_metadata: dict[str, Any],
    budget: RadarExecutionBudget,
    external_budget: RadarExternalCallBudget | None,
    events: list[LiveRadarPipelineEvent],
    executed_task_ids: list[str],
) -> tuple[list[RadarSourceEvidence], list[dict[str, Any]], dict[str, Any]]:
    task_service = TaskExecutionService()
    planned_tasks = _dedupe_planned_tasks(_dict_list(provider_metadata.get("cross_source_disambiguation_tasks")))
    if not planned_tasks:
        return sources, observations, provider_metadata

    updated_tasks: list[dict[str, Any]] = []
    execution_records: list[dict[str, Any]] = _dict_list(provider_metadata.get("cross_source_disambiguation_execution"))
    for planned in planned_tasks:
        if str(planned.get("status") or "planned") not in {"planned", ""}:
            updated_tasks.append(planned)
            continue
        source_ids = [str(item) for item in planned.get("source_ids", []) if str(item).strip()]
        entity_name = str(planned.get("entity_name") or "").strip()
        if not source_ids:
            updated = _task_outcome(planned, outcome="skipped_policy_limited", reason="No allowed cross-check source was available.")
            updated_tasks.append(updated)
            execution_records.append(updated)
            events.append(_event(updated))
            continue
        task = _execution_task_from_planned(planned, source_ids=source_ids, entity_name=entity_name)
        result = task_service.run_task(
            provider=provider,
            radar=radar,
            task=task,
            radar_id=execution_plan.radar_id,
            budget=budget,
            external_budget=external_budget,
        )
        budget_decision = result.provider_metadata.get("budget_decision")
        if isinstance(budget_decision, dict) and budget_decision.get("accepted") is False:
            updated = _task_outcome(
                planned,
                outcome="skipped_budget_limited",
                reason=str(budget_decision.get("message") or "Cross-source disambiguation budget was exhausted."),
                budget_key=str(budget_decision.get("key") or ""),
            )
        elif _schema_invalid(result.provider_metadata):
            updated = _task_outcome(planned, outcome="schema_failed", reason="Cross-source extraction failed strict schema validation.")
            sources, observations, provider_metadata = task_service.merger.merge_result(
                sources, observations, provider_metadata, result
            )
        elif result.sources or result.candidate_observations:
            sources, observations, provider_metadata = task_service.merger.merge_result(
                sources, observations, provider_metadata, result
            )
            provider_metadata = _mark_confirmed_relation(provider_metadata, planned, result)
            updated = _task_outcome(
                planned,
                outcome="confirmed_relation",
                reason="Cross-source evidence was returned for the review-needed entity.",
                source_count=len(result.sources),
                observation_count=len(result.candidate_observations),
                source_refs=[source.evidence_ref for source in result.sources if source.evidence_ref],
            )
        else:
            updated = _task_outcome(planned, outcome="no_supporting_evidence", reason="Cross-source check returned no supporting evidence.")
        updated_tasks.append(updated)
        execution_records.append(updated)
        executed_task_ids.append(f"{task.task_id}:cross_source_disambiguation")
        events.append(_event(updated))

    provider_metadata = {
        **provider_metadata,
        "cross_source_disambiguation_tasks": updated_tasks,
        "cross_source_disambiguation_execution": execution_records,
    }
    return sources, observations, provider_metadata


def _execution_task_from_planned(planned: dict[str, Any], *, source_ids: list[str], entity_name: str) -> RadarExecutionTask:
    return RadarExecutionTask(
        task_id=str(planned.get("task_id") or f"cross-check:{entity_name}"),
        stage="coverage_check",
        subject_type="radar",
        subject_id="cross_source_disambiguation",
        query=(
            f"Cross-check whether {entity_name} is connected to the configured target group or legal entity. "
            "Return only source-backed evidence for this entity."
        ),
        purpose=str(planned.get("purpose") or "Cross-check ambiguous upstream registry observation."),
        expected_evidence=["official_or_web_relation"],
        source_scope="global",
        source_ids=source_ids,
        candidate_scope=[entity_name] if entity_name else [],
    )


def _mark_confirmed_relation(
    provider_metadata: dict[str, Any],
    planned: dict[str, Any],
    result: Any,
) -> dict[str, Any]:
    entity_name = str(planned.get("entity_name") or "").strip()
    source_refs = [source.evidence_ref for source in result.sources if source.evidence_ref]
    updated_results: list[dict[str, Any]] = []
    for item in _dict_list(provider_metadata.get("upstream_disambiguation_results")):
        payload = dict(item)
        if entity_name and str(payload.get("entity_name") or payload.get("legal_name") or "").strip() == entity_name:
            payload["resolution_status"] = payload.get("resolution_status") or "review_needed"
            payload["cross_source_disambiguation_status"] = "confirmed_relation"
            payload["cross_source_refs"] = sorted(set([*_string_list(payload.get("cross_source_refs")), *source_refs]))
            payload["review_flags"] = sorted(set([*_string_list(payload.get("review_flags")), "official_source_cross_checked"]))
        updated_results.append(payload)
    linked_facts = [
        *_dict_list(provider_metadata.get("linked_entity_facts")),
        {
            "entity_name": entity_name,
            "entity_type": str(planned.get("entity_type") or "unknown_entity"),
            "resolution_status": "review_needed",
            "relation": "cross_source_supported",
            "source_refs": source_refs,
        },
    ] if entity_name and source_refs else _dict_list(provider_metadata.get("linked_entity_facts"))
    return {
        **provider_metadata,
        "upstream_disambiguation_results": updated_results,
        "linked_entity_facts": linked_facts,
    }


def _task_outcome(
    planned: dict[str, Any],
    *,
    outcome: str,
    reason: str,
    budget_key: str = "",
    source_count: int = 0,
    observation_count: int = 0,
    source_refs: list[str] | None = None,
) -> dict[str, Any]:
    return {
        **planned,
        "status": "executed" if outcome in {"confirmed_relation", "no_supporting_evidence", "schema_failed"} else "skipped",
        "outcome": outcome,
        "reason": reason,
        "budget_key": budget_key,
        "source_count": source_count,
        "observation_count": observation_count,
        "source_refs": source_refs or [],
    }


def _event(payload: dict[str, Any]) -> LiveRadarPipelineEvent:
    outcome = str(payload.get("outcome") or "unknown")
    return LiveRadarPipelineEvent(
        event_type=(
            "cross_source_disambiguation_confirmed"
            if outcome == "confirmed_relation"
            else "cross_source_disambiguation_unresolved"
            if outcome == "no_supporting_evidence"
            else "cross_source_disambiguation_skipped"
        ),
        phase="validation",
        actor="application",
        node_name="cross_source_disambiguation",
        visibility="operator",
        summary=f"Cross-source disambiguation {outcome} for {payload.get('entity_name') or 'entity'}.",
        payload=payload,
        source_refs=[str(item) for item in payload.get("source_refs", [])],
        candidate_refs=[str(payload.get("entity_name"))] if payload.get("entity_name") else [],
    )


def _schema_invalid(metadata: dict[str, Any]) -> bool:
    for item in _dict_list(metadata.get("extraction_validation_results")):
        if str(item.get("state")) == "extraction_schema_invalid":
            return True
    for item in _dict_list(metadata.get("extraction_validation_issues")):
        if str(item.get("severity")) == "error":
            return True
    return False


def _dedupe_planned_tasks(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, str, tuple[str, ...]]] = set()
    for item in tasks:
        key = (
            str(item.get("task_id") or ""),
            str(item.get("entity_name") or ""),
            tuple(str(source_id) for source_id in item.get("source_ids", []) if str(source_id).strip()),
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(dict(item))
    return result


def _dict_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]
