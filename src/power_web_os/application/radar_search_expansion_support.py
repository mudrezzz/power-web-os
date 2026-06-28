from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from power_web_os.application.live_radar_source_cards import RadarPlannerSourceCard, planner_source_cards_for_policy
from power_web_os.application.radar_search_expansion_models import (
    RadarExpansionTarget,
    RadarSearchExpansionVariant,
    _ExpansionSource,
)


def variants_for_target(
    *,
    target: RadarExpansionTarget,
    sources: list[_ExpansionSource],
    relation_terms: list[str],
) -> list[RadarSearchExpansionVariant]:
    variants: list[RadarSearchExpansionVariant] = []
    official_sources = [source for source in sources if source.source_id in target.allowed_source_ids and source.supports_official]
    web_sources = [source for source in sources if source.source_id in target.allowed_source_ids and source.supports_open_web]
    relation = relation_terms[0] if relation_terms else ""
    for source in official_sources:
        domain_prefix = f"site:{source.domain} " if source.domain else ""
        variants.append(_variant(
            query=f"{domain_prefix}{target.target_label}",
            source=source,
            target=target,
            reason="official_domain_coverage",
            reserve_key="official_coverage_probe",
            facts=["official_relation", "coverage"],
        ))
        if relation:
            variants.append(_variant(
                query=f"{domain_prefix}{target.target_label} {relation}",
                source=source,
                target=target,
                reason="official_domain_relation_query",
                reserve_key="official_coverage_probe",
                facts=["official_relation", "coverage"],
            ))
        variants.append(_variant(
            query=f"{domain_prefix}{target.target_label} завод ГПЗ площадка филиал",
            source=source,
            target=target,
            reason="official_domain_industrial_coverage",
            reserve_key="official_coverage_probe",
            facts=["official_relation", "production_site", "branch"],
        ))
    for source in web_sources:
        if relation:
            variants.append(_variant(
                query=f"{target.target_label} {relation}",
                source=source,
                target=target,
                reason="open_web_relation_query",
                reserve_key="open_web_coverage_probe",
                facts=["web_relation", "coverage"],
                source_scope="additional",
            ))
            variants.append(_variant(
                query=f"{target.target_label} входит в {relation}",
                source=source,
                target=target,
                reason="open_web_membership_query",
                reserve_key="open_web_coverage_probe",
                facts=["web_relation", "coverage"],
                source_scope="additional",
            ))
        variants.append(_variant(
            query=f"{target.target_label} ИНН ОГРН",
            source=source,
            target=target,
            reason="open_web_identity_query",
            reserve_key="open_web_coverage_probe",
            facts=["identity", "registry_hint"],
            source_scope="additional",
        ))
        variants.append(_variant(
            query=f"{target.target_label} завод ГПЗ площадка филиал",
            source=source,
            target=target,
            reason="open_web_industrial_site_query",
            reserve_key="open_web_coverage_probe",
            facts=["production_site", "branch", "asset"],
            source_scope="additional",
        ))
    return variants


def _variant(
    *,
    query: str,
    source: _ExpansionSource,
    target: RadarExpansionTarget,
    reason: str,
    reserve_key: str,
    facts: list[str],
    source_scope: str = "global",
) -> RadarSearchExpansionVariant:
    return RadarSearchExpansionVariant(
        query=" ".join(query.split()),
        source_ids=[source.source_id],
        source_scope=source_scope,
        reason=reason,
        expected_fact_kinds=dedupe_text([*facts, *target.expected_fact_kinds, *source.returned_fact_kinds]),
        target_id=target.target_id,
        target_type=target.target_type,
        budget_reserve_key=reserve_key,
        priority=target.priority,
    )


def expansion_sources(
    *,
    radar: dict[str, Any],
    source_cards: list[RadarPlannerSourceCard] | None,
) -> list[_ExpansionSource]:
    policy = radar.get("global_search_policy") if isinstance(radar.get("global_search_policy"), dict) else {}
    policy_sources = dict_list(policy.get("sources"))
    cards = {card.source_id: card for card in (source_cards or planner_source_cards_for_policy(policy))}
    result: list[_ExpansionSource] = []
    for source in policy_sources:
        source_id = str(source.get("source_id") or source.get("reference") or "")
        obligation = str(source.get("usage_obligation") or source.get("usage_mode") or "preferred")
        if not source_id or obligation == "disabled":
            continue
        card = cards.get(source_id)
        source_type = str(source.get("source_type") or getattr(card, "source_type", ""))
        supports_official = bool(
            card
            and (card.source_type == "url" or card.capability_class == "official_or_domain_coverage")
            and card.supports_coverage
        ) or source_type in {"url", "official_website", "website"}
        supports_open_web = bool(card and card.supports_broad_discovery and card.supports_coverage) or source_type in {"web", "search_engine"}
        if not (supports_official or supports_open_web):
            continue
        reference = str(source.get("reference") or "")
        result.append(_ExpansionSource(
            source_id=source_id,
            source_type=source_type,
            reference=reference,
            domain=_domain_from_source(source, card),
            supports_official=supports_official,
            supports_open_web=supports_open_web,
            returned_fact_kinds=list(getattr(card, "returned_fact_kinds", []) or []),
        ))
    return result


def raw_target_items(
    *,
    radar: dict[str, Any],
    candidate_scope: list[str],
    provider_metadata: dict[str, Any],
    unresolved_candidate_gaps: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for source in (
        unresolved_candidate_gaps,
        dict_list(provider_metadata.get("candidate_universe_gaps")),
        dict_list(provider_metadata.get("upstream_disambiguation_results")),
        dict_list(provider_metadata.get("review_needed_upstream_entities")),
    ):
        for item in source:
            label = str(item.get("legal_name") or item.get("entity_name") or item.get("name") or "")
            if label:
                result.append({
                    "label": label,
                    "source_refs": item.get("source_refs", []),
                    "reason": item.get("reason") or "Source-backed unresolved universe gap.",
                    "entity_type": item.get("entity_type"),
                    "target_type": "source_backed_universe_gap_target",
                })
    for item in candidate_scope:
        result.append({"label": item, "reason": "Existing low-confidence candidate scope needs coverage."})
    task_context = radar.get("task_context") if isinstance(radar.get("task_context"), dict) else {}
    benchmark_targets = [
        *dict_list(provider_metadata.get("benchmark_recall_targets")),
        *(
            dict_list(task_context.get("benchmark_target_hints"))
            if str(task_context.get("benchmark_profile") or "").startswith("benchmark_")
            else []
        ),
    ]
    for item in benchmark_targets:
        label = str(item.get("canonical_name") or item.get("name") or item.get("label") or "")
        if label:
            result.append({
                "label": label,
                "source_refs": item.get("source_refs", []),
                "reason": "Explicit benchmark context target.",
                "entity_type": item.get("entity_type"),
                "target_type": "benchmark_baseline_like_target",
            })
    if not any(is_actionable_term(str(item.get("label") or "")) for item in result):
        for item in radar_seed_terms(radar):
            result.append({"label": item, "reason": "Radar definition seed target."})
    return result


def target_type(label: str, raw: dict[str, Any]) -> str:
    entity_type = str(raw.get("entity_type") or "").strip()
    if entity_type in {"production_site", "branch", "asset", "project"}:
        return "production_site_or_branch_target"
    lowered = label.casefold()
    if any(marker in lowered for marker in ("гпз", "нпз", "завод", "площадк", "филиал", "site", "plant")):
        return "production_site_or_branch_target"
    if any(marker in lowered for marker in ("holding", "холдинг", "group", "группа")):
        return "holding_or_group_target"
    if any(marker in lowered for marker in ("jsc", "pjsc", "llc", "ао ", "пао ", "ооо ")):
        return "known_subsidiary_or_legal_entity_target"
    if re.fullmatch(r"[A-Z0-9][A-Z0-9\-\"' ]{2,}", label):
        return "alias_or_language_variant_target"
    configured_type = str(raw.get("target_type") or "")
    if configured_type == "benchmark_baseline_like_target":
        return configured_type
    return configured_type or "source_backed_universe_gap_target"


def target_priority(target_type: str) -> int:
    return {
        "holding_or_group_target": 10,
        "production_site_or_branch_target": 15,
        "known_subsidiary_or_legal_entity_target": 20,
        "source_backed_universe_gap_target": 40,
        "alias_or_language_variant_target": 50,
        "benchmark_baseline_like_target": 60,
        "low_confidence_registry_suggestion_target": 70,
    }.get(target_type, 100)


def target_reason(target_type: str) -> str:
    return {
        "holding_or_group_target": "Holding or group target needs upstream recall coverage.",
        "known_subsidiary_or_legal_entity_target": "Known legal-entity-like target needs source-backed coverage.",
        "production_site_or_branch_target": "Production site or branch target needs review-needed coverage.",
        "alias_or_language_variant_target": "Alias or language variant needs cross-source coverage.",
    }.get(target_type, "Source-backed target needs recall expansion.")


def expected_fact_kinds(target_type: str) -> list[str]:
    if target_type == "production_site_or_branch_target":
        return ["production_site", "branch", "official_relation", "coverage"]
    if target_type in {"known_subsidiary_or_legal_entity_target", "alias_or_language_variant_target"}:
        return ["legal_identity", "registry_hint", "coverage"]
    return ["candidate_universe_gap", "coverage"]


def reserve_key_for_target(target_type: str) -> str:
    if target_type == "production_site_or_branch_target":
        return "official_coverage_probe"
    return "recall_expansion"


def expansion_reason(
    *,
    candidate_scope: list[str],
    provider_metadata: dict[str, Any],
    coverage_checks: list[dict[str, Any]],
    unresolved_candidate_gaps: list[dict[str, Any]],
) -> str:
    if _has_blocking_source_provider_outcome(provider_metadata):
        return ""
    if dict_list(provider_metadata.get("benchmark_recall_targets")):
        return "benchmark_targets_uncovered"
    gaps = [*unresolved_candidate_gaps, *dict_list(provider_metadata.get("candidate_universe_gaps"))]
    if gaps and any(is_actionable_term(str(item.get("legal_name") or item.get("entity_name") or "")) for item in gaps):
        return "candidate_universe_has_review_gaps"
    if len(candidate_scope) == 0:
        return "candidate_scope_empty"
    if any(str(item.get("completeness_risk") or "") in {"high", "medium"} for item in coverage_checks):
        return "coverage_risk_not_low"
    retrieved_count = int(provider_metadata.get("retrieved_source_count") or 0)
    linked_count = len(dict_list(provider_metadata.get("linked_entity_facts")))
    if retrieved_count and linked_count == 0:
        return "retrieved_sources_not_linked"
    return ""


def _has_blocking_source_provider_outcome(provider_metadata: dict[str, Any]) -> bool:
    blocking = {"provider_unavailable", "invalid_credentials", "rate_limited", "schema_invalid"}
    for item in dict_list(provider_metadata.get("source_provider_outcomes")):
        outcome = str(item.get("outcome") or item.get("status") or "")
        if outcome in blocking:
            return True
    return False


def radar_seed_terms(radar: dict[str, Any]) -> list[str]:
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
    return [value for value in values if is_actionable_term(value)]


def relation_terms(radar: dict[str, Any]) -> list[str]:
    text = " ".join(radar_seed_terms(radar))
    result: list[str] = []
    if re.search(r"\bSIBUR\b", text, flags=re.IGNORECASE) or "СИБУР" in text.upper():
        result.extend(["СИБУР", "SIBUR"])
    tokens = re.findall(r"\b[A-ZА-ЯЁ][A-ZА-ЯЁ0-9\-]{2,}\b", text)
    result.extend(tokens[:3])
    return dedupe_text(result)


def source_texts(provider_metadata: dict[str, Any]) -> list[str]:
    texts: list[str] = []
    for source in dict_list(provider_metadata.get("retrieved_sources")):
        texts.append(" ".join(str(source.get(key) or "") for key in ("title", "snippet", "url")))
    return texts


def is_actionable_term(value: str) -> bool:
    text = " ".join(str(value).split())
    if len(text) < 3 or len(text) > 140:
        return False
    lowered = text.lower()
    if any(marker in lowered for marker in ("task:", "query:", "candidate scope", "кандидаты из шага")):
        return False
    return any(char.isalnum() for char in text)


def search_safe_terms(values: list[str]) -> list[str]:
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


def _domain_from_source(source: dict[str, Any], card: RadarPlannerSourceCard | None) -> str:
    candidates = [
        str(source.get("reference") or ""),
        str(source.get("url") or ""),
        str(source.get("source_id") or ""),
        str(source.get("label") or ""),
        str(getattr(card, "source_label", "") or ""),
    ]
    for value in candidates:
        if not value:
            continue
        parsed = urlparse(value if "://" in value else f"https://{value}")
        host = parsed.netloc or parsed.path.split("/", 1)[0]
        host = host.lower().strip()
        if "." in host and " " not in host and not host.startswith("openrouter"):
            return host.removeprefix("www.")
    return ""


def target_id(label: str, target_type: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9А-Яа-яЁё]+", "_", label.casefold()).strip("_")
    return f"{target_type}:{normalized or 'target'}"[:120]


def dedupe_variants(variants: list[RadarSearchExpansionVariant]) -> list[RadarSearchExpansionVariant]:
    seen: set[tuple[str, tuple[str, ...]]] = set()
    result: list[RadarSearchExpansionVariant] = []
    for item in sorted(variants, key=lambda variant: (variant.priority, _variant_reason_priority(variant.reason), variant.query.casefold())):
        key = (item.query.casefold(), tuple(item.source_ids))
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _variant_reason_priority(reason: str) -> int:
    return {
        "official_domain_coverage": 1,
        "official_domain_relation_query": 2,
        "open_web_relation_query": 3,
        "open_web_identity_query": 4,
        "official_domain_industrial_coverage": 5,
        "open_web_industrial_site_query": 6,
        "open_web_membership_query": 7,
    }.get(reason, 20)


def dedupe_targets(targets: list[RadarExpansionTarget]) -> list[RadarExpansionTarget]:
    seen: set[str] = set()
    result: list[RadarExpansionTarget] = []
    for item in targets:
        key = item.target_id
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def dedupe_text(values: list[str]) -> list[str]:
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


def string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def dict_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]
