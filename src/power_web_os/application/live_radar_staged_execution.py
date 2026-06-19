"""Execute qualification-first Radar plans through the provider port."""

from __future__ import annotations
from typing import Any

from power_web_os.application.live_radar_contracts import (
    LiveRadarCandidate,
    LiveRadarPipelineEvent,
    RadarCoverageCheckRecord,
    RadarExecutionPlan,
    RadarExecutionTask,
    RadarSourceEvidence,
    WebSearchProvider,
    WebSearchProviderResult,
)
from power_web_os.application.live_radar_execution_budget import SubjectTaskBudget
from power_web_os.application.live_radar_execution_plan import execution_task_to_search_plan, scoped_execution_task
from power_web_os.application.live_radar_normalization import _dedupe_sources, normalize_live_candidate
from power_web_os.application.live_radar_universe import (
    candidate_name,
    candidate_name_set,
    candidate_universe_entries,
    coverage_risk,
    coverage_warnings as coverage_warning_messages,
    dedupe_gap_payloads,
    filter_signal_result,
    first_task_id,
    gap_items,
    gap_observations,
    gap_payloads,
    merge_provider_metadata,
)

MAX_DISCOVERY_ITERATIONS = 2
MAX_CANDIDATE_UNIVERSE_SIZE = 50
MAX_SIGNAL_CANDIDATES = 8
MAX_SIGNAL_TASKS = 12


def run_staged_radar_execution(
    *,
    radar: dict[str, Any],
    execution_plan: RadarExecutionPlan,
    provider: WebSearchProvider,
    max_web_tasks_per_subject: int | None = None,
) -> tuple[WebSearchProviderResult, list[LiveRadarPipelineEvent], dict[str, Any]]:
    sources: list[RadarSourceEvidence] = []
    observations: list[dict[str, Any]] = []
    provider_metadata: dict[str, Any] = {}
    events: list[LiveRadarPipelineEvent] = []
    executed_task_ids: list[str] = []
    completed_qualification_ids: list[str] = []
    gate_results: list[dict[str, Any]] = []
    candidate_scope: list[str] = []
    coverage_checks: list[dict[str, Any]] = []
    unresolved_candidate_gaps: list[dict[str, Any]] = []
    coverage_warnings: list[str] = []
    discovery_iteration_count = 0
    task_budget = SubjectTaskBudget(max_web_tasks_per_subject)

    discovery_tasks = _tasks_for_stage(execution_plan, "qualification_discovery")
    for task in discovery_tasks:
        result = _run_task(provider=provider, radar=radar, task=task, radar_id=execution_plan.radar_id, budget=task_budget)
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

    gate_tasks = _tasks_for_stage(execution_plan, "qualification_gate")
    sources, observations, provider_metadata, candidate_scope = _run_gate_pass(
        radar=radar,
        execution_plan=execution_plan,
        provider=provider,
        tasks=gate_tasks,
        sources=sources,
        observations=observations,
        provider_metadata=provider_metadata,
        candidate_scope=candidate_scope,
        completed_qualification_ids=completed_qualification_ids,
        gate_results=gate_results,
        events=events,
        executed_task_ids=executed_task_ids,
        budget=task_budget,
    )

    coverage_tasks = _tasks_for_stage(execution_plan, "coverage_check")
    for iteration in range(1, MAX_DISCOVERY_ITERATIONS + 1):
        if not coverage_tasks:
            break
        if len(_normalized_candidates(radar=radar, sources=sources, observations=observations)) >= MAX_CANDIDATE_UNIVERSE_SIZE:
            coverage_warnings.append(f"Candidate universe reached max size {MAX_CANDIDATE_UNIVERSE_SIZE}.")
            break
        discovery_iteration_count = iteration
        names_before = candidate_name_set(observations)
        iteration_new_names: set[str] = set()
        for task in coverage_tasks:
            scoped_task = scoped_execution_task(task, candidate_scope=candidate_scope)
            result = _run_task(provider=provider, radar=radar, task=scoped_task, radar_id=execution_plan.radar_id, budget=task_budget)
            gaps = gap_items(result)
            result = result.model_copy(update={
                "candidate_observations": [
                    *result.candidate_observations,
                    *gap_observations(gaps, origin_task_id=task.task_id),
                ],
            })
            sources, observations, provider_metadata = _merge_result(sources, observations, provider_metadata, result)
            executed_task_ids.append(f"{task.task_id}:iteration-{iteration}")
            names_after = candidate_name_set(observations)
            new_names = names_after - names_before
            iteration_new_names.update(new_names)
            unresolved_candidate_gaps.extend(gap_payloads(gaps, origin_task_id=task.task_id))
            warnings = coverage_warning_messages(result)
            coverage_warnings.extend(warnings)
            coverage_record = RadarCoverageCheckRecord(
                task_id=task.task_id,
                iteration=iteration,
                source_count=len(result.sources),
                candidate_observation_count=len(result.candidate_observations),
                new_candidate_count=len(new_names),
                gap_count=len(gaps),
                completeness_risk=coverage_risk(result),  # type: ignore[arg-type]
                warnings=warnings,
            ).model_dump()
            coverage_checks.append(coverage_record)
            events.append(_task_event(scoped_task, result, "coverage_warning" if warnings else "candidate_universe_discovered", payload=coverage_record))
            names_before = names_after

        if not iteration_new_names:
            break
        new_candidate_scope = _candidate_names_matching(observations, iteration_new_names)
        sources, observations, provider_metadata, _ = _run_gate_pass(
            radar=radar,
            execution_plan=execution_plan,
            provider=provider,
            tasks=[*discovery_tasks, *gate_tasks],
            sources=sources,
            observations=observations,
            provider_metadata=provider_metadata,
            candidate_scope=new_candidate_scope,
            completed_qualification_ids=completed_qualification_ids,
            gate_results=gate_results,
            events=events,
            executed_task_ids=executed_task_ids,
            budget=task_budget,
        )
        candidate_scope = _eligible_candidate_names(
            radar=radar,
            sources=sources,
            observations=observations,
            completed_qualification_ids=completed_qualification_ids,
        )

    signal_task_count = 0
    signal_budget_warnings: list[str] = []
    max_signal_candidates = task_budget.limit or MAX_SIGNAL_CANDIDATES
    max_signal_tasks = None if task_budget.limit else MAX_SIGNAL_TASKS
    signal_candidate_scope = candidate_scope[:max_signal_candidates]
    if len(candidate_scope) > max_signal_candidates:
        signal_budget_warnings.append(
            f"Signal search candidate scope was limited to {max_signal_candidates} of {len(candidate_scope)} candidates."
        )
    signal_budget_exhausted = False
    for task in _tasks_for_stage(execution_plan, "signal_search"):
        if signal_budget_exhausted:
            break
        for scoped_candidate_name in signal_candidate_scope:
            if max_signal_tasks is not None and signal_task_count >= max_signal_tasks:
                signal_budget_warnings.append(f"Signal search task budget reached {max_signal_tasks} tasks.")
                signal_budget_exhausted = True
                break
            scoped_task = scoped_execution_task(task, candidate_scope=[scoped_candidate_name])
            events.append(_signal_planned_event(scoped_task))
            result = _run_task(provider=provider, radar=radar, task=scoped_task, radar_id=execution_plan.radar_id, budget=task_budget)
            result = filter_signal_result(result, allowed_candidate_names={scoped_candidate_name})
            unresolved_candidate_gaps.extend(gap_payloads(gap_items(result), origin_task_id=task.task_id))
            sources, observations, provider_metadata = _merge_result(sources, observations, provider_metadata, result)
            executed_task_ids.append(f"{task.task_id}:{scoped_candidate_name}")
            signal_task_count += 1
    if signal_budget_warnings:
        coverage_warnings.extend(signal_budget_warnings)
        events.append(_budget_warning_event(signal_budget_warnings))
    if task_budget.warnings:
        coverage_warnings.extend(task_budget.warnings)
        events.append(_budget_warning_event(task_budget.warnings))

    normalized_candidates = _normalized_candidates(radar=radar, sources=sources, observations=observations)
    candidate_universe = candidate_universe_entries(
        candidates=normalized_candidates,
        completed_qualification_ids=completed_qualification_ids,
        origin_task_id=first_task_id(execution_plan.tasks),
        gap_names={candidate_name(item) for item in unresolved_candidate_gaps if candidate_name(item)},
    )
    return (
        WebSearchProviderResult(
            sources=_dedupe_sources(sources),
            candidate_observations=_merge_candidate_observations(observations),
            provider_metadata={**provider_metadata, "execution_mode": "qualification_first_iterative_coverage"},
        ),
        events,
        {
            "execution_mode": "qualification_first_iterative_coverage",
            "executed_task_count": len(executed_task_ids),
            "executed_task_ids": executed_task_ids,
            "gate_results": gate_results,
            "signal_task_count": signal_task_count,
            "candidate_scope": candidate_scope,
            "signal_candidate_scope": signal_candidate_scope,
            "signal_budget_warnings": signal_budget_warnings,
            "max_signal_candidates": max_signal_candidates,
            "max_signal_tasks": max_signal_tasks or task_budget.limit,
            "max_web_tasks_per_subject": task_budget.limit,
            "web_task_counts_by_subject": task_budget.counts,
            "web_task_budget_warnings": task_budget.warnings,
            "candidate_universe": [item.model_dump() for item in candidate_universe],
            "coverage_checks": coverage_checks,
            "coverage_warnings": sorted(set(coverage_warnings)),
            "unresolved_candidate_gaps": dedupe_gap_payloads(unresolved_candidate_gaps, known_candidate_names=candidate_name_set(observations)),
            "discovery_iteration_count": discovery_iteration_count,
            "max_discovery_iterations": MAX_DISCOVERY_ITERATIONS,
            "max_candidate_universe_size": MAX_CANDIDATE_UNIVERSE_SIZE,
            "rejected_candidates": _rejected_candidate_summaries(
                normalized_candidates
            ),
        },
    )


def _run_gate_pass(
    *,
    radar: dict[str, Any],
    execution_plan: RadarExecutionPlan,
    provider: WebSearchProvider,
    tasks: list[RadarExecutionTask],
    sources: list[RadarSourceEvidence],
    observations: list[dict[str, Any]],
    provider_metadata: dict[str, Any],
    candidate_scope: list[str],
    completed_qualification_ids: list[str],
    gate_results: list[dict[str, Any]],
    events: list[LiveRadarPipelineEvent],
    executed_task_ids: list[str],
    budget: SubjectTaskBudget,
) -> tuple[list[RadarSourceEvidence], list[dict[str, Any]], dict[str, Any], list[str]]:
    for task in tasks:
        scoped_task = scoped_execution_task(task, candidate_scope=candidate_scope)
        result = _run_task(provider=provider, radar=radar, task=scoped_task, radar_id=execution_plan.radar_id, budget=budget)
        sources, observations, provider_metadata = _merge_result(sources, observations, provider_metadata, result)
        executed_task_ids.append(task.task_id if not candidate_scope else f"{task.task_id}:{len(candidate_scope)}-candidates")
        candidates = _normalized_candidates(radar=radar, sources=sources, observations=observations)
        gate_summary = _gate_summary(candidates, task.subject_id)
        gate_results.append(gate_summary)
        events.append(_task_event(scoped_task, result, "qualification_gate_applied", payload=gate_summary))
        events.extend(_candidate_filtered_events(task, candidates))
        if task.subject_id not in completed_qualification_ids:
            completed_qualification_ids.append(task.subject_id)
        candidate_scope = _eligible_candidate_names(
            radar=radar,
            sources=sources,
            observations=observations,
            completed_qualification_ids=completed_qualification_ids,
        )
    return sources, observations, provider_metadata, candidate_scope


def _run_task(
    *,
    provider: WebSearchProvider,
    radar: dict[str, Any],
    task: RadarExecutionTask,
    radar_id: str,
    budget: SubjectTaskBudget,
) -> WebSearchProviderResult:
    if not budget.reserve(task):
        return WebSearchProviderResult(
            sources=[],
            candidate_observations=[],
            provider_metadata={
                "provider": "execution_budget",
                "coverage_findings": [{
                    "summary": budget.last_warning or f"Web task budget reached for {task.subject_id}.",
                    "completeness_risk": "medium",
                    "warnings": [budget.last_warning] if budget.last_warning else [],
                }],
            },
        )
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
        merge_provider_metadata(metadata, result.provider_metadata),
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


def _candidate_names_matching(observations: list[dict[str, Any]], lower_names: set[str]) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for item in observations:
        name = candidate_name(item)
        key = name.lower()
        if name and key in lower_names and key not in seen:
            seen.add(key)
            names.append(name)
    return names


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


def _budget_warning_event(warnings: list[str]) -> LiveRadarPipelineEvent:
    return LiveRadarPipelineEvent(
        event_type="validation_warning",
        phase="validation",
        actor="workflow",
        node_name="execution-budget",
        visibility="operator",
        summary="Radar execution budget limited remaining signal searches.",
        payload={"warnings": list(warnings)},
    )


def _list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]
