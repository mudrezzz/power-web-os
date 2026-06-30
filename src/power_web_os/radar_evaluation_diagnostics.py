"""Diagnostic classifiers for Radar benchmark evaluation reports."""

from __future__ import annotations

import re
from typing import Any


def false_negative_diagnostics(*, false_negatives: list[dict[str, Any]], dossier: dict[str, Any]) -> list[dict[str, Any]]:
    observed_text = _normalized_blob(_iter_text_values([
        dossier.get("candidates"),
        dossier.get("candidate_universe"),
        dossier.get("entity_resolution_results"),
        dossier.get("upstream_disambiguation_results"),
        dossier.get("linked_entity_facts"),
        dossier.get("unresolved_candidate_gaps"),
    ]))
    source_text = _normalized_blob(_iter_text_values([
        dossier.get("sources"),
        dossier.get("source_lifecycle"),
        dossier.get("retrieved_sources"),
        dossier.get("analyzed_sources"),
        _dict(dossier.get("execution_results")).get("retrieved_sources"),
        _dict(dossier.get("execution_results")).get("analyzed_sources"),
    ]))
    expansion_target_text = _normalized_blob(_iter_text_values([
        dossier.get("expansion_target_queue"),
        dossier.get("search_expansion_query_variants"),
    ]))
    expansion_result_text = _normalized_blob(_iter_text_values([dossier.get("search_expansion_results")]))
    not_searched_text = _normalized_blob(_iter_text_values([dossier.get("targets_not_searched")]))
    diagnostics: list[dict[str, Any]] = []
    for item in false_negatives:
        names = [
            str(item.get("canonical_name") or ""),
            *[str(value) for value in item.get("aliases", []) if isinstance(value, str)],
        ]
        normalized_names = [_normalize_name(value) for value in names if value]
        if _projection_type_lost(item=item, dossier=dossier):
            bucket = "projection_type_lost"
            message = "Entity is present in observed universe diagnostics, but its review entity type was projected as unknown."
        elif any(name and name in observed_text for name in normalized_names):
            bucket = "present_not_matched"
            message = "Entity-like text is present in observed candidate/universe diagnostics but did not match the baseline."
        elif any(name and name in source_text for name in normalized_names):
            bucket = "present_not_projected"
            message = "Entity text is present in source diagnostics but was not projected into observed entities."
        elif any(name and name in expansion_result_text for name in normalized_names):
            bucket = _expansion_result_bucket(item=item, dossier=dossier)
            message = "Expansion searched this target class, but no matching observed entity was projected."
        elif any(name and name in not_searched_text for name in normalized_names):
            bucket = _not_searched_bucket(item=item, dossier=dossier)
            message = "Expansion generated this target but did not execute it before the run stopped."
        elif any(name and name in expansion_target_text for name in normalized_names):
            bucket = "expansion_not_selected"
            message = "Expansion generated this target, but it did not receive an execution slot in the bounded pass."
        else:
            bucket = "not_retrieved_in_run"
            message = "No baseline name or alias was found in the persisted dossier source diagnostics."
        diagnostics.append({
            "baseline_id": item.get("baseline_id"),
            "canonical_name": item.get("canonical_name"),
            "entity_type": item.get("entity_type"),
            "bucket": bucket,
            "message": message,
        })
    return diagnostics


def _projection_type_lost(*, item: dict[str, Any], dossier: dict[str, Any]) -> bool:
    expected_type = str(item.get("entity_type") or "")
    if expected_type == "legal_entity":
        return False
    names = [
        str(item.get("canonical_name") or ""),
        *[str(value) for value in item.get("aliases", []) if isinstance(value, str)],
    ]
    normalized_names = [_normalize_name(value) for value in names if value]
    observed_records = [
        *_list(dossier.get("candidate_universe")),
        *_list(dossier.get("entity_resolution_results")),
        *_list(dossier.get("upstream_disambiguation_results")),
        *_list(dossier.get("linked_entity_facts")),
        *_list(dossier.get("unresolved_candidate_gaps")),
    ]
    for record in observed_records:
        if str(record.get("entity_type") or "") != "unknown_entity":
            continue
        text = _normalized_blob(_iter_text_values([record]))
        if _any_name_matches_text(normalized_names, text):
            return True
    return False


def _expansion_result_bucket(*, item: dict[str, Any], dossier: dict[str, Any]) -> str:
    for result in _matching_records(item=item, records=_list(dossier.get("search_expansion_results"))):
        status = str(result.get("execution_status") or "")
        if status in {"not_searched", "not_executed"}:
            return _reason_bucket(str(result.get("not_searched_reason") or ""))
        if status == "executed_no_support":
            return "expansion_searched_no_support"
        if int(result.get("source_count") or 0) == 0:
            return "expansion_searched_no_support"
        if int(result.get("candidate_observation_count") or 0) == 0:
            return "expansion_source_found_not_projected"
    return "expansion_searched_not_projected"


def _not_searched_bucket(*, item: dict[str, Any], dossier: dict[str, Any]) -> str:
    for result in _matching_records(item=item, records=_list(dossier.get("targets_not_searched"))):
        return _reason_bucket(str(result.get("not_searched_reason") or result.get("reason") or ""))
    return "expansion_not_selected"


def _reason_bucket(reason: str) -> str:
    lowered = reason.lower()
    if "completion_cap" in lowered or "completion_limit" in lowered:
        return "completion_cap_exhausted"
    if "completion_lane_quota" in lowered:
        return "completion_lane_quota_exhausted"
    if "selector_priority" in lowered:
        return "selector_priority_lost"
    if "completion_not_selected" in lowered:
        return "completion_not_selected"
    if "scheduler" in lowered or "admission" in lowered:
        return "scheduler_rejected"
    if "external_budget" in lowered or "openrouter" in lowered or "server_tool" in lowered:
        return "external_budget_limited"
    if "global_budget" in lowered:
        return "expansion_global_budget_limited"
    if "source_found_not_projected" in lowered or "projection" in lowered:
        return "source_found_not_projected"
    if "reserve" in lowered:
        return "expansion_reserve_limited"
    if "budget" in lowered or "reserve" in lowered:
        return "expansion_budget_limited"
    if "policy" in lowered or "source" in lowered:
        return "expansion_source_policy_limited"
    if "not_selected" in lowered:
        return "expansion_not_selected"
    return "expansion_not_executed"


def _matching_records(*, item: dict[str, Any], records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    names = [
        str(item.get("canonical_name") or ""),
        *[str(value) for value in item.get("aliases", []) if isinstance(value, str)],
    ]
    normalized_names = [_normalize_name(value) for value in names if value]
    result: list[dict[str, Any]] = []
    for record in records:
        text = _normalized_blob(_iter_text_values([record]))
        if any(name and name in text for name in normalized_names):
            result.append(record)
    return result


def _any_name_matches_text(normalized_names: list[str], text: str) -> bool:
    text_tokens = set(text.split())
    for name in normalized_names:
        if not name:
            continue
        if name in text:
            return True
        name_tokens = {token for token in name.split() if len(token) >= 4 and token not in {"сибур", "sibur"}}
        if len(name_tokens) >= 2 and name_tokens.issubset(text_tokens):
            return True
    return False


def _iter_text_values(values: list[Any]) -> list[str]:
    result: list[str] = []

    def visit(value: Any) -> None:
        if isinstance(value, str):
            result.append(value)
        elif isinstance(value, dict):
            for key, nested in value.items():
                if str(key).lower() in {"raw", "request", "headers", "authorization"}:
                    continue
                visit(nested)
        elif isinstance(value, list):
            for nested in value:
                visit(nested)

    for value in values:
        visit(value)
    return result


def _normalized_blob(values: list[str]) -> str:
    return "\n".join(_normalize_name(value) for value in values if value)


def _normalize_name(value: str) -> str:
    cyrillic_range = "\u0430-\u044f"
    legal_forms = "|".join((
        "\u043e\u043e\u043e",
        "\u043e\u0430\u043e",
        "\u0430\u043e",
        "\u043f\u0430\u043e",
        "\u0437\u0430\u043e",
        "llc",
        "pjsc",
        "jsc",
        "inc",
        "ltd",
    ))
    cleaned = value.lower().replace("\u0451", "\u0435")
    cleaned = re.sub(r"[\"'«»“”„]", "", cleaned)
    cleaned = re.sub(rf"\b({legal_forms})\b", "", cleaned)
    cleaned = re.sub(rf"[^a-z{cyrillic_range}0-9]+", " ", cleaned)
    return " ".join(cleaned.split())


def _dict(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]
