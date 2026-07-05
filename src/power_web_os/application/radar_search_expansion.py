from __future__ import annotations

from typing import Any

from power_web_os.application.radar.candidate_discovery.contracts import RadarExecutionTask
from power_web_os.application.radar.shared.source_cards import RadarPlannerSourceCard
from power_web_os.application.radar_registry_lookup_terms import RegistryLookupTermGenerator
from power_web_os.application.radar_search_expansion_models import (
    RadarExpansionTarget,
    RadarSearchExpansionPlan,
    RadarSearchExpansionVariant,
    _ExpansionSource,
)
from power_web_os.application.radar_search_expansion_support import (
    dedupe_targets as _dedupe_targets,
    dedupe_text as _dedupe_text,
    dedupe_variants as _dedupe_variants,
    dict_list as _dict_list,
    expected_fact_kinds as _expected_fact_kinds,
    expansion_reason as _expansion_reason,
    expansion_sources as _expansion_sources,
    is_actionable_term as _is_actionable_term,
    radar_seed_terms as _radar_seed_terms,
    raw_target_items as _raw_target_items,
    relation_terms as _relation_terms,
    reserve_key_for_target as _reserve_key_for_target,
    search_safe_terms as _search_safe_terms,
    source_texts as _source_texts,
    string_list as _string_list,
    target_id as _target_id,
    target_priority as _target_priority,
    target_reason as _target_reason,
    target_type as _target_type,
    variants_for_target as _variants_for_target,
)
from power_web_os.application.radar_search_expansion_selection import (
    select_guaranteed_variants as _select_guaranteed_variants,
)


class RadarSearchExpansionService:
    """Create bounded source-profile-driven query variants when discovery is weak."""

    def __init__(self, *, max_variants: int = 6) -> None:
        self._max_variants = max(max_variants, 1)
        self._lookup_terms = RegistryLookupTermGenerator()

    def plan_expansion(
        self,
        *,
        radar: dict[str, Any],
        candidate_scope: list[str],
        provider_metadata: dict[str, Any],
        coverage_checks: list[dict[str, Any]],
        unresolved_candidate_gaps: list[dict[str, Any]],
        source_cards: list[RadarPlannerSourceCard] | None = None,
    ) -> RadarSearchExpansionPlan:
        reason = _expansion_reason(
            candidate_scope=candidate_scope,
            provider_metadata=provider_metadata,
            coverage_checks=coverage_checks,
            unresolved_candidate_gaps=unresolved_candidate_gaps,
        )
        if not reason:
            return RadarSearchExpansionPlan(should_expand=False, variants=[], reason="coverage_is_sufficient")
        sources = _expansion_sources(radar=radar, source_cards=source_cards)
        if not sources:
            return RadarSearchExpansionPlan(should_expand=False, variants=[], reason="no_allowed_expansion_sources")
        targets = self._target_queue(
            radar=radar,
            candidate_scope=candidate_scope,
            provider_metadata=provider_metadata,
            unresolved_candidate_gaps=unresolved_candidate_gaps,
            sources=sources,
        )
        candidate_variants = _dedupe_variants([
            variant
            for target in targets
            for variant in _variants_for_target(
                target=target,
                sources=sources,
                relation_terms=_relation_terms(radar),
            )
        ])
        selection = _select_guaranteed_variants(
            candidate_variants,
            max_variants=self._max_variants,
            minimums=_benchmark_target_probe_minimums(radar),
            completion_target_limit=_coverage_completion_target_limit(radar),
            targets=[target.to_payload() for target in targets],
        )
        return RadarSearchExpansionPlan(
            should_expand=bool(selection.variants),
            variants=selection.variants,
            targets=targets,
            reason=reason,
            selection_summary=selection.to_summary(),
            selection_diagnostics=selection.diagnostics,
        )

    def tasks_from_plan(
        self,
        *,
        plan: RadarSearchExpansionPlan,
        base_task: RadarExecutionTask | None,
    ) -> list[RadarExecutionTask]:
        if not plan.should_expand:
            return []
        result: list[RadarExecutionTask] = []
        for index, variant in enumerate(plan.variants, start=1):
            task_id = f"search-expansion-{index}" if base_task is None else f"{base_task.task_id}:search-expansion-{index}"
            result.append(RadarExecutionTask(
                task_id=task_id,
                stage="coverage_check",
                subject_type="radar",
                subject_id=variant.target_id or "recall_first_expansion",
                rule_snapshot=getattr(base_task, "rule_snapshot", "") if base_task is not None else "",
                query=variant.query,
                purpose="Expand weak upstream discovery with source-backed recall-first search.",
                expected_evidence=variant.expected_fact_kinds or ["candidate_universe_gaps", "coverage"],
                source_scope=variant.source_scope,
                source_ids=variant.source_ids,
                candidate_scope=[variant.target_id] if variant.target_id else [],
            ))
        return result

    def _target_queue(
        self,
        *,
        radar: dict[str, Any],
        candidate_scope: list[str],
        provider_metadata: dict[str, Any],
        unresolved_candidate_gaps: list[dict[str, Any]],
        sources: list[_ExpansionSource],
    ) -> list[RadarExpansionTarget]:
        raw_items = _raw_target_items(
            radar=radar,
            candidate_scope=candidate_scope,
            provider_metadata=provider_metadata,
            unresolved_candidate_gaps=unresolved_candidate_gaps,
        )
        source_texts = _source_texts(provider_metadata)
        targets: list[RadarExpansionTarget] = []
        for raw in raw_items:
            label = str(raw.get("label") or "").strip()
            if not _is_actionable_term(label):
                continue
            term_plan = self._lookup_terms.terms_for_lookup(query=label, source_texts=source_texts, limit=4)
            labels = _dedupe_text([label, *_search_safe_terms(term_plan.values)])
            for index, target_label in enumerate(labels):
                target_type = _target_type(target_label, raw)
                target_origin = str(raw.get("target_origin") or _target_origin(raw))
                rank_reason = _completion_rank_reason(target_origin=target_origin, target_label=target_label)
                targets.append(RadarExpansionTarget(
                    target_id=_target_id(target_label, target_type),
                    target_label=target_label,
                    target_type=target_type,
                    source_refs=_string_list(raw.get("source_refs")),
                    why_target_exists=str(raw.get("reason") or _target_reason(target_type)),
                    priority=_target_priority(target_type) + index,
                    allowed_source_ids=[source.source_id for source in sources],
                    expected_fact_kinds=_expected_fact_kinds(target_type),
                    budget_reserve_key=_reserve_key_for_target(target_type),
                    target_origin=target_origin,
                    completion_rank_reason=rank_reason,
                    deprioritized_reason=_deprioritized_reason(target_label),
                    uncovered_baseline_target=bool(raw.get("uncovered_baseline_target")),
                ))
        return sorted(_dedupe_targets(targets), key=lambda item: (item.priority, item.target_label.casefold()))


def _benchmark_target_probe_minimums(radar: dict[str, Any]) -> dict[str, int]:
    task_context = radar.get("task_context") if isinstance(radar.get("task_context"), dict) else {}
    raw = task_context.get("benchmark_target_probe_minimums")
    if not isinstance(raw, dict) or not task_context.get("benchmark_profile"):
        return {}
    result: dict[str, int] = {}
    for key, value in raw.items():
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            continue
        if parsed > 0:
            result[str(key)] = parsed
    return result


def _coverage_completion_target_limit(radar: dict[str, Any]) -> int:
    task_context = radar.get("task_context") if isinstance(radar.get("task_context"), dict) else {}
    if not task_context.get("benchmark_profile"):
        return 0
    try:
        parsed = int(task_context.get("coverage_completion_target_limit") or 0)
    except (TypeError, ValueError):
        return 0
    return max(parsed, 0)


def _target_origin(raw: dict[str, Any]) -> str:
    reason = str(raw.get("reason") or "")
    if reason == "Explicit benchmark context target.":
        return "benchmark_context"
    if _string_list(raw.get("source_refs")):
        return "retrieved_source"
    if reason == "Existing low-confidence candidate scope needs coverage.":
        return "candidate_gap"
    if reason == "Radar definition seed target.":
        return "radar_seed"
    return "unknown"


def _completion_rank_reason(*, target_origin: str, target_label: str) -> str:
    quality = _label_quality_reason(target_label)
    if target_origin == "benchmark_context":
        return f"explicit_benchmark_target:{quality}"
    if target_origin == "retrieved_source":
        return f"source_backed_target:{quality}"
    if target_origin == "candidate_gap":
        return f"candidate_gap_target:{quality}"
    return f"{target_origin or 'unknown'}:{quality}"


def _deprioritized_reason(target_label: str) -> str:
    quality = _label_quality_reason(target_label)
    if quality == "numeric_only":
        return "numeric_only_label"
    if quality == "document_like":
        return "document_like_label"
    if quality == "generic_industrial":
        return "generic_industrial_label"
    return ""


def _label_quality_reason(value: str) -> str:
    text = " ".join(str(value).split()).casefold()
    if not text:
        return "empty"
    if text.isdigit():
        return "numeric_only"
    if text.startswith(("pdf ", "doc ", "xls ", "xlsx ", "csv ")):
        return "document_like"
    if text in {"production site", "industrial site", "plant", "site"}:
        return "generic_industrial"
    if text in {"производственная площадка", "промышленная площадка", "завод", "филиал"}:
        return "generic_industrial"
    return "clean_named_target"
