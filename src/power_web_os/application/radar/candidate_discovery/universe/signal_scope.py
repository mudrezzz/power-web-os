"""Signal-search scope helpers for the frozen candidate universe."""

from __future__ import annotations

from power_web_os.application.radar.candidate_discovery.contracts import WebSearchProviderResult
from power_web_os.application.radar.candidate_discovery.universe.identity import candidate_name
from power_web_os.application.radar.candidate_discovery.universe.metadata import dict_list


def filter_signal_result(result: WebSearchProviderResult, *, allowed_candidate_names: set[str]) -> WebSearchProviderResult:
    allowed = {name.lower() for name in allowed_candidate_names}
    accepted: list[dict[str, Any]] = []
    gaps = dict_list(result.provider_metadata.get("candidate_universe_gaps"))
    for item in result.candidate_observations:
        name = candidate_name(item)
        if name.lower() in allowed:
            accepted.append(item)
        elif name:
            gaps.append({
                "legal_name": name,
                "description": str(item.get("description") or ""),
                "source_refs": list(item.get("evidence_refs", [])) if isinstance(item.get("evidence_refs"), list) else [],
                "reason": "Signal task mentioned a new entity after candidate universe freeze.",
            })
    return result.model_copy(update={
        "candidate_observations": accepted,
        "provider_metadata": {**result.provider_metadata, "candidate_universe_gaps": gaps},
    })
