from __future__ import annotations

from power_web_os.application.radar_search_expansion_models import RadarSearchExpansionVariant


def select_diversified_variants(
    variants: list[RadarSearchExpansionVariant],
    *,
    max_variants: int,
) -> list[RadarSearchExpansionVariant]:
    """Pick early expansion variants across target types and target ids."""
    deduped = _dedupe_variants(variants)
    if len(deduped) <= max_variants:
        return deduped
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
    used_indexes = {target_id: 0 for target_id in grouped}
    lane_order = sorted(lanes, key=_target_type_lane_priority)
    while len(result) < max_variants and any(used_indexes[target_id] < len(grouped[target_id]) for target_id in grouped):
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
            if len(result) >= max_variants:
                break
        if not progressed:
            break
    return result


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
