"""Source capability contracts and the bounded HH public-web architecture probe."""

from __future__ import annotations

from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field


CapabilityOutcome = Literal[
    "available",
    "public_search_only",
    "blocked_auth",
    "blocked_policy",
    "deferred",
    "unsupported",
]


class PowerWebSourceCapabilityCard(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str
    lane: str
    access_mode: str
    domain_restrictions: tuple[str, ...] = ()
    authentication: str = "none"
    allowed_operations: tuple[str, ...] = ()
    available_fields: tuple[str, ...] = ()
    freshness: str
    rate_or_cost_limits: str
    retention: str
    privacy_rules: tuple[str, ...] = ()
    outcome: CapabilityOutcome
    reason: str


class PublicWebSearchReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    query_pattern: str
    query: str
    domain_restriction: str
    outcome: Literal["citation_found", "source_not_found", "search_failed"]
    url: str | None = None
    title: str | None = None
    excerpt: str | None = Field(default=None, max_length=600)
    page_access_limited: bool = False
    api_calls: int = 0


class PublicWebSearchPort(Protocol):
    def search(self, *, query: str, domain: str) -> PublicWebSearchReceipt: ...


class HHPublicWebProbe:
    """Runs three bounded public-search patterns without using the HH API."""

    def __init__(self, search: PublicWebSearchPort) -> None:
        self._search = search

    def run(self, *, organization: str, role: str, unit: str, geography: str) -> tuple[PublicWebSearchReceipt, ...]:
        queries = (
            ("organization_role", f'"{organization}" "{role}" резюме'),
            ("organization_unit", f'"{organization}" "{unit}" резюме'),
            ("role_geography", f'"{role}" "{geography}" профиль резюме'),
        )
        receipts: list[PublicWebSearchReceipt] = []
        for pattern, query in queries:
            receipt = self._search.search(query=query, domain="hh.ru")
            receipts.append(receipt.model_copy(update={
                "query_pattern": pattern,
                "query": query,
                "domain_restriction": "hh.ru",
            }))
        return tuple(receipts)


def default_source_capability_cards() -> tuple[PowerWebSourceCapabilityCard, ...]:
    common_privacy = (
        "public_product_safe_metadata_only",
        "no_private_contacts",
        "no_automated_outreach",
        "no_auth_or_captcha_bypass",
    )
    return (
        PowerWebSourceCapabilityCard(
            source_id="hh_public_web",
            lane="professional_profile",
            access_mode="public_search_only",
            domain_restrictions=("hh.ru",),
            allowed_operations=("web_search", "read_public_indexed_page"),
            available_fields=("url", "title", "snippet", "public_role", "public_employer", "public_geography"),
            freshness="search_index_dependent",
            rate_or_cost_limits="bounded_web_search_budget",
            retention="metadata_excerpt_and_fingerprints_only",
            privacy_rules=common_privacy,
            outcome="public_search_only",
            reason="HH API access is unavailable; indexed public results remain useful source leads.",
        ),
        PowerWebSourceCapabilityCard(
            source_id="official_company",
            lane="official_company",
            access_mode="public_web",
            domain_restrictions=(),
            allowed_operations=("web_search", "read_public_page"),
            available_fields=("name", "title", "unit", "publication", "event"),
            freshness="source_dependent",
            rate_or_cost_limits="bounded_web_search_and_verification_budget",
            retention="metadata_and_excerpt_only",
            privacy_rules=common_privacy,
            outcome="available",
            reason="Official public pages can support employment and relationship claims.",
        ),
        PowerWebSourceCapabilityCard(
            source_id="professional_networks",
            lane="professional_profile",
            access_mode="public_search_only",
            allowed_operations=("web_search", "read_public_indexed_page"),
            available_fields=("name", "headline", "employer", "location", "profile_url"),
            freshness="profile_dependent",
            rate_or_cost_limits="bounded_web_search_budget",
            retention="metadata_excerpt_and_fingerprints_only",
            privacy_rules=common_privacy,
            outcome="public_search_only",
            reason="Only publicly indexed profile metadata is allowed without authorization.",
        ),
        PowerWebSourceCapabilityCard(
            source_id="publications_events",
            lane="publications_events",
            access_mode="public_web",
            allowed_operations=("web_search", "read_public_page"),
            available_fields=("author", "speaker", "title", "organization", "date", "url"),
            freshness="dated_publication_or_event",
            rate_or_cost_limits="bounded_web_search_and_verification_budget",
            retention="metadata_and_excerpt_only",
            privacy_rules=common_privacy,
            outcome="available",
            reason="Dated authorship and participation can support identity and relationship claims.",
        ),
        PowerWebSourceCapabilityCard(
            source_id="procurement_patents",
            lane="structured_public_records",
            access_mode="public_web",
            allowed_operations=("web_search", "read_public_record"),
            available_fields=("person", "organization", "role", "record_date", "record_url"),
            freshness="record_dependent",
            rate_or_cost_limits="bounded_search_and_record_verification_budget",
            retention="metadata_and_excerpt_only",
            privacy_rules=common_privacy,
            outcome="available",
            reason="Public records may support role and relationship claims with dates.",
        ),
        PowerWebSourceCapabilityCard(
            source_id="industry_web",
            lane="industry_web",
            access_mode="public_web",
            allowed_operations=("web_search", "read_public_page"),
            available_fields=("name", "role", "organization", "event", "date", "url"),
            freshness="source_dependent",
            rate_or_cost_limits="bounded_web_search_budget",
            retention="metadata_and_excerpt_only",
            privacy_rules=common_privacy,
            outcome="available",
            reason="Industry sources provide broad recall but require provenance validation.",
        ),
        PowerWebSourceCapabilityCard(
            source_id="generic_web",
            lane="generic_web",
            access_mode="public_web",
            allowed_operations=("web_search", "read_public_page"),
            available_fields=("url", "title", "snippet", "public_page_metadata"),
            freshness="unknown_until_validated",
            rate_or_cost_limits="bounded_web_search_budget",
            retention="metadata_and_excerpt_only",
            privacy_rules=common_privacy,
            outcome="available",
            reason="Generic web is recall-oriented and cannot confirm identity without corroboration.",
        ),
        PowerWebSourceCapabilityCard(
            source_id="image_evidence",
            lane="image_evidence",
            access_mode="public_metadata_only",
            allowed_operations=("exact_fingerprint", "perceptual_fingerprint"),
            available_fields=("source_url", "exact_fingerprint", "perceptual_fingerprint"),
            freshness="not_applicable",
            rate_or_cost_limits="bounded_source_verification_budget",
            retention="fingerprints_only_no_binary_image",
            privacy_rules=(*common_privacy, "no_face_embeddings", "no_reverse_face_search"),
            outcome="available",
            reason="Non-biometric duplicate-image clues are allowed but never confirm identity alone.",
        ),
        PowerWebSourceCapabilityCard(
            source_id="hh_authorized_api",
            lane="professional_profile",
            access_mode="authorized_api",
            domain_restrictions=("api.hh.ru",),
            authentication="employer_oauth_and_licensed_access",
            allowed_operations=(),
            available_fields=(),
            freshness="unavailable",
            rate_or_cost_limits="unknown_until_contract_and_budget_exist",
            retention="not_applicable",
            privacy_rules=common_privacy,
            outcome="deferred",
            reason="Deferred until licensed access, budget and an approved usage model exist.",
        ),
    )
