"""Generate bounded company-registry lookup terms for Radar identity checks."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from power_web_os.application.radar.candidate_discovery.sources.lookup_terms import (
    is_concrete_lookup_term,
    is_placeholder_candidate_scope,
    looks_like_broad_discovery,
)


@dataclass(frozen=True)
class RegistryLookupTerm:
    value: str
    source: str
    priority: int


@dataclass(frozen=True)
class RegistryLookupTermPlan:
    original: str
    terms: list[RegistryLookupTerm] = field(default_factory=list)

    @property
    def values(self) -> list[str]:
        return [item.value for item in self.terms]

    def to_payload(self) -> dict[str, Any]:
        return {
            "original": self.original,
            "lookup_terms": [
                {"value": item.value, "source": item.source, "priority": item.priority}
                for item in self.terms
            ],
        }


class RegistryLookupTermGenerator:
    """Build concrete DaData/registry lookup terms from source-backed context."""

    def terms_for_lookup(
        self,
        *,
        query: str,
        candidate_scope: list[str] | None = None,
        source_texts: list[str] | None = None,
        source_keywords: list[str] | None = None,
        limit: int = 8,
    ) -> RegistryLookupTermPlan:
        original = _clean_text(candidate_scope[0] if candidate_scope else query)
        candidates: list[RegistryLookupTerm] = []
        for text in [*(candidate_scope or []), query, *(source_texts or []), *(source_keywords or [])]:
            candidates.extend(_terms_from_text(str(text)))
        terms = _dedupe_terms(candidates)
        return RegistryLookupTermPlan(original=original, terms=terms[: max(limit, 1)])


def _terms_from_text(text: str) -> list[RegistryLookupTerm]:
    value = _clean_text(text)
    if not value or is_placeholder_candidate_scope(value):
        return []
    identifiers = [
        RegistryLookupTerm(item, "identifier", 0)
        for item in re.findall(r"\b\d{10}\b|\b\d{13}\b|\b\d{15}\b", value)
    ]
    if identifiers:
        return identifiers
    if looks_like_broad_discovery(value) and not _looks_like_company_or_site(value):
        return []

    base_terms = [_strip_registry_noise(value)]
    base_terms.extend(_quoted_terms(value))
    base_terms.extend(_legal_form_terms(value))
    base_terms.extend(_latin_alias_terms(value))
    base_terms.extend(_site_relation_terms(value))

    result: list[RegistryLookupTerm] = []
    for term in base_terms:
        cleaned = _clean_text(term)
        if not cleaned or is_placeholder_candidate_scope(cleaned):
            continue
        if _too_generic_registry_term(cleaned):
            continue
        if not is_concrete_lookup_term(cleaned) and not _looks_like_company_or_site(cleaned):
            continue
        result.append(RegistryLookupTerm(cleaned, _term_source(cleaned), _term_priority(cleaned)))
    return result


def _quoted_terms(value: str) -> list[str]:
    return [
        item
        for item in re.findall(r"[\"«]([^\"»]{3,120})[\"»]", value)
        if item.strip()
    ]


def _legal_form_terms(value: str) -> list[str]:
    stripped = _strip_registry_noise(value)
    if _looks_like_site_or_asset(stripped):
        return [stripped]
    without_forms = re.sub(r"\b(JSC|PJSC|LLC|АО|ПАО|ООО|ОАО|ЗАО|НАО)\b", "", stripped, flags=re.IGNORECASE)
    without_forms = _clean_text(without_forms.strip(" \"«»"))
    terms = [stripped]
    if without_forms:
        terms.append(without_forms)
        if _contains_cyrillic(without_forms):
            terms.extend([f"АО {without_forms}", f"ПАО {without_forms}", f"ООО {without_forms}"])
    return terms


def _latin_alias_terms(value: str) -> list[str]:
    stripped = _strip_registry_noise(value)
    if not re.search(r"[A-Za-z]", stripped):
        return []
    without_forms = re.sub(r"\b(JSC|PJSC|LLC)\b", "", stripped, flags=re.IGNORECASE).strip(" \"«»")
    transliterated = _transliterate_known_company_alias(without_forms)
    terms = [without_forms] if without_forms else []
    if transliterated and transliterated != without_forms:
        terms.extend([transliterated, f"АО {transliterated}", f"ПАО {transliterated}", f"ООО {transliterated}"])
    return terms


def _site_relation_terms(value: str) -> list[str]:
    cleaned = _strip_registry_noise(value)
    terms: list[str] = []
    if _looks_like_site_or_asset(cleaned):
        terms.append(cleaned)
        short = _short_site_name(cleaned)
        if short and short != cleaned:
            terms.append(short)
        if "СИБУР" in cleaned.upper():
            terms.append(cleaned)
        else:
            terms.append(f"{cleaned} СИБУР")
        if "ГАЗОПЕРЕРАБАТ" in cleaned.upper() and "СИБУРТЮМЕНЬГАЗ" not in cleaned.upper():
            terms.append(f"{cleaned} СИБУРТЮМЕНЬГАЗ")
    return terms


def _transliterate_known_company_alias(value: str) -> str:
    normalized = _clean_text(value).replace("_", "-")
    token_map = {
        "sibur": "СИБУР",
        "neftekhim": "Нефтехим",
        "khimprom": "Химпром",
        "polief": "ПОЛИЭФ",
        "rusvinyl": "РусВинил",
        "zapsibneftekhim": "ЗапСибНефтехим",
        "kazanorgsintez": "Казаньоргсинтез",
        "siburtyumengaz": "СибурТюменьГаз",
        "tobolsk": "Тобольск",
    }
    parts = re.split(r"([\s\-/]+)", normalized)
    converted: list[str] = []
    changed = False
    for part in parts:
        key = re.sub(r"[^A-Za-z]", "", part).lower()
        if key in token_map:
            converted.append(token_map[key])
            changed = True
        else:
            converted.append(part)
    result = _clean_text("".join(converted)) if changed else normalized
    if changed and _contains_cyrillic(result) and re.search(r"[A-Za-z]", result):
        return normalized
    return result


def _dedupe_terms(terms: list[RegistryLookupTerm]) -> list[RegistryLookupTerm]:
    seen: set[str] = set()
    result: list[RegistryLookupTerm] = []
    for term in sorted(terms, key=lambda item: (item.priority, len(item.value))):
        key = term.value.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(term)
    return result


def _term_source(value: str) -> str:
    if re.fullmatch(r"\d{10}|\d{13}|\d{15}", value):
        return "identifier"
    if _contains_cyrillic(value) and re.search(r"\b(АО|ПАО|ООО|ОАО|ЗАО|НАО)\b", value, flags=re.IGNORECASE):
        return "russian_legal_form"
    if _contains_cyrillic(value):
        return "russian_alias"
    if re.search(r"\b(JSC|PJSC|LLC)\b", value, flags=re.IGNORECASE):
        return "english_legal_form"
    return "english_alias"


def _term_priority(value: str) -> int:
    if re.fullmatch(r"\d{10}|\d{13}|\d{15}", value):
        return 0
    source = _term_source(value)
    return {
        "russian_legal_form": 1,
        "russian_alias": 2,
        "english_legal_form": 3,
        "english_alias": 4,
    }.get(source, 5)


def _strip_registry_noise(value: str) -> str:
    cleaned = re.sub(r"\b(?:Candidate scope|Current task|Search|Find|Проверить|Найти)\b[:\s]*", " ", value, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip(" ,.;")


def _short_site_name(value: str) -> str:
    text = _clean_text(value)
    replacements = {
        "ГАЗОПЕРЕРАБАТЫВАЮЩИЙ ЗАВОД": "ГПЗ",
        "газоперерабатывающий завод": "ГПЗ",
        "промышленная площадка": "площадка",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return _clean_text(text)


def _looks_like_company_or_site(value: str) -> bool:
    return is_concrete_lookup_term(value) or _looks_like_site_or_asset(value)


def _looks_like_site_or_asset(value: str) -> bool:
    upper = value.upper()
    return any(marker in upper for marker in ("ЗАВОД", "ГПЗ", "ПЛОЩАДК", "ФИЛИАЛ", "ПРОИЗВОДСТВ", "КОМПЛЕКС"))


def _too_generic_registry_term(value: str) -> bool:
    normalized = re.sub(r"[^A-Za-zА-Яа-яЁё0-9]+", "", value).casefold()
    return normalized in {"сибур", "sibur"}


def _contains_cyrillic(value: str) -> bool:
    return bool(re.search(r"[А-Яа-яЁё]", value))


def _clean_text(value: object) -> str:
    return " ".join(str(value or "").replace("«", '"').replace("»", '"').split()).strip()
