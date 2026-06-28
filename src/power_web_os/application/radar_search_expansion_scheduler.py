"""Schedule guaranteed recall-expansion lanes before optional expansion work."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from power_web_os.application.radar_search_expansion_models import RadarSearchExpansionVariant


@dataclass(frozen=True)
class RadarScheduledExpansionVariant:
    variant: RadarSearchExpansionVariant
    schedule_role: str
    schedule_reason: str

    def to_payload(self) -> dict[str, Any]:
        return {
            **self.variant.to_payload(),
            "schedule_role": self.schedule_role,
            "schedule_reason": self.schedule_reason,
            "execution_status": "scheduled",
        }


@dataclass(frozen=True)
class RadarExpansionSchedule:
    scheduled_variants: list[RadarScheduledExpansionVariant] = field(default_factory=list)
    unscheduled_targets: list[dict[str, Any]] = field(default_factory=list)
    lane_allocation: dict[str, dict[str, int | bool]] = field(default_factory=dict)

    @property
    def variants(self) -> list[RadarSearchExpansionVariant]:
        return [item.variant for item in self.scheduled_variants]

    def to_metadata(self) -> dict[str, Any]:
        return {
            "expansion_schedule": [item.to_payload() for item in self.scheduled_variants],
            "target_lane_allocation": self.lane_allocation,
            "targets_not_scheduled": list(self.unscheduled_targets),
        }


def schedule_guaranteed_expansion_variants(
    *,
    variants: list[RadarSearchExpansionVariant],
    targets: list[dict[str, Any]],
    minimums: dict[str, int],
) -> RadarExpansionSchedule:
    """Order expansion variants so target-lane minimums get first execution slots."""
    parsed_minimums = _positive_minimums(minimums)
    if not parsed_minimums:
        return RadarExpansionSchedule(
            scheduled_variants=[
                RadarScheduledExpansionVariant(variant=item, schedule_role="optional", schedule_reason="no_lane_minimums")
                for item in variants
            ],
            lane_allocation=_lane_allocation(variants=variants, targets=targets, minimums={}),
        )

    remaining = list(_dedupe_variants(variants))
    guaranteed: list[RadarScheduledExpansionVariant] = []
    used_target_ids: set[str] = set()
    for target_type, required in parsed_minimums.items():
        selected_for_lane = 0
        for variant in list(remaining):
            if selected_for_lane >= required:
                break
            if variant.target_type != target_type:
                continue
            target_id = variant.target_id or variant.query.casefold()
            if target_id in used_target_ids:
                continue
            guaranteed.append(RadarScheduledExpansionVariant(
                variant=variant,
                schedule_role="guaranteed",
                schedule_reason=f"lane_minimum:{target_type}",
            ))
            used_target_ids.add(target_id)
            remaining.remove(variant)
            selected_for_lane += 1

    optional = [
        RadarScheduledExpansionVariant(variant=item, schedule_role="optional", schedule_reason="after_lane_minimums")
        for item in remaining
    ]
    scheduled = [*guaranteed, *optional]
    scheduled_ids = {item.variant.target_id for item in scheduled if item.variant.target_id}
    unscheduled_targets = [
        {
            **target,
            "execution_status": "not_searched",
            "not_searched_reason": "selected_but_not_scheduled",
        }
        for target in targets
        if str(target.get("target_id") or "") and str(target.get("target_id") or "") not in scheduled_ids
    ]
    return RadarExpansionSchedule(
        scheduled_variants=scheduled,
        unscheduled_targets=unscheduled_targets,
        lane_allocation=_lane_allocation(variants=[item.variant for item in scheduled], targets=targets, minimums=parsed_minimums),
    )


def _positive_minimums(value: dict[str, int]) -> dict[str, int]:
    result: dict[str, int] = {}
    for key, raw in value.items():
        try:
            parsed = int(raw)
        except (TypeError, ValueError):
            continue
        if parsed > 0:
            result[str(key)] = parsed
    return result


def _dedupe_variants(variants: list[RadarSearchExpansionVariant]) -> list[RadarSearchExpansionVariant]:
    result: list[RadarSearchExpansionVariant] = []
    seen: set[tuple[str, tuple[str, ...], str]] = set()
    for item in variants:
        key = (item.query.casefold(), tuple(item.source_ids), item.target_id)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _lane_allocation(
    *,
    variants: list[RadarSearchExpansionVariant],
    targets: list[dict[str, Any]],
    minimums: dict[str, int],
) -> dict[str, dict[str, int | bool]]:
    target_types = sorted({
        *minimums.keys(),
        *{str(item.get("target_type") or "") for item in targets if str(item.get("target_type") or "")},
        *{item.target_type for item in variants if item.target_type},
    })
    result: dict[str, dict[str, int | bool]] = {}
    for target_type in target_types:
        generated = {
            str(item.get("target_id") or "")
            for item in targets
            if str(item.get("target_type") or "") == target_type and str(item.get("target_id") or "")
        }
        scheduled = {
            item.target_id
            for item in variants
            if item.target_type == target_type and item.target_id
        }
        required = int(minimums.get(target_type, 0))
        result[target_type] = {
            "required": required,
            "generated_count": len(generated),
            "scheduled_count": len(scheduled),
            "scheduled_minimum_satisfied": required <= 0 or len(scheduled) >= required,
        }
    return result
