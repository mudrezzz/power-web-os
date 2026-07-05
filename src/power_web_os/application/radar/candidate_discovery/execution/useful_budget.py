"""Useful-result retry budget for staged Radar discovery tasks."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from power_web_os.application.radar.candidate_discovery.contracts import RadarExecutionTask, WebSearchProviderResult
from power_web_os.application.live_radar_universe import gap_items


@dataclass(frozen=True, slots=True)
class UsefulResultBudget:
    """Useful-result retry thresholds for candidate-discovery tasks.

    Owns:
    - Minimum useful source/candidate thresholds and bounded retry count.

    Does not own:
    - Hard task admission, provider-call accounting, checkpoint recovery, or signal-monitoring budgets.

    Architecture:
    docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md#usefulresultbudget
    """

    min_sources: int | None = None
    min_candidates: int | None = None
    max_retries: int | None = None

    @property
    def enabled(self) -> bool:
        return bool((self.max_retries or 0) > 0 and ((self.min_sources or 0) > 0 or (self.min_candidates or 0) > 0))


def run_task_with_useful_retries(
    *,
    task: RadarExecutionTask,
    useful_budget: UsefulResultBudget,
    execution_id: str,
    run_task: Callable[[RadarExecutionTask], WebSearchProviderResult],
    combine_results: Callable[[WebSearchProviderResult, WebSearchProviderResult], WebSearchProviderResult],
) -> tuple[WebSearchProviderResult, list[str], list[dict[str, Any]], list[str]]:
    result = run_task(task)
    combined = result
    run_ids = [execution_id]
    retry_records: list[dict[str, Any]] = []
    warnings: list[str] = []
    if not useful_budget.enabled:
        return combined, run_ids, retry_records, warnings

    for retry_index in range(1, (useful_budget.max_retries or 0) + 1):
        assessment = useful_result_assessment(combined, useful_budget=useful_budget)
        if assessment["useful"]:
            break
        warning = (
            f"Useful result threshold not met for {task.task_id}: "
            f"{assessment['useful_source_count']} useful sources and "
            f"{assessment['candidate_count']} candidates."
        )
        warnings.append(warning)
        retry_records.append({"task_id": task.task_id, "retry_index": retry_index, **assessment})
        retry_result = run_task(retry_task(task, retry_index=retry_index, assessment=assessment))
        combined = combine_results(combined, retry_result)
        run_ids.append(f"{execution_id}:retry-{retry_index}")
    return combined, run_ids, retry_records, warnings


def useful_result_assessment(result: WebSearchProviderResult, *, useful_budget: UsefulResultBudget) -> dict[str, Any]:
    useful_source_count = sum(1 for source in result.sources if source.verification_state in {"reachable", "not_checked"})
    candidate_count = len(result.candidate_observations) + len(gap_items(result))
    min_sources = useful_budget.min_sources or 0
    min_candidates = useful_budget.min_candidates or 0
    source_ok = useful_source_count >= min_sources if min_sources else True
    candidate_ok = candidate_count >= min_candidates if min_candidates else True
    return {
        "useful": source_ok and candidate_ok,
        "useful_source_count": useful_source_count,
        "source_count": len(result.sources),
        "candidate_count": candidate_count,
        "min_sources": min_sources,
        "min_candidates": min_candidates,
        "reason": useful_result_reason(source_ok=source_ok, candidate_ok=candidate_ok),
    }


def useful_result_reason(*, source_ok: bool, candidate_ok: bool) -> str:
    if not source_ok and not candidate_ok:
        return "provider_empty_or_verification_limited"
    if not source_ok:
        return "verification_limited"
    if not candidate_ok:
        return "provider_empty"
    return "useful"


def retry_task(task: RadarExecutionTask, *, retry_index: int, assessment: dict[str, Any]) -> RadarExecutionTask:
    query = (
        f"{task.query}\n"
        f"Retry {retry_index}: previous bounded attempt was {assessment['reason']} "
        f"with {assessment['useful_source_count']} useful sources and "
        f"{assessment['candidate_count']} candidates. Find additional source-backed "
        "candidate evidence for the same stage and rule only."
    )
    return task.model_copy(update={"query": query})
