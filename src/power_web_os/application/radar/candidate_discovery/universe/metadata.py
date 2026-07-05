"""Provider metadata merge helpers for candidate-discovery universe state."""

from __future__ import annotations

from typing import Any


def dict_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def merge_provider_metadata(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = {**existing, **incoming}
    for key in (
        "candidate_universe_gaps",
        "coverage_findings",
        "retrieved_sources",
        "retrieval_source_outcomes",
        "source_outcomes",
        "source_provider_outcomes",
        "source_verification_results",
        "extraction_validation_results",
        "extraction_validation_issues",
        "extraction_repair_results",
        "entity_resolution_results",
        "linked_entity_facts",
        "entity_resolution_warnings",
        "structured_company_observations",
        "upstream_disambiguation_results",
        "cross_source_disambiguation_tasks",
        "search_expansion_tasks",
        "search_expansion_query_variants",
        "search_expansion_results",
        "registry_lookup_terms",
        "registry_lookup_attempts",
        "identity_obligation_review_records",
        "review_needed_upstream_entities",
    ):
        merged[key] = [*dict_list(existing.get(key)), *dict_list(incoming.get(key))]
    return merged
