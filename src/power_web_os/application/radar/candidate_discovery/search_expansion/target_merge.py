"""Target dedupe and metadata merge helpers for search expansion."""

from __future__ import annotations

from power_web_os.application.radar.candidate_discovery.search_expansion.models import RadarExpansionTarget


def dedupe_targets(targets: list[RadarExpansionTarget]) -> list[RadarExpansionTarget]:
    by_id: dict[str, RadarExpansionTarget] = {}
    order: list[str] = []
    for item in targets:
        key = item.target_id
        existing = by_id.get(key)
        if existing is None:
            by_id[key] = item
            order.append(key)
            continue
        by_id[key] = _merge_target(existing, item)
    return [by_id[key] for key in order]


def _merge_target(left: RadarExpansionTarget, right: RadarExpansionTarget) -> RadarExpansionTarget:
    preferred = _preferred_target(left, right)
    other = right if preferred is left else left
    return RadarExpansionTarget(
        target_id=preferred.target_id,
        target_label=preferred.target_label,
        target_type=preferred.target_type,
        source_refs=_dedupe_text([*left.source_refs, *right.source_refs]),
        why_target_exists=preferred.why_target_exists or other.why_target_exists,
        priority=min(left.priority, right.priority),
        allowed_source_ids=_dedupe_text([*left.allowed_source_ids, *right.allowed_source_ids]),
        expected_fact_kinds=_dedupe_text([*left.expected_fact_kinds, *right.expected_fact_kinds]),
        budget_reserve_key=preferred.budget_reserve_key or other.budget_reserve_key,
        target_origin=preferred.target_origin or other.target_origin,
        completion_rank_reason=preferred.completion_rank_reason or other.completion_rank_reason,
        deprioritized_reason=preferred.deprioritized_reason or other.deprioritized_reason,
        uncovered_baseline_target=left.uncovered_baseline_target or right.uncovered_baseline_target,
        benchmark_id=preferred.benchmark_id or other.benchmark_id,
        aliases=_dedupe_text([*left.aliases, *right.aliases]),
        expected_source_hints=_dedupe_text([*left.expected_source_hints, *right.expected_source_hints]),
        execution_status=preferred.execution_status or other.execution_status,
        not_searched_reason=preferred.not_searched_reason or other.not_searched_reason,
    )


def _preferred_target(left: RadarExpansionTarget, right: RadarExpansionTarget) -> RadarExpansionTarget:
    if right.target_origin == "benchmark_context" and left.target_origin != "benchmark_context":
        return right
    if left.target_origin == "benchmark_context" and right.target_origin != "benchmark_context":
        return left
    if right.uncovered_baseline_target and not left.uncovered_baseline_target:
        return right
    return left if left.priority <= right.priority else right


def _dedupe_text(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = " ".join(str(value).split())
        key = text.casefold()
        if not text or key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result
