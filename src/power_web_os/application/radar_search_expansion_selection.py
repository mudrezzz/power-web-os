from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from power_web_os.application.radar_search_expansion_models import RadarSearchExpansionVariant


@dataclass(frozen=True)
class RadarVariantSelection:
    variants: list[RadarSearchExpansionVariant]
    effective_max_variants: int
    selected_guaranteed_count: int
    selected_optional_count: int
    diagnostics: list[dict[str, Any]] = field(default_factory=list)

    def to_summary(self) -> dict[str, Any]:
        return {
            "effective_max_variants": self.effective_max_variants,
            "selected_guaranteed_count": self.selected_guaranteed_count,
            "selected_optional_count": self.selected_optional_count,
            "diagnostic_count": len(self.diagnostics),
            "missing_minimums": [
                item for item in self.diagnostics if item.get("reason") in {"target_not_generated", "no_executable_variant_for_target", "selection_below_minimum"}
            ],
        }


def select_diversified_variants(
    variants: list[RadarSearchExpansionVariant],
    *,
    max_variants: int,
) -> list[RadarSearchExpansionVariant]:
    """Pick early expansion variants across target types and target ids."""
    return select_guaranteed_variants(variants, max_variants=max_variants, minimums={}).variants


def select_guaranteed_variants(
    variants: list[RadarSearchExpansionVariant],
    *,
    max_variants: int,
    minimums: dict[str, int],
    targets: list[dict[str, Any]] | None = None,
) -> RadarVariantSelection:
    """Select required target-lane variants before optional variants."""
    deduped = _dedupe_variants(variants)
    parsed_minimums = _positive_minimums(minimums)
    effective_max = max(max_variants, sum(parsed_minimums.values()), 1)
    grouped: dict[str, list[RadarSearchExpansionVariant]] = {}
    for item in deduped:
        grouped.setdefault(item.target_id or "unclassified", []).append(item)
    for target_id, items in list(grouped.items()):
        grouped[target_id] = sorted(items, key=lambda item: (_variant_reason_priority(item.reason), item.query.casefold()))

    target_order = sorted(
        grouped,
        key=lambda target_id: (
            _target_type_lane_priority(grouped[target_id][0].target_type),
            grouped[target_id][0].priority,
            grouped[target_id][0].query.casefold(),
        ),
    )
    lanes: dict[str, list[str]] = {}
    for target_id in target_order:
        lanes.setdefault(grouped[target_id][0].target_type or "unknown", []).append(target_id)

    result: list[RadarSearchExpansionVariant] = []
    selected_target_ids: set[str] = set()
    diagnostics: list[dict[str, Any]] = _no_executable_variant_diagnostics(targets or [], grouped)
    for lane in sorted(parsed_minimums, key=_target_type_lane_priority):
        required = parsed_minimums[lane]
        selected_for_lane = 0
        for target_id in lanes.get(lane, []):
            if selected_for_lane >= required or len(result) >= effective_max:
                break
            if target_id in selected_target_ids:
                continue
            variants_for_target = grouped.get(target_id, [])
            if not variants_for_target:
                continue
            result.append(variants_for_target[0])
            selected_target_ids.add(target_id)
            selected_for_lane += 1
        if selected_for_lane < required:
            diagnostics.append(_lane_diagnostic(
                target_type=lane,
                required=required,
                selected=selected_for_lane,
                generated=_generated_count(targets or [], lane),
                executable=_executable_target_count(grouped, lane),
            ))

    used_indexes = {target_id: 0 for target_id in grouped}
    for item in result:
        used_indexes[item.target_id or "unclassified"] = max(used_indexes.get(item.target_id or "unclassified", 0), 1)
    lane_order = sorted(lanes, key=_target_type_lane_priority)
    while len(result) < effective_max and any(used_indexes[target_id] < len(grouped[target_id]) for target_id in grouped):
        progressed = False
        for lane in lane_order:
            target_ids = lanes.get(lane, [])
            if not target_ids:
                continue
            available = [target_id for target_id in target_ids if used_indexes[target_id] < len(grouped[target_id])]
            if not available:
                continue
            target_id = min(
                available,
                key=lambda item: (
                    grouped[item][0].priority,
                    used_indexes[item],
                    grouped[item][0].query.casefold(),
                ),
            )
            index = used_indexes[target_id]
            result.append(grouped[target_id][index])
            used_indexes[target_id] = index + 1
            progressed = True
            if len(result) >= effective_max:
                break
        if not progressed:
            break
    return RadarVariantSelection(
        variants=result,
        effective_max_variants=effective_max,
        selected_guaranteed_count=len(selected_target_ids),
        selected_optional_count=max(len(result) - len(selected_target_ids), 0),
        diagnostics=diagnostics,
    )


def _dedupe_variants(variants: list[RadarSearchExpansionVariant]) -> list[RadarSearchExpansionVariant]:
    seen: set[tuple[str, tuple[str, ...]]] = set()
    result: list[RadarSearchExpansionVariant] = []
    for item in sorted(variants, key=lambda variant: (variant.priority, _variant_reason_priority(variant.reason), variant.query.casefold())):
        key = (item.query.casefold(), tuple(item.source_ids))
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


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


def _no_executable_variant_diagnostics(
    targets: list[dict[str, Any]],
    grouped: dict[str, list[RadarSearchExpansionVariant]],
) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    for target in targets:
        target_id = str(target.get("target_id") or "")
        if not target_id or target_id in grouped:
            continue
        diagnostics.append({
            "target_id": target_id,
            "target_type": str(target.get("target_type") or ""),
            "reason": "no_executable_variant_for_target",
            "message": "Target was generated but no source-policy/capability-compatible query variant was available.",
        })
    return diagnostics


def _lane_diagnostic(
    *,
    target_type: str,
    required: int,
    selected: int,
    generated: int,
    executable: int,
) -> dict[str, Any]:
    if generated <= 0:
        reason = "target_not_generated"
    elif executable <= 0:
        reason = "no_executable_variant_for_target"
    else:
        reason = "selection_below_minimum"
    return {
        "target_type": target_type,
        "required": required,
        "selected": selected,
        "generated_count": generated,
        "executable_target_count": executable,
        "missing_count": max(required - selected, 0),
        "reason": reason,
        "message": f"Selected {selected} of {required} required expansion targets for {target_type}.",
    }


def _generated_count(targets: list[dict[str, Any]], target_type: str) -> int:
    return len({
        str(item.get("target_id") or "")
        for item in targets
        if str(item.get("target_type") or "") == target_type and str(item.get("target_id") or "")
    })


def _executable_target_count(grouped: dict[str, list[RadarSearchExpansionVariant]], target_type: str) -> int:
    return sum(1 for items in grouped.values() if items and items[0].target_type == target_type)


def _target_type_lane_priority(target_type: str) -> int:
    return {
        "production_site_or_branch_target": 0,
        "holding_or_group_target": 1,
        "known_subsidiary_or_legal_entity_target": 2,
        "benchmark_baseline_like_target": 3,
        "source_backed_universe_gap_target": 4,
        "alias_or_language_variant_target": 5,
        "low_confidence_registry_suggestion_target": 6,
    }.get(target_type, 20)


def _variant_reason_priority(reason: str) -> int:
    return {
        "official_domain_coverage": 1,
        "open_web_relation_query": 2,
        "official_domain_relation_query": 3,
        "open_web_identity_query": 4,
        "official_domain_industrial_coverage": 5,
        "open_web_industrial_site_query": 6,
        "open_web_membership_query": 7,
    }.get(reason, 20)
