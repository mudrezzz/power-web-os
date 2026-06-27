"""Recall-first search expansion for weak Radar upstream discovery."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from power_web_os.application.live_radar_contracts import RadarExecutionTask
from power_web_os.application.radar_registry_lookup_terms import RegistryLookupTermGenerator


@dataclass(frozen=True)
class RadarSearchExpansionVariant:
    query: str
    source_ids: list[str]
    source_scope: str
    reason: str
    expected_fact_kinds: list[str] = field(default_factory=list)

    def to_payload(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "source_ids": list(self.source_ids),
            "source_scope": self.source_scope,
            "reason": self.reason,
            "expected_fact_kinds": list(self.expected_fact_kinds),
        }


@dataclass(frozen=True)
class RadarSearchExpansionPlan:
    should_expand: bool
    variants: list[RadarSearchExpansionVariant]
    reason: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "should_expand": self.should_expand,
            "reason": self.reason,
            "variants": [item.to_payload() for item in self.variants],
        }


class RadarSearchExpansionService:
    """Create bounded official/open-web query variants when coverage is weak."""

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
    ) -> RadarSearchExpansionPlan:
        reason = _expansion_reason(
            candidate_scope=candidate_scope,
            provider_metadata=provider_metadata,
            coverage_checks=coverage_checks,
            unresolved_candidate_gaps=unresolved_candidate_gaps,
        )
        if not reason:
            return RadarSearchExpansionPlan(should_expand=False, variants=[], reason="coverage_is_sufficient")
        source_ids = _expansion_source_ids(radar)
        if not source_ids:
            return RadarSearchExpansionPlan(should_expand=False, variants=[], reason="no_allowed_expansion_sources")
        terms = self._seed_terms(
            radar=radar,
            candidate_scope=candidate_scope,
            provider_metadata=provider_metadata,
            unresolved_candidate_gaps=unresolved_candidate_gaps,
        )
        variants = _dedupe_variants([
            variant
            for term in terms
            for variant in _variants_for_term(term=term, source_ids=source_ids)
        ])[: self._max_variants]
        return RadarSearchExpansionPlan(should_expand=bool(variants), variants=variants, reason=reason)

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
                subject_id="recall_first_expansion",
                rule_snapshot=getattr(base_task, "rule_snapshot", "") if base_task is not None else "",
                query=variant.query,
                purpose="Expand weak upstream discovery with source-backed recall-first search.",
                expected_evidence=variant.expected_fact_kinds or ["candidate_universe_gaps", "coverage"],
                source_scope=variant.source_scope,
                source_ids=variant.source_ids,
            ))
        return result

    def _seed_terms(
        self,
        *,
        radar: dict[str, Any],
        candidate_scope: list[str],
        provider_metadata: dict[str, Any],
        unresolved_candidate_gaps: list[dict[str, Any]],
    ) -> list[str]:
        source_texts = _source_texts(provider_metadata)
        raw_terms = [
            *[str(item.get("legal_name") or item.get("entity_name") or "") for item in unresolved_candidate_gaps],
            *[str(item.get("legal_name") or item.get("entity_name") or "") for item in _dict_list(provider_metadata.get("candidate_universe_gaps"))],
            *[str(item.get("legal_name") or item.get("entity_name") or "") for item in _dict_list(provider_metadata.get("upstream_disambiguation_results"))],
            *candidate_scope,
        ]
        if not any(_is_actionable_term(item) for item in raw_terms):
            raw_terms.extend(_radar_seed_terms(radar))
        terms: list[str] = []
        for value in raw_terms:
            if not str(value).strip():
                continue
            if _is_actionable_term(str(value)):
                terms.append(str(value))
            term_plan = self._lookup_terms.terms_for_lookup(query=str(value), source_texts=source_texts, limit=4)
            terms.extend(_search_safe_terms(term_plan.values))
        return _dedupe_text([item for item in terms if _is_actionable_term(item)])


def _variants_for_term(*, term: str, source_ids: list[str]) -> list[RadarSearchExpansionVariant]:
    official_ids = [source_id for source_id in source_ids if source_id != "openrouter_web"]
    web_ids = [source_id for source_id in source_ids if source_id == "openrouter_web"]
    variants: list[RadarSearchExpansionVariant] = []
    for source_id in official_ids:
        variants.extend([
            RadarSearchExpansionVariant(
                query=f"site:sibur.ru {term}",
                source_ids=[source_id],
                source_scope="global",
                reason="official_domain_coverage",
                expected_fact_kinds=["official_relation", "coverage"],
            ),
            RadarSearchExpansionVariant(
                query=f"site:sibur.ru {term} завод СИБУР",
                source_ids=[source_id],
                source_scope="global",
                reason="official_domain_industrial_coverage",
                expected_fact_kinds=["official_relation", "production_site"],
            ),
        ])
    for source_id in web_ids:
        variants.extend([
            RadarSearchExpansionVariant(
                query=f"{term} СИБУР",
                source_ids=[source_id],
                source_scope="additional",
                reason="open_web_relation_query",
                expected_fact_kinds=["web_relation", "coverage"],
            ),
            RadarSearchExpansionVariant(
                query=f"{term} ИНН ОГРН",
                source_ids=[source_id],
                source_scope="additional",
                reason="open_web_identity_query",
                expected_fact_kinds=["identity", "registry_hint"],
            ),
            RadarSearchExpansionVariant(
                query=f"{term} завод ГПЗ площадка филиал",
                source_ids=[source_id],
                source_scope="additional",
                reason="open_web_industrial_site_query",
                expected_fact_kinds=["production_site", "branch", "asset"],
            ),
        ])
    return variants


def _expansion_source_ids(radar: dict[str, Any]) -> list[str]:
    policy = radar.get("global_search_policy") if isinstance(radar.get("global_search_policy"), dict) else {}
    result: list[str] = []
    for source in _dict_list(policy.get("sources")):
        source_id = str(source.get("source_id") or source.get("reference") or "")
        source_type = str(source.get("source_type") or "")
        obligation = str(source.get("usage_obligation") or source.get("usage_mode") or "preferred")
        if not source_id or obligation == "disabled":
            continue
        if source_type in {"url", "official_website", "web", "website", "search_engine"}:
            result.append(source_id)
    return _dedupe_text(result)


def _expansion_reason(
    *,
    candidate_scope: list[str],
    provider_metadata: dict[str, Any],
    coverage_checks: list[dict[str, Any]],
    unresolved_candidate_gaps: list[dict[str, Any]],
) -> str:
    if _has_blocking_source_provider_outcome(provider_metadata):
        return ""
    gaps = [*unresolved_candidate_gaps, *_dict_list(provider_metadata.get("candidate_universe_gaps"))]
    if gaps:
        if any(_is_actionable_term(str(item.get("legal_name") or item.get("entity_name") or "")) for item in gaps):
            return "candidate_universe_has_review_gaps"
    if len(candidate_scope) == 0:
        return "candidate_scope_empty"
    if any(str(item.get("completeness_risk") or "") in {"high", "medium"} for item in coverage_checks):
        return "coverage_risk_not_low"
    retrieved_count = int(provider_metadata.get("retrieved_source_count") or 0)
    linked_count = len(_dict_list(provider_metadata.get("linked_entity_facts")))
    if retrieved_count and linked_count == 0:
        return "retrieved_sources_not_linked"
    return ""


def _has_blocking_source_provider_outcome(provider_metadata: dict[str, Any]) -> bool:
    blocking = {"provider_unavailable", "invalid_credentials", "rate_limited", "schema_invalid"}
    for item in _dict_list(provider_metadata.get("source_provider_outcomes")):
        outcome = str(item.get("outcome") or item.get("status") or "")
        if outcome in blocking:
            return True
    return False


def _radar_seed_terms(radar: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("name", "description"):
        if radar.get(key):
            values.append(str(radar[key]))
    for keyword in radar.get("keywords", []):
        if isinstance(keyword, str):
            values.append(keyword)
    for criterion in radar.get("qualification_criteria", []):
        if not isinstance(criterion, dict):
            continue
        values.extend(str(criterion.get(key) or "") for key in ("label", "rule", "generated_value"))
    if any("СИБУР" in value.upper() for value in values):
        values.extend([
            "СИБУР производственные предприятия",
            "СИБУР дочерние общества заводы",
            "СИБУР ГПЗ площадка",
        ])
    return values


def _source_texts(provider_metadata: dict[str, Any]) -> list[str]:
    texts: list[str] = []
    for source in _dict_list(provider_metadata.get("retrieved_sources")):
        texts.append(" ".join(str(source.get(key) or "") for key in ("title", "snippet", "url")))
    return texts


def _is_actionable_term(value: str) -> bool:
    text = " ".join(str(value).split())
    if len(text) < 3 or len(text) > 140:
        return False
    lowered = text.lower()
    if any(marker in lowered for marker in ("task:", "query:", "candidate scope")):
        return False
    return bool(re.search(r"[A-Za-zА-Яа-яЁё0-9]", text))


def _search_safe_terms(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = " ".join(str(value).split())
        if re.match(r"^(АО|ПАО|ООО|ОАО|ЗАО|НАО)\s+", text, flags=re.IGNORECASE) and _looks_like_site_query(text):
            continue
        result.append(text)
    return result


def _looks_like_site_query(value: str) -> bool:
    upper = value.upper()
    return any(marker in upper for marker in ("ЗАВОД", "ГПЗ", "ПЛОЩАДК", "ФИЛИАЛ"))


def _dedupe_variants(variants: list[RadarSearchExpansionVariant]) -> list[RadarSearchExpansionVariant]:
    seen: set[tuple[str, tuple[str, ...]]] = set()
    result: list[RadarSearchExpansionVariant] = []
    for item in variants:
        key = (item.query.casefold(), tuple(item.source_ids))
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


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


def _dict_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]
