"""Map persisted Radar definitions into the live Radar runtime contract.

The persisted catalog definition is richer than the original live mini Radar
shape. The live execution pipeline still has legacy readers for
`qualification_criteria` and compact signal fields, so this adapter preserves
the active definition payload and adds the backward-compatible projection in
one application-owned boundary.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from power_web_os.application.radar_records import RadarDefinitionRecord


def active_definition_to_live_radar_payload(record: RadarDefinitionRecord) -> dict[str, Any]:
    """Return the canonical live runtime payload for an active definition."""

    payload = deepcopy(record.definition_payload)
    metadata = _dict(payload.get("metadata"))
    radar_id = str(payload.get("radar_id") or record.radar_id)
    result = {
        **payload,
        "definition_id": str(payload.get("definition_id") or record.definition_id),
        "definition_version": record.definition_version,
        "radar_id": radar_id,
        "name": str(payload.get("name") or metadata.get("name") or radar_id),
        "description": str(payload.get("description") or metadata.get("description") or ""),
    }
    result.setdefault("global_search_policy", _dict(payload.get("global_search_policy")))
    result["qualification_criteria"] = _qualification_criteria(result)
    result["intent_signals"] = _intent_signals(result)
    result.setdefault("source_policy", _legacy_source_policy(_dict(result.get("global_search_policy"))))
    return result


def _qualification_criteria(payload: dict[str, Any]) -> list[dict[str, Any]]:
    direct = payload.get("qualification_criteria")
    if isinstance(direct, list):
        return [dict(item) for item in direct if isinstance(item, dict)]
    group = _dict(_dict(payload.get("account_qualification")).get("rule_group"))
    return [_criterion_from_rule(rule, operator=str(group.get("operator") or "AND")) for rule in _rules_from_group(group)]


def _criterion_from_rule(rule: dict[str, Any], *, operator: str) -> dict[str, Any]:
    rule_id = str(rule.get("rule_id") or rule.get("code") or rule.get("id") or "qualification")
    description = str(rule.get("description") or rule.get("rule") or rule.get("name") or rule_id)
    return {
        **rule,
        "code": str(rule.get("code") or rule_id),
        "label": str(rule.get("label") or rule.get("name") or description),
        "rule": description,
        "operator": str(rule.get("operator") or operator or "AND"),
        "requirement_level": str(rule.get("requirement_level") or "required"),
        "cross_validation_required": bool(rule.get("cross_validation_required", False)),
        "source_policy": _dict(rule.get("source_policy")),
    }


def _intent_signals(payload: dict[str, Any]) -> list[dict[str, Any]]:
    signals = payload.get("intent_signals")
    if not isinstance(signals, list):
        return []
    return [_signal_from_payload(signal) for signal in signals if isinstance(signal, dict)]


def _signal_from_payload(signal: dict[str, Any]) -> dict[str, Any]:
    code = str(signal.get("code") or signal.get("signal_id") or "signal")
    trigger_rules = _rules_from_group(_dict(signal.get("trigger_rule_group")))
    trigger_description = " ".join(str(rule.get("description") or rule.get("name") or "") for rule in trigger_rules).strip()
    description = str(signal.get("description") or trigger_description or signal.get("name") or code)
    return {
        **signal,
        "code": code,
        "label": str(signal.get("label") or signal.get("name") or description),
        "rule": str(signal.get("rule") or trigger_description or description),
        "source_policy": _dict(signal.get("source_policy")),
    }


def _rules_from_group(group: dict[str, Any]) -> list[dict[str, Any]]:
    rules = [dict(rule) for rule in group.get("rules", []) if isinstance(rule, dict)]
    for child in group.get("groups", []):
        if isinstance(child, dict):
            rules.extend(_rules_from_group(child))
    return rules


def _legacy_source_policy(global_search_policy: dict[str, Any]) -> dict[str, Any]:
    preferred_domains: list[str] = []
    for source in global_search_policy.get("sources", []):
        if not isinstance(source, dict):
            continue
        reference = str(source.get("reference") or "")
        if reference.startswith("http"):
            preferred_domains.append(reference.removeprefix("https://").removeprefix("http://").split("/", 1)[0])
    return {
        "preferred_domains": preferred_domains,
        "allow_open_web": bool(global_search_policy.get("allow_system_sources", True)),
        "human_review_required": True,
    }


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}
