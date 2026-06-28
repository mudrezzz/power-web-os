from __future__ import annotations

import json
from typing import Any

from power_web_os.radar_benchmark import (
    BENCHMARK_RADAR_IDS,
    benchmark_radar_ids,
    benchmark_result_summary,
    benchmark_task_context,
    run_radar_benchmark,
)
from power_web_os.radar_coverage_probe import CoverageProbeTarget, run_coverage_probe
from power_web_os.application.live_radar_contracts import RadarSourceEvidence, WebSearchProviderResult


def test_benchmark_task_context_uses_explicit_smoke_budgets() -> None:
    context = benchmark_task_context(profile="benchmark_smoke", radar_id="benchmark-mining-toir")

    assert context["benchmark_profile"] == "benchmark_smoke"
    assert context["run_profile"] == "smoke"
    assert context["benchmark_radar_id"] == "benchmark-mining-toir"
    assert context["max_total_web_tasks_per_run"] == 18
    assert context["max_openrouter_calls_per_run"] == 16
    assert context["max_openrouter_web_task_calls_per_run"] == 8
    assert context["max_recall_expansion_openrouter_calls_per_run"] == 5
    assert context["max_openrouter_server_tool_web_searches_per_run"] == 45
    assert context["max_provider_retries_per_task"] == 2
    assert context["budget_reserve_limits"]["official_coverage_probe"] == 5
    assert context["budget_reserve_limits"]["open_web_coverage_probe"] == 5
    assert context["budget_reserve_limits"]["production_site_coverage_probe"] == 3
    assert context["semantic_task_reserve_limits"]["recall_expansion"] == 6
    assert context["semantic_task_reserve_limits"]["production_site_coverage_probe"] == 3
    assert context["benchmark_target_probe_minimums"]["holding_or_group_target"] == 1
    assert context["benchmark_target_probe_minimums"]["known_subsidiary_or_legal_entity_target"] == 2
    assert context["benchmark_target_probe_minimums"]["production_site_or_branch_target"] == 2
    assert context["source"] == "radar_benchmark_cli"


def test_sibur_benchmark_task_context_includes_curated_target_hints() -> None:
    context = benchmark_task_context(profile="benchmark_smoke", radar_id="benchmark-sibur-holding-contour")

    hints = context["benchmark_target_hints"]
    assert len(hints) >= 10
    assert {item["entity_type"] for item in hints} >= {"legal_entity", "production_site"}
    assert any(item["baseline_id"] == "gubkinsky-gpp" for item in hints)


def test_benchmark_all_expands_to_benchmark_radars_only() -> None:
    assert benchmark_radar_ids("all") == BENCHMARK_RADAR_IDS
    assert "toir-quick-live" not in benchmark_radar_ids("all")
    assert benchmark_radar_ids("benchmark-mining-toir") == ("benchmark-mining-toir",)


def test_benchmark_result_summary_reports_budget_limited_run() -> None:
    result = benchmark_result_summary(
        radar_id="benchmark-mining-toir",
        profile="benchmark_smoke",
        run={
            "run_id": "radar-run-1",
            "status": "completed",
            "started_at": "2026-06-25T22:00:00Z",
            "completed_at": "2026-06-25T22:00:05Z",
        },
        dossier={
            "summary": {
                "execution_outcome": "stopped_for_review",
                "execution_outcome_reason": "Budget exhausted before signal search.",
                "candidate_count": 0,
                "source_count": 0,
                "retrieved_source_count": 3,
                "diagnostic_source_count": 3,
                "source_cards_count": 2,
                "source_capability_decision_count": 4,
            },
            "stopped_for_review_reason": "Budget exhausted before signal search.",
            "budget_exhaustion_events": [{"reason": "total_run_budget_exhausted"}],
            "checkpoint_summary": {"stopped_for_review": True},
            "extraction_recovery_records": [{"outcome": "recovered"}],
            "cross_source_disambiguation_execution": [{"outcome": "skipped_budget_limited"}],
            "candidates": [],
        },
    )

    assert result["verdict"] == "budget_limited"
    assert result["retrieved_source_count"] == 3
    assert result["extraction_recovery_count"] == 1
    assert result["cross_source_outcomes"] == {"skipped_budget_limited": 1}
    assert result["elapsed_seconds"] == 5.0
    _assert_safe(result)


def test_benchmark_result_summary_counts_only_executed_expansion_results() -> None:
    result = benchmark_result_summary(
        radar_id="benchmark-sibur-holding-contour",
        profile="benchmark_smoke",
        run={"run_id": "radar-run-1", "status": "completed"},
        dossier={
            "summary": {"execution_outcome": "stopped_for_review"},
            "search_expansion_results": [
                {
                    "target_id": "site-1",
                    "target_type": "production_site_or_branch_target",
                    "execution_status": "not_executed",
                    "not_searched_reason": "not_executed_global_budget_limited",
                },
                {
                    "target_id": "site-2",
                    "target_type": "production_site_or_branch_target",
                    "execution_status": "executed_source_found",
                    "source_count": 1,
                    "candidate_observation_count": 1,
                },
            ],
            "targets_not_searched": [
                {
                    "target_id": "site-1",
                    "target_type": "production_site_or_branch_target",
                    "not_searched_reason": "not_executed_global_budget_limited",
                }
            ],
            "search_expansion_execution_summary": {
                "generated_count": 2,
                "selected_count": 2,
                "attempted_count": 2,
                "executed_count": 1,
                "not_executed_global_budget_limited_count": 1,
            },
            "budget_exhaustion_events": [{"reason": "external_call_budget_exhausted"}],
        },
    )

    assert result["expansion_result_count"] == 1
    assert result["search_expansion_results_by_target_type"] == {"production_site_or_branch_target": 1}
    assert result["targets_not_searched_by_target_type"] == {"production_site_or_branch_target": 1}
    assert result["search_expansion_execution_summary"]["executed_count"] == 1


def test_benchmark_result_summary_exposes_semantic_budget_guarantees_and_verification_cache() -> None:
    result = benchmark_result_summary(
        radar_id="benchmark-sibur-holding-contour",
        profile="benchmark_smoke",
        run={"run_id": "radar-run-1", "status": "completed"},
        dossier={
            "summary": {"execution_outcome": "stopped_for_review"},
            "semantic_task_budget_counters": {"semantic_reserve:production_site_coverage_probe": 2},
            "semantic_task_budget_exhaustion_events": [{"reason": "semantic_task_reserve_exhausted"}],
            "target_probe_guarantees": {
                "target_probe_minimums_satisfied": False,
                "by_target_type": {
                    "production_site_or_branch_target": {"required": 2, "executed_count": 1, "satisfied": False}
                },
            },
            "target_probe_guarantee_failures": [
                {"target_type": "production_site_or_branch_target", "reason": "semantic_task_budget_limited"}
            ],
            "source_verification_cache_stats": {
                "source_verification_unique_request_count": 1,
                "source_verification_cache_hit_count": 2,
                "source_verification_duplicate_skip_count": 2,
            },
            "source_verification_unique_request_count": 1,
            "source_verification_duplicate_skip_count": 2,
        },
    )

    assert result["semantic_task_budget_counters"] == {"semantic_reserve:production_site_coverage_probe": 2}
    assert result["semantic_task_budget_exhaustion_count"] == 1
    assert result["target_probe_guarantees"]["target_probe_minimums_satisfied"] is False
    assert result["target_probe_guarantee_failures"][0]["reason"] == "semantic_task_budget_limited"
    assert result["source_verification_unique_request_count"] == 1
    assert result["source_verification_duplicate_skip_count"] == 2


def test_benchmark_result_summary_treats_external_budget_exhaustion_as_budget_limited() -> None:
    result = benchmark_result_summary(
        radar_id="benchmark-sibur-holding-contour",
        profile="benchmark_smoke",
        run={"run_id": "radar-run-1", "status": "completed"},
        dossier={
            "summary": {"execution_outcome": "stopped_for_review"},
            "external_call_budget_settings": {
                "max_openrouter_calls_per_run": 14,
                "max_recall_expansion_openrouter_calls_per_run": 4,
            },
            "external_call_budget_counters": {
                "openrouter:run": 14,
                "openrouter_recall_expansion:run": 0,
            },
            "external_call_budget_counters_by_role": {
                "openrouter": 14,
                "openrouter_recall_expansion": 0,
            },
            "external_call_budget_exhaustion_events": [
                {
                    "reason": "external_call_budget_exhausted",
                    "key": "openrouter:run",
                }
            ],
        },
    )

    assert result["verdict"] == "budget_limited"
    assert result["external_call_budget_settings"]["max_openrouter_calls_per_run"] == 14
    assert result["external_call_budget_counters"]["openrouter:run"] == 14
    assert result["external_call_budget_exhaustion_count"] == 1


def test_benchmark_runner_queues_runs_and_writes_report_shape() -> None:
    client = _FakeBenchmarkClient()

    report = run_radar_benchmark(
        client=client,
        radar_ids=("benchmark-sibur-holding-contour", "benchmark-mining-toir"),
        profile="benchmark_smoke",
        poll_interval_seconds=0,
        timeout_seconds=5,
    )

    assert [item["radar_id"] for item in report["results"]] == [
        "benchmark-sibur-holding-contour",
        "benchmark-mining-toir",
    ]
    assert report["summary"]["by_verdict"] == {"ready_for_quality_review": 2}
    assert client.posts[0][0] == "/api/radars/benchmark-sibur-holding-contour/runs"
    assert client.posts[0][1]["task_context"]["benchmark_profile"] == "benchmark_smoke"
    assert client.posts[0][1]["task_context"]["max_total_web_tasks_per_run"] == 18
    _assert_safe(report)


def test_coverage_probe_classifies_official_source_with_fake_provider() -> None:
    provider = _FakeCoverageProvider()

    report = run_coverage_probe(
        run={"run_id": "radar-run-1"},
        radar_id="benchmark-sibur-holding-contour",
        targets=[
            CoverageProbeTarget(
                baseline_id="gubkinsky-gpp",
                canonical_name="Губкинский газоперерабатывающий завод",
                aliases=("Губкинский ГПЗ",),
                entity_type="production_site",
            )
        ],
        provider=provider,
        probe_limit=1,
    )

    assert provider.queries == ["Губкинский газоперерабатывающий завод Губкинский ГПЗ СИБУР site:sibur.ru"]
    assert report["summary"] == {"probe_found_official_source": 1}
    assert report["results"][0]["urls"] == ["https://www.sibur.ru/example/gubkinsky-gpp"]
    _assert_safe(report)


def test_coverage_probe_prefers_found_official_source_over_retry_budget_marker() -> None:
    provider = _FakeCoverageProvider(with_budget_marker=True)

    report = run_coverage_probe(
        run={"run_id": "radar-run-1"},
        radar_id="benchmark-sibur-holding-contour",
        targets=[
            CoverageProbeTarget(
                baseline_id="gubkinsky-gpp",
                canonical_name="Губкинский газоперерабатывающий завод",
                aliases=("Губкинский ГПЗ",),
                entity_type="production_site",
            )
        ],
        provider=provider,
        probe_limit=1,
    )

    assert report["summary"] == {"probe_found_official_source": 1}
    assert report["results"][0]["status"] == "probe_found_official_source"
    _assert_safe(report)


class _FakeBenchmarkClient:
    def __init__(self) -> None:
        self.posts: list[tuple[str, dict[str, Any]]] = []
        self._run_counter = 0

    def post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.posts.append((path, payload))
        self._run_counter += 1
        return {"run_id": f"radar-run-{self._run_counter}", "status": "queued"}

    def get_json(self, path: str) -> dict[str, Any]:
        if path.endswith("/dossier"):
            return {
                "summary": {
                    "execution_outcome": "completed_with_candidates",
                    "candidate_count": 1,
                    "source_count": 1,
                    "retrieved_source_count": 2,
                    "diagnostic_source_count": 2,
                    "source_cards_count": 2,
                    "source_capability_decision_count": 3,
                },
                "checkpoint_summary": {"stopped_for_review": False},
                "budget_exhaustion_events": [],
                "candidates": [{"legal_name": "Candidate A", "tier": "Monitor", "review_flags": []}],
            }
        return {
            "run_id": path.rsplit("/", 1)[-1],
            "status": "completed",
            "started_at": "2026-06-25T22:00:00Z",
            "completed_at": "2026-06-25T22:00:03Z",
        }


class _FakeCoverageProvider:
    def __init__(self, *, with_budget_marker: bool = False) -> None:
        self.queries: list[str] = []
        self.with_budget_marker = with_budget_marker

    def run_search_plan(self, *, radar: dict[str, object], search_plan):
        _ = radar
        self.queries.append(search_plan.queries[0].query)
        return WebSearchProviderResult(
            sources=[
                RadarSourceEvidence(
                    evidence_ref="src_probe",
                    title="СИБУР Губкинский ГПЗ",
                    url="https://www.sibur.ru/example/gubkinsky-gpp",
                    snippet="Губкинский ГПЗ связан с СИБУР.",
                )
            ],
            provider_metadata={"budget_decision": {"accepted": False}} if self.with_budget_marker else {},
        )


def _assert_safe(payload: dict[str, Any]) -> None:
    serialized = json.dumps(payload, ensure_ascii=False)
    forbidden = ("OPENROUTER_API_KEY", "DADATA_API_KEY", "DADATA_SECRET_KEY", "Authorization", "Bearer", "chain_of_thought", "hidden_reasoning", "internal_thoughts")
    assert not any(token in serialized for token in forbidden)
