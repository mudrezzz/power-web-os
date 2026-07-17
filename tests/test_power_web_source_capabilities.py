from __future__ import annotations

from pathlib import Path

from power_web_os.application.radar.power_web_discovery.source_capabilities import (
    HHPublicWebProbe,
    PublicWebSearchReceipt,
    default_source_capability_cards,
)


class RecordingPublicSearch:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def search(self, *, query: str, domain: str) -> PublicWebSearchReceipt:
        self.calls.append((query, domain))
        return PublicWebSearchReceipt(
            query_pattern="pending",
            query=query,
            domain_restriction=domain,
            outcome="citation_found",
            url=f"https://{domain}/resumes/public-result",
            title="Public indexed result",
            excerpt="Anonymous public role metadata.",
            page_access_limited=True,
            api_calls=0,
        )


def test_hh_public_web_probe_uses_three_domain_restricted_queries() -> None:
    search = RecordingPublicSearch()
    receipts = HHPublicWebProbe(search).run(
        organization="Example plant",
        role="chief engineer",
        unit="production department",
        geography="Perm",
    )

    assert len(receipts) == 3
    assert {item.query_pattern for item in receipts} == {
        "organization_role",
        "organization_unit",
        "role_geography",
    }
    assert all(domain == "hh.ru" for _, domain in search.calls)
    assert all(item.api_calls == 0 for item in receipts)


def test_hh_api_is_deferred_and_not_required() -> None:
    cards = {card.source_id: card for card in default_source_capability_cards()}

    assert cards["hh_public_web"].outcome == "public_search_only"
    assert cards["hh_public_web"].authentication == "none"
    assert cards["hh_authorized_api"].outcome == "deferred"
    assert cards["hh_authorized_api"].allowed_operations == ()


def test_source_capability_matrix_is_complete() -> None:
    cards = default_source_capability_cards()

    assert {card.source_id for card in cards} == {
        "hh_public_web",
        "official_company",
        "professional_networks",
        "publications_events",
        "procurement_patents",
        "industry_web",
        "generic_web",
        "image_evidence",
        "hh_authorized_api",
    }
    assert all(card.outcome and card.retention and card.privacy_rules for card in cards)
    image_card = next(card for card in cards if card.source_id == "image_evidence")
    assert "no_face_embeddings" in image_card.privacy_rules


def test_production_package_contains_no_benchmark_company_hardcodes() -> None:
    package = Path("src/power_web_os/application/radar/power_web_discovery")
    source = "\n".join(path.read_text(encoding="utf-8").casefold() for path in package.glob("*.py"))

    assert "сибур" not in source
    assert "sibur" not in source
