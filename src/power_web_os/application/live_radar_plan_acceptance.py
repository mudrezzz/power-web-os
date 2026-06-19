"""Accept and normalize LLM discovery plans before execution compilation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from power_web_os.application.live_radar_contracts import (
    RadarCriterionRoleDecision,
    RadarDiscoveryPlanningInput,
    RadarDiscoveryPlan,
    RadarDiscoveryPlanStep,
    RadarDiscoveryPlanValidationResult,
)
from power_web_os.application.live_radar_discovery_planning import (
    RadarDiscoveryPlanValidator,
    global_source_ids,
    rule_id,
)


class RadarDiscoveryPlanAcceptanceResult(BaseModel):
    accepted_plan: RadarDiscoveryPlan
    validation: RadarDiscoveryPlanValidationResult
    corrections: list[dict[str, Any]] = Field(default_factory=list)


class RadarDiscoveryPlanAcceptanceService:
    """Backend authority for repairable planner output mismatches."""

    def __init__(self, validator: RadarDiscoveryPlanValidator | None = None) -> None:
        self._validator = validator or RadarDiscoveryPlanValidator()

    def accept(
        self,
        *,
        planning_input: RadarDiscoveryPlanningInput,
        plan: RadarDiscoveryPlan,
        fallback_used: bool = False,
    ) -> RadarDiscoveryPlanAcceptanceResult:
        role_decisions = _role_decisions(planning_input=planning_input, plan=plan)
        normalized_plan, corrections = _normalize_plan(
            planning_input=planning_input,
            plan=plan,
            role_decisions=role_decisions,
            fallback_used=fallback_used,
        )
        validation = self._validator.validate(planning_input=planning_input, plan=normalized_plan)
        validation = validation.model_copy(update={"corrections": [*validation.corrections, *corrections]})
        normalized_plan = normalized_plan.model_copy(update={
            "acceptance_metadata": {
                **normalized_plan.acceptance_metadata,
                "accepted": validation.accepted,
                "fallback_used": fallback_used,
                "correction_count": len(validation.corrections),
                "corrections": validation.corrections,
                "validation_errors": list(validation.errors),
                "validation_warnings": list(validation.warnings),
            }
        })
        return RadarDiscoveryPlanAcceptanceResult(
            accepted_plan=normalized_plan,
            validation=validation,
            corrections=validation.corrections,
        )


def _role_decisions(
    *,
    planning_input: RadarDiscoveryPlanningInput,
    plan: RadarDiscoveryPlan,
) -> list[RadarCriterionRoleDecision]:
    known = {
        decision.rule_id: decision
        for decision in plan.criterion_role_decisions
        if decision.rule_id.strip()
    }
    decisions: list[RadarCriterionRoleDecision] = []
    previous_required = ""
    for index, rule in enumerate(planning_input.qualification_rules):
        current_rule_id = rule_id(rule, fallback=f"Q{index + 1}")
        existing = known.get(current_rule_id)
        if existing is not None:
            decisions.append(existing)
            if _is_required_positive_rule(rule):
                previous_required = current_rule_id
            continue
        role = _infer_role(rule=rule, index=index)
        depends_on = [previous_required] if previous_required and role in {"downstream_gate", "attribute_enrichment", "exclusion"} else []
        decisions.append(RadarCriterionRoleDecision(
            rule_id=current_rule_id,
            role=role,
            depends_on=depends_on,
            confidence="medium",
            reason=_role_reason(rule=rule, role=role, index=index),
        ))
        if _is_required_positive_rule(rule):
            previous_required = current_rule_id
    return decisions


def _normalize_plan(
    *,
    planning_input: RadarDiscoveryPlanningInput,
    plan: RadarDiscoveryPlan,
    role_decisions: list[RadarCriterionRoleDecision],
    fallback_used: bool,
) -> tuple[RadarDiscoveryPlan, list[dict[str, Any]]]:
    corrections: list[dict[str, Any]] = []
    global_ids = set(global_source_ids(planning_input.global_search_policy))
    roles = {decision.rule_id: decision.role for decision in role_decisions}
    normalized_steps: list[RadarDiscoveryPlanStep] = []
    dependency_rewrites: dict[str, str] = {}

    for step in plan.steps:
        base_step, source_corrections = _normalize_source_scope(step=step, global_ids=global_ids)
        corrections.extend(source_corrections)
        split_steps, split_corrections = _split_multi_rule_step(step=base_step, roles=roles)
        corrections.extend(split_corrections)
        if split_steps:
            dependency_rewrites[step.step_id] = split_steps[-1].step_id
        normalized_steps.extend(split_steps)

    rewritten_steps = [
        step.model_copy(update={"depends_on": [_rewrite_dependency(item, dependency_rewrites) for item in step.depends_on]})
        for step in normalized_steps
    ]
    enriched_steps = [_with_default_source_fields(step) for step in rewritten_steps]
    return plan.model_copy(update={
        "criterion_role_decisions": role_decisions,
        "steps": enriched_steps,
        "acceptance_metadata": {
            **plan.acceptance_metadata,
            "fallback_used": fallback_used,
            "original_step_count": len(plan.steps),
            "normalized_step_count": len(enriched_steps),
        },
    }), corrections


def _normalize_source_scope(
    *,
    step: RadarDiscoveryPlanStep,
    global_ids: set[str],
) -> tuple[RadarDiscoveryPlanStep, list[dict[str, Any]]]:
    if step.source_scope == "local" and any(source_id in global_ids for source_id in step.source_ids):
        return step.model_copy(update={
            "source_scope": "global",
            "source_base": "global_configured",
            "application_scope": "rule_scope",
        }), [{
            "type": "source_scope_corrected",
            "step_id": step.step_id,
            "from": "local",
            "to": "global",
            "source_base": "global_configured",
            "application_scope": "rule_scope",
            "reason": "Configured global source id was applied to a rule-scoped task.",
        }]
    return step, []


def _split_multi_rule_step(
    *,
    step: RadarDiscoveryPlanStep,
    roles: dict[str, str],
) -> tuple[list[RadarDiscoveryPlanStep], list[dict[str, Any]]]:
    if step.stage not in {"candidate_universe_discovery", "source_probe", "qualification_gate"} or len(step.subject_rule_ids) <= 1:
        return [step], []
    split_steps: list[RadarDiscoveryPlanStep] = []
    previous_step_id = ""
    for index, current_rule_id in enumerate(step.subject_rule_ids):
        role = roles.get(current_rule_id, "downstream_gate")
        stage = step.stage if index == 0 and role == "upstream_discovery" else "qualification_gate"
        step_id = step.step_id if index == 0 else f"{step.step_id}-{current_rule_id.lower()}"
        split_steps.append(step.model_copy(update={
            "step_id": step_id,
            "stage": stage,
            "subject_rule_ids": [current_rule_id],
            "depends_on": [previous_step_id] if previous_step_id else list(step.depends_on),
            "application_scope": "whole_universe" if stage == "candidate_universe_discovery" else "rule_scope",
        }))
        previous_step_id = step_id
    return split_steps, [{
        "type": "multi_rule_step_split",
        "step_id": step.step_id,
        "rule_ids": list(step.subject_rule_ids),
        "normalized_step_ids": [item.step_id for item in split_steps],
        "reason": "Strategic planning step referenced multiple qualification rules; executable checks are rule-scoped.",
    }]


def _with_default_source_fields(step: RadarDiscoveryPlanStep) -> RadarDiscoveryPlanStep:
    source_base = step.source_base or _source_base_from_scope(step.source_scope)
    if step.application_scope:
        application_scope = step.application_scope
    elif step.candidate_scope:
        application_scope = "candidate_scope"
    elif step.stage in {"candidate_universe_discovery", "source_probe"}:
        application_scope = "whole_universe"
    else:
        application_scope = "rule_scope"
    return step.model_copy(update={"source_base": source_base, "application_scope": application_scope})


def _source_base_from_scope(source_scope: str) -> str:
    if source_scope == "global":
        return "global_configured"
    if source_scope == "local":
        return "rule_local"
    if source_scope == "system":
        return "system"
    return "additional"


def _rewrite_dependency(value: str, rewrites: dict[str, str]) -> str:
    return rewrites.get(value, value)


def _infer_role(*, rule: dict[str, Any], index: int) -> str:
    operator = str(rule.get("operator") or "AND").upper()
    requirement = str(rule.get("requirement_level") or "required").lower()
    text = " ".join(str(rule.get(key, "")) for key in ("label", "rule", "description")).lower()
    if "NOT" in operator:
        return "exclusion"
    if requirement != "required":
        return "attribute_enrichment"
    if index == 0:
        return "upstream_discovery"
    if any(marker in text for marker in ("revenue", "выруч", "region", "регион", "industry", "отрасл", "industrial", "производ")):
        return "downstream_gate"
    return "downstream_gate"


def _is_required_positive_rule(rule: dict[str, Any]) -> bool:
    operator = str(rule.get("operator") or "AND").upper()
    requirement = str(rule.get("requirement_level") or "required").lower()
    return "NOT" not in operator and requirement == "required"


def _role_reason(*, rule: dict[str, Any], role: str, index: int) -> str:
    label = str(rule.get("label") or rule.get("rule") or rule.get("description") or f"rule {index + 1}")
    if role == "upstream_discovery":
        return f"{label} is the first required positive qualification criterion and defines the initial candidate universe."
    if role == "exclusion":
        return f"{label} is an exclusion criterion and should remove candidates after discovery."
    if role == "attribute_enrichment":
        return f"{label} is not required for universe discovery and should enrich or flag candidates."
    return f"{label} is a downstream qualification gate applied to the discovered candidate universe."
