"""Deterministic search-expansion variant selection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from power_web_os.application.radar.candidate_discovery.search_expansion.models import RadarSearchExpansionVariant


@dataclass(frozen=True)
class RadarVariantSelection:
    variants: list[RadarSearchExpansionVariant]
    effective_max_variants: int
    selected_guaranteed_count: int
    selected_optional_count: int
    selected_completion_count: int = 0
    completion_target_limit: int = 0
    diagnostics: list[dict[str, Any]] = field(default_factory=list)

    def to_summary(self) -> dict[str, Any]:
        return {
            "effective_max_variants": self.effective_max_variants,
            "selected_guaranteed_count": self.selected_guaranteed_count,
            "selected_completion_count": self.selected_completion_count,
            "selected_optional_count": self.selected_optional_count,
            "completion_target_limit": self.completion_target_limit,
            "diagnostic_count": len(self.diagnostics),
            "missing_minimums": [
                item for item in self.diagnostics if item.get("reason") in {"target_not_generated", "no_executable_variant_for_target", "selection_below_minimum"}
            ],
            "completion_diagnostics": [
                item for item in self.diagnostics if str(item.get("reason") or "").startswith("completion_")
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
    completion_target_limit: int = 0,
    targets: list[dict[str, Any]] | None = None,
) -> RadarVariantSelection:
    """Select required target-lane variants before optional variants."""
    deduped = _dedupe_variants(variants)
    parsed_minimums = _positive_minimums(minimums)
    completion_limit = max(int(completion_target_limit or 0), 0)
    effective_max = max(max_variants, sum(parsed_minimums.values()) + completion_limit, 1)
    grouped: dict[str, list[RadarSearchExpansionVariant]] = {}
    for item in deduped:
        grouped.setdefault(item.target_id or "unclassified", []).append(item)
    for target_id, items in list(grouped.items()):
        grouped[target_id] = sorted(items, key=lambda item: (_variant_reason_priority(item.reason), item.query.casefold()))
    target_metadata = _target_metadata_by_id(targets or [])

    target_order = sorted(
        grouped,
        key=lambda target_id: (
            _target_type_lane_priority(grouped[target_id][0].target_type),
            *_target_rank_key(target_id=target_id, grouped=grouped, target_metadata=target_metadata),
        ),
    )
    lanes: dict[str, list[str]] = {}
    for target_id in target_order:
        lanes.setdefault(grouped[target_id][0].target_type or "unknown", []).append(target_id)

    result: list[RadarSearchExpansionVariant] = []
    selected_target_ids: set[str] = set()
    guaranteed_target_ids: set[str] = set()
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
            guaranteed_target_ids.add(target_id)
            selected_for_lane += 1
        if selected_for_lane < required:
            diagnostics.append(_lane_diagnostic(
                target_type=lane,
                required=required,
                selected=selected_for_lane,
                generated=_generated_count(targets or [], lane),
                executable=_executable_target_count(grouped, lane),
            ))

    completion_count = 0
    completion_target_ids: set[str] = set()
    if completion_limit > 0:
        for target_id in _completion_target_order(
            grouped=grouped,
            selected_target_ids=selected_target_ids,
            target_metadata=target_metadata,
        ):
            if completion_count >= completion_limit or len(result) >= effective_max:
                break
            variants_for_target = grouped.get(target_id, [])
            if not variants_for_target:
                continue
            result.append(variants_for_target[0])
            selected_target_ids.add(target_id)
            completion_target_ids.add(target_id)
            completion_count += 1
    diagnostics.extend(_completion_not_selected_diagnostics(
        targets=targets or [],
        grouped=grouped,
        selected_target_ids=selected_target_ids,
        completion_limit=completion_limit,
        completion_count=completion_count,
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
        selected_guaranteed_count=len(guaranteed_target_ids),
        selected_completion_count=completion_count,
        selected_optional_count=max(len(result) - len(guaranteed_target_ids) - completion_count, 0),
        completion_target_limit=completion_limit,
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


def _completion_target_order(
    *,
    grouped: dict[str, list[RadarSearchExpansionVariant]],
    selected_target_ids: set[str],
    target_metadata: dict[str, dict[str, Any]] | None = None,
) -> list[str]:
    candidates = [target_id for target_id in grouped if target_id not in selected_target_ids]
    metadata = target_metadata or {}
    return sorted(
        candidates,
        key=lambda target_id: (
            _completion_target_uncovered_priority(target_metadata=metadata.get(target_id, {})),
            _completion_target_type_priority(grouped[target_id][0].target_type),
            *_target_rank_key(target_id=target_id, grouped=grouped, target_metadata=metadata),
        ),
    )


def _completion_not_selected_diagnostics(
    *,
    targets: list[dict[str, Any]],
    grouped: dict[str, list[RadarSearchExpansionVariant]],
    selected_target_ids: set[str],
    completion_limit: int,
    completion_count: int,
) -> list[dict[str, Any]]:
    if completion_limit <= 0:
        return []
    diagnostics: list[dict[str, Any]] = []
    for target in targets:
        target_id = str(target.get("target_id") or "")
        if not target_id or target_id in selected_target_ids or target_id not in grouped:
            continue
        reason = "completion_cap_exhausted" if completion_count >= completion_limit else "selector_priority_lost"
        diagnostics.append({
            "target_id": target_id,
            "target_type": str(target.get("target_type") or ""),
            "reason": reason,
            "completion_target_limit": completion_limit,
            "selected_completion_count": completion_count,
            "target_origin": str(target.get("target_origin") or "unknown"),
            "completion_rank_reason": str(target.get("completion_rank_reason") or ""),
            "deprioritized_reason": str(target.get("deprioritized_reason") or ""),
            "uncovered_baseline_target": bool(target.get("uncovered_baseline_target")),
            "message": "Target was generated and executable, but was not selected by the bounded completion pass.",
        })
    return diagnostics


def _target_metadata_by_id(targets: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("target_id") or ""): item
        for item in targets
        if str(item.get("target_id") or "")
    }


def _target_rank_key(
    *,
    target_id: str,
    grouped: dict[str, list[RadarSearchExpansionVariant]],
    target_metadata: dict[str, dict[str, Any]],
) -> tuple[int, int, int, int, str]:
    first = grouped[target_id][0]
    metadata = target_metadata.get(target_id, {})
    label = str(metadata.get("target_label") or first.query)
    origin = str(metadata.get("target_origin") or first.target_origin or "")
    return (
        _target_origin_priority(origin, metadata),
        _label_quality_penalty(label),
        int(first.priority),
        _variant_reason_priority(first.reason),
        first.query.casefold(),
    )


def _target_origin_priority(origin: str, metadata: dict[str, Any]) -> int:
    return {
        "benchmark_context": 0,
        "retrieved_source": 10,
        "candidate_gap": 20,
        "generated_alias": 30,
        "radar_seed": 35,
        "unknown": 40,
    }.get(origin, 40)


def _label_quality_penalty(value: str) -> int:
    text = " ".join(str(value).split()).casefold()
    if not text:
        return 50
    if text.isdigit():
        return 40
    if text.startswith(("pdf ", "doc ", "xls ", "xlsx ", "csv ")):
        return 30
    if text in {"production site", "industrial site", "plant", "site"}:
        return 20
    if text in {"производственная площадка", "промышленная площадка", "завод", "филиал"}:
        return 20
    return 0


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


def _completion_target_type_priority(target_type: str) -> int:
    return {
        "production_site_or_branch_target": 0,
        "known_subsidiary_or_legal_entity_target": 1,
        "holding_or_group_target": 2,
        "benchmark_baseline_like_target": 3,
        "source_backed_universe_gap_target": 4,
        "alias_or_language_variant_target": 5,
        "low_confidence_registry_suggestion_target": 6,
    }.get(target_type, 20)


def _completion_target_uncovered_priority(*, target_metadata: dict[str, Any]) -> int:
    if bool(target_metadata.get("uncovered_baseline_target")):
        return 0
    return 10


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
