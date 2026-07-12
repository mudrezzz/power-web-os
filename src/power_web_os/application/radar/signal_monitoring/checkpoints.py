"""Aggregate task-level retrieval into honest candidate/criterion outcomes."""

from __future__ import annotations

from collections import defaultdict

from power_web_os.application.radar.signal_monitoring.contracts import (
    SignalMonitoringCheckpointDecision,
    SignalObservation,
    SignalSearchExecutionReceipt,
    SignalSearchTask,
    SignalSourceLaneLedgerEntry,
)


class SignalMonitoringCheckpointService:
    """Project pair outcomes only after required source coverage is known."""

    def review(
        self,
        *,
        tasks: list[SignalSearchTask],
        task_observations: list[SignalObservation],
        ledger: list[SignalSourceLaneLedgerEntry],
        receipts: list[SignalSearchExecutionReceipt],
    ) -> tuple[list[SignalObservation], list[SignalMonitoringCheckpointDecision]]:
        task_by_id = {item.task_id: item for item in tasks}
        observation_by_task = {item.task_id: item for item in task_observations}
        receipt_by_task = {item.task_id: item for item in receipts}
        grouped: dict[tuple[str, str], list[SignalSearchTask]] = defaultdict(list)
        for task in tasks:
            grouped[(task.candidate_id, task.signal_code)].append(task)
        # Unscheduled required tasks still participate in the coverage decision.
        for item in ledger:
            task = task_by_id.get(item.task_id)
            if task is not None and task not in grouped[(task.candidate_id, task.signal_code)]:
                grouped[(task.candidate_id, task.signal_code)].append(task)

        outcomes: list[SignalObservation] = []
        decisions: list[SignalMonitoringCheckpointDecision] = []
        ledger_by_task = {item.task_id: item for item in ledger}
        for (candidate_id, signal_code), pair_tasks in grouped.items():
            required = [item for item in pair_tasks if item.required]
            completed = [
                item for item in required
                if ledger_by_task.get(item.task_id)
                and ledger_by_task[item.task_id].status == "executed"
                and receipt_by_task.get(item.task_id)
                and receipt_by_task[item.task_id].outcome in {"retrieved", "no_results"}
            ]
            pair_observations = [observation_by_task[item.task_id] for item in pair_tasks if item.task_id in observation_by_task]
            observed = [item for item in pair_observations if item.observation_status == "observed"]
            duplicate = [item for item in pair_observations if item.search_status == "duplicate_existing_signal"]
            diagnostic_rows = [
                item for item in pair_observations
                if item.search_status not in {
                    "searched",
                    "duplicate_existing_signal",
                    "rejected_out_of_window",
                }
            ]
            if observed:
                projected = _merge_observed(observed)
                action = "observed"
                reason = "validated_evidence_found"
            elif diagnostic_rows:
                projected = diagnostic_rows[0]
                revision_exists = any(item.revision_index > 0 for item in pair_tasks)
                repairable = projected.search_status in {"evidence_linking_failed", "review_needed"}
                action = "revise_query" if repairable and not revision_exists else "review_needed_coverage_incomplete"
                reason = "evidence_quality_requires_query_revision" if action == "revise_query" else projected.search_status
            elif len(completed) < len(required):
                explicit = _ledger_diagnostic(candidate_id, signal_code, pair_tasks, ledger_by_task)
                if explicit is not None:
                    projected = explicit
                    action = "review_needed_coverage_incomplete"
                    reason = projected.search_status
                else:
                    projected = SignalObservation(
                        task_id=f"signal-{candidate_id}-{signal_code}-checkpoint",
                        candidate_id=candidate_id,
                        signal_code=signal_code,
                        observation_status="unclear",
                        search_status="review_needed",
                        summary="Required signal-search coverage was incomplete.",
                    )
                    action = "review_needed_coverage_incomplete"
                    reason = "required_lane_coverage_incomplete"
            elif duplicate and len(duplicate) == len(pair_observations):
                projected = duplicate[0]
                action = "not_observed"
                reason = "only_previously_observed_evidence_found"
            else:
                projected = _searched_negative(candidate_id, signal_code, pair_observations)
                action = "not_observed"
                reason = "all_required_lanes_searched_without_valid_evidence"
            outcomes.append(projected)
            decisions.append(SignalMonitoringCheckpointDecision(
                candidate_id=candidate_id,
                signal_code=signal_code,
                action=action,  # type: ignore[arg-type]
                reason=reason,
                required_task_count=len(required),
                completed_required_task_count=len(completed),
                task_ids=[item.task_id for item in pair_tasks],
            ))
        return outcomes, decisions


def _merge_observed(items: list[SignalObservation]) -> SignalObservation:
    first = items[0]
    sources = {source.source_ref: source for item in items for source in item.sources}
    evidence = {evidence.source_ref: evidence for item in items for evidence in item.evidence}
    return first.model_copy(update={
        "evidence": list(evidence.values()),
        "source_refs": sorted(sources),
        "sources": list(sources.values()),
        "score": max(item.score for item in items),
    })


def _searched_negative(
    candidate_id: str,
    signal_code: str,
    observations: list[SignalObservation],
) -> SignalObservation:
    sources = {source.source_ref: source for item in observations for source in item.sources}
    evidence = {evidence.source_ref: evidence for item in observations for evidence in item.evidence}
    return SignalObservation(
        task_id=f"signal-{candidate_id}-{signal_code}-checkpoint",
        candidate_id=candidate_id,
        signal_code=signal_code,
        observation_status="not_observed",
        search_status="searched",
        summary="All required signal-search lanes were searched and no valid evidence was observed.",
        source_refs=sorted(sources),
        sources=list(sources.values()),
        evidence=list(evidence.values()),
    )


def _ledger_diagnostic(
    candidate_id: str,
    signal_code: str,
    tasks: list[SignalSearchTask],
    ledger_by_task: dict[str, SignalSourceLaneLedgerEntry],
) -> SignalObservation | None:
    statuses = {ledger_by_task[item.task_id].status for item in tasks if item.task_id in ledger_by_task}
    if "not_scheduled_budget_limited" in statuses:
        search_status = "not_searched_budget_limited"
        summary = "Required signal-search work was not scheduled because the task budget was exhausted."
    elif statuses.intersection({"policy_limited", "not_executable"}):
        search_status = "not_searched_policy_limited"
        summary = "Required signal-search work was not executable under source policy or plan acceptance."
    else:
        return None
    return SignalObservation(
        task_id=f"signal-{candidate_id}-{signal_code}-checkpoint",
        candidate_id=candidate_id,
        signal_code=signal_code,
        observation_status="unclear",
        search_status=search_status,  # type: ignore[arg-type]
        summary=summary,
    )
