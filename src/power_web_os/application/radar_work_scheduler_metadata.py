"""Metadata helpers for Radar work scheduler reports."""

from __future__ import annotations

from typing import Any


def merge_work_scheduler_metadata(existing: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    """Append scheduler portfolio metadata without losing earlier admissions."""

    if not update:
        return dict(existing)
    merged = dict(existing)
    existing_plan = _dict(existing.get("work_scheduler_plan"))
    update_plan = _dict(update.get("work_scheduler_plan"))
    if existing_plan or update_plan:
        merged["work_scheduler_plan"] = {
            **existing_plan,
            **update_plan,
            "work_item_count": _int(existing_plan.get("work_item_count")) + _int(update_plan.get("work_item_count")),
        }
    decisions = [
        *_dict_list(existing.get("work_admission_decisions")),
        *_dict_list(update.get("work_admission_decisions")),
    ]
    merged["work_admission_decisions"] = decisions
    merged["work_scheduler_ledger"] = ledger_payload_from_decisions(decisions)
    merged["work_lane_summary"] = merge_lane_summaries(
        _dict(existing.get("work_lane_summary")),
        _dict(update.get("work_lane_summary")),
    )
    for key in ("work_execution_order", "rejected_work_items", "deferred_work_items", "work_guarantee_failures"):
        merged[key] = [*_dict_list(existing.get(key)), *_dict_list(update.get(key))]
    return merged


def count_by_lane(decisions: list[Any]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for item in decisions:
        lane = str(getattr(item, "lane", "unknown"))
        accepted = bool(getattr(item, "accepted", False))
        bucket = result.setdefault(lane, {"accepted": 0, "rejected": 0})
        bucket["accepted" if accepted else "rejected"] += 1
    return result


def lane_summary(work_items: list[Any], decisions: list[Any]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for item in work_items:
        bucket = result.setdefault(str(getattr(item, "lane", "unknown")), {"planned": 0, "accepted": 0, "rejected": 0})
        bucket["planned"] += 1
    for decision in decisions:
        bucket = result.setdefault(str(getattr(decision, "lane", "unknown")), {"planned": 0, "accepted": 0, "rejected": 0})
        bucket["accepted" if getattr(decision, "accepted", False) else "rejected"] += 1
    return result


def merge_lane_summaries(left: dict[str, Any], right: dict[str, Any]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for source in (left, right):
        for lane, values in source.items():
            if not isinstance(values, dict):
                continue
            bucket = result.setdefault(str(lane), {"planned": 0, "accepted": 0, "rejected": 0})
            bucket["planned"] += _int(values.get("planned"))
            bucket["accepted"] += _int(values.get("accepted"))
            bucket["rejected"] += _int(values.get("rejected"))
    return result


def guarantee_failures(decisions: list[Any]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for decision in decisions:
        if getattr(decision, "accepted", False) or getattr(decision, "schedule_role", "") != "guaranteed":
            continue
        failures.append({
            "work_id": getattr(decision, "work_id", ""),
            "task_id": getattr(decision, "task_id", ""),
            "lane": getattr(decision, "lane", ""),
            "target_id": getattr(decision, "target_id", ""),
            "target_type": getattr(decision, "target_type", ""),
            "reason": getattr(decision, "reason", ""),
            "message": getattr(decision, "message", ""),
            "reserve_key": getattr(decision, "reserve_key", ""),
        })
    return failures


def ledger_payload_from_decisions(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    accepted_count = sum(1 for item in decisions if item.get("accepted"))
    return {
        "accepted_count": accepted_count,
        "rejected_count": len(decisions) - accepted_count,
        "decisions_by_lane": _count_payload_by_lane(decisions),
    }


def _count_payload_by_lane(decisions: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for item in decisions:
        lane = str(item.get("lane") or "unknown")
        bucket = result.setdefault(lane, {"accepted": 0, "rejected": 0})
        bucket["accepted" if item.get("accepted") else "rejected"] += 1
    return result


def _dict(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _dict_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0

