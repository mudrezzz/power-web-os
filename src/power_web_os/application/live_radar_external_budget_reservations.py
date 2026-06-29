"""Helpers for Radar external-call reservation diagnostics."""

from __future__ import annotations

from typing import Any


def guaranteed_recall_expansion_reservation_metadata(
    *,
    tasks: dict[str, dict[str, object]],
    used_task_ids: set[str],
) -> dict[str, object]:
    used = sorted(used_task_ids)
    remaining = sorted(task_id for task_id in tasks if task_id not in used_task_ids)
    return {
        "reserved_task_count": len(tasks),
        "first_call_used_count": len(used),
        "first_call_remaining_count": len(remaining),
        "reserved_tasks": [dict(value) for value in tasks.values()],
        "first_call_used_task_ids": used,
        "first_call_remaining_task_ids": remaining,
    }


def openrouter_reserved_remaining_by_lane(
    *,
    reservations: dict[str, dict[str, object]],
    guaranteed_tasks: dict[str, dict[str, object]],
    used_task_ids: set[str],
    protected_used: int,
) -> dict[str, int]:
    result: dict[str, int] = {}
    for lane, payload in reservations.items():
        units = _int(payload.get("units", 0))
        if lane == "recall_expansion":
            if guaranteed_tasks:
                result[lane] = max(_guaranteed_first_calls_remaining(guaranteed_tasks, used_task_ids), 0)
            else:
                result[lane] = max(units - protected_used, 0)
        else:
            result[lane] = max(units, 0)
    return result


def _guaranteed_first_calls_remaining(tasks: dict[str, Any], used_task_ids: set[str]) -> int:
    return sum(1 for task_id in tasks if task_id not in used_task_ids)


def _int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0

