"""Approved cross-run reproducibility policy evaluation."""

from __future__ import annotations

from typing import Any


def evaluate_reproducibility_policy(
    *,
    matrix: dict[str, dict[str, Any]],
    positive_control_count: int,
    negative_control_count: int,
    unknown_control_count: int,
    initial_run_count: int,
    policy: dict[str, Any],
) -> dict[str, Any]:
    minimum = int(
        policy.get("minimum_positive_controls_per_initial_run")
        or positive_control_count
    )
    accepted_drift_ids = {
        str(item)
        for item in policy.get("accepted_provider_search_drift_control_ids", [])
    }
    matched_ids = {
        str(control_id)
        for item in matrix.values()
        for control_id in item["positive"].get("matched_ids", [])
    }
    missing_by_run = {
        run_id: {str(control_id) for control_id in item["positive"].get("missing", [])}
        for run_id, item in matrix.items()
    }
    for run_id, missing_ids in missing_by_run.items():
        matrix[run_id]["provider_search_drift"] = sorted(missing_ids & accepted_drift_ids)
    per_run_controls = all(
        item["positive"]["matched"] >= minimum
        and item["negative"]["matched"] >= min(2, negative_control_count)
        and item["unknown"]["matched"] == unknown_control_count
        for item in matrix.values()
    ) and len(matrix) == initial_run_count
    one_complete = any(
        item["positive"]["matched"] == positive_control_count
        for item in matrix.values()
    )
    require_one_complete = bool(policy.get("require_one_complete_initial_run", False))
    complete = (
        per_run_controls
        and len(matched_ids) == positive_control_count
        and (one_complete if require_one_complete else all(
            item["positive"]["matched"] == positive_control_count
            for item in matrix.values()
        ))
        and all(missing_ids <= accepted_drift_ids for missing_ids in missing_by_run.values())
    )
    return {
        "complete": complete,
        "minimum": minimum,
        "matched_count": len(matched_ids),
        "one_complete": one_complete,
        "accepted_drift_ids": accepted_drift_ids,
    }
