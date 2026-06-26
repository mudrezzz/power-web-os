"""Optional post-run coverage probes for Radar benchmark false negatives."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from power_web_os.application.live_radar_contracts import RadarSearchPlan, RadarSearchQuery, WebSearchProvider
from power_web_os.application.live_radar_external_budget import (
    RadarExternalCallBudget,
    RadarExternalCallBudgetSettings,
    external_call_budget_context,
)
from power_web_os.integrations.live_radar_openrouter import OpenRouterWebSearchProvider
from power_web_os.radar_evaluation import evaluate_radar_dossier, load_evaluation_baseline
from power_web_os.radar_evaluation_runner import HttpxRadarEvaluationClient, resolve_evaluation_run


class CoverageProbeHttpClient(Protocol):
    def get_json(self, path: str) -> dict[str, Any] | list[Any]: ...


@dataclass(slots=True)
class CoverageProbeTarget:
    baseline_id: str
    canonical_name: str
    aliases: tuple[str, ...]
    entity_type: str


def generate_radar_coverage_probe_report(
    *,
    api_url: str,
    run_id: str | None,
    radar_id: str,
    latest: bool,
    baseline_path: Path,
    output_path: Path,
    probe_limit: int,
    provider: WebSearchProvider | None = None,
) -> dict[str, Any]:
    client = HttpxRadarEvaluationClient(api_url=api_url)
    resolved_run = resolve_evaluation_run(client=client, run_id=run_id, radar_id=radar_id, latest=latest)
    dossier = client.get_json(f"/api/radar-runs/{resolved_run['run_id']}/dossier")
    if not isinstance(dossier, dict):
        raise ValueError("Radar dossier endpoint returned a non-object payload.")
    baseline = load_evaluation_baseline(baseline_path)
    evaluation = evaluate_radar_dossier(run=resolved_run, dossier=dossier, baseline=baseline)
    targets = _targets_from_evaluation(evaluation, limit=probe_limit)
    report = run_coverage_probe(
        run=resolved_run,
        radar_id=radar_id,
        targets=targets,
        provider=provider or OpenRouterWebSearchProvider(),
        probe_limit=probe_limit,
    )
    write_coverage_probe_report(output_path, report)
    return report


def run_coverage_probe(
    *,
    run: dict[str, Any],
    radar_id: str,
    targets: list[CoverageProbeTarget],
    provider: WebSearchProvider,
    probe_limit: int,
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    budget = RadarExternalCallBudget(RadarExternalCallBudgetSettings(
        run_profile="smoke",
        max_openrouter_calls_per_run=probe_limit,
        max_openrouter_web_task_calls_per_run=probe_limit,
        max_openrouter_server_tool_web_searches_per_run=max(probe_limit * 6, 1),
        max_provider_retries_per_task=0,
        openrouter_web_max_results_per_call=3,
        openrouter_web_max_total_results_per_call=6,
    ))
    with external_call_budget_context(budget):
        for target in targets[:max(probe_limit, 0)]:
            try:
                result = provider.run_search_plan(
                    radar={"radar_id": radar_id, "source_policy": {"allow_open_web": True, "preferred_domains": ["sibur.ru"]}},
                    search_plan=_target_search_plan(radar_id=radar_id, target=target),
                )
            except Exception as error:  # pragma: no cover - defensive for live CLI probes.
                results.append(_probe_result(target, "probe_provider_failed", message=str(error)))
                continue
            urls = [source.url for source in result.sources]
            if result.provider_metadata.get("budget_decision"):
                results.append(_probe_result(target, "probe_budget_limited", urls=urls, message="Probe budget limited."))
            elif any("sibur.ru" in url.lower() for url in urls):
                results.append(_probe_result(target, "probe_found_official_source", urls=urls))
            elif urls:
                results.append(_probe_result(target, "probe_found_open_web_source", urls=urls))
            else:
                results.append(_probe_result(target, "probe_no_source", urls=[]))
    report = {
        "artifact_type": "radar_coverage_probe_report",
        "artifact_version": "0.7.6.3.2",
        "run_id": run.get("run_id"),
        "radar_id": radar_id,
        "probe_limit": probe_limit,
        "target_count": len(targets),
        "probed_count": len(results),
        "summary": _count_by(results, "status"),
        "results": results,
        "external_call_budget": budget.to_metadata(),
    }
    _assert_no_secrets(report)
    return report


def write_coverage_probe_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _targets_from_evaluation(evaluation: dict[str, Any], *, limit: int) -> list[CoverageProbeTarget]:
    targets: list[CoverageProbeTarget] = []
    for item in evaluation.get("false_negatives", []):
        if not isinstance(item, dict):
            continue
        targets.append(CoverageProbeTarget(
            baseline_id=str(item.get("baseline_id") or ""),
            canonical_name=str(item.get("canonical_name") or ""),
            aliases=tuple(str(value) for value in item.get("aliases", []) if isinstance(value, str)),
            entity_type=str(item.get("entity_type") or ""),
        ))
        if len(targets) >= limit:
            break
    return targets


def _target_search_plan(*, radar_id: str, target: CoverageProbeTarget) -> RadarSearchPlan:
    aliases = " ".join(target.aliases)
    query = f'{target.canonical_name} {aliases} СИБУР site:sibur.ru'
    return RadarSearchPlan(
        radar_id=radar_id,
        queries=[
            RadarSearchQuery(
                query_id=f"coverage-probe-{target.baseline_id}",
                query=query,
                purpose="Diagnostic post-run coverage probe for a missed benchmark baseline entity.",
                expected_evidence=[target.baseline_id],
                stage="coverage_check",
                subject_type="qualification",
                subject_id=target.baseline_id,
                source_scope="additional",
            )
        ],
    )


def _probe_result(
    target: CoverageProbeTarget,
    status: str,
    *,
    urls: list[str] | None = None,
    message: str = "",
) -> dict[str, Any]:
    return {
        "baseline_id": target.baseline_id,
        "canonical_name": target.canonical_name,
        "entity_type": target.entity_type,
        "status": status,
        "urls": urls or [],
        "message": message,
    }


def _count_by(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = str(item.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts


def _assert_no_secrets(payload: dict[str, Any]) -> None:
    serialized = json.dumps(payload, ensure_ascii=False)
    forbidden = ("OPENROUTER_API_KEY", "DADATA_API_KEY", "DADATA_SECRET_KEY", "Authorization", "Bearer", "chain_of_thought", "hidden_reasoning", "internal_thoughts")
    if any(token in serialized for token in forbidden):
        raise ValueError("Coverage probe report contains forbidden secret or hidden reasoning marker.")
