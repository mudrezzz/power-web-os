"""Lookup-term helpers for structured Radar source providers."""

from __future__ import annotations

import re
from collections.abc import Iterable


def lookup_terms_from_text(text: str) -> list[str]:
    normalized = " ".join(str(text).split())
    if not normalized:
        return []
    identifiers = re.findall(r"\b\d{10}\b|\b\d{13}\b|\b\d{15}\b", normalized)
    quoted = re.findall(r"[\"«]([^\"»]{3,120})[\"»]", normalized)
    legal_patterns = re.findall(
        r"\b(?:АО|ПАО|ОАО|ЗАО|ООО|НАО|JSC|PJSC|LLC)\s+[\"«]?[A-Za-zА-Яа-яЁё0-9 .,\-]{3,90}",
        normalized,
        flags=re.IGNORECASE,
    )
    terms = [*identifiers, *quoted, *legal_patterns]
    if is_concrete_lookup_term(normalized):
        terms.append(normalized)
    return _dedupe_text(terms)


def is_concrete_lookup_term(term: str) -> bool:
    value = " ".join(str(term).split())
    if re.fullmatch(r"\d{10}|\d{13}|\d{15}", value):
        return True
    if is_placeholder_candidate_scope(value):
        return False
    if re.search(r"\b(АО|ПАО|ОАО|ЗАО|ООО|НАО|JSC|PJSC|LLC)\b", value, flags=re.IGNORECASE):
        return True
    return 3 <= len(value) <= 90 and not looks_like_broad_discovery(value)


def looks_like_broad_discovery(text: str) -> bool:
    lowered = str(text).lower()
    return any(marker in lowered for marker in (
        "find ",
        "all ",
        "candidate universe",
        "holding",
        "contour",
        "universe",
        "найд",
        "все ",
        "контур",
        "периметр",
        "холдинг",
        "групп",
        "юр лиц",
        "юридическ",
    ))


def concrete_candidate_scope_terms(candidate_scope: list[str]) -> list[str]:
    return [
        value
        for value in _dedupe_text(str(item) for item in candidate_scope)
        if value and not is_placeholder_candidate_scope(value) and is_concrete_lookup_term(value)
    ]


def is_placeholder_candidate_scope(value: str) -> bool:
    normalized = " ".join(str(value).split()).strip().lower()
    if not normalized:
        return True
    return any(marker in normalized for marker in (
        "кандидаты из шага",
        "кандидаты с шага",
        "кандидаты из предыдущего шага",
        "candidate from step",
        "candidates from step",
        "candidates from previous step",
        "candidate scope",
        "known candidates",
        "current candidates",
    ))


def _dedupe_text(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = " ".join(str(value).split())
        if normalized and normalized.lower() not in seen:
            seen.add(normalized.lower())
            result.append(normalized)
    return result
