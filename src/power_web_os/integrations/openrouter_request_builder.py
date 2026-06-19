"""Build bounded OpenRouter requests for one live Radar execution task."""

from __future__ import annotations

import json
from typing import Any

from power_web_os.application.live_radar_contracts import RadarSearchPlan, RadarSearchQuery


def build_openrouter_request(
    *,
    radar: dict[str, Any],
    search_plan: RadarSearchPlan,
    model: str,
    web_mode: str,
) -> dict[str, Any]:
    query = search_plan.queries[0] if len(search_plan.queries) == 1 else None
    prompt = {
        "task": _task_text(query),
        "radar": _scoped_radar(radar, query),
        "current_task": query.model_dump() if query is not None else {},
        "search_plan": search_plan.model_dump(),
        "output_schema": _output_schema(query),
        "rules": _task_rules(query),
    }
    request: dict[str, Any] = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are an ABM research agent. Return strict JSON only. Use Russian names and summaries when source content is Russian.",
            },
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    if web_mode == "server_tools":
        request["tools"] = [{
            "type": "openrouter:web_search",
            "parameters": {"engine": "auto", "max_results": 5, "max_total_results": 12, "search_context_size": "low"},
        }]
    elif web_mode == "plugin_web":
        request["plugins"] = [{"id": "web"}]
    elif web_mode == "model_native":
        request["metadata"] = {"web_mode": "model_native"}
    else:
        raise ValueError(f"Unsupported OPENROUTER_WEB_MODE: {web_mode}")
    return request


def _task_text(query: RadarSearchQuery | None) -> str:
    if query is None:
        return "Run a live ICP radar search. Use web search and return only JSON."
    if query.stage == "qualification_discovery":
        return "Discover candidate accounts for the current qualification rule only. Do not search or score intent signals."
    if query.stage == "qualification_gate":
        return "Filter the provided candidate scope through this qualification rule only. Do not search or score intent signals."
    if query.stage == "coverage_check":
        return "Check candidate universe coverage for the current qualified scope. Return missing source-backed candidates as gaps. Do not search or score intent signals."
    if query.stage == "signal_search":
        return "Search the provided qualified candidate scope for this one intent signal only. Do not discover new candidates."
    return "Run the bounded Radar task and return only JSON."


def _scoped_radar(radar: dict[str, Any], query: RadarSearchQuery | None) -> dict[str, Any]:
    scoped = {key: value for key, value in radar.items() if key not in {"qualification_criteria", "intent_signals"}}
    if query is None:
        scoped["qualification_criteria"] = radar.get("qualification_criteria", [])
        scoped["intent_signals"] = radar.get("intent_signals", [])
        return scoped
    if query.stage in {"qualification_discovery", "qualification_gate", "coverage_check"}:
        scoped["qualification_criteria"] = [
            item for item in radar.get("qualification_criteria", [])
            if isinstance(item, dict) and str(item.get("code")) == query.subject_id
        ]
        scoped["intent_signals"] = []
    elif query.stage == "signal_search":
        scoped["qualification_criteria"] = []
        scoped["intent_signals"] = [
            item for item in radar.get("intent_signals", [])
            if isinstance(item, dict) and str(item.get("code")) == query.subject_id
        ]
    return scoped


def _output_schema(query: RadarSearchQuery | None) -> dict[str, Any]:
    candidate: dict[str, Any] = {
        "legal_name": "candidate legal name",
        "description": "short account description",
        "review_flags": ["why human review is needed"],
    }
    if query is None or query.stage in {"qualification_discovery", "qualification_gate", "coverage_check"}:
        candidate["qualification"] = [{
            "criterion_code": query.subject_id if query else "Q1",
            "status": "confirmed|weak|unknown|rejected",
            "confidence": "high|medium|low",
            "rationale": "why this status",
            "evidence_refs": ["source ids"],
            "evidence_findings": [{"source_ref": "source id", "fact": "source-backed fact", "why_it_matches_rule": "why it matches"}],
        }]
    if query is None or query.stage == "signal_search":
        candidate["signals"] = [{
            "signal_code": query.subject_id if query else "S1",
            "status": "observed|not_observed|unclear",
            "score": "0|1|2",
            "confidence": "high|medium|low",
            "summary": "short signal summary",
            "evidence_refs": ["source ids"],
            "evidence_findings": [{"source_ref": "source id", "fact": "source-backed fact", "why_it_matches_signal": "why it matches"}],
        }]
    schema = {
        "sources": [{"evidence_ref": "stable short id", "title": "source title", "url": "https://...", "snippet": "short evidence summary", "query_id": "search query id"}],
        "candidates": [candidate],
        "source_outcomes": [{"source_ref": "source id", "outcome": "used|duplicate|irrelevant|policy_skipped|insufficient_evidence|unreachable|not_used_by_candidate", "reason": "why"}],
    }
    if query and query.stage in {"qualification_discovery", "coverage_check"}:
        schema["candidate_universe_gaps"] = [{
            "legal_name": "source-backed entity not yet in candidate universe",
            "description": "why it may belong",
            "source_refs": ["source ids"],
            "reason": "why this is a universe gap",
        }]
        schema["coverage_findings"] = [{
            "summary": "coverage check result",
            "completeness_risk": "low|medium|high",
            "candidate_count_estimate": "range or unknown",
            "warnings": ["coverage warning"],
        }]
    return schema


def _task_rules(query: RadarSearchQuery | None) -> list[str]:
    rules = [
        "Do not invent candidates without source evidence.",
        "If evidence is weak, mark it weak/unclear and add a review flag.",
        "Do not include secrets, request headers, raw tool dumps, or hidden chain-of-thought.",
    ]
    if query and query.stage in {"qualification_discovery", "qualification_gate"}:
        rules.append("Return qualification evidence only for the current qualification rule.")
    if query and query.stage == "coverage_check":
        rules.append("Return coverage findings and missing source-backed candidates only; do not return signal evidence.")
    if query and query.stage == "signal_search":
        rules.append("Return signal evidence only for the current signal and candidate scope.")
        rules.append("Do not add new candidates. If the source mentions a new entity, return it only in candidate_universe_gaps.")
    return rules
