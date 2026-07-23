from __future__ import annotations

from power_web_os.application.radar.power_web_discovery.people_search.contracts import (
    PeopleSearchBudgetSettings,
    PeopleSearchProviderResult,
    PeopleSearchProviderSource,
)
from power_web_os.application.radar.power_web_discovery.people_search.execution import PeopleSearchStageExecutor
from power_web_os.application.radar.power_web_discovery.people_search.planning import PowerWebPeopleSearchPlanningInputBuilder
from power_web_os.application.radar.power_web_discovery.people_search.service import PeopleSearchPlanningService

from power_web_people_search_fixtures import make_handoff


class RecordedProvider:
    runtime_name = "recorded_people_search"
    model_id = "recorded/model"

    def __init__(self, *, fail_first: bool = False) -> None:
        self.calls = 0
        self.fail_first = fail_first

    def search(self, task):
        self.calls += 1
        if self.fail_first and self.calls == 1:
            raise TimeoutError("recorded timeout")
        domain = task.domain_restrictions[0] if task.domain_restrictions else "example.org"
        return PeopleSearchProviderResult(
            outcome="searched_results",
            sources=(PeopleSearchProviderSource(
                source_ref=f"source-{task.task_id}",
                url=f"https://{domain}/public/{task.semantic_role_code}",
                title=f"АО СИБУР-Химпром {task.semantic_role_code}",
                excerpt=f"Technical buying role for {task.semantic_role_code}",
                rank=1,
                page_access_limited=task.lane == "hh_public_web",
            ),),
            engine="recorded",
            model_id=self.model_id,
            server_tool_searches=1,
        )


class RevisionProvider(RecordedProvider):
    def search(self, task):
        self.calls += 1
        if task.revision == 0:
            return PeopleSearchProviderResult(
                outcome="searched_no_results",
                engine="recorded",
                model_id=self.model_id,
                server_tool_searches=1,
            )
        domain = task.domain_restrictions[0] if task.domain_restrictions else "example.org"
        return PeopleSearchProviderResult(
            outcome="searched_results",
            sources=(PeopleSearchProviderSource(
                source_ref=f"source-{task.task_id}",
                url=f"https://{domain}/public/{task.semantic_role_code}",
                title=f"АО СИБУР-Химпром {task.semantic_role_code}",
                excerpt=f"Technical buying role for {task.semantic_role_code}",
                rank=1,
            ),),
            engine="recorded",
            model_id=self.model_id,
            server_tool_searches=1,
        )


def _planned():
    planning_input = PowerWebPeopleSearchPlanningInputBuilder().build(
        make_handoff(),
        official_domains=("sibur.ru",),
        official_domain_evidence_refs=("source-account-official",),
        language="ru",
    )
    plan = PeopleSearchPlanningService(provider=None, settings=PeopleSearchBudgetSettings()).build(planning_input)
    return planning_input, plan


def _artifact(*, fail_first: bool = False):
    planning_input, plan = _planned()
    provider = RecordedProvider(fail_first=fail_first)
    artifact = PeopleSearchStageExecutor(provider, settings=PeopleSearchBudgetSettings()).execute(
        planning_input=planning_input,
        proposals=plan.proposals,
        accepted_hypotheses=plan.accepted_hypotheses,
        acceptance=plan.acceptance,
        lane_decisions=plan.lane_decisions,
        tasks=plan.tasks,
        hypothesis_provider_calls=plan.hypothesis_provider_calls,
        model_profile_id="power_web_people_search_default",
    )
    return artifact, provider


def test_quality_plan_has_three_mandatory_lanes_per_role() -> None:
    _, plan = _planned()
    assert len(plan.lane_decisions) == 24
    assert len(plan.tasks) == 24
    for demand_id in {item.demand_id for item in plan.tasks}:
        assert {item.lane for item in plan.tasks if item.demand_id == demand_id} == {
            "official_company", "hh_public_web", "generic_web"
        }


def test_every_selected_lane_has_terminal_outcome() -> None:
    artifact, _ = _artifact()
    assert all(item.status == "executed" for item in artifact.lane_decisions)
    assert {item.decision_id for item in artifact.lane_decisions} == {item.decision_id for item in artifact.tasks}


def test_hh_tasks_are_domain_restricted_and_never_use_hh_api() -> None:
    artifact, _ = _artifact()
    hh_tasks = [item for item in artifact.tasks if item.lane == "hh_public_web"]
    assert len(hh_tasks) == 8
    assert all(item.domain_restrictions == ("hh.ru",) for item in hh_tasks)
    assert artifact.hh_api_calls == 0


def test_executed_tasks_have_product_safe_receipts() -> None:
    artifact, _ = _artifact()
    assert len(artifact.receipts) == 24
    assert all(item.source_refs and item.attempts for item in artifact.receipts)
    payload = artifact.model_dump(mode="json")
    assert payload["raw_provider_payload_retained"] is False
    assert payload["raw_html_retained"] is False
    assert payload["credentials_retained"] is False
    assert payload["private_contacts_retained"] is False
    assert payload["hidden_reasoning_retained"] is False
    assert not any(key in payload for key in ("raw_payload", "html", "headers", "credentials", "contacts", "hidden_reasoning"))


def test_provider_failure_never_becomes_searched_no_results() -> None:
    artifact, provider = _artifact(fail_first=True)
    first = artifact.receipts[0]
    assert [item.outcome for item in first.attempts] == ["provider_error", "searched_results"]
    assert first.terminal_outcome == "searched_results"
    assert provider.calls == 25


def test_people_search_budget_is_independent_and_bounded() -> None:
    artifact, _ = _artifact(fail_first=True)
    assert artifact.budgets.provider_calls == 25
    assert artifact.budgets.retries == 1
    assert artifact.budgets.provider_calls <= artifact.budgets.settings.max_provider_calls
    assert artifact.budgets.hypothesis_provider_calls == 0


def test_successful_no_results_gets_one_bounded_query_revision() -> None:
    planning_input, plan = _planned()
    provider = RevisionProvider()
    artifact = PeopleSearchStageExecutor(provider, settings=PeopleSearchBudgetSettings()).execute(
        planning_input=planning_input,
        proposals=plan.proposals,
        accepted_hypotheses=plan.accepted_hypotheses,
        acceptance=plan.acceptance,
        lane_decisions=plan.lane_decisions,
        tasks=plan.tasks,
        hypothesis_provider_calls=plan.hypothesis_provider_calls,
        model_profile_id="power_web_people_search_default",
    )

    revisions = [item for item in artifact.tasks if item.revision == 1]
    assert len(revisions) == 16
    assert artifact.budgets.query_revisions == 16
    assert artifact.budgets.people_search_tasks == 40
    assert artifact.budgets.provider_calls == 40
    assert len({(item.demand_id, item.lane) for item in revisions}) == 16
    assert {item.lane for item in revisions} == {"official_company", "hh_public_web", "generic_web"}
