"""Collection helpers shared by live Radar normalization and execution."""

from __future__ import annotations

from power_web_os.application.live_radar_contracts import LiveRadarCandidate, RadarSourceEvidence


def rank_candidates(candidates: list[LiveRadarCandidate]) -> list[LiveRadarCandidate]:
    return sorted(
        candidates,
        key=lambda item: (-item.score.fit_score, -item.score.intent_score, item.legal_name),
    )


def dedupe_sources(sources: list[RadarSourceEvidence]) -> list[RadarSourceEvidence]:
    seen: set[tuple[str, str]] = set()
    result = []
    for source in sources:
        key = (source.evidence_ref, source.url)
        if key in seen:
            continue
        seen.add(key)
        result.append(source)
    return result
