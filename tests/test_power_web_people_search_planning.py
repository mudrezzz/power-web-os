from __future__ import annotations

import pytest
from pydantic import ValidationError

from power_web_os.application.radar.power_web_discovery.people_search.planning import (
    AccountRoleTitleHypothesisAcceptanceService,
    AccountRoleTitleHypothesisPlanner,
    PowerWebPeopleSearchPlanningInputBuilder,
)
from power_web_os.application.radar.power_web_discovery.people_search.contracts import PeopleSearchBudgetSettings
from power_web_os.application.radar.power_web_discovery.people_search.service import PeopleSearchPlanningService

from power_web_people_search_fixtures import make_handoff, make_two_product_handoff


def _input():
    return PowerWebPeopleSearchPlanningInputBuilder().build(
        make_handoff(),
        official_domains=("https://www.sibur.ru/",),
        official_domain_evidence_refs=("source-account-official",),
        language="ru",
    )


def test_planning_input_preserves_all_handoff_demands() -> None:
    planning_input = _input()
    assert len(planning_input.role_demands) == 8
    assert {item.demand_id for item in planning_input.role_demands} == {
        f"demand-{index}" for index in range(1, 9)
    }
    assert planning_input.official_domains == ("sibur.ru",)
    assert planning_input.official_domain_evidence_refs == ("source-account-official",)


def test_recorded_two_product_handoff_preserves_all_fourteen_demands() -> None:
    planning_input = PowerWebPeopleSearchPlanningInputBuilder().build(
        make_two_product_handoff(), language="ru"
    )

    assert len(planning_input.role_demands) == 14
    assert {item.product_id for item in planning_input.role_demands} == {
        "product-smartdiagnostics", "product-energy-optimization"
    }
    assert len({item.demand_id for item in planning_input.role_demands}) == 14


def test_official_domain_requires_evidence_ref() -> None:
    with pytest.raises(ValidationError, match="official domains require source evidence refs"):
        PowerWebPeopleSearchPlanningInputBuilder().build(
            make_handoff(), official_domains=("sibur.ru",), language="ru"
        )


def test_hypothesis_acceptance_cannot_mutate_role_policy() -> None:
    planning_input = _input()
    demand = planning_input.role_demands[0]
    planner = AccountRoleTitleHypothesisPlanner()
    proposals = list(planner.proposals_from_values(planning_input, {demand.demand_id: ("Chief engineer",)}))
    proposals[0] = proposals[0].model_copy(update={"product_id": "another-product"})
    accepted, decisions = AccountRoleTitleHypothesisAcceptanceService().accept(
        planning_input, tuple(proposals)
    )
    assert any(item.reason_code == "lineage_or_role_mismatch" for item in decisions)
    assert any(item.demand_id == demand.demand_id and item.origin == "deterministic_fallback" for item in accepted)
    assert all(item.product_id == demand.product_id for item in accepted if item.demand_id == demand.demand_id)


def test_hypothesis_acceptance_rejects_duplicates_unrelated_and_private_values() -> None:
    planning_input = _input()
    demand = planning_input.role_demands[0]
    planner = AccountRoleTitleHypothesisPlanner()
    proposals = list(planner.proposals_from_values(planning_input, {
        demand.demand_id: (
            "Unrelated role mutation",
            "Chief engineer",
            "Chief engineer",
            "https://private.example/person",
        ),
    }))
    proposals[0] = proposals[0].model_copy(update={"semantic_role_code": "unrelated-role"})
    accepted, decisions = AccountRoleTitleHypothesisAcceptanceService().accept(planning_input, tuple(proposals))
    reasons = {item.reason_code for item in decisions if not item.accepted}
    assert {"lineage_or_role_mismatch", "duplicate", "private_contact_or_url"} <= reasons
    assert len([item for item in accepted if item.demand_id == demand.demand_id]) >= 1


def test_hypothesis_planner_uses_one_bounded_schema_retry() -> None:
    planning_input = _input()

    class RetryProvider:
        def __init__(self) -> None:
            self.calls = 0

        def propose(self, value):
            self.calls += 1
            if self.calls == 1:
                return {"unknown-demand": ("Chief engineer",)}
            return {item.demand_id: (item.display_name,) for item in value.role_demands}

    provider = RetryProvider()
    plan = PeopleSearchPlanningService(
        provider=provider, settings=PeopleSearchBudgetSettings()
    ).build(planning_input)

    assert provider.calls == 2
    assert plan.hypothesis_provider_calls == 2
    assert "hypothesis_schema_retry:1" in plan.diagnostics
    assert {item.demand_id for item in plan.accepted_hypotheses} == {
        item.demand_id for item in planning_input.role_demands
    }


def test_missing_official_domain_is_not_executable_without_generic_masquerading() -> None:
    planning_input = PowerWebPeopleSearchPlanningInputBuilder().build(make_handoff(), language="ru")
    plan = PeopleSearchPlanningService(
        provider=None, settings=PeopleSearchBudgetSettings()
    ).build(planning_input)

    official = [item for item in plan.lane_decisions if item.lane == "official_company"]
    assert len(official) == 8
    assert all(item.status == "not_executable" for item in official)
    assert all(item.reason_code == "official_domain_missing" for item in official)
    assert len(plan.tasks) == 16
    assert {item.lane for item in plan.tasks} == {"hh_public_web", "generic_web"}
