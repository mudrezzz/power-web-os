"""Helper payloads for bounded DaData lookup attempts."""

from __future__ import annotations

import re
from typing import Any

from power_web_os.application.radar_source_providers import CompanyLookupRequest, CompanySourceOutcome


def lookup_terms_for_execution(request: CompanyLookupRequest) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in [*request.lookup_terms, request.query]:
        text = " ".join(str(value).split())
        if not text or text.casefold() in seen:
            continue
        seen.add(text.casefold())
        result.append(text)
    return result or [request.query]


def request_for_term(request: CompanyLookupRequest, term: str) -> CompanyLookupRequest:
    return request.model_copy(update={"query": term, "lookup_terms": [term]})


def attempt_payload(*, term: str, outcome: CompanySourceOutcome, observation_count: int) -> dict[str, Any]:
    return {
        "term": term,
        "outcome": outcome.outcome,
        "reason": outcome.reason,
        "observation_count": observation_count,
    }


def term_payload(term: str) -> dict[str, str]:
    if re.fullmatch(r"\d{10}|\d{13}|\d{15}", term):
        source = "identifier"
    elif _contains_cyrillic(term) and re.search(r"\b(АО|ПАО|ООО|ОАО|ЗАО|НАО)\b", term, flags=re.IGNORECASE):
        source = "russian_legal_form"
    elif _contains_cyrillic(term):
        source = "russian_alias"
    elif re.search(r"\b(JSC|PJSC|LLC)\b", term, flags=re.IGNORECASE):
        source = "english_legal_form"
    else:
        source = "english_alias"
    return {"value": term, "source": source}


def _contains_cyrillic(value: str) -> bool:
    return bool(re.search(r"[А-Яа-яЁё]", value))
