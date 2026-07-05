"""Execution-result diagnostics for live Radar extraction gates."""

from __future__ import annotations

from typing import Any

from power_web_os.application.radar.candidate_discovery.contracts import LiveRadarPipelineEvent


def extraction_validation_issues(provider_metadata: dict[str, Any]) -> list[dict[str, Any]]:
    return _unique_issue_payloads(_list(provider_metadata.get("extraction_validation_issues")))


def extraction_repair_results(provider_metadata: dict[str, Any]) -> list[dict[str, Any]]:
    return _list(provider_metadata.get("extraction_repair_results"))


def extraction_contract_state(provider_metadata: dict[str, Any]) -> str:
    states = {
        str(item.get("state"))
        for item in _list(provider_metadata.get("extraction_validation_results"))
        if str(item.get("state", "")).strip()
    }
    if "evidence_linking_failed" in states:
        return "evidence_linking_failed"
    if "extraction_schema_invalid" in states:
        return "extraction_schema_invalid"
    if "extraction_repair_needed" in states:
        return "extraction_repair_needed"
    return "accepted"


def extraction_validation_event(
    issues: list[dict[str, Any]],
    repair_results: list[dict[str, Any]],
) -> LiveRadarPipelineEvent:
    error_count = sum(1 for issue in issues if str(issue.get("severity")) == "error")
    warning_count = len(issues) - error_count
    return LiveRadarPipelineEvent(
        event_type="validation_warning",
        phase="extraction",
        actor="application",
        node_name="extraction_contract_gate",
        visibility="operator",
        summary=f"Extraction contract gate reported {error_count} errors and {warning_count} warnings.",
        payload={"issues": issues, "repair_results": repair_results},
    )


def _unique_issue_payloads(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    seen: set[tuple[str, str, str]] = set()
    for issue in issues:
        key = (str(issue.get("code")), str(issue.get("severity")), str(issue.get("path")))
        if key in seen:
            continue
        seen.add(key)
        result.append(issue)
    return result


def _list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]
