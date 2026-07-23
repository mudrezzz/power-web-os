from __future__ import annotations

from power_web_os.application.radar.power_web_discovery.people_search.contracts import PeopleSearchTask
from power_web_os.application.radar.power_web_discovery.people_search.planning import PowerWebPeopleSearchPlanningInputBuilder
from power_web_os.integrations.openrouter_people_search import OpenRouterPeopleSearchProvider

from power_web_people_search_fixtures import make_handoff


def _provider() -> OpenRouterPeopleSearchProvider:
    return OpenRouterPeopleSearchProvider(
        planner_model_id="planner/test", search_model_id="search/test", api_key="test-key"
    )


def _input():
    return PowerWebPeopleSearchPlanningInputBuilder().build(
        make_handoff(),
        official_domains=("sibur.ru",),
        official_domain_evidence_refs=("source-account-official",),
        language="ru",
    )


def test_people_title_request_contains_roles_but_no_blind_controls_or_search_hints() -> None:
    request = _provider()._hypothesis_request(_input())
    content = request["messages"][1]["content"]
    assert "demand-1" in content
    assert "role-1" in content
    assert "expected_display_name" not in content
    assert "provenance_urls" not in content
    assert "test-key" not in content
    assert "tools" not in request


def test_hh_search_request_uses_public_web_tool_and_domain_restriction() -> None:
    task = PeopleSearchTask(
        task_id="task-hh", decision_id="decision-hh", demand_id="demand-1",
        account_id="account-1", product_id="product-1", sales_playbook_version_id="sales-v1",
        buying_role_policy_version_id="roles-v1", semantic_role_code="technical-owner",
        hypothesis_ids=("hypothesis-1",), lane="hh_public_web",
        query='"SIBUR" "chief engineer" resume', domain_restrictions=("hh.ru",),
    )
    request = _provider()._search_request(task)
    content = request["messages"][1]["content"]
    assert '"hh.ru"' in content
    assert request["tools"][0]["type"] == "openrouter:web_search"
    assert "API" in content and "authentication" in content
    assert "test-key" not in content


def test_search_normalizes_annotations_filters_domains_and_redacts_contacts(monkeypatch) -> None:
    provider = _provider()
    monkeypatch.setattr(provider, "_post", lambda _request: {
        "choices": [{"message": {
            "content": '{"sources": []}',
            "annotations": [
                {"url_citation": {"url": "https://hh.ru/resume/1", "title": "Chief engineer", "content": "mail me@example.com +7 999 123-45-67"}},
                {"url_citation": {"url": "https://other.test/person", "title": "Wrong domain", "content": "ignored"}},
            ],
        }}],
        "usage": {"server_tool_use_details": {"web_search_requests": 1}},
    })
    task = PeopleSearchTask(
        task_id="task-hh", decision_id="decision-hh", demand_id="demand-1",
        account_id="account-1", product_id="product-1", sales_playbook_version_id="sales-v1",
        buying_role_policy_version_id="roles-v1", semantic_role_code="technical-owner",
        hypothesis_ids=("hypothesis-1",), lane="hh_public_web", query="query", domain_restrictions=("hh.ru",),
    )
    result = provider.search(task)
    assert result.outcome == "searched_results"
    assert len(result.sources) == 1
    assert result.sources[0].url == "https://hh.ru/resume/1"
    assert "example.com" not in result.sources[0].excerpt
    assert "999" not in result.sources[0].excerpt
    assert result.sources[0].page_access_limited is True
    assert result.server_tool_searches == 1
