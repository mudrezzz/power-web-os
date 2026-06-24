"""Fast contracts for adaptive Radar checkpoint execution.

These tests deliberately distinguish a checkpoint *decision* from executed
adaptive behavior.
"""

from __future__ import annotations

from typing import Any

from power_web_os.application.live_radar_contracts import (
    RadarExecutionPlan,
    RadarExecutionTask,
    RadarSourceEvidence,
    RadarSearchPlan,
    WebSearchProviderResult,
)
from power_web_os.application.live_radar_staged_execution import run_staged_radar_execution


def test_unrecovered_weak_discovery_does_not_start_signal_search() -> None:
    provider = ScriptedProvider([weak_result()])

    result, events, execution_results = run_staged_radar_execution(
        radar=radar_definition(),
        execution_plan=base_plan(),
        provider=provider,
    )

    assert result.candidate_observations == []
    assert provider.stages == ["qualification_discovery", "qualification_discovery"]
    assert execution_results["signal_task_count"] == 0
    assert execution_results["checkpoint_summary"]["stopped_for_review"] is True
    assert execution_results["checkpoint_decisions"][-1]["action"] == "stop_review_needed"
    assert "execution_stopped_for_review" in [event.event_type for event in events]


def test_weak_discovery_should_retry_same_source_then_continue() -> None:
    provider = ScriptedProvider([weak_result(), strong_discovery_result(), signal_result()])

    _, _, execution_results = run_staged_radar_execution(
        radar=radar_definition(),
        execution_plan=base_plan(),
        provider=provider,
        max_checkpoint_retries_per_stage=1,
    )

    assert provider.stages == ["qualification_discovery", "qualification_discovery", "signal_search"]
    assert execution_results["signal_task_count"] == 1
    assert any(
        action.get("action") == "retry_same_source" and action.get("outcome") in {"executed", "applied"}
        for action in execution_results["adaptive_actions"]
    )


def test_weak_discovery_should_expand_allowed_sources() -> None:
    provider = SourceExpansionProvider()

    _, _, execution_results = run_staged_radar_execution(
        radar=radar_definition(),
        execution_plan=base_plan(source_scope="global", source_ids=["sibur_site"]),
        provider=provider,
        max_checkpoint_retries_per_stage=1,
    )

    discovery_calls = [call.queries[0] for call in provider.calls if call.queries[0].stage == "qualification_discovery"]
    assert [query.source_scope for query in discovery_calls] == ["global", "additional"]
    assert execution_results["signal_task_count"] == 1
    assert any(
        action.get("action") == "expand_sources" and action.get("outcome") in {"executed", "applied"}
        for action in execution_results["adaptive_actions"]
    )


def test_schema_failure_should_apply_plan_revision() -> None:
    provider = ScriptedProvider([schema_invalid_result(), strong_discovery_result(), signal_result()])

    _, _, execution_results = run_staged_radar_execution(
        radar=radar_definition(),
        execution_plan=base_plan(),
        provider=provider,
        max_checkpoint_revisions_per_run=1,
    )

    assert provider.stages == ["qualification_discovery", "qualification_discovery", "signal_search"]
    assert execution_results["signal_task_count"] == 1
    assert any(
        action.get("action") == "revise_plan" and action.get("outcome") in {"executed", "applied"}
        for action in execution_results["adaptive_actions"]
    )


def test_revision_limit_should_stop_for_review_without_blind_fallback() -> None:
    provider = ScriptedProvider([schema_invalid_result(), schema_invalid_result(), schema_invalid_result()])

    _, _, execution_results = run_staged_radar_execution(
        radar=radar_definition(),
        execution_plan=base_plan(),
        provider=provider,
        max_checkpoint_revisions_per_run=2,
    )

    assert provider.stages == ["qualification_discovery", "qualification_discovery", "qualification_discovery"]
    assert execution_results["signal_task_count"] == 0
    assert execution_results["checkpoint_summary"]["stopped_for_review"] is True
    assert "revision" in execution_results["stopped_for_review_reason"].lower()


def test_retry_limit_should_stop_for_review_without_signal_search() -> None:
    provider = ScriptedProvider([weak_result(), weak_result()])

    _, _, execution_results = run_staged_radar_execution(
        radar=radar_definition(),
        execution_plan=base_plan(),
        provider=provider,
        max_checkpoint_retries_per_stage=1,
    )

    assert provider.stages == ["qualification_discovery", "qualification_discovery"]
    assert execution_results["signal_task_count"] == 0
    assert execution_results["checkpoint_summary"]["stopped_for_review"] is True
    assert "retry" in execution_results["stopped_for_review_reason"].lower()


class ScriptedProvider:
    runtime_name = "scripted-adaptive-red"

    def __init__(self, results: list[WebSearchProviderResult]) -> None:
        self._results = list(results)
        self.calls: list[RadarSearchPlan] = []

    @property
    def stages(self) -> list[str | None]:
        return [call.queries[0].stage for call in self.calls]

    def run_search_plan(self, *, radar: dict[str, Any], search_plan: RadarSearchPlan) -> WebSearchProviderResult:
        _ = radar
        self.calls.append(search_plan)
        return self._results.pop(0) if self._results else WebSearchProviderResult()


class SourceExpansionProvider:
    runtime_name = "source-expansion-adaptive-red"

    def __init__(self) -> None:
        self.calls: list[RadarSearchPlan] = []

    def run_search_plan(self, *, radar: dict[str, Any], search_plan: RadarSearchPlan) -> WebSearchProviderResult:
        _ = radar
        self.calls.append(search_plan)
        query = search_plan.queries[0]
        if query.stage == "qualification_discovery" and query.source_scope == "additional":
            return strong_discovery_result(query_id=query.query_id)
        if query.stage == "signal_search":
            return signal_result(query_id=query.query_id)
        return weak_result()


def radar_definition() -> dict[str, Any]:
    return {
        "radar_id": "adaptive-red",
        "qualification_criteria": [{"code": "Q1", "label": "Find companies", "requirement_level": "required"}],
        "intent_signals": [{"code": "S1", "label": "Signal", "rule": "Find signal."}],
        "global_search_policy": {
            "sources": [
                {"source_id": "sibur_site", "source_type": "web", "usage_obligation": "preferred"},
                {"source_id": "open_web", "source_type": "web", "usage_obligation": "optional"},
            ],
        },
    }


def base_plan(*, source_scope: str = "additional", source_ids: list[str] | None = None) -> RadarExecutionPlan:
    return RadarExecutionPlan(
        radar_id="adaptive-red",
        tasks=[
            RadarExecutionTask(
                task_id="discover-q1",
                stage="qualification_discovery",
                subject_type="qualification",
                subject_id="Q1",
                query="Find candidate universe.",
                purpose="Discover candidates.",
                source_scope=source_scope,  # type: ignore[arg-type]
                source_ids=source_ids or [],
            ),
            RadarExecutionTask(
                task_id="signal-s1",
                stage="signal_search",
                subject_type="signal",
                subject_id="S1",
                query="Find signal.",
                purpose="Search signal.",
                candidate_scope=["Candidate A"],
            ),
        ],
    )


def weak_result() -> WebSearchProviderResult:
    return WebSearchProviderResult(
        provider_metadata={
            "provider": "adaptive-red",
            "retrieval_source_outcomes": [
                {"source_ref": "retrieved-weak", "outcome": "not_used_by_candidate", "reason": "No linked evidence."}
            ],
        }
    )


def schema_invalid_result() -> WebSearchProviderResult:
    return WebSearchProviderResult(
        provider_metadata={
            "provider": "adaptive-red",
            "extraction_validation_results": [
                {"state": "extraction_schema_invalid", "message": "Provider output field candidates must be a list."}
            ],
        }
    )


def strong_discovery_result(*, query_id: str = "discover-q1") -> WebSearchProviderResult:
    return WebSearchProviderResult(
        sources=[source("src_candidate_a", query_id=query_id)],
        candidate_observations=[
            {
                "legal_name": "Candidate A",
                "entity_type": "legal_entity",
                "qualification": [{"criterion_code": "Q1", "status": "confirmed", "evidence_refs": ["src_candidate_a"]}],
                "evidence_refs": ["src_candidate_a"],
            }
        ],
        provider_metadata={"provider": "adaptive-red"},
    )


def signal_result(*, query_id: str = "signal-s1") -> WebSearchProviderResult:
    return WebSearchProviderResult(
        sources=[source("src_signal_a", query_id=query_id)],
        candidate_observations=[
            {
                "legal_name": "Candidate A",
                "signals": [{"signal_code": "S1", "status": "observed", "score": 1, "evidence_refs": ["src_signal_a"]}],
            }
        ],
        provider_metadata={"provider": "adaptive-red"},
    )


def source(evidence_ref: str, *, query_id: str) -> RadarSourceEvidence:
    return RadarSourceEvidence(
        evidence_ref=evidence_ref,
        title=f"{evidence_ref} title",
        url=f"https://example.test/{evidence_ref}",
        snippet=f"{evidence_ref} supports Candidate A.",
        query_id=query_id,
    )
