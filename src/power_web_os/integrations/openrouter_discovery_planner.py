"""OpenRouter adapter for structured Radar discovery planning."""

from __future__ import annotations

import json
import os
from pathlib import Path
from time import perf_counter
from typing import Any

from power_web_os.application.live_radar_contracts import (
    RadarDiscoveryPlanner,
    RadarDiscoveryPlanningInput,
    RadarDiscoveryPlan,
    RadarDiscoveryPlanValidationResult,
)
from power_web_os.application.live_radar_external_budget import reserve_openrouter_http_call
from power_web_os.application.radar_technical_trace import RadarRunTechnicalTraceCommand, append_current_trace
from power_web_os.integrations.live_radar_openrouter import _load_env_file


class OpenRouterDiscoveryPlanner(RadarDiscoveryPlanner):
    runtime_name = "openrouter_discovery_planner"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        env_path: Path | None = None,
        timeout_seconds: float = 90,
    ) -> None:
        self._env = _load_env_file(env_path or Path.cwd() / ".env")
        self._api_key = api_key or self._env.get("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")
        advanced_model = self._env.get("OPENROUTER_ADVANCED_MODEL") or os.getenv("OPENROUTER_ADVANCED_MODEL")
        self._model = (
            model
            or self._env.get("OPENROUTER_PLANNER_MODEL")
            or os.getenv("OPENROUTER_PLANNER_MODEL")
            or advanced_model
            or self._env.get("OPENROUTER_MODEL")
            or os.getenv("OPENROUTER_MODEL")
        )
        self._timeout_seconds = timeout_seconds

    @property
    def model(self) -> str:
        return self._model or "openai/gpt-4.1-mini"

    def propose_plan(
        self,
        *,
        planning_input: RadarDiscoveryPlanningInput,
        previous_validation: RadarDiscoveryPlanValidationResult | None = None,
    ) -> RadarDiscoveryPlan:
        if not self._api_key:
            raise RuntimeError("OPENROUTER_API_KEY is required for live Radar discovery planning")
        try:
            import httpx
        except ImportError as error:  # pragma: no cover - install-shape guard.
            raise RuntimeError("Install the agent extra to run OpenRouter discovery planning: pip install -e .[agent]") from error

        payload = build_openrouter_discovery_planner_request(
            planning_input=planning_input,
            previous_validation=previous_validation,
            model=self.model,
        )
        append_current_trace(RadarRunTechnicalTraceCommand(
            run_id="",
            phase="planning",
            node_name="discovery_planner",
            trace_type="provider_request",
            title="OpenRouter discovery planner request",
            summary="OpenRouter request for structured discovery plan.",
            payload={"url": "https://openrouter.ai/api/v1/chat/completions", "model": self.model, "request": payload},
        ))
        budget_decision = reserve_openrouter_http_call(role="planner", task_id="discovery_planner")
        if not budget_decision.accepted:
            append_current_trace(RadarRunTechnicalTraceCommand(
                run_id="",
                phase="planning",
                node_name="discovery_planner",
                trace_type="provider_error",
                title="OpenRouter discovery planner skipped by external budget",
                summary=budget_decision.message,
                payload={"model": self.model, "budget_decision": budget_decision.to_payload()},
            ))
            raise RuntimeError(budget_decision.message or "OpenRouter discovery planner skipped by external budget.")
        started_at = perf_counter()
        try:
            response = httpx.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/mudrezzz/power-web-os",
                    "X-Title": "Power Web OS Radar Discovery Planner",
                },
                json=payload,
                timeout=self._timeout_seconds,
            )
        except Exception as error:
            append_current_trace(RadarRunTechnicalTraceCommand(
                run_id="",
                phase="planning",
                node_name="discovery_planner",
                trace_type="provider_error",
                title="OpenRouter discovery planner error",
                summary=str(error),
                duration_ms=_duration_ms(started_at),
                payload={"error_type": error.__class__.__name__, "message": str(error), "model": self.model},
            ))
            raise
        if response.status_code >= 400:
            append_current_trace(RadarRunTechnicalTraceCommand(
                run_id="",
                phase="planning",
                node_name="discovery_planner",
                trace_type="provider_error",
                title="OpenRouter discovery planner response error",
                summary=f"OpenRouter returned HTTP {response.status_code}.",
                duration_ms=_duration_ms(started_at),
                payload={"status_code": response.status_code, "body": response.text[:2000], "model": self.model},
            ))
            raise RuntimeError(f"OpenRouter discovery planner failed with {response.status_code}: {response.text[:240]}")
        response_payload = response.json()
        append_current_trace(RadarRunTechnicalTraceCommand(
            run_id="",
            phase="planning",
            node_name="discovery_planner",
            trace_type="provider_response",
            title="OpenRouter discovery planner response",
            summary="OpenRouter returned a structured discovery plan response.",
            duration_ms=_duration_ms(started_at),
            payload=_response_trace_payload(response_payload, model=self.model),
        ))
        return _plan_from_response(response_payload)


def build_openrouter_discovery_planner_request(
    *,
    planning_input: RadarDiscoveryPlanningInput,
    previous_validation: RadarDiscoveryPlanValidationResult | None,
    model: str,
) -> dict[str, Any]:
    prompt = {
        "task": "Create a structured candidate-universe discovery plan. Do not execute search. Do not evaluate intent signals.",
        "planning_input": planning_input.model_dump(),
        "previous_validation": previous_validation.model_dump() if previous_validation else None,
        "output_schema": {
            "plan_summary": "short product-safe explanation",
            "criterion_role_decisions": [{
                "rule_id": "qualification rule id",
                "role": "upstream_discovery|downstream_gate|attribute_enrichment|exclusion",
                "depends_on": ["upstream rule ids"],
                "confidence": "low|medium|high",
                "reason": "product-safe reason for this role",
                "warnings": ["optional role warning"],
            }],
            "steps": [{
                "step_id": "stable id",
                "stage": "candidate_universe_discovery|source_probe|qualification_gate|coverage_check",
                "subject_rule_ids": ["qualification rule ids only"],
                "source_scope": "global|local|additional|system (legacy projection)",
                "source_base": "global_configured|rule_local|additional|system",
                "application_scope": "whole_universe|rule_scope|candidate_scope",
                "source_ids": ["configured source ids when used"],
                "source_use": [{
                    "source_id": "configured source id",
                    "connector_profile_id": "connector profile id from source_cards",
                    "intended_use": "broad_discovery|identity_lookup|enrichment|coverage|signal_evidence|official_evidence",
                    "input_shape": "broad_query|concrete_company|candidate_scope|domain_or_url|unknown",
                    "expected_fact_kinds": ["fact kinds from source card"],
                    "rationale": "why this source capability matches the step",
                }],
                "external_source_hints": ["domains or registries when additional/system is allowed"],
                "query": "bounded search instruction",
                "purpose": "why this step is needed",
                "expected_evidence": ["evidence expected"],
                "acceptance_criteria": ["how backend/user should judge this step"],
                "skip_rationale": "why skipped if this is coverage/source decision",
                "depends_on": ["step ids"],
                "candidate_scope": ["candidate names only when already known"],
            }],
            "source_policy_decisions": [{
                "source_id": "id",
                "source_label": "label",
                "decision": "selected|skipped",
                "reason": "why",
                "rule_ids": ["Q1"],
                "usage_obligation": "required|preferred|optional|fallback|disabled|required_for_identity|required_for_coverage|required_for_signal",
                "obligation_status": "planned|skipped_with_rationale|not_applicable",
            }],
            "coverage_hypotheses": [{"summary": "coverage hypothesis", "expected_candidate_count": "range or unknown", "completeness_risk": "low|medium|high"}],
            "warnings": ["product-safe warning"],
        },
        "rules": [
            "Return strict JSON only.",
            "Do not include raw hidden chain-of-thought.",
            "Do not include prompt headers, secrets, or API keys.",
            "Use only qualification rules in discovery planning.",
            "First classify qualification criteria by role before proposing executable steps.",
            "Use upstream_discovery for criteria that define the open candidate universe.",
            "Use downstream_gate for criteria applied after candidates are known.",
            "Do not mix qualification and intent signals in one planning step.",
            "Separate source_base from application_scope: a globally configured source can be applied to one rule_scope without marking it as rule_local.",
            "Use source_cards to decide whether a source can handle broad discovery, identity lookup, enrichment, coverage, or signal evidence.",
            "For every selected source in a step, fill source_use with intended_use, input_shape, expected_fact_kinds, and rationale.",
            "Do not send broad_query input to a source card with requires_concrete_input unless supports_broad_discovery is true.",
            "Use lookup-only registry sources only after concrete company names, INN, OGRN, or candidate_scope is available.",
            "Do not use registry/enrichment-only sources for signal_evidence unless source_cards explicitly says supports_signal_evidence.",
            "If configured sources are useful, select them before open web sources.",
            "If a configured source is not useful, skip it with a concise reason.",
            "Never skip a source whose usage_obligation starts with required; plan it for the matching identity, coverage, or signal stage.",
            "Never select disabled sources.",
            "Use fallback sources only after required and preferred sources are selected or explicitly skipped with rationale.",
        ],
    }
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a B2B account discovery planning agent. Return strict JSON only."},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "metadata": {"planner_role": "discovery_strategy"},
    }


def _plan_from_response(payload: dict[str, Any]) -> RadarDiscoveryPlan:
    content = payload.get("choices", [{}])[0].get("message", {}).get("content") or "{}"
    parsed = _parse_json_object(content)
    _normalize_planner_payload(parsed)
    return RadarDiscoveryPlan.model_validate(parsed)


def _normalize_planner_payload(payload: dict[str, Any]) -> None:
    for item in payload.get("coverage_hypotheses", []):
        if isinstance(item, dict):
            item["completeness_risk"] = _normalize_risk(item.get("completeness_risk"))


def _normalize_risk(value: object) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"low", "medium", "high"}:
        return normalized
    if normalized in {"низкий", "низкая", "low risk"}:
        return "low"
    if normalized in {"средний", "средняя", "moderate", "moderate risk"}:
        return "medium"
    if normalized in {"высокий", "высокая", "high risk"}:
        return "high"
    return "medium"


def _parse_json_object(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        start = value.find("{")
        end = value.rfind("}")
        if start >= 0 and end > start:
            try:
                parsed = json.loads(value[start:end + 1])
                return parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError:
                return {}
    return {}


def _response_trace_payload(payload: dict[str, Any], *, model: str) -> dict[str, Any]:
    message = payload.get("choices", [{}])[0].get("message", {})
    return {
        "response_id": payload.get("id"),
        "model": model,
        "usage": payload.get("usage", {}),
        "message": {"role": message.get("role"), "content": message.get("content")},
    }


def _duration_ms(started_at: float) -> int:
    return int((perf_counter() - started_at) * 1000)
