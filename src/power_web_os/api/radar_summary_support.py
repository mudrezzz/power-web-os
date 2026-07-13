"""Small product-safe projections shared by Radar summary mappers."""

from __future__ import annotations

from typing import Any


def display_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    context = metadata.get("task_context") if isinstance(metadata.get("task_context"), dict) else {}
    return {
        "execution_mode": str(metadata.get("execution_mode") or ""),
        "requester": str(metadata.get("requester") or ""),
        "run_profile": str(context.get("run_profile") or metadata.get("run_profile") or ""),
        "benchmark_profile": str(context.get("benchmark_profile") or ""),
        "benchmark_mode": str(context.get("benchmark_mode") or metadata.get("benchmark_mode") or ""),
        "signal_execution_mode": str(context.get("signal_execution_mode") or ""),
    }


def is_accepted_candidate(candidate: dict[str, Any]) -> bool:
    return candidate.get("candidate_surface_status") == "accepted_product_candidate" or candidate.get(
        "product_acceptance_status"
    ) == "product_candidate"


def is_review_candidate(candidate: dict[str, Any]) -> bool:
    return candidate.get("candidate_surface_status") == "review_needed_candidate" or candidate.get(
        "product_acceptance_status"
    ) == "review_required"
