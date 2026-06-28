"""Bounded Radar benchmark runner and report mapper."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import sleep
from typing import Any, Protocol

import httpx


BENCHMARK_RADAR_IDS = (
    "benchmark-sibur-holding-contour",
    "benchmark-mining-toir",
    "benchmark-retail-energy-efficiency",
)


BENCHMARK_PROFILES: dict[str, dict[str, Any]] = {
    "benchmark_smoke": {
        "run_profile": "smoke",
        "max_web_tasks_per_subject": 1,
        "max_discovery_tasks_per_rule": 3,
        "max_gate_tasks_per_candidate_rule": 1,
        "max_signal_tasks_per_candidate_signal": 1,
        "max_total_web_tasks_per_run": 18,
        "min_useful_sources_per_discovery_task": 1,
        "min_candidates_per_discovery_task": 1,
        "max_discovery_retries_per_task": 0,
        "max_checkpoint_revisions_per_run": 1,
        "max_checkpoint_retries_per_stage": 1,
        "max_openrouter_calls_per_run": 16,
        "max_openrouter_planner_calls_per_run": 2,
        "max_openrouter_web_task_calls_per_run": 8,
        "max_recall_expansion_openrouter_calls_per_run": 5,
        "max_openrouter_server_tool_web_searches_per_run": 45,
        "max_dadata_lookups_per_run": 4,
        "max_source_verification_requests_per_run": 30,
        "max_provider_retries_per_task": 2,
        "openrouter_web_max_results_per_call": 3,
        "openrouter_web_max_total_results_per_call": 6,
        "smoke_max_candidates": 3,
        "smoke_max_signals": 1,
        "budget_reserve_limits": {
            "official_coverage_probe": 5,
            "open_web_coverage_probe": 5,
            "production_site_coverage_probe": 3,
        },
        "semantic_task_reserve_limits": {
            "recall_expansion": 6,
            "production_site_coverage_probe": 3,
            "official_coverage_probe": 3,
            "open_web_coverage_probe": 3,
        },
        "benchmark_target_probe_minimums": {
            "holding_or_group_target": 1,
            "known_subsidiary_or_legal_entity_target": 2,
            "production_site_or_branch_target": 2,
        },
    },
    "benchmark_live": {
        "run_profile": "live",
        "max_web_tasks_per_subject": 2,
        "max_discovery_tasks_per_rule": 5,
        "max_gate_tasks_per_candidate_rule": 2,
        "max_signal_tasks_per_candidate_signal": 2,
        "max_total_web_tasks_per_run": 80,
        "min_useful_sources_per_discovery_task": 2,
        "min_candidates_per_discovery_task": 3,
        "max_discovery_retries_per_task": 1,
        "max_checkpoint_revisions_per_run": 2,
        "max_checkpoint_retries_per_stage": 1,
        "max_openrouter_calls_per_run": 32,
        "max_openrouter_planner_calls_per_run": 3,
        "max_openrouter_web_task_calls_per_run": 26,
        "max_openrouter_server_tool_web_searches_per_run": 120,
        "max_dadata_lookups_per_run": 12,
        "max_source_verification_requests_per_run": 100,
        "max_provider_retries_per_task": 1,
        "openrouter_web_max_results_per_call": 5,
        "openrouter_web_max_total_results_per_call": 10,
        "smoke_max_candidates": 0,
        "smoke_max_signals": 0,
    },
}


class RadarBenchmarkHttpClient(Protocol):
    def post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]: ...

    def get_json(self, path: str) -> dict[str, Any]: ...


@dataclass(slots=True)
class HttpxRadarBenchmarkClient:
    api_url: str
    timeout_seconds: float = 30.0

    def post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client(base_url=self.api_url.rstrip("/"), timeout=self.timeout_seconds) as client:
            response = client.post(path, json=payload)
            response.raise_for_status()
            return dict(response.json())

    def get_json(self, path: str) -> dict[str, Any]:
        with httpx.Client(base_url=self.api_url.rstrip("/"), timeout=self.timeout_seconds) as client:
            response = client.get(path)
            response.raise_for_status()
            return dict(response.json())


def benchmark_radar_ids(value: str) -> tuple[str, ...]:
    return BENCHMARK_RADAR_IDS if value == "all" else (value,)


def benchmark_task_context(*, profile: str, radar_id: str) -> dict[str, Any]:
    if profile not in BENCHMARK_PROFILES:
        raise ValueError(f"Unsupported benchmark profile: {profile}")
    return {
        **BENCHMARK_PROFILES[profile],
        "benchmark_profile": profile,
        "source": "radar_benchmark_cli",
        "benchmark_radar_id": radar_id,
        "benchmark_target_hints": benchmark_target_hints(radar_id),
    }


def benchmark_target_hints(radar_id: str) -> list[dict[str, Any]]:
    if radar_id != "benchmark-sibur-holding-contour":
        return []
    path = Path(__file__).resolve().parents[2] / "demo" / "fixtures" / "radar_evaluation" / "sibur_contour_baseline.json"
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    entities = payload.get("entities")
    if not isinstance(entities, list):
        return []
    return [
        {
            "baseline_id": str(item.get("baseline_id") or ""),
            "canonical_name": str(item.get("canonical_name") or ""),
            "aliases": [str(alias) for alias in item.get("aliases", []) if str(alias).strip()] if isinstance(item.get("aliases"), list) else [],
            "entity_type": str(item.get("entity_type") or ""),
            "expected_source_hints": [
                str(hint) for hint in item.get("expected_source_hints", []) if str(hint).strip()
            ] if isinstance(item.get("expected_source_hints"), list) else [],
        }
        for item in entities
        if isinstance(item, dict) and str(item.get("canonical_name") or "").strip()
    ]


def run_radar_benchmark(
    *,
    client: RadarBenchmarkHttpClient,
    radar_ids: tuple[str, ...],
    profile: str,
    poll_interval_seconds: float = 5.0,
    timeout_seconds: float = 1200.0,
) -> dict[str, Any]:
    started_at = _utc_now()
    results: list[dict[str, Any]] = []
    for radar_id in radar_ids:
        run = client.post_json(
            f"/api/radars/{radar_id}/runs",
            {
                "live": True,
                "requester": "radar-benchmark-cli",
                "task_context": benchmark_task_context(profile=profile, radar_id=radar_id),
            },
        )
        run_id = str(run.get("run_id") or "")
        terminal = _poll_run(
            client=client,
            run_id=run_id,
            poll_interval_seconds=poll_interval_seconds,
            timeout_seconds=timeout_seconds,
        )
        dossier = client.get_json(f"/api/radar-runs/{run_id}/dossier") if run_id else {}
        results.append(benchmark_result_summary(radar_id=radar_id, profile=profile, run=terminal, dossier=dossier))
    return {
        "artifact_type": "radar_benchmark_report",
        "artifact_version": "0.7.6.2",
        "generated_at": _utc_now(),
        "started_at": started_at,
        "profile": profile,
        "radar_ids": list(radar_ids),
        "result_count": len(results),
        "summary": _report_summary(results),
        "results": results,
    }


def generate_radar_benchmark_report(
    *,
    api_url: str,
    profile: str,
    radar_id: str,
    output_path: Path,
    poll_interval_seconds: float,
    timeout_seconds: float,
) -> dict[str, Any]:
    report = run_radar_benchmark(
        client=HttpxRadarBenchmarkClient(api_url=api_url),
        radar_ids=benchmark_radar_ids(radar_id),
        profile=profile,
        poll_interval_seconds=poll_interval_seconds,
        timeout_seconds=timeout_seconds,
    )
    _assert_no_secrets(report)
    write_benchmark_report(output_path, report)
    return report


def benchmark_result_summary(
    *,
    radar_id: str,
    profile: str,
    run: dict[str, Any],
    dossier: dict[str, Any],
) -> dict[str, Any]:
    summary = _dict(dossier.get("summary"))
    checkpoint_summary = _dict(dossier.get("checkpoint_summary"))
    external_counters = _dict(dossier.get("external_call_budget_counters"))
    budget_events = _list(dossier.get("budget_exhaustion_events"))
    external_budget_events = _list(dossier.get("external_call_budget_exhaustion_events"))
    cross_execution = _list(dossier.get("cross_source_disambiguation_execution"))
    extraction_records = _list(dossier.get("extraction_recovery_records"))
    candidates = _list(dossier.get("candidates"))
    expansion_targets = _list(dossier.get("expansion_target_queue"))
    expansion_results = _list(dossier.get("search_expansion_results"))
    targets_not_searched = _list(dossier.get("targets_not_searched"))
    executed_expansion_results = [item for item in expansion_results if _is_executed_expansion_result(item)]
    expansion_results_by_type = _count_by(executed_expansion_results, "target_type")
    targets_not_searched_by_type = _count_by(targets_not_searched, "target_type")
    status = str(run.get("status") or "unknown")
    execution_outcome = str(summary.get("execution_outcome") or "")
    verdict = _verdict(
        status=status,
        execution_outcome=execution_outcome,
        budget_events=[*budget_events, *external_budget_events],
    )
    return {
        "radar_id": radar_id,
        "profile": profile,
        "run_id": run.get("run_id"),
        "status": status,
        "started_at": run.get("started_at"),
        "completed_at": run.get("completed_at"),
        "elapsed_seconds": _elapsed_seconds(run.get("started_at"), run.get("completed_at")),
        "execution_outcome": execution_outcome,
        "execution_outcome_reason": summary.get("execution_outcome_reason"),
        "stopped_for_review_reason": dossier.get("stopped_for_review_reason"),
        "verdict": verdict,
        "candidate_count": summary.get("candidate_count", 0),
        "source_count": summary.get("source_count", 0),
        "retrieved_source_count": summary.get("retrieved_source_count", 0),
        "diagnostic_source_count": summary.get("diagnostic_source_count", 0),
        "source_cards_count": summary.get("source_cards_count", 0),
        "source_capability_decision_count": summary.get("source_capability_decision_count", 0),
        "checkpoint_summary": checkpoint_summary,
        "external_call_budget_settings": _dict(dossier.get("external_call_budget_settings")),
        "external_call_budget_counters": external_counters,
        "external_call_budget_counters_by_role": _dict(dossier.get("external_call_budget_counters_by_role")),
        "external_call_budget_exhaustion_count": len(external_budget_events),
        "budget_reserve_counters": _dict(dossier.get("budget_reserve_counters")),
        "budget_reserve_exhaustion_count": len(_list(dossier.get("budget_reserve_exhaustion_events"))),
        "semantic_task_budget_counters": _dict(dossier.get("semantic_task_budget_counters")),
        "semantic_task_budget_exhaustion_count": len(_list(dossier.get("semantic_task_budget_exhaustion_events"))),
        "target_probe_guarantees": _dict(dossier.get("target_probe_guarantees")),
        "target_probe_guarantee_failures": _list(dossier.get("target_probe_guarantee_failures")),
        "source_verification_cache_stats": _dict(dossier.get("source_verification_cache_stats")),
        "source_verification_unique_request_count": dossier.get("source_verification_unique_request_count", 0),
        "source_verification_duplicate_skip_count": dossier.get("source_verification_duplicate_skip_count", 0),
        "source_capability_strategy_summary": _dict(dossier.get("source_capability_strategy_summary")),
        "expansion_target_count": len(expansion_targets),
        "expansion_target_summary_by_type": _dict(dossier.get("expansion_target_summary_by_type")),
        "expansion_result_count": len(executed_expansion_results),
        "search_expansion_execution_summary": _dict(dossier.get("search_expansion_execution_summary")),
        "search_expansion_results_by_target_type": expansion_results_by_type,
        "targets_not_searched_count": len(targets_not_searched),
        "targets_not_searched_by_target_type": targets_not_searched_by_type,
        "benchmark_recall_target_summary": _dict(dossier.get("benchmark_recall_target_summary")),
        "registry_ambiguity_fanout_summary": _dict(dossier.get("registry_ambiguity_fanout_summary")),
        "budget_exhaustion_count": len(budget_events),
        "extraction_recovery_count": len(extraction_records),
        "cross_source_outcomes": _count_by(cross_execution, "outcome"),
        "top_candidates": [
            {
                "legal_name": item.get("legal_name"),
                "tier": item.get("tier"),
                "fit_score": item.get("fit_score"),
                "intent_score": item.get("intent_score"),
                "review_flags": item.get("review_flags", []),
            }
            for item in candidates[:5]
            if isinstance(item, dict)
        ],
    }


def _poll_run(
    *,
    client: RadarBenchmarkHttpClient,
    run_id: str,
    poll_interval_seconds: float,
    timeout_seconds: float,
) -> dict[str, Any]:
    deadline = datetime.now(timezone.utc).timestamp() + timeout_seconds
    latest: dict[str, Any] = {"run_id": run_id, "status": "unknown"}
    while datetime.now(timezone.utc).timestamp() <= deadline:
        latest = client.get_json(f"/api/radar-runs/{run_id}")
        if latest.get("status") in {"completed", "failed", "cancelled"}:
            return latest
        sleep(max(poll_interval_seconds, 0.0))
    return {**latest, "status": "timeout", "error_message": "Benchmark polling timed out."}


def _report_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "by_verdict": _count_by(results, "verdict"),
        "by_status": _count_by(results, "status"),
        "ready_for_quality_review_count": sum(1 for item in results if item.get("verdict") == "ready_for_quality_review"),
        "stopped_diagnostic_count": sum(1 for item in results if item.get("verdict") == "stopped_diagnostic"),
        "budget_limited_count": sum(1 for item in results if item.get("verdict") == "budget_limited"),
        "failed_runtime_count": sum(1 for item in results if item.get("verdict") == "failed_runtime"),
    }


def _verdict(*, status: str, execution_outcome: str, budget_events: list[Any]) -> str:
    if status not in {"completed", "unknown"}:
        return "failed_runtime"
    if budget_events or "budget" in execution_outcome:
        return "budget_limited"
    if execution_outcome in {"completed_with_candidates", "completed_empty"}:
        return "ready_for_quality_review"
    if execution_outcome in {"stopped_for_review", "blocked_by_policy"}:
        return "stopped_diagnostic"
    return "stopped_diagnostic"


def _elapsed_seconds(started_at: object, completed_at: object) -> float | None:
    try:
        if not started_at or not completed_at:
            return None
        started = datetime.fromisoformat(str(started_at).replace("Z", "+00:00"))
        completed = datetime.fromisoformat(str(completed_at).replace("Z", "+00:00"))
    except ValueError:
        return None
    return round((completed - started).total_seconds(), 3)


def _count_by(items: list[Any], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        value = str(item.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts


def _is_executed_expansion_result(item: dict[str, Any]) -> bool:
    status = str(item.get("execution_status") or "executed_source_found")
    return status.startswith("executed")


def _dict(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _list(value: object) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_benchmark_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _assert_no_secrets(payload: dict[str, Any]) -> None:
    serialized = json.dumps(payload, ensure_ascii=False)
    forbidden = (
        "OPENROUTER_API_KEY",
        "DADATA_API_KEY",
        "DADATA_SECRET_KEY",
        "Authorization",
        "Bearer",
        "chain_of_thought",
        "hidden_reasoning",
        "internal_thoughts",
    )
    if any(token in serialized for token in forbidden):
        raise ValueError("Benchmark report contains forbidden secret or hidden reasoning marker.")
