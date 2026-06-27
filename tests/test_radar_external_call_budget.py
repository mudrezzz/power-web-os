from __future__ import annotations

from typing import Any

from power_web_os.application.live_radar_contracts import (
    RadarExecutionTask,
    RadarSearchPlan,
    RadarSearchQuery,
    RadarSourceEvidence,
    WebSearchProviderResult,
)
from power_web_os.application.live_radar_execution_budget import RadarExecutionBudget, budget_settings_from_context
from power_web_os.application.live_radar_external_budget import (
    RadarExternalCallBudget,
    RadarExternalCallBudgetSettings,
    external_call_budget_context,
    record_openrouter_server_tool_usage,
    reserve_openrouter_http_call,
)
from power_web_os.application.live_radar_staged_helpers import run_task
from power_web_os.application.radar_source_obligations import obligation_decisions_from_plan, source_obligation_summary
from power_web_os.application.radar_source_providers import CompanyLookupRequest
from power_web_os.integrations.dadata_provider import RecordedDaDataCompanyRegistryProvider
from power_web_os.integrations.openrouter_request_builder import build_openrouter_request
from power_web_os.integrations.live_radar_source_verification import SourceReachabilityResult, verify_sources


def test_external_call_budget_blocks_fourth_openrouter_call_when_limit_is_three() -> None:
    budget = RadarExternalCallBudget(RadarExternalCallBudgetSettings(max_openrouter_calls_per_run=3))

    decisions = [budget.reserve("openrouter", key="run") for _ in range(4)]

    assert [item.accepted for item in decisions] == [True, True, True, False]
    assert decisions[-1].reason == "external_call_budget_exhausted"
    assert budget.exhaustion_events[-1]["reason"] == "external_call_budget_exhausted"


def test_openrouter_planner_and_web_task_calls_share_total_budget() -> None:
    budget = RadarExternalCallBudget(
        RadarExternalCallBudgetSettings(
            max_openrouter_calls_per_run=2,
            max_openrouter_planner_calls_per_run=1,
            max_openrouter_web_task_calls_per_run=2,
        )
    )

    with external_call_budget_context(budget):
        planner = reserve_openrouter_http_call(role="planner", task_id="planner")
        first_web = reserve_openrouter_http_call(role="web_task", task_id="web-1")
        second_web = reserve_openrouter_http_call(role="web_task", task_id="web-2")

    assert planner.accepted
    assert first_web.accepted
    assert not second_web.accepted
    assert second_web.kind == "openrouter"
    assert budget.counts["openrouter:run"] == 2
    assert budget.counts["openrouter_planner:run"] == 1
    assert budget.counts["openrouter_web_task:run"] == 1


def test_server_tool_web_search_usage_blocks_following_web_tasks() -> None:
    budget = RadarExternalCallBudget(
        RadarExternalCallBudgetSettings(
            max_openrouter_calls_per_run=10,
            max_openrouter_web_task_calls_per_run=10,
            max_openrouter_server_tool_web_searches_per_run=4,
        )
    )

    with external_call_budget_context(budget):
        first = reserve_openrouter_http_call(role="web_task", task_id="web-1")
        usage = record_openrouter_server_tool_usage(count=4, task_id="web-1")
        second = reserve_openrouter_http_call(role="web_task", task_id="web-2")

    assert first.accepted
    assert usage.accepted
    assert not second.accepted
    assert second.kind == "openrouter_server_tool_web_search"
    assert budget.to_metadata()["openrouter_server_tool_usage"]["web_search_requests"] == 4


def test_server_tool_usage_overrun_is_recorded_after_completed_call() -> None:
    budget = RadarExternalCallBudget(RadarExternalCallBudgetSettings(max_openrouter_server_tool_web_searches_per_run=3))

    decision = budget.record_server_tool_web_search_usage(count=4, task_id="web-1")

    assert not decision.accepted
    assert decision.reason == "external_call_budget_overrun"
    assert budget.post_call_budget_overruns[0]["task_id"] == "web-1"


def test_openrouter_request_uses_smoke_web_result_caps() -> None:
    request = build_openrouter_request(
        radar={"radar_id": "radar"},
        search_plan=RadarSearchPlan(
                radar_id="radar",
                queries=[
                    RadarSearchQuery(
                        query_id="q1",
                        query="find",
                        purpose="Find.",
                        expected_evidence=["Q1"],
                        stage="qualification_discovery",
                        subject_type="qualification",
                        subject_id="Q1",
                    )
                ],
            ),
        model="model",
        web_mode="server_tools",
        web_max_results=3,
        web_max_total_results=6,
    )

    params = request["tools"][0]["parameters"]
    assert params["max_results"] == 3
    assert params["max_total_results"] == 6


def test_source_verification_budget_marks_extra_sources_not_checked() -> None:
    sources = [
        RadarSourceEvidence(evidence_ref=f"src_{index}", title=f"Source {index}", url=f"https://example.com/{index}", snippet="ok")
        for index in range(3)
    ]
    budget = RadarExternalCallBudget(RadarExternalCallBudgetSettings(max_source_verification_requests_per_run=1))
    calls: list[str] = []

    def fake_check(url: str) -> SourceReachabilityResult:
        calls.append(url)
        return SourceReachabilityResult(state="reachable", reason="ok", status_code=200)

    with external_call_budget_context(budget):
        verified = verify_sources(sources, mode="soft", reachability_check=fake_check)

    assert calls == ["https://example.com/0"]
    assert verified[0].verification_state == "reachable"
    assert [item.verification_state for item in verified[1:]] == ["not_checked", "not_checked"]
    assert "budget" in verified[1].verification_reason.lower()


def test_dadata_lookup_budget_returns_explicit_not_executed_outcome() -> None:
    provider = RecordedDaDataCompanyRegistryProvider(fixtures=[{"legal_name": "Test Company", "inn": "123"}])
    request = CompanyLookupRequest(
        radar_id="radar",
        task_id="task-1",
        stage="qualification_discovery",
        subject_id="Q1",
        query="Test Company",
        source_id="dadata_registry",
        lookup_terms=["Test Company"],
    )
    budget = RadarExternalCallBudget(RadarExternalCallBudgetSettings(max_dadata_lookups_per_run=0))

    with external_call_budget_context(budget):
        result = provider.lookup_companies(request)

    assert result.observations == []
    assert result.outcomes[0].outcome == "not_executed_budget_limited"
    assert result.provider_metadata["budget_decision"]["state"] == "not_executed_budget_limited"


def test_provider_schema_invalid_result_gets_one_budgeted_retry_then_succeeds() -> None:
    provider = _SequencedProvider([
        WebSearchProviderResult(
            provider_metadata={
                "provider_error": {"error_type": "JSONDecodeError", "message": "bad json"},
            }
        ),
        WebSearchProviderResult(
            sources=[RadarSourceEvidence(evidence_ref="src_1", title="ok", url="https://example.com", snippet="ok")],
            candidate_observations=[{"legal_name": "Test Company", "evidence_refs": ["src_1"]}],
        ),
    ])
    budget = RadarExternalCallBudget(RadarExternalCallBudgetSettings(max_provider_retries_per_task=1))

    result = run_task(
        provider=provider,
        radar={"radar_id": "radar"},
        task=_task(),
        radar_id="radar",
        budget=RadarExecutionBudget(budget_settings_from_context()),
        external_budget=budget,
    )

    assert provider.calls == 2
    assert result.candidate_observations[0]["legal_name"] == "Test Company"
    assert budget.retry_records[0]["reason"] == "provider_schema_invalid"


def test_provider_schema_invalid_stops_when_retry_budget_is_exhausted() -> None:
    provider = _SequencedProvider([
        WebSearchProviderResult(provider_metadata={"provider_error": {"message": "bad json"}}),
    ])
    budget = RadarExternalCallBudget(RadarExternalCallBudgetSettings(max_provider_retries_per_task=0))

    result = run_task(
        provider=provider,
        radar={"radar_id": "radar"},
        task=_task(),
        radar_id="radar",
        budget=RadarExecutionBudget(budget_settings_from_context()),
        external_budget=budget,
    )

    assert provider.calls == 1
    assert result.provider_metadata["provider_retry_exhausted"] is True
    assert result.provider_metadata["budget_decision"]["state"] == "not_executed_budget_limited"


def test_required_dadata_no_match_is_identity_not_confirmed_not_satisfied() -> None:
    decisions = obligation_decisions_from_plan(
        global_policy={"sources": [_source("dadata_registry", "company_registry", "required_for_identity")]},
        steps=[_task_with_source("step-1", "qualification_discovery", ["dadata_registry"])],
        source_policy_decisions=[{"source_id": "dadata_registry", "decision": "selected", "reason": "Required identity."}],
        source_provider_outcomes=[{"source_id": "dadata_registry", "outcome": "no_match", "observation_count": 0}],
    )

    assert decisions[0]["status"] == "identity_not_confirmed_after_all_terms"
    assert source_obligation_summary(decisions)["blocking_count"] == 1


def test_required_dadata_useful_outcome_is_not_overwritten_by_later_budget_limit() -> None:
    decisions = obligation_decisions_from_plan(
        global_policy={"sources": [_source("dadata_registry", "company_registry", "required_for_identity")]},
        steps=[_task_with_source("step-1", "qualification_discovery", ["dadata_registry"])],
        source_policy_decisions=[{"source_id": "dadata_registry", "decision": "selected", "reason": "Required identity."}],
        source_provider_outcomes=[
            {"source_id": "dadata_registry", "outcome": "used", "observation_count": 1, "query": "ПАО «СИБУР Холдинг»"},
            {
                "source_id": "dadata_registry",
                "outcome": "not_executed_budget_limited",
                "observation_count": 0,
                "query": "Проверить Candidate scope: ПАО «СИБУР Холдинг»",
            },
        ],
    )

    assert decisions[0]["status"] == "satisfied"
    assert decisions[0]["runtime_outcome"]["outcome"] == "used"
    assert source_obligation_summary(decisions)["blocking_count"] == 0


def test_required_dadata_registry_lookup_insufficient_is_attempted_insufficient() -> None:
    decisions = obligation_decisions_from_plan(
        global_policy={"sources": [_source("dadata_registry", "company_registry", "required_for_identity")]},
        steps=[_task_with_source("step-1", "qualification_discovery", ["dadata_registry"])],
        source_policy_decisions=[{"source_id": "dadata_registry", "decision": "selected", "reason": "Required identity."}],
        source_provider_outcomes=[
            {"source_id": "dadata_registry", "outcome": "registry_lookup_insufficient", "observation_count": 0}
        ],
    )

    assert decisions[0]["status"] == "attempted_insufficient"
    assert source_obligation_summary(decisions)["blocking_source_ids"] == ["dadata_registry"]


def test_required_dadata_registry_without_concrete_input_is_blocked() -> None:
    decisions = obligation_decisions_from_plan(
        global_policy={"sources": [_source("dadata_registry", "company_registry", "required_for_identity")]},
        steps=[_task_with_source("step-1", "qualification_gate", ["dadata_registry"])],
        source_policy_decisions=[{"source_id": "dadata_registry", "decision": "selected", "reason": "Required identity."}],
        source_provider_outcomes=[
            {"source_id": "dadata_registry", "outcome": "not_executed_input_not_available", "observation_count": 0}
        ],
    )

    assert decisions[0]["status"] == "blocked"
    assert decisions[0]["runtime_outcome"]["outcome"] == "not_executed_input_not_available"
    assert source_obligation_summary(decisions)["blocking_source_ids"] == ["dadata_registry"]


def test_required_web_coverage_with_unlinked_sources_is_attempted_unlinked() -> None:
    decisions = obligation_decisions_from_plan(
        global_policy={"sources": [_source("openrouter_web", "search_engine", "required_for_coverage")]},
        steps=[_task_with_source("coverage", "coverage_check", ["openrouter_web"])],
        source_policy_decisions=[{"source_id": "openrouter_web", "decision": "selected", "reason": "Required coverage."}],
        sources=[RadarSourceEvidence(evidence_ref="src_1", title="Source", url="https://example.com", snippet="ok")],
        observations=[],
    )

    assert decisions[0]["status"] == "attempted_unlinked"
    assert decisions[0]["runtime_outcome"]["outcome"] == "retrieved_without_linked_evidence"


def test_required_source_with_linked_evidence_is_satisfied() -> None:
    decisions = obligation_decisions_from_plan(
        global_policy={"sources": [_source("openrouter_web", "search_engine", "required_for_coverage")]},
        steps=[_task_with_source("coverage", "coverage_check", ["openrouter_web"])],
        source_policy_decisions=[{"source_id": "openrouter_web", "decision": "selected", "reason": "Required coverage."}],
        sources=[RadarSourceEvidence(evidence_ref="src_1", title="Source", url="https://example.com", snippet="ok")],
        observations=[{"legal_name": "Company", "evidence_refs": ["src_1"]}],
    )

    assert decisions[0]["status"] == "satisfied"


class _SequencedProvider:
    runtime_name = "sequenced"

    def __init__(self, results: list[WebSearchProviderResult]) -> None:
        self._results = list(results)
        self.calls = 0

    def run_search_plan(self, *, radar: dict[str, Any], search_plan: RadarSearchPlan) -> WebSearchProviderResult:
        _ = radar, search_plan
        self.calls += 1
        return self._results.pop(0)


def _task() -> RadarExecutionTask:
    return RadarExecutionTask(
        task_id="task-1",
        stage="qualification_discovery",
        subject_type="qualification",
        subject_id="Q1",
        query="Find companies",
        purpose="Discovery",
        expected_evidence=["Q1"],
    )


def _task_with_source(task_id: str, stage: str, source_ids: list[str]) -> RadarExecutionTask:
    return RadarExecutionTask(
        task_id=task_id,
        stage=stage,
        subject_type="qualification",
        subject_id="Q1",
        query="Find companies",
        purpose="Discovery",
        expected_evidence=["Q1"],
        source_ids=source_ids,
    )


def _source(source_id: str, source_type: str, usage_obligation: str) -> dict[str, str]:
    return {
        "source_id": source_id,
        "label": source_id,
        "source_type": source_type,
        "usage_obligation": usage_obligation,
    }
