"""Record checkpoint decisions into candidate-discovery execution state."""

from __future__ import annotations

from typing import Any

from .models import RadarExecutionCheckpointInput
from .policy import RadarExecutionCheckpointService
from power_web_os.application.radar.candidate_discovery.contracts import LiveRadarPipelineEvent, RadarSourceEvidence
from power_web_os.application.radar.candidate_discovery.execution.task_budget import RadarExecutionBudget


def record_execution_checkpoint(
    *,
    checkpoint_id: str,
    phase: str,
    service: RadarExecutionCheckpointService,
    candidate_count: int,
    sources: list[RadarSourceEvidence],
    observations: list[dict[str, Any]],
    provider_metadata: dict[str, Any],
    candidate_scope: list[str],
    coverage_checks: list[dict[str, Any]],
    coverage_warnings: list[str],
    unresolved_candidate_gaps: list[dict[str, Any]],
    budget: RadarExecutionBudget,
    useful_result_retry_records: list[dict[str, Any]],
    source_obligation_decisions: list[dict[str, Any]],
    checkpoint_decisions: list[dict[str, Any]],
    adaptive_actions: list[dict[str, Any]],
    checkpoint_warnings: list[str],
    events: list[LiveRadarPipelineEvent],
):
    checkpoint = RadarExecutionCheckpointInput(
        checkpoint_id=checkpoint_id,
        phase=phase,  # type: ignore[arg-type]
        candidate_count=candidate_count,
        candidate_scope_count=len(candidate_scope),
        source_count=len(sources),
        retrieved_source_count=_retrieved_source_count(provider_metadata),
        linked_source_count=_linked_source_count(observations, sources),
        diagnostic_source_count=_diagnostic_source_count(provider_metadata),
        analyzed_source_count=_analyzed_source_count(provider_metadata),
        search_expansion_target_count=len(_dict_list(provider_metadata.get("expansion_target_queue"))),
        search_expansion_result_count=len(_dict_list(provider_metadata.get("search_expansion_results"))),
        targets_not_searched_count=len(_dict_list(provider_metadata.get("targets_not_searched"))),
        uncovered_target_hint_count=len(_dict_list(provider_metadata.get("benchmark_recall_targets"))),
        source_obligation_decisions=source_obligation_decisions,
        extraction_issue_codes=_extraction_issue_codes(provider_metadata),
        evidence_linking_issue_count=_extraction_issue_codes(provider_metadata).count("evidence_linking_failed"),
        coverage_warnings=list(coverage_warnings),
        coverage_checks=list(coverage_checks),
        unresolved_gap_count=len(unresolved_candidate_gaps),
        budget_exhaustion_events=list(budget.exhaustion_events),
        useful_result_retry_count=len(useful_result_retry_records),
        remaining_signal_task_count=0,
    )
    decision = service.review(checkpoint)
    payload = decision.model_dump()
    if not checkpoint_decisions or checkpoint_decisions[-1] != payload:
        checkpoint_decisions.append(payload)
    if decision.action != "continue":
        adaptive_actions.append({
            "checkpoint_id": decision.checkpoint_id,
            "phase": decision.phase,
            "action": decision.action,
            "reason_code": decision.reason_code,
            "message": decision.message,
        })
    if decision.severity != "info":
        checkpoint_warnings.append(decision.message)
    events.extend(_checkpoint_events(decision))
    return decision


def _checkpoint_events(decision) -> list[LiveRadarPipelineEvent]:
    reviewed = LiveRadarPipelineEvent(
        event_type="execution_checkpoint_reviewed",
        phase="validation",
        actor="application",
        node_name="execution_checkpoint",
        visibility="operator",
        summary=decision.message,
        payload=decision.model_dump(),
    )
    selected = LiveRadarPipelineEvent(
        event_type=(
            "execution_stopped_for_review"
            if decision.action == "stop_review_needed"
            else "execution_checkpoint_failed"
            if decision.action == "fail_hard"
            else "execution_plan_revised"
            if decision.action == "revise_plan"
            else "execution_checkpoint_action_selected"
        ),
        phase="validation",
        actor="application",
        node_name="execution_checkpoint",
        visibility="operator",
        summary=f"{decision.phase}: {decision.action}",
        payload={
            "checkpoint_id": decision.checkpoint_id,
            "action": decision.action,
            "reason_code": decision.reason_code,
            "message": decision.message,
        },
    )
    return [reviewed] if decision.action == "continue" else [reviewed, selected]


def _linked_source_count(observations: list[dict[str, Any]], sources: list[RadarSourceEvidence]) -> int:
    known_refs = {source.evidence_ref for source in sources if source.evidence_ref}
    refs: set[str] = set()
    for item in observations:
        refs.update(_string_list(item.get("evidence_refs")))
        for section in [*_dict_list(item.get("qualification")), *_dict_list(item.get("signals"))]:
            refs.update(_string_list(section.get("evidence_refs")))
            for finding in _dict_list(section.get("evidence_findings")):
                ref = str(finding.get("source_ref") or "").strip()
                if ref:
                    refs.add(ref)
    return len(refs & known_refs)


def _extraction_issue_codes(provider_metadata: dict[str, Any]) -> list[str]:
    if str(provider_metadata.get("post_extraction_salvage_outcome") or "") == "post_extraction_salvage_recovered":
        return []
    codes: list[str] = []
    for issue in _dict_list(provider_metadata.get("extraction_validation_issues")):
        code = str(issue.get("code") or "").strip()
        if code:
            codes.append(code)
    for result in _dict_list(provider_metadata.get("extraction_validation_results")):
        state = str(result.get("state") or "").strip()
        if state in {"extraction_schema_invalid", "evidence_linking_failed"}:
            codes.append(state)
    return codes


def _analyzed_source_count(provider_metadata: dict[str, Any]) -> int:
    outcomes = _dict_list(provider_metadata.get("retrieval_source_outcomes")) or _dict_list(provider_metadata.get("source_outcomes"))
    return len(outcomes)


def _retrieved_source_count(provider_metadata: dict[str, Any]) -> int:
    value = provider_metadata.get("retrieved_source_count")
    if isinstance(value, int):
        return max(value, 0)
    retrieved = _dict_list(provider_metadata.get("retrieved_sources"))
    if retrieved:
        refs = {str(item.get("source_ref") or item.get("evidence_ref") or item.get("url") or "") for item in retrieved}
        return len({item for item in refs if item})
    return len(_dict_list(provider_metadata.get("retrieval_source_outcomes")))


def _diagnostic_source_count(provider_metadata: dict[str, Any]) -> int:
    refs: set[str] = set()
    for key in (
        "retrieved_sources",
        "analyzed_sources",
        "retrieval_source_outcomes",
        "source_outcomes",
        "source_provider_outcomes",
    ):
        for item in _dict_list(provider_metadata.get(key)):
            ref = str(item.get("source_ref") or item.get("evidence_ref") or item.get("url") or item.get("source_id") or "").strip()
            if ref:
                refs.add(ref)
    return len(refs)


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _dict_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]
