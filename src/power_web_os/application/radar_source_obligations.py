"""Source usage obligation rules for Radar planning and diagnostics.

The planner may propose a source strategy, but application code owns whether a
configured source is optional, preferred, required, fallback-only, or disabled.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

SourceUsageObligation = str

SOURCE_USAGE_OBLIGATIONS = {
    "required",
    "preferred",
    "optional",
    "fallback",
    "disabled",
    "required_for_identity",
    "required_for_coverage",
    "required_for_signal",
}
REQUIRED_OBLIGATIONS = {"required", "required_for_identity", "required_for_coverage", "required_for_signal"}


def source_usage_obligation(source: dict[str, Any]) -> SourceUsageObligation:
    value = str(source.get("usage_obligation") or source.get("usage_mode") or "preferred").strip().lower()
    return value if value in SOURCE_USAGE_OBLIGATIONS else "preferred"


def source_obligations_for_policy(global_policy: dict[str, Any]) -> list[dict[str, Any]]:
    obligations: list[dict[str, Any]] = []
    for source in _global_sources(global_policy):
        source_id = source_id_for_source(source)
        if not source_id:
            continue
        obligation = source_usage_obligation(source)
        obligations.append({
            "source_id": source_id,
            "source_label": str(source.get("label") or source_id),
            "source_type": str(source.get("source_type") or ""),
            "reference": str(source.get("reference") or ""),
            "trust_level": str(source.get("trust_level") or ""),
            "usage_obligation": obligation,
            "required": obligation in REQUIRED_OBLIGATIONS,
        })
    return obligations


def source_obligation_summary(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    by_status = Counter(str(item.get("status") or "unknown") for item in decisions)
    by_obligation = Counter(str(item.get("usage_obligation") or "preferred") for item in decisions)
    blocked = [
        item for item in decisions
        if str(item.get("status")) in {
            "blocked",
            "violated",
            "unavailable",
            "empty",
            "attempted_empty",
            "attempted_insufficient",
            "attempted_unlinked",
            "identity_not_confirmed_after_all_terms",
        }
    ]
    return {
        "decision_count": len(decisions),
        "by_status": dict(by_status),
        "by_obligation": dict(by_obligation),
        "blocking_count": len(blocked),
        "blocking_source_ids": [str(item.get("source_id")) for item in blocked if item.get("source_id")],
    }


def validate_source_obligations(
    *,
    global_policy: dict[str, Any],
    steps: list[Any],
    source_policy_decisions: list[Any],
) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    """Validate accepted planner output against source usage obligations."""

    errors: list[str] = []
    warnings: list[str] = []
    decisions = _decision_index(source_policy_decisions)
    required_or_preferred_pending = _required_or_preferred_pending(global_policy, decisions)

    for obligation in source_obligations_for_policy(global_policy):
        source_id = str(obligation["source_id"])
        usage = str(obligation["usage_obligation"])
        decision = decisions.get(source_id)
        selected = bool(decision and str(decision.get("decision")) == "selected")
        skipped = bool(decision and str(decision.get("decision")) == "skipped")
        reason = str(decision.get("reason") or "").strip() if decision else ""

        if usage == "disabled" and selected:
            errors.append(f"Disabled source {source_id} must not be selected by the discovery plan.")
        if usage in REQUIRED_OBLIGATIONS:
            if skipped:
                errors.append(f"Required source {source_id} cannot be skipped by planner output.")
            if not selected:
                errors.append(f"Required source {source_id} must be selected by planner output.")
            if selected and not _source_used_for_required_stage(source_id=source_id, usage_obligation=usage, steps=steps):
                errors.append(_required_stage_error(source_id=source_id, usage_obligation=usage))
        elif usage == "preferred" and skipped and reason:
            warnings.append(f"Preferred source {source_id} was skipped with rationale: {reason}")
        elif usage == "preferred" and skipped and not reason:
            errors.append(f"Preferred source {source_id} can be skipped only with rationale.")

        if usage == "fallback" and selected and required_or_preferred_pending:
            errors.append(
                f"Fallback source {source_id} cannot be selected before required/preferred sources are selected or explicitly skipped."
            )

    coverage_required = [
        item["source_id"]
        for item in source_obligations_for_policy(global_policy)
        if item["usage_obligation"] == "required_for_coverage"
    ]
    if coverage_required:
        coverage_steps = [step for step in steps if getattr(step, "stage", "") == "coverage_check"]
        if not coverage_steps:
            errors.append("A required_for_coverage source requires an explicit coverage_check step.")
        for source_id in coverage_required:
            if not any(source_id in list(getattr(step, "source_ids", [])) for step in coverage_steps):
                errors.append(f"required_for_coverage source {source_id} must be named in a coverage_check step.")

    return errors, warnings, source_obligations_for_policy(global_policy)


def obligation_decisions_from_plan(
    *,
    global_policy: dict[str, Any],
    steps: list[Any],
    source_policy_decisions: list[Any],
    source_provider_outcomes: list[dict[str, Any]] | None = None,
    sources: list[Any] | None = None,
    observations: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    planner_decisions = _decision_index(source_policy_decisions)
    provider_by_source: dict[str, dict[str, Any]] = {}
    for item in source_provider_outcomes or []:
        if not isinstance(item, dict):
            continue
        source_id = str(item.get("source_id") or "")
        if not source_id:
            continue
        provider_by_source[source_id] = _preferred_provider_outcome(provider_by_source.get(source_id), item)
    result: list[dict[str, Any]] = []
    for obligation in source_obligations_for_policy(global_policy):
        source_id = str(obligation["source_id"])
        planner_decision = planner_decisions.get(source_id, {})
        provider_outcome = provider_by_source.get(source_id)
        selected = str(planner_decision.get("decision") or "") == "selected"
        skipped = str(planner_decision.get("decision") or "") == "skipped"
        runtime_outcome = _runtime_obligation_outcome(
            obligation=obligation,
            provider_outcome=provider_outcome,
            selected=selected,
            steps=steps,
            sources=sources or [],
            observations=observations or [],
        )
        if runtime_outcome:
            status = runtime_outcome["status"]
        elif selected and _source_used_for_any_stage(source_id=source_id, steps=steps):
            status = "satisfied"
        elif skipped:
            status = "skipped_with_rationale" if str(planner_decision.get("reason") or "").strip() else "violated"
        elif obligation["usage_obligation"] in REQUIRED_OBLIGATIONS:
            status = "violated"
        else:
            status = "not_applicable"
        result.append({
            **obligation,
            "status": status,
            "planner_decision": planner_decision,
            "provider_outcome": provider_outcome or {},
            "runtime_outcome": runtime_outcome or {},
            "stage_task_ids": [
                str(getattr(step, "step_id", getattr(step, "task_id", "")))
                for step in steps
                if source_id in list(getattr(step, "source_ids", []))
            ],
        })
    return result


def _runtime_obligation_outcome(
    *,
    obligation: dict[str, Any],
    provider_outcome: dict[str, Any] | None,
    selected: bool,
    steps: list[Any],
    sources: list[Any],
    observations: list[dict[str, Any]],
) -> dict[str, Any]:
    usage = str(obligation.get("usage_obligation") or "")
    source_id = str(obligation.get("source_id") or "")
    source_type = str(obligation.get("source_type") or "")
    required = usage in REQUIRED_OBLIGATIONS
    if provider_outcome:
        outcome = str(provider_outcome.get("outcome") or "")
        observation_count = _int_value(provider_outcome.get("observation_count"))
        if outcome in {"provider_unavailable", "rate_limited", "invalid_credentials"}:
            return {"status": "unavailable", "outcome": outcome, "useful": False}
        if outcome in {"policy_skipped", "not_executed_budget_limited", "not_executed_input_not_available"}:
            return {"status": "blocked", "outcome": outcome, "useful": False}
        if (
            usage == "required_for_identity"
            and outcome in {"empty", "provider_empty", "no_match"}
            and _has_source_backed_identity_evidence(sources=sources, observations=observations)
        ):
            return {"status": "cross_source_identity_supported", "outcome": outcome, "useful": True}
        if usage == "required_for_identity" and outcome in {"empty", "provider_empty", "no_match"}:
            return {"status": "identity_not_confirmed_after_all_terms", "outcome": outcome, "useful": False}
        if outcome in {"empty", "provider_empty", "no_match"} or observation_count == 0 and outcome in {"used", "no_match"}:
            return {"status": "attempted_empty", "outcome": outcome, "useful": False}
        if outcome == "ambiguous_match" and _int_value(provider_outcome.get("review_needed_entity_count")) > 0:
            return {"status": "attempted_review_needed", "outcome": outcome, "useful": True}
        if outcome in {"registry_lookup_insufficient", "schema_invalid", "ambiguous_match"}:
            return {"status": "attempted_insufficient", "outcome": outcome, "useful": False}
        if observation_count > 0 or outcome == "used":
            return {"status": "satisfied", "outcome": outcome, "useful": True}
    if not required or not selected or not _source_used_for_any_stage(source_id=source_id, steps=steps):
        return {}
    linked_source_refs = _linked_source_refs(observations)
    source_refs = {_source_ref(source) for source in sources if _source_ref(source)}
    if source_type == "search_engine" and source_refs and not (source_refs & linked_source_refs):
        return {"status": "attempted_unlinked", "outcome": "retrieved_without_linked_evidence", "useful": False}
    if source_refs & linked_source_refs:
        return {"status": "satisfied", "outcome": "linked_evidence", "useful": True}
    return {}


def _preferred_provider_outcome(current: dict[str, Any] | None, candidate: dict[str, Any]) -> dict[str, Any]:
    """Keep the most useful runtime outcome for a source obligation."""

    if current is None:
        return candidate
    current_rank = _provider_outcome_rank(current)
    candidate_rank = _provider_outcome_rank(candidate)
    return candidate if candidate_rank > current_rank else current


def _provider_outcome_rank(outcome_payload: dict[str, Any]) -> int:
    outcome = str(outcome_payload.get("outcome") or "")
    observation_count = _int_value(outcome_payload.get("observation_count"))
    if outcome == "used" and observation_count > 0:
        return 50
    if observation_count > 0:
        return 40
    if outcome == "ambiguous_match" and _int_value(outcome_payload.get("review_needed_entity_count")) > 0:
        return 35
    if outcome in {"registry_lookup_insufficient", "schema_invalid", "ambiguous_match"}:
        return 20
    if outcome in {"empty", "provider_empty", "no_match"}:
        return 10
    if outcome in {"not_executed_budget_limited", "not_executed_input_not_available", "policy_skipped"}:
        return 0
    if outcome:
        return 5
    return 0


def _linked_source_refs(observations: list[dict[str, Any]]) -> set[str]:
    refs: set[str] = set()
    for observation in observations:
        if not isinstance(observation, dict):
            continue
        for ref in observation.get("evidence_refs", []):
            if str(ref).strip():
                refs.add(str(ref))
        for section_name in ("qualification", "signals"):
            section = observation.get(section_name, [])
            if not isinstance(section, list):
                continue
            for item in section:
                if not isinstance(item, dict):
                    continue
                for ref in item.get("evidence_refs", []):
                    if str(ref).strip():
                        refs.add(str(ref))
    return refs


def _has_source_backed_identity_evidence(*, sources: list[Any], observations: list[dict[str, Any]]) -> bool:
    linked_refs = _linked_source_refs(observations)
    if not linked_refs:
        return False
    for source in sources:
        ref = _source_ref(source)
        if not ref or ref not in linked_refs:
            continue
        source_type = str(source.get("source_type") if isinstance(source, dict) else getattr(source, "source_type", "") or "")
        url = str(source.get("url") if isinstance(source, dict) else getattr(source, "url", "") or "")
        if source_type != "company_registry" or url:
            return True
    return False


def _int_value(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return -1


def _source_ref(source: Any) -> str:
    if isinstance(source, dict):
        return str(source.get("evidence_ref") or "")
    return str(getattr(source, "evidence_ref", "") or "")


def source_id_for_source(source: dict[str, Any]) -> str:
    return str(source.get("source_id") or source.get("reference") or source.get("label") or "").strip()


def _global_sources(global_policy: dict[str, Any]) -> list[dict[str, Any]]:
    return [dict(item) for item in global_policy.get("sources", []) if isinstance(item, dict)]


def _decision_index(source_policy_decisions: list[Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in source_policy_decisions:
        if hasattr(item, "model_dump"):
            payload = item.model_dump()
        elif isinstance(item, dict):
            payload = dict(item)
        else:
            continue
        source_id = str(payload.get("source_id") or "").strip()
        if source_id:
            result[source_id] = payload
    return result


def _required_or_preferred_pending(global_policy: dict[str, Any], decisions: dict[str, dict[str, Any]]) -> bool:
    for obligation in source_obligations_for_policy(global_policy):
        if obligation["usage_obligation"] not in {"required", "required_for_identity", "required_for_coverage", "required_for_signal", "preferred"}:
            continue
        decision = decisions.get(str(obligation["source_id"]))
        if not decision:
            return True
        if str(decision.get("decision")) == "skipped" and not str(decision.get("reason") or "").strip():
            return True
    return False


def _source_used_for_any_stage(*, source_id: str, steps: list[Any]) -> bool:
    return any(source_id in list(getattr(step, "source_ids", [])) for step in steps)


def _source_used_for_required_stage(*, source_id: str, usage_obligation: str, steps: list[Any]) -> bool:
    if usage_obligation == "required":
        return _source_used_for_any_stage(source_id=source_id, steps=steps)
    if usage_obligation == "required_for_identity":
        return any(
            getattr(step, "stage", "") in {"candidate_universe_discovery", "source_probe", "qualification_gate"}
            and source_id in list(getattr(step, "source_ids", []))
            for step in steps
        )
    if usage_obligation == "required_for_coverage":
        return any(
            getattr(step, "stage", "") == "coverage_check" and source_id in list(getattr(step, "source_ids", []))
            for step in steps
        )
    if usage_obligation == "required_for_signal":
        return any(
            getattr(step, "stage", "") == "signal_search" and source_id in list(getattr(step, "source_ids", []))
            for step in steps
        )
    return True


def _required_stage_error(*, source_id: str, usage_obligation: str) -> str:
    if usage_obligation == "required_for_identity":
        return f"required_for_identity source {source_id} must be named in discovery or qualification steps."
    if usage_obligation == "required_for_coverage":
        return f"required_for_coverage source {source_id} must be named in a coverage_check step."
    if usage_obligation == "required_for_signal":
        return f"required_for_signal source {source_id} must be named in signal_search steps."
    return f"Required source {source_id} must be named in at least one executable step."
