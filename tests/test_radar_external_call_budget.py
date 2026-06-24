from __future__ import annotations

from typing import Any

from power_web_os.application.live_radar_contracts import (
    RadarExecutionTask,
    RadarSearchPlan,
    RadarSourceEvidence,
    WebSearchProviderResult,
)
from power_web_os.application.live_radar_execution_budget import RadarExecutionBudget, budget_settings_from_context
from power_web_os.application.live_radar_external_budget import (
    RadarExternalCallBudget,
    RadarExternalCallBudgetSettings,
    external_call_budget_context,
)
from power_web_os.application.live_radar_staged_helpers import run_task
from power_web_os.application.radar_source_providers import CompanyLookupRequest
from power_web_os.integrations.dadata_provider import RecordedDaDataCompanyRegistryProvider
from power_web_os.integrations.live_radar_source_verification import SourceReachabilityResult, verify_sources


def test_external_call_budget_blocks_fourth_openrouter_call_when_limit_is_three() -> None:
    budget = RadarExternalCallBudget(RadarExternalCallBudgetSettings(max_openrouter_calls_per_run=3))

    decisions = [budget.reserve("openrouter", key="run") for _ in range(4)]

    assert [item.accepted for item in decisions] == [True, True, True, False]
    assert decisions[-1].reason == "external_call_budget_exhausted"
    assert budget.exhaustion_events[-1]["reason"] == "external_call_budget_exhausted"


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
