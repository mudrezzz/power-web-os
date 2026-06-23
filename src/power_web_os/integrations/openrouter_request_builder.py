"""Build bounded OpenRouter requests for one live Radar execution task."""

from __future__ import annotations

import json
from typing import Any

from power_web_os.application.live_radar_contracts import RadarSearchPlan, RadarSearchQuery
from power_web_os.application.live_radar_retrieval_plan import (
    RadarRetrievalTaskPrompt,
    response_contract_for_stage,
    stage_task_label,
    retrieval_task_from_search_query,
)


def build_openrouter_request(
    *,
    radar: dict[str, Any],
    search_plan: RadarSearchPlan,
    model: str,
    web_mode: str,
    web_search_engine: str = "auto",
) -> dict[str, Any]:
    query = search_plan.queries[0] if len(search_plan.queries) == 1 else None
    prompt = compact_task_prompt(radar=radar, search_plan=search_plan).model_dump()
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
            "parameters": {
                "engine": web_search_engine,
                "max_results": 5,
                "max_total_results": 12,
                "search_context_size": "low",
            },
        }]
    elif web_mode == "plugin_web":
        request["plugins"] = [{"id": "web"}]
    elif web_mode == "model_native":
        request["metadata"] = {"web_mode": "model_native"}
    else:
        raise ValueError(f"Unsupported OPENROUTER_WEB_MODE: {web_mode}")
    return request


def openrouter_compiled_prompt_summary(payload: dict[str, Any]) -> dict[str, Any]:
    messages = payload.get("messages", [])
    user_message = messages[1] if isinstance(messages, list) and len(messages) > 1 else {}
    content = user_message.get("content") if isinstance(user_message, dict) else None
    if not isinstance(content, str):
        return {}
    try:
        value = json.loads(content)
    except json.JSONDecodeError:
        return {"raw_content_excerpt": content[:1000]}
    if not isinstance(value, dict):
        return {}
    constraints = value.get("constraints", [])
    return {
        "task_card": value.get("task_card", {}),
        "response_contract": value.get("response_contract", {}),
        "constraint_count": len(constraints) if isinstance(constraints, list) else 0,
    }


def compact_task_prompt(*, radar: dict[str, Any], search_plan: RadarSearchPlan) -> RadarRetrievalTaskPrompt:
    query = search_plan.queries[0] if len(search_plan.queries) == 1 else None
    if query is None:
        return RadarRetrievalTaskPrompt(
            task_card={
                "task_id": "multi-task-plan",
                "radar_id": search_plan.radar_id,
                "stage": "multi_task_plan",
                "query_count": len(search_plan.queries),
                "purpose": "Run the provided bounded Radar search tasks.",
                "queries": [item.query for item in search_plan.queries],
            },
            response_contract=_compact_response_contract(None),
            constraints=_task_rules(None),
        )
    task = retrieval_task_from_search_query(query)
    task_card = {
        "task_id": task.task_id,
        "radar_id": search_plan.radar_id,
        "task": _task_text(query),
        "stage": task.stage,
        "subject_type": task.subject_type,
        "subject_id": task.subject_id,
        "query": task.query,
        "purpose": task.purpose,
        "expected_evidence": task.expected_evidence,
        "rule_snapshot": task.rule_snapshot,
        "source_policy": {
            "scope": task.source_scope,
            "source_base": task.source_base,
            "application_scope": task.application_scope,
            "source_ids": task.source_ids,
            "external_source_hints": task.external_source_hints,
            "preferred_domains": list(_source_policy(radar).get("preferred_domains", [])),
            "allow_open_web": _source_policy(radar).get("allow_open_web", True),
        },
        "candidate_scope": task.candidate_scope,
        "depends_on": task.depends_on,
    }
    return RadarRetrievalTaskPrompt(
        task_card={key: value for key, value in task_card.items() if value not in ("", None, [], {})},
        response_contract=_compact_response_contract(query),
        constraints=_task_rules(query),
    )


def _task_text(query: RadarSearchQuery | None) -> str:
    if query is None:
        return "Run a live ICP radar search. Use web search and return only JSON."
    return stage_task_label(query.stage)


def _compact_response_contract(query: RadarSearchQuery | None) -> dict[str, Any]:
    if query is None:
        return {
            "schema_id": "radar_task_result_v1",
            "return_json_sections": ["sources", "candidates", "source_outcomes"],
        }
    contract = response_contract_for_stage(query.stage, query.subject_id).model_dump()
    if query.stage == "signal_search":
        contract["finding_shape"] = {
            "sources": "evidence refs with title, url, snippet, query_id",
            "candidates.signals": "one signal finding for current signal and candidate scope",
            "source_outcomes": "used/duplicate/irrelevant/policy_skipped/insufficient_evidence/unreachable/not_used_by_candidate",
        }
    elif query.stage == "coverage_check":
        contract["finding_shape"] = {
            "sources": "source refs used for coverage observations",
            "candidate_universe_gaps": "source-backed entities missing from current universe",
            "coverage_findings": "completeness risk and warnings",
            "source_outcomes": "source usage outcome",
        }
    else:
        contract["finding_shape"] = {
            "sources": "evidence refs with title, url, snippet, query_id",
            "candidates.qualification": "one qualification finding for current criterion",
            "source_outcomes": "source usage outcome",
        }
    return contract


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


def _source_policy(radar: dict[str, Any]) -> dict[str, Any]:
    value = radar.get("source_policy")
    return dict(value) if isinstance(value, dict) else {}
