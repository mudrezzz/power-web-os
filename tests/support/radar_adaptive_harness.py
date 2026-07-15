"""Reusable fake Radar providers and assertions for adaptive execution tests."""

from __future__ import annotations

from typing import Any

from power_web_os.application.radar.candidate_discovery.contracts import (
    RadarExecutionPlan,
    RadarExecutionTask,
    RadarSourceEvidence,
    RadarSearchPlan,
    WebSearchProviderResult,
)


class ScriptedProvider:
    runtime_name = "scripted-adaptive"

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
    runtime_name = "source-expansion-adaptive"

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


def radar_definition(*, required_source: bool = False, allow_additional_sources: bool = True) -> dict[str, Any]:
    sources = [
        {"source_id": "sibur_site", "source_type": "web", "usage_obligation": "preferred"},
        {"source_id": "open_web", "source_type": "web", "usage_obligation": "optional"},
    ]
    if required_source:
        sources.append({"source_id": "required_web", "source_type": "web", "usage_obligation": "required_for_coverage"})
    return {
        "radar_id": "adaptive-harness",
        "qualification_criteria": [{"code": "Q1", "label": "Find companies", "requirement_level": "required"}],
        "intent_signals": [{"code": "S1", "label": "Signal", "rule": "Find signal."}],
        "global_search_policy": {"allow_additional_sources": allow_additional_sources, "sources": sources},
    }


def base_plan(
    *,
    source_scope: str = "additional",
    source_ids: list[str] | None = None,
    include_coverage: bool = False,
) -> RadarExecutionPlan:
    tasks = [
        RadarExecutionTask(
            task_id="discover-q1",
            stage="qualification_discovery",
            subject_type="qualification",
            subject_id="Q1",
            query="Find candidate universe.",
            purpose="Discover candidates.",
            source_scope=source_scope,  # type: ignore[arg-type]
            source_ids=source_ids or [],
        )
    ]
    if include_coverage:
        tasks.append(
            RadarExecutionTask(
                task_id="coverage-q1",
                stage="coverage_check",
                subject_type="radar",
                subject_id="adaptive-harness",
                query="Check candidate coverage.",
                purpose="Check coverage.",
                source_scope=source_scope,  # type: ignore[arg-type]
                source_ids=source_ids or [],
            )
        )
    tasks.append(
        RadarExecutionTask(
            task_id="signal-s1",
            stage="signal_search",
            subject_type="signal",
            subject_id="S1",
            query="Find signal.",
            purpose="Search signal.",
            candidate_scope=["Candidate A"],
        )
    )
    return RadarExecutionPlan(radar_id="adaptive-harness", tasks=tasks)


def source_policy_selected(source_id: str) -> list[dict[str, str]]:
    return [{"source_id": source_id, "source_label": source_id, "decision": "selected", "reason": "Required by test."}]


def weak_result() -> WebSearchProviderResult:
    return WebSearchProviderResult(
        provider_metadata={
            "provider": "adaptive-harness",
            "retrieval_source_outcomes": [
                {"source_ref": "retrieved-weak", "outcome": "not_used_by_candidate", "reason": "No linked evidence."}
            ],
        }
    )


def schema_invalid_result() -> WebSearchProviderResult:
    return WebSearchProviderResult(
        provider_metadata={
            "provider": "adaptive-harness",
            "extraction_validation_results": [
                {"state": "extraction_schema_invalid", "message": "Provider output field candidates must be a list."}
            ],
        }
    )


def source_backed_schema_invalid_result() -> WebSearchProviderResult:
    return WebSearchProviderResult(
        sources=[
            RadarSourceEvidence(
                evidence_ref="citation_1",
                title="LLC Candidate A",
                url="https://example.test/source",
                snippet="LLC Candidate A is listed as a production company.",
                query_id="discover-q1",
            )
        ],
        provider_metadata={
            "provider": "adaptive-harness",
            "extraction_validation_results": [
                {"state": "extraction_schema_invalid", "message": "Provider output field candidates must be a list."}
            ],
            "extraction_validation_issues": [
                {"code": "extraction_schema_invalid", "severity": "error", "path": "$.candidates"}
            ],
        },
    )


def evidence_linking_failed_result() -> WebSearchProviderResult:
    return WebSearchProviderResult(
        sources=[source("src_known", query_id="discover-q1")],
        candidate_observations=[
            {
                "legal_name": "Candidate A",
                "entity_type": "legal_entity",
                "qualification": [{"criterion_code": "Q1", "status": "confirmed", "evidence_refs": ["missing_src"]}],
            }
        ],
        provider_metadata={
            "provider": "adaptive-harness",
            "extraction_validation_results": [
                {"state": "evidence_linking_failed", "message": "Evidence ref missing_src did not resolve."}
            ],
        },
    )


def evidence_linking_failed_with_source_diagnostics_result() -> WebSearchProviderResult:
    result = evidence_linking_failed_result()
    return result.model_copy(
        update={
            "sources": [
                RadarSourceEvidence(
                    evidence_ref="src_known",
                    title="LLC Candidate A",
                    url="https://example.test/src_known",
                    snippet="LLC Candidate A is listed as a production company.",
                    query_id="discover-q1",
                )
            ]
        }
    )


def evidence_linking_failed_without_sources_result() -> WebSearchProviderResult:
    return WebSearchProviderResult(
        candidate_observations=[
            {
                "legal_name": "Candidate A",
                "entity_type": "legal_entity",
                "qualification": [
                    {"criterion_code": "Q1", "status": "confirmed", "evidence_refs": ["missing_src"]}
                ],
            }
        ],
        provider_metadata={
            "provider": "adaptive-harness",
            "extraction_validation_results": [
                {"state": "evidence_linking_failed", "message": "Evidence ref missing_src did not resolve."}
            ],
        },
    )


def high_coverage_risk_result() -> WebSearchProviderResult:
    return WebSearchProviderResult(
        provider_metadata={
            "provider": "adaptive-harness",
            "coverage_findings": [{"summary": "Coverage risk is high.", "completeness_risk": "high"}],
        }
    )


def required_source_unavailable_result(*, source_id: str = "required_web") -> WebSearchProviderResult:
    return WebSearchProviderResult(
        sources=[source("src_candidate_a", query_id="discover-q1")],
        candidate_observations=[
            {
                "legal_name": "Candidate A",
                "entity_type": "legal_entity",
                "qualification": [{"criterion_code": "Q1", "status": "confirmed", "evidence_refs": ["src_candidate_a"]}],
                "evidence_refs": ["src_candidate_a"],
            }
        ],
        provider_metadata={
            "provider": "adaptive-harness",
            "source_provider_outcomes": [{"source_id": source_id, "outcome": "provider_unavailable", "reason": "Test outage."}],
        },
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
        provider_metadata={"provider": "adaptive-harness"},
    )


def discovery_result_with_raw_negative_signal(*, query_id: str = "discover-q1") -> WebSearchProviderResult:
    result = strong_discovery_result(query_id=query_id)
    candidate = dict(result.candidate_observations[0])
    candidate["signals"] = [
        {
            "signal_code": "S1",
            "status": "not_observed",
            "search_status": "searched",
            "summary": "No signal evidence found.",
        }
    ]
    return result.model_copy(update={"candidate_observations": [candidate]})


def strong_discovery_with_cross_check_plan(*, query_id: str = "discover-q1") -> WebSearchProviderResult:
    result = strong_discovery_result(query_id=query_id)
    return result.model_copy(update={
        "provider_metadata": {
            **result.provider_metadata,
            "upstream_disambiguation_results": [
                {
                    "entity_name": "Candidate A Plant",
                    "legal_name": "Candidate A Plant",
                    "entity_type": "production_site",
                    "resolution_status": "review_needed",
                    "review_flags": ["registry_match_ambiguous", "requires_human_review"],
                }
            ],
            "cross_source_disambiguation_tasks": [
                {
                    "task_id": "cross-check-candidate-a-plant",
                    "origin_task_id": query_id,
                    "entity_name": "Candidate A Plant",
                    "entity_type": "production_site",
                    "source_ids": ["sibur_site"],
                    "status": "planned",
                }
            ],
        },
    })


def cross_check_supporting_result(*, query_id: str = "cross-check-candidate-a-plant") -> WebSearchProviderResult:
    return WebSearchProviderResult(
        sources=[source("src_cross_check_a", query_id=query_id)],
        candidate_observations=[
            {
                "legal_name": "Candidate A Plant",
                "entity_type": "production_site",
                "entity_resolution_status": "review_needed",
                "review_flags": ["official_source_cross_checked", "requires_human_review"],
                "evidence_refs": ["src_cross_check_a"],
            }
        ],
        provider_metadata={"provider": "adaptive-harness"},
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
        provider_metadata={"provider": "adaptive-harness"},
    )


def source(evidence_ref: str, *, query_id: str) -> RadarSourceEvidence:
    return RadarSourceEvidence(
        evidence_ref=evidence_ref,
        title=f"{evidence_ref} title",
        url=f"https://example.test/{evidence_ref}",
        snippet=f"{evidence_ref} supports Candidate A.",
        query_id=query_id,
    )


def assert_signal_search_ran(execution_results: dict[str, Any]) -> None:
    assert execution_results["signal_task_count"] >= 1
    assert execution_results["checkpoint_decisions"][-1]["action"] == "continue"


def assert_stopped_for_review(execution_results: dict[str, Any], *, reason: str | None = None) -> None:
    assert execution_results["signal_task_count"] == 0
    assert execution_results["checkpoint_summary"]["stopped_for_review"] is True
    assert any(item.get("action") == "stop_review_needed" for item in execution_results["checkpoint_decisions"])
    assert execution_results["stopped_for_review_reason"]
    if reason:
        assert reason in execution_results["stopped_for_review_reason"].lower()


def assert_action_executed(execution_results: dict[str, Any], action: str) -> None:
    matches = [
        item for item in execution_results["adaptive_actions"]
        if item.get("action") == action and item.get("outcome") == "executed"
    ]
    assert matches
    for item in matches:
        assert item.get("attempt") is not None
        assert item.get("task_id")
        assert "source_ids" in item
        assert item.get("outcome") == "executed"


def assert_no_normal_negative_signal_projection(execution_results: dict[str, Any]) -> None:
    statuses = execution_results.get("signal_search_statuses", [])
    assert not any(item.get("search_status") == "searched" for item in statuses)
    assert not any(item.get("search_status") == "not_observed" for item in statuses)
