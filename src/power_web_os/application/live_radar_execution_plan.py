"""Compile Radar definitions into backend-owned staged execution plans."""

from __future__ import annotations

from typing import Any

from power_web_os.application.live_radar_contracts import (
    RadarExecutionPlan,
    RadarExecutionTask,
    RadarSearchPlan,
    RadarSearchQuery,
)


def compile_radar_execution_plan(radar: dict[str, Any]) -> RadarExecutionPlan:
    """Build a generic qualification-first plan from a Radar definition."""

    radar_id = str(radar.get("radar_id") or "radar")
    tasks: list[RadarExecutionTask] = []
    qualification_rules = [dict(item) for item in radar.get("qualification_criteria", []) if isinstance(item, dict)]
    signal_rules = [dict(item) for item in radar.get("intent_signals", []) if isinstance(item, dict)]

    if qualification_rules:
        first_rule = qualification_rules[0]
        tasks.append(_task_from_rule(
            radar=radar,
            rule=first_rule,
            task_id=f"qualify-discover-{_rule_code(first_rule).lower()}",
            stage="qualification_discovery",
            purpose="Discover the initial candidate universe for the first qualification rule.",
        ))
        previous_task_id = tasks[-1].task_id
        for rule in qualification_rules[1:]:
            task = _task_from_rule(
                radar=radar,
                rule=rule,
                task_id=f"qualify-gate-{_rule_code(rule).lower()}",
                stage="qualification_gate",
                purpose="Filter the current candidate universe through the next qualification gate.",
                depends_on=[previous_task_id],
            )
            tasks.append(task)
            previous_task_id = task.task_id
    else:
        previous_task_id = "qualify-discover-candidates"
        tasks.append(RadarExecutionTask(
            task_id=previous_task_id,
            stage="qualification_discovery",
            subject_type="radar",
            subject_id=radar_id,
            query=_compact_query([str(radar.get("name", radar_id)), str(radar.get("description", ""))]),
            purpose="Discover candidate accounts for this Radar.",
            expected_evidence=[],
        ))

    coverage_task_id = "coverage-check-candidate-universe"
    tasks.append(RadarExecutionTask(
        task_id=coverage_task_id,
        stage="coverage_check",
        subject_type="radar",
        subject_id=radar_id,
        query=_compact_query([str(radar.get("name", radar_id)), "candidate universe coverage check"]),
        purpose="Check whether the candidate universe has source-backed gaps before signal search.",
        expected_evidence=["candidate_universe_gaps", "coverage_findings"],
        depends_on=[previous_task_id],
    ))
    previous_task_id = coverage_task_id

    for signal in signal_rules:
        code = _rule_code(signal)
        tasks.append(RadarExecutionTask(
            task_id=f"signal-search-{code.lower()}",
            stage="signal_search",
            subject_type="signal",
            subject_id=code,
            rule_snapshot=str(signal.get("rule") or signal.get("label") or code),
            query=_compact_query([str(radar.get("name", "")), str(signal.get("label", "")), str(signal.get("rule", ""))]),
            purpose=f"Search one qualified candidate scope for signal {code}.",
            expected_evidence=[code],
            depends_on=[previous_task_id],
        ))

    return RadarExecutionPlan(radar_id=radar_id, tasks=tasks)


def execution_plan_to_search_plan(plan: RadarExecutionPlan) -> RadarSearchPlan:
    return RadarSearchPlan(
        radar_id=plan.radar_id,
        queries=[execution_task_to_query(task) for task in plan.tasks],
    )


def execution_task_to_search_plan(task: RadarExecutionTask, *, radar_id: str) -> RadarSearchPlan:
    return RadarSearchPlan(radar_id=radar_id, queries=[execution_task_to_query(task)])


def execution_task_to_query(task: RadarExecutionTask) -> RadarSearchQuery:
    return RadarSearchQuery(
        query_id=task.task_id,
        query=_query_with_scope(task),
        purpose=task.purpose,
        expected_evidence=list(task.expected_evidence),
        stage=task.stage,
        subject_type=task.subject_type,
        subject_id=task.subject_id,
        rule_snapshot=task.rule_snapshot,
        source_scope=task.source_scope,
        source_ids=list(task.source_ids),
        external_source_hints=list(task.external_source_hints),
        depends_on=list(task.depends_on),
        candidate_scope=list(task.candidate_scope),
    )


def scoped_execution_task(task: RadarExecutionTask, *, candidate_scope: list[str]) -> RadarExecutionTask:
    return task.model_copy(update={"candidate_scope": list(candidate_scope)})


def _task_from_rule(
    *,
    radar: dict[str, Any],
    rule: dict[str, Any],
    task_id: str,
    stage: str,
    purpose: str,
    depends_on: list[str] | None = None,
) -> RadarExecutionTask:
    code = _rule_code(rule)
    return RadarExecutionTask(
        task_id=task_id,
        stage=stage,  # type: ignore[arg-type]
        subject_type="qualification",
        subject_id=code,
        rule_snapshot=str(rule.get("rule") or rule.get("label") or code),
        query=_compact_query([str(radar.get("name", "")), str(rule.get("label", "")), str(rule.get("rule", ""))]),
        purpose=purpose,
        expected_evidence=[code],
        depends_on=list(depends_on or []),
    )


def _query_with_scope(task: RadarExecutionTask) -> str:
    if not task.candidate_scope:
        return task.query
    return _compact_query([task.query, "Candidate scope:", "; ".join(task.candidate_scope)])


def _rule_code(rule: dict[str, Any]) -> str:
    return str(rule.get("code") or rule.get("criterion_code") or rule.get("signal_code") or rule.get("id") or "rule")


def _compact_query(parts: list[str]) -> str:
    value = " ".join(part.strip() for part in parts if part.strip())
    return " ".join(value.split())[:700]
