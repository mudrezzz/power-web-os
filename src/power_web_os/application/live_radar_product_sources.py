"""Projection helpers for strict product source lists."""

from __future__ import annotations

from typing import Any

from power_web_os.application.live_radar_candidate_refs import candidate_source_refs
from power_web_os.application.live_radar_contracts import RadarSourceEvidence


def product_sources_for_candidates(
    *,
    sources: list[RadarSourceEvidence],
    candidates: list[dict[str, Any]],
) -> tuple[list[RadarSourceEvidence], list[dict[str, Any]]]:
    used_refs = candidate_source_refs(candidates)
    used = [source for source in sources if source.evidence_ref in used_refs]
    analyzed = [
        {
            "evidence_ref": source.evidence_ref,
            "title": source.title,
            "url": source.url,
            "query_id": source.query_id,
            "reason": "not_used_by_candidate",
            "verification_state": source.verification_state,
            "verification_mode": source.verification_mode,
            "verification_reason": source.verification_reason,
            "verification_status_code": source.verification_status_code,
        }
        for source in sources
        if source.evidence_ref not in used_refs
    ]
    return used, analyzed
