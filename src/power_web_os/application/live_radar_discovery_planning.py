"""Discovery planning contracts implementation for live Radar runs."""

from __future__ import annotations

from typing import Any

from power_web_os.application.live_radar_contracts import (
    RadarDiscoveryCoverageHypothesis,
    RadarDiscoveryPlanner,
    RadarDiscoveryPlanningInput,
    RadarDiscoveryPlan,
    RadarDiscoveryPlanStep,
    RadarDiscoveryPlanValidationResult,
    RadarDiscoverySourcePolicyDecision,
    RadarExecutionPlan,
    RadarExecutionTask,
    RadarSourceEvidence,
)


class DeterministicRadarDiscoveryPlanner(RadarDiscoveryPlanner):
    """Safe fallback planner used by tests and non-live recorded runs."""

    runtime_name = "deterministic_discovery_planner"

    def propose_plan(
        self,
        *,
        planning_input: RadarDiscoveryPlanningInput,
        previous_validation: RadarDiscoveryPlanValidationResult | None = None,
    ) -> RadarDiscoveryPlan:
        _ = previous_validation
        steps: list[RadarDiscoveryPlanStep] = []
        previous_step_id = ""
        for index, rule in enumerate(planning_input.qualification_rules):
            rule_id = _rule_id(rule, fallback=f"Q{index + 1}")
            stage = "candidate_universe_discovery" if index == 0 else "qualification_gate"
            step_id = f"discover-{rule_id.lower()}" if index == 0 else f"gate-{rule_id.lower()}"
            source_scope, source_ids = _preferred_source_scope(rule, planning_input.global_search_policy)
            steps.append(RadarDiscoveryPlanStep(
                step_id=step_id,
                stage=stage,
                subject_rule_ids=[rule_id],
                source_scope=source_scope,
                source_ids=source_ids,
                query=_compact_query([planning_input.name, str(rule.get("label", "")), str(rule.get("rule", rule.get("description", "")))]),
                purpose=(
                    "Discover the candidate universe for the first qualification rule."
                    if index == 0
                    else "Apply the next qualification gate to the current candidate universe."
                ),
                expected_evidence=[rule_id],
                acceptance_criteria=[str(rule.get("rule") or rule.get("description") or rule.get("label") or rule_id)],
                depends_on=[previous_step_id] if previous_step_id else [],
            ))
            previous_step_id = step_id

        decisions = _source_policy_decisions(planning_input)
        return RadarDiscoveryPlan(
            plan_summary=f"Discovery plan for {planning_input.name} with {len(steps)} qualification steps.",
            steps=steps,
            source_policy_decisions=decisions,
            coverage_hypotheses=[
                RadarDiscoveryCoverageHypothesis(
                    summary="Candidate universe coverage depends on configured source bases and follow-up qualification gates.",
                    expected_candidate_count="unknown_before_execution",
                    completeness_risk="medium",
                )
            ],
            warnings=[],
        )


class RadarDiscoveryPlanValidator:
    """Backend-owned policy checks for planner output."""

    def validate(self, *, planning_input: RadarDiscoveryPlanningInput, plan: RadarDiscoveryPlan) -> RadarDiscoveryPlanValidationResult:
        errors: list[str] = []
        warnings: list[str] = []
        rule_ids = {_rule_id(rule, fallback=f"Q{index + 1}") for index, rule in enumerate(planning_input.qualification_rules)}
        global_source_ids = _global_source_ids(planning_input.global_search_policy)

        if not plan.steps:
            errors.append("Discovery plan must contain at least one step.")
        if len(plan.steps) > planning_input.max_steps:
            errors.append(f"Discovery plan has {len(plan.steps)} steps but max_steps is {planning_input.max_steps}.")

        for step in plan.steps:
            unknown_rules = [rule_id for rule_id in step.subject_rule_ids if rule_id not in rule_ids]
            if unknown_rules:
                errors.append(f"Step {step.step_id} references non-qualification rules: {', '.join(unknown_rules)}.")
            if step.source_scope in {"additional", "system"} and not _additional_sources_allowed(planning_input, step.subject_rule_ids):
                errors.append(f"Step {step.step_id} uses {step.source_scope} sources while additional sources are disabled.")
            if step.source_scope == "global" and global_source_ids and not step.source_ids:
                errors.append(f"Step {step.step_id} uses global sources but does not name source_ids.")

        selected = {item.source_id for item in plan.source_policy_decisions if item.decision == "selected"}
        skipped = {item.source_id for item in plan.source_policy_decisions if item.decision == "skipped" and item.reason.strip()}
        for source_id in global_source_ids:
            if source_id not in selected and source_id not in skipped:
                errors.append(f"Global source {source_id} must be selected or skipped with rationale.")

        first_gate_index = next((index for index, step in enumerate(plan.steps) if step.stage == "qualification_gate"), None)
        first_discovery_index = next((index for index, step in enumerate(plan.steps) if step.stage == "candidate_universe_discovery"), None)
        if first_gate_index is not None and first_discovery_index is not None and first_gate_index < first_discovery_index:
            errors.append("Qualification gates must not run before candidate universe discovery.")
        if not plan.coverage_hypotheses:
            warnings.append("Discovery plan does not explain candidate universe coverage.")

        return RadarDiscoveryPlanValidationResult(accepted=not errors, errors=errors, warnings=warnings)


def build_discovery_planning_input(
    *,
    radar: dict[str, Any],
    task_context: dict[str, Any],
    live: bool,
    provider_metadata: dict[str, Any] | None = None,
) -> RadarDiscoveryPlanningInput:
    provider_metadata = provider_metadata or {}
    rules = _qualification_rules(radar)
    return RadarDiscoveryPlanningInput(
        radar_id=str(radar.get("radar_id") or "radar"),
        name=str(radar.get("name") or radar.get("radar_id") or "Radar"),
        description=str(radar.get("description") or ""),
        qualification_rules=rules,
        global_search_policy=_global_search_policy(radar),
        task_context=dict(task_context),
        requester=str(task_context.get("requester", "")),
        live=live,
        model=str(provider_metadata.get("model")) if provider_metadata.get("model") else None,
        web_mode=str(provider_metadata.get("web_mode")) if provider_metadata.get("web_mode") else None,
    )


def discovery_plan_to_execution_plan(*, radar: dict[str, Any], plan: RadarDiscoveryPlan) -> RadarExecutionPlan:
    radar_id = str(radar.get("radar_id") or "radar")
    tasks: list[RadarExecutionTask] = []
    previous_qualification_task_id = ""
    for step in plan.steps:
        if step.stage not in {"candidate_universe_discovery", "source_probe", "qualification_gate"}:
            continue
        subject_id = step.subject_rule_ids[0] if step.subject_rule_ids else step.step_id
        stage = "qualification_discovery" if not previous_qualification_task_id else "qualification_gate"
        depends_on = [previous_qualification_task_id] if previous_qualification_task_id else list(step.depends_on)
        task = RadarExecutionTask(
            task_id=step.step_id,
            stage=stage,
            subject_type="qualification",
            subject_id=subject_id,
            rule_snapshot="; ".join(step.acceptance_criteria),
            query=step.query,
            purpose=step.purpose,
            expected_evidence=list(step.expected_evidence),
            source_scope=step.source_scope,
            source_ids=list(step.source_ids),
            external_source_hints=list(step.external_source_hints),
            depends_on=[item for item in depends_on if item],
            candidate_scope=list(step.candidate_scope),
        )
        tasks.append(task)
        previous_qualification_task_id = task.task_id

    if not tasks:
        from power_web_os.application.live_radar_execution_plan import compile_radar_execution_plan

        return compile_radar_execution_plan(radar)

    for signal in [dict(item) for item in radar.get("intent_signals", []) if isinstance(item, dict)]:
        code = str(signal.get("code") or signal.get("signal_code") or signal.get("id") or "signal")
        tasks.append(RadarExecutionTask(
            task_id=f"signal-search-{code.lower()}",
            stage="signal_search",
            subject_type="signal",
            subject_id=code,
            rule_snapshot=str(signal.get("rule") or signal.get("label") or signal.get("description") or code),
            query=_compact_query([str(radar.get("name", "")), str(signal.get("label", "")), str(signal.get("rule", signal.get("description", "")))]),
            purpose=f"Search one qualified candidate scope for signal {code}.",
            expected_evidence=[code],
            depends_on=[previous_qualification_task_id] if previous_qualification_task_id else [],
        ))
    return RadarExecutionPlan(radar_id=radar_id, tasks=tasks)


def product_sources_for_candidates(
    *,
    sources: list[RadarSourceEvidence],
    candidates: list[dict[str, Any]],
) -> tuple[list[RadarSourceEvidence], list[dict[str, Any]]]:
    used_refs = _candidate_source_refs(candidates)
    used = [source for source in sources if source.evidence_ref in used_refs]
    analyzed = [
        {
            "evidence_ref": source.evidence_ref,
            "title": source.title,
            "url": source.url,
            "query_id": source.query_id,
            "reason": "not_used_by_candidate",
        }
        for source in sources
        if source.evidence_ref not in used_refs
    ]
    return used, analyzed


def _qualification_rules(radar: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(radar.get("qualification_criteria"), list):
        return [dict(item) for item in radar["qualification_criteria"] if isinstance(item, dict)]
    rule_group = _dict(_dict(radar.get("account_qualification")).get("rule_group"))
    return _flatten_rules(rule_group)


def _flatten_rules(group: dict[str, Any]) -> list[dict[str, Any]]:
    rules = [dict(item) for item in group.get("rules", []) if isinstance(item, dict)]
    for child in group.get("groups", []):
        if isinstance(child, dict):
            rules.extend(_flatten_rules(child))
    return rules


def _global_search_policy(radar: dict[str, Any]) -> dict[str, Any]:
    value = radar.get("global_search_policy")
    if isinstance(value, dict):
        return dict(value)
    value = radar.get("source_policy")
    if isinstance(value, dict):
        preferred = value.get("preferred_domains", [])
        return {
            "sources": [
                {"source_id": str(domain), "label": str(domain), "source_type": "domain", "reference": str(domain)}
                for domain in preferred
                if isinstance(domain, str)
            ],
            "allow_system_sources": bool(value.get("allow_open_web", True)),
        }
    return {"sources": [], "allow_system_sources": True}


def _source_policy(rule: dict[str, Any]) -> dict[str, Any]:
    return _dict(rule.get("source_policy"))


def _preferred_source_scope(rule: dict[str, Any], global_policy: dict[str, Any]) -> tuple[str, list[str]]:
    policy = _source_policy(rule)
    source_ids = [str(item) for item in policy.get("source_ids", []) if str(item).strip()]
    if source_ids:
        return "global", source_ids
    global_ids = _global_source_ids(global_policy)
    if policy.get("use_global_search_policy", True) and global_ids:
        return "global", global_ids
    if policy.get("local_sources"):
        return "local", []
    return ("additional", [])


def _source_policy_decisions(planning_input: RadarDiscoveryPlanningInput) -> list[RadarDiscoverySourcePolicyDecision]:
    decisions: list[RadarDiscoverySourcePolicyDecision] = []
    sources = [dict(item) for item in planning_input.global_search_policy.get("sources", []) if isinstance(item, dict)]
    rules_using_global = [
        _rule_id(rule, fallback=f"Q{index + 1}")
        for index, rule in enumerate(planning_input.qualification_rules)
        if _source_policy(rule).get("use_global_search_policy", True)
    ]
    for source in sources:
        source_id = str(source.get("source_id") or source.get("reference") or source.get("label") or "")
        if not source_id:
            continue
        decisions.append(RadarDiscoverySourcePolicyDecision(
            source_id=source_id,
            source_label=str(source.get("label") or source_id),
            decision="selected" if rules_using_global else "skipped",
            reason="Configured global source is allowed by qualification source policy." if rules_using_global else "No qualification rule requested the global source policy.",
            rule_ids=rules_using_global,
        ))
    return decisions


def _additional_sources_allowed(planning_input: RadarDiscoveryPlanningInput, rule_ids: list[str]) -> bool:
    if not rule_ids:
        return bool(planning_input.global_search_policy.get("allow_system_sources", True))
    rules = {_rule_id(rule, fallback=f"Q{index + 1}"): rule for index, rule in enumerate(planning_input.qualification_rules)}
    return all(_source_policy(rules.get(rule_id, {})).get("allow_additional_sources", True) for rule_id in rule_ids)


def _global_source_ids(global_policy: dict[str, Any]) -> list[str]:
    return [
        str(item.get("source_id") or item.get("reference") or item.get("label"))
        for item in global_policy.get("sources", [])
        if isinstance(item, dict) and str(item.get("source_id") or item.get("reference") or item.get("label") or "").strip()
    ]


def _candidate_source_refs(candidates: list[dict[str, Any]]) -> set[str]:
    refs: set[str] = set()
    for candidate in candidates:
        refs.update(str(ref) for ref in candidate.get("evidence_refs", []) if isinstance(ref, str))
        for section_name in ("qualification", "signals"):
            for item in candidate.get(section_name, []):
                if not isinstance(item, dict):
                    continue
                refs.update(str(ref) for ref in item.get("evidence_refs", []) if isinstance(ref, str))
                refs.update(str(usage.get("source_ref", "")) for usage in item.get("source_usages", []) if isinstance(usage, dict))
                refs.update(str(finding.get("source_ref", "")) for finding in item.get("evidence_findings", []) if isinstance(finding, dict))
    return {ref for ref in refs if ref}


def _rule_id(rule: dict[str, Any], *, fallback: str) -> str:
    return str(rule.get("code") or rule.get("criterion_code") or rule.get("rule_id") or rule.get("id") or fallback)


def _compact_query(parts: list[str]) -> str:
    value = " ".join(part.strip() for part in parts if part.strip())
    return " ".join(value.split())[:700]


def _dict(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}
