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
    diagnostics: list[dict[str, Any]] = []
    for item in false_negatives:
        names = [
            str(item.get("canonical_name") or ""),
            *[str(value) for value in item.get("aliases", []) if isinstance(value, str)],
        ]
        normalized_names = [_normalize_name(value) for value in names if value]
        if any(name and name in observed_text for name in normalized_names):
            bucket = "present_not_matched"
            message = "Entity-like text is present in observed candidate/universe diagnostics but did not match the baseline."
        elif any(name and name in source_text for name in normalized_names):
            bucket = "present_not_projected"
            message = "Entity text is present in source diagnostics but was not projected into observed entities."
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
    cleaned = value.lower().replace("ё", "е")
    cleaned = re.sub(r"[\"'«»“”„]", "", cleaned)
    cleaned = re.sub(r"\b(ооо|оао|ао|пао|зао|llc|pjsc|jsc|inc|ltd)\b", "", cleaned)
    cleaned = re.sub(r"[^a-zа-я0-9]+", " ", cleaned)
    return " ".join(cleaned.split())


def _dict(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}
