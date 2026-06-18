"""Execute qualification-first Radar plans through the provider port."""

from __future__ import annotations

from typing import Any

from power_web_os.application.live_radar_contracts import (
    LiveRadarCandidate,
    LiveRadarPipelineEvent,
    RadarExecutionPlan,
    RadarExecutionTask,
    RadarSourceEvidence,
    WebSearchProvider,
    WebSearchProviderResult,
)
from power_web_os.application.live_radar_execution_plan import execution_task_to_search_plan, scoped_execution_task
from power_web_os.application.live_radar_normalization import _dedupe_sources, normalize_live_candidate


def run_staged_radar_execution(
    *,
    radar: dict[str, Any],
    execution_plan: RadarExecutionPlan,
    provider: WebSearchProvider,
) -> tuple[WebSearchProviderResult, list[LiveRadarPipelineEvent], dict[str, Any]]:
    sources: list[RadarSourceEvidence] = []
    observations: list[dict[str, Any]] = []
    provider_metadata: dict[str, Any] = {}
    events: list[LiveRadarPipelineEvent] = []
    executed_task_ids: list[str] = []
    completed_qualification_ids: list[str] = []
    gate_results: list[dict[str, Any]] = []
    candidate_scope: list[str] = []

    for task in _tasks_for_stage(execution_plan, "qualification_discovery"):
        result = _run_task(provider=provider, radar=radar, task=task, radar_id=execution_plan.radar_id)
        sources, observations, provider_metadata = _merge_result(sources, observations, provider_metadata, result)
        executed_task_ids.append(task.task_id)
        completed_qualification_ids.append(task.subject_id)
        candidate_scope = _eligible_candidate_names(
            radar=radar,
            sources=sources,
            observations=observations,
            completed_qualification_ids=completed_qualification_ids,
        )
        events.append(_task_event(task, result, "qualification_discovery_planned"))

    for task in _tasks_for_stage(execution_plan, "qualification_gate"):
        scoped_task = scoped_execution_task(task, candidate_scope=candidate_scope)
        result = _run_task(provider=provider, radar=radar, task=scoped_task, radar_id=execution_plan.radar_id)
        sources, observations, provider_metadata = _merge_result(sources, observations, provider_metadata, result)
        executed_task_ids.append(task.task_id)
        candidates = _normalized_candidates(radar=radar, sources=sources, observations=observations)
        gate_summary = _gate_summary(candidates, task.subject_id)
        gate_results.append(gate_summary)
        events.append(_task_event(scoped_task, result, "qualification_gate_applied", payload=gate_summary))
        events.extend(_candidate_filtered_events(task, candidates))
        completed_qualification_ids.append(task.subject_id)
        candidate_scope = _eligible_candidate_names(
            radar=radar,
            sources=sources,
            observations=observations,
            completed_qualification_ids=completed_qualification_ids,
        )

    signal_task_count = 0
    for task in _tasks_for_stage(execution_plan, "signal_search"):
        for candidate_name in candidate_scope:
            scoped_task = scoped_execution_task(task, candidate_scope=[candidate_name])
            events.append(_signal_planned_event(scoped_task))
            result = _run_task(provider=provider, radar=radar, task=scoped_task, radar_id=execution_plan.radar_id)
            sources, observations, provider_metadata = _merge_result(sources, observations, provider_metadata, result)
            executed_task_ids.append(f"{task.task_id}:{candidate_name}")
            signal_task_count += 1

    return (
        WebSearchProviderResult(
            sources=_dedupe_sources(sources),
            candidate_observations=_merge_candidate_observations(observations),
            provider_metadata={**provider_metadata, "execution_mode": "qualification_first"},
        ),
        events,
        {
            "execution_mode": "qualification_first",
            "executed_task_count": len(executed_task_ids),
            "executed_task_ids": executed_task_ids,
            "gate_results": gate_results,
            "signal_task_count": signal_task_count,
            "candidate_scope": candidate_scope,
            "rejected_candidates": _rejected_candidate_summaries(
                _normalized_candidates(radar=radar, sources=sources, observations=observations)
            ),
        },
    )


def _run_task(
    *,
    provider: WebSearchProvider,
    radar: dict[str, Any],
    task: RadarExecutionTask,
    radar_id: str,
) -> WebSearchProviderResult:
    return provider.run_search_plan(radar=radar, search_plan=execution_task_to_search_plan(task, radar_id=radar_id))


def _tasks_for_stage(execution_plan: RadarExecutionPlan, stage: str) -> list[RadarExecutionTask]:
    return [task for task in execution_plan.tasks if task.stage == stage]


def _merge_result(
    sources: list[RadarSourceEvidence],
    observations: list[dict[str, Any]],
    metadata: dict[str, Any],
    result: WebSearchProviderResult,
) -> tuple[list[RadarSourceEvidence], list[dict[str, Any]], dict[str, Any]]:
    return (
        _dedupe_sources([*sources, *result.sources]),
        _merge_candidate_observations([*observations, *result.candidate_observations]),
        {**metadata, **result.provider_metadata},
    )


def _merge_candidate_observations(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for item in observations:
        name = str(item.get("legal_name") or item.get("name") or "").strip()
        if not name:
            continue
        target = merged.setdefault(name.lower(), {"legal_name": name, "qualification": [], "signals": [], "review_flags": []})
        target["description"] = target.get("description") or item.get("description", "")
        target["qualification"] = _merge_section(target.get("qualification", []), item.get("qualification", []), "criterion_code")
        target["signals"] = _merge_section(target.get("signals", []), item.get("signals", []), "signal_code")
        target["review_flags"] = sorted({str(flag) for flag in [*target.get("review_flags", []), *item.get("review_flags", [])] if str(flag).strip()})
    return list(merged.values())


def _merge_section(existing: object, incoming: object, key: str) -> list[dict[str, Any]]:
    merged = {str(item.get(key) or item.get("code") or ""): dict(item) for item in _list(existing)}
    for item in _list(incoming):
        section_id = str(item.get(key) or item.get("code") or "")
        if section_id:
            merged[section_id] = {**merged.get(section_id, {}), **item}
    return list(merged.values())


def _eligible_candidate_names(
    *,
    radar: dict[str, Any],
    sources: list[RadarSourceEvidence],
    observations: list[dict[str, Any]],
    completed_qualification_ids: list[str],
) -> list[str]:
    return [
        candidate.legal_name
        for candidate in _normalized_candidates(radar=radar, sources=sources, observations=observations)
        if not _candidate_rejected(candidate, completed_qualification_ids=completed_qualification_ids)
    ]


def _normalized_candidates(*, radar: dict[str, Any], sources: list[RadarSourceEvidence], observations: list[dict[str, Any]]) -> list[LiveRadarCandidate]:
    return [normalize_live_candidate(item, radar=radar, sources=sources) for item in _merge_candidate_observations(observations)]


def _candidate_rejected(candidate: LiveRadarCandidate, *, completed_qualification_ids: list[str] | None = None) -> bool:
    completed = set(completed_qualification_ids or [item.criterion_code for item in candidate.qualification])
    return any(
        item.criterion_code in completed
        and item.requirement_level == "required"
        and item.final_assessment == "does_not_match"
        for item in candidate.qualification
    )


def _gate_summary(candidates: list[LiveRadarCandidate], subject_id: str) -> dict[str, Any]:
    statuses = {"accepted": 0, "unknown": 0, "rejected": 0}
    for candidate in candidates:
        rule = next((item for item in candidate.qualification if item.criterion_code == subject_id), None)
        if rule is None or rule.final_assessment in {"unknown", "partially_matches"}:
            statuses["unknown"] += 1
        elif rule.final_assessment == "does_not_match":
            statuses["rejected"] += 1
        else:
            statuses["accepted"] += 1
    return {"subject_id": subject_id, **statuses}


def _rejected_candidate_summaries(candidates: list[LiveRadarCandidate]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": candidate.candidate_id,
            "legal_name": candidate.legal_name,
            "failed_rules": [
                item.criterion_code
                for item in candidate.qualification
                if item.requirement_level == "required" and item.final_assessment == "does_not_match"
            ],
        }
        for candidate in candidates
        if _candidate_rejected(candidate)
    ]


def _task_event(
    task: RadarExecutionTask,
    result: WebSearchProviderResult,
    event_type: str,
    *,
    payload: dict[str, Any] | None = None,
) -> LiveRadarPipelineEvent:
    return LiveRadarPipelineEvent(
        event_type=event_type,
        phase="collection",
        actor="workflow",
        node_name=task.task_id,
        visibility="operator",
        summary=f"Executed {task.stage} task {task.task_id}.",
        payload={
            "stage": task.stage,
            "subject_type": task.subject_type,
            "subject_id": task.subject_id,
            "candidate_scope": list(task.candidate_scope),
            "source_count": len(result.sources),
            "candidate_observation_count": len(result.candidate_observations),
            **(payload or {}),
        },
        source_refs=[source.evidence_ref for source in result.sources if source.evidence_ref],
    )


def _candidate_filtered_events(task: RadarExecutionTask, candidates: list[LiveRadarCandidate]) -> list[LiveRadarPipelineEvent]:
    return [
        LiveRadarPipelineEvent(
            event_type="candidate_filtered",
            phase="collection",
            actor="workflow",
            node_name=task.task_id,
            visibility="operator",
            summary=f"Candidate {candidate.legal_name} did not pass qualification gate {task.subject_id}.",
            payload={"subject_id": task.subject_id, "failed_rules": item["failed_rules"]},
            candidate_refs=[candidate.candidate_id],
        )
        for item in _rejected_candidate_summaries(candidates)
        for candidate in candidates
        if candidate.candidate_id == item["candidate_id"]
    ]


def _signal_planned_event(task: RadarExecutionTask) -> LiveRadarPipelineEvent:
    return LiveRadarPipelineEvent(
        event_type="signal_search_planned",
        phase="planning",
        actor="workflow",
        node_name=task.task_id,
        summary=f"Planned signal search {task.subject_id} for {', '.join(task.candidate_scope)}.",
        payload={"subject_id": task.subject_id, "candidate_scope": list(task.candidate_scope)},
        candidate_refs=list(task.candidate_scope),
    )


def _list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]
