"""Coverage diagnostics helpers for candidate-discovery universe state."""

from __future__ import annotations

from power_web_os.application.radar.candidate_discovery.contracts import WebSearchProviderResult
from power_web_os.application.radar.candidate_discovery.universe.metadata import dict_list


def coverage_warnings(result: WebSearchProviderResult) -> list[str]:
    warnings: list[str] = []
    for item in dict_list(result.provider_metadata.get("coverage_findings")):
        if isinstance(item.get("warnings"), list):
            warnings.extend(str(value) for value in item.get("warnings", []) if str(value).strip())
        if str(item.get("completeness_risk") or "") == "high":
            warnings.append(str(item.get("summary") or "Coverage risk is high."))
    return [item for item in warnings if item]


def coverage_risk(result: WebSearchProviderResult) -> str:
    risks = [str(item.get("completeness_risk") or "medium") for item in dict_list(result.provider_metadata.get("coverage_findings"))]
    if "high" in risks:
        return "high"
    if "medium" in risks:
        return "medium"
    if "low" in risks:
        return "low"
    return "medium"
