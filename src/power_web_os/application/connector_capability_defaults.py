from __future__ import annotations

from typing import Any


def _required_input_kinds(text: str) -> list[str]:
    result: list[str] = []
    for key, terms in {
        "legal_name": ["legal name", "company name"],
        "inn": ["inn", "инн"],
        "ogrn": ["ogrn", "огрн"],
        "domain": ["domain"],
        "url": ["url"],
        "free_text_query": ["free text", "natural-language", "web search"],
        "candidate_scope": ["candidate scope"],
    }.items():
        if _has_any(text, terms):
            result.append(key)
    return result


def _returned_fact_kinds(profile: Any) -> list[str]:
    if getattr(profile, "returned_fact_kinds", ()):
        return list(profile.returned_fact_kinds)
    facts: list[str] = []
    text = _profile_text(profile)
    for key, terms in {
        "legal_identity": ["legal entity", "legal name", "inn", "ogrn"],
        "registry_status": ["status"],
        "address": ["address"],
        "okved": ["okved"],
        "web_source": ["url", "citation", "snippet", "web page"],
        "signal_evidence": ["signal", "intent", "event", "news"],
    }.items():
        if _has_any(text, terms):
            facts.append(key)
    return facts


def _useful_result_criteria(
    profile: Any,
    *,
    supports_identity: bool,
    supports_coverage: bool,
) -> list[str]:
    if supports_identity:
        return ["resolved legal entity identity", "source-backed registry observation"]
    if supports_coverage:
        return ["retrieved source with URL/title/snippet", "source-backed coverage finding"]
    return [f"source result from {profile.display_name}"]


def _accepted_input_shapes(
    *,
    supports_broad: bool,
    supports_identity: bool,
    requires_concrete: bool,
    source_type: str,
) -> list[str]:
    result: list[str] = []
    if supports_broad:
        result.append("broad_query")
    if supports_identity or requires_concrete:
        result.extend(["concrete_company", "candidate_scope", "inn", "ogrn", "alias_or_language_variant"])
    if source_type == "url":
        result.extend(["domain_or_url", "official_domain_query"])
    return _dedupe_strings(result)


def _bad_input_shapes(*, supports_signal: bool, requires_concrete: bool, supports_broad: bool) -> list[str]:
    result: list[str] = []
    if requires_concrete and not supports_broad:
        result.extend(["broad_query", "placeholder_candidate_scope", "holding_contour_enumeration"])
    if not supports_signal:
        result.append("signal_evidence_query")
    return _dedupe_strings(result)


def _non_blocking_outcomes(*, source_type: str) -> list[str]:
    if source_type == "company_registry":
        return [
            "alias_no_match_non_blocking",
            "registry_lookup_insufficient",
            "ambiguous_match_review_needed",
            "identity_lookup_needs_better_terms",
        ]
    return ["retrieved_not_linked", "no_supporting_evidence", "analyzed_only"]


def _language_hints(profile: Any) -> list[str]:
    text = _profile_text(profile)
    result: list[str] = []
    if _has_any(text, ["russian", "росси", "inn", "ogrn", "инн", "огрн"]):
        result.append("ru")
    if _has_any(text, ["english", "alias", "jsc", "llc", "pjsc"]):
        result.append("en")
    return result or ["source_language"]


def _capability_class(
    *,
    source_type: str,
    supports_broad: bool,
    supports_identity: bool,
    requires_concrete: bool,
) -> str:
    if source_type == "company_registry" or (supports_identity and requires_concrete and not supports_broad):
        return "lookup_only_identity_enrichment"
    if source_type == "url":
        return "official_or_domain_coverage"
    if supports_broad:
        return "broad_web_retrieval"
    return "generic_source"


def _dedupe_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = value.strip().casefold()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(value.strip())
    return result


def _profile_text(profile: Any) -> str:
    values = [
        getattr(profile, "id", ""),
        getattr(profile, "display_name", ""),
        getattr(profile, "description", ""),
        getattr(profile, "source_type", ""),
        getattr(profile, "runtime_provider_id", ""),
        *list(getattr(profile, "good_inputs", ()) or ()),
        *list(getattr(profile, "bad_inputs", ()) or ()),
        *list(getattr(profile, "expected_facts", ()) or ()),
        *list(getattr(profile, "limitations", ()) or ()),
        *list(getattr(profile, "accepted_input_shapes", ()) or ()),
        *list(getattr(profile, "bad_input_shapes", ()) or ()),
        *list(getattr(profile, "returned_fact_kinds", ()) or ()),
        *list(getattr(profile, "useful_result_criteria", ()) or ()),
        *list(getattr(profile, "non_blocking_outcomes", ()) or ()),
        *list(getattr(profile, "language_hints", ()) or ()),
    ]
    return " ".join(str(value) for value in values).lower()



def _has_any(text: str, terms: list[str]) -> bool:
    return any(term.lower() in text for term in terms)
