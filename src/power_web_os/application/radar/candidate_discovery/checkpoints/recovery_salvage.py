"""Checkpoint integration for post-extraction salvage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from power_web_os.application.radar.candidate_discovery.contracts import RadarSourceEvidence
from power_web_os.application.radar.candidate_discovery.execution.task_runner import TaskExecutionService
from power_web_os.application.radar.candidate_discovery.extraction.recovery import PostExtractionSalvageService


@dataclass(frozen=True, slots=True)
class CheckpointSalvageResult:
    sources: list[RadarSourceEvidence]
    observations: list[dict[str, Any]]
    provider_metadata: dict[str, Any]
    candidate_scope: list[str]
    recovered: bool


def attempt_post_extraction_salvage(
    *,
    checkpoint_id: str,
    phase: str,
    radar: dict[str, Any],
    sources: list[RadarSourceEvidence],
    observations: list[dict[str, Any]],
    provider_metadata: dict[str, Any],
    completed_qualification_ids: list[str],
    adaptive_actions: list[dict[str, Any]],
    task_service: TaskExecutionService,
    salvage_service: PostExtractionSalvageService,
) -> CheckpointSalvageResult:
    salvage = salvage_service.recover(
        radar=radar,
        sources=sources,
        observations=observations,
        provider_metadata=provider_metadata,
    )
    if not salvage.recovered:
        return CheckpointSalvageResult(
            sources=sources,
            observations=observations,
            provider_metadata=_with_post_extraction_salvage_metadata(
                provider_metadata,
                outcome=salvage.outcome,
                records=salvage.records,
                unrecovered_reason=salvage.unrecovered_reason,
            ),
            candidate_scope=[],
            recovered=False,
        )
    merged_sources, merged_observations, merged_metadata = task_service.merger.merge_result(
        sources,
        observations,
        provider_metadata,
        salvage.recovered_result,
    )
    adaptive_actions.append({
        "checkpoint_id": checkpoint_id,
        "phase": phase,
        "action": "post_extraction_salvage",
        "attempt": 1,
        "task_id": "post-extraction-salvage",
        "outcome": "recovered",
        "message": "Recovered source-backed upstream leads after extraction schema failure.",
        "recovered_candidate_count": len(salvage.recovered_result.candidate_observations),
    })
    return CheckpointSalvageResult(
        sources=merged_sources,
        observations=merged_observations,
        provider_metadata=merged_metadata,
        candidate_scope=task_service.eligible_candidate_names(
            radar=radar,
            sources=merged_sources,
            observations=merged_observations,
            completed_qualification_ids=completed_qualification_ids,
        ),
        recovered=True,
    )


def extraction_recovery_stop_reason(metadata: dict[str, Any]) -> str:
    outcome = str(metadata.get("extraction_recovery_outcome") or "")
    if outcome:
        return outcome
    for attempt in reversed([item for item in metadata.get("extraction_model_attempts", []) if isinstance(item, dict)]):
        reason = str(attempt.get("reason") or attempt.get("outcome") or "")
        if reason:
            return reason
    for issue in metadata.get("extraction_validation_issues", []):
        if not isinstance(issue, dict):
            continue
        path = str(issue.get("path") or "")
        message = str(issue.get("message") or issue.get("code") or "")
        if path or message:
            return " ".join(part for part in [path, message] if part)
    return ""


def _with_post_extraction_salvage_metadata(
    metadata: dict[str, Any],
    *,
    outcome: str,
    records: list[dict[str, Any]],
    unrecovered_reason: str,
) -> dict[str, Any]:
    merged_records = [
        *[dict(item) for item in metadata.get("post_extraction_salvage_records", []) if isinstance(item, dict)],
        *[dict(item) for item in records if isinstance(item, dict)],
    ]
    return {
        **metadata,
        "post_extraction_salvage_records": merged_records,
        "post_extraction_salvage_count": int(metadata.get("post_extraction_salvage_count") or 0),
        "post_extraction_salvage_outcome": outcome,
        "post_extraction_salvage_unrecovered_reason": unrecovered_reason,
    }
