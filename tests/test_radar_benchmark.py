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


def test_benchmark_task_context_uses_explicit_smoke_budgets() -> None:
    context = benchmark_task_context(profile="benchmark_smoke", radar_id="benchmark-mining-toir")

    assert context["benchmark_profile"] == "benchmark_smoke"
    assert context["run_profile"] == "smoke"
    assert context["benchmark_radar_id"] == "benchmark-mining-toir"
    assert context["max_total_web_tasks_per_run"] == 18
    assert context["max_openrouter_calls_per_run"] == 10
    assert context["source"] == "radar_benchmark_cli"


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


def _assert_safe(payload: dict[str, Any]) -> None:
    serialized = json.dumps(payload, ensure_ascii=False)
    forbidden = ("OPENROUTER_API_KEY", "DADATA_API_KEY", "DADATA_SECRET_KEY", "Authorization", "Bearer", "chain_of_thought", "hidden_reasoning", "internal_thoughts")
    assert not any(token in serialized for token in forbidden)
