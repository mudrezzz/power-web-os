"""OpenRouter retrieval-result mapping for live Radar provider traces."""

from __future__ import annotations

from typing import Any

from power_web_os.application.live_radar_web_retrieval import (
    RadarRetrievalSourceOutcome,
    RadarRetrievedSource,
    RadarWebRetrievalResult,
)


def retrieval_result_from_openrouter_response(
    payload: dict[str, Any],
    *,
    provider_id: str,
    engine: str,
    query: str,
) -> RadarWebRetrievalResult:
    message = payload.get("choices", [{}])[0].get("message", {})
    annotations = message.get("annotations", [])
    sources = _sources_from_annotations(annotations, provider_id=provider_id, engine=engine)
    return RadarWebRetrievalResult(
        provider_id=provider_id,
        engine=engine,
        status="retrieved" if sources else "empty",
        query=query,
        retrieved_sources=sources,
        source_outcomes=[
            RadarRetrievalSourceOutcome(
                source_ref=source.source_ref,
                outcome="retrieved",
                reason="Provider returned this source as a web citation.",
                provider_id=provider_id,
                engine=engine,
            )
            for source in sources
        ],
        provider_metadata={"annotation_count": len(annotations) if isinstance(annotations, list) else 0},
    )


def _sources_from_annotations(
    annotations: Any,
    *,
    provider_id: str,
    engine: str,
) -> list[RadarRetrievedSource]:
    if not isinstance(annotations, list):
        return []
    sources: list[RadarRetrievedSource] = []
    for rank, annotation in enumerate(annotations, start=1):
        if not isinstance(annotation, dict):
            continue
        url_info = annotation.get("url_citation") or annotation
        if not isinstance(url_info, dict) or not url_info.get("url"):
            continue
        sources.append(RadarRetrievedSource(
            source_ref=f"retrieved_{rank}",
            title=str(url_info.get("title") or url_info.get("url") or ""),
            url=str(url_info.get("url") or ""),
            snippet=str(url_info.get("content") or url_info.get("snippet") or ""),
            rank=rank,
            citation_index=rank,
            provider_id=provider_id,
            engine=engine,
            raw_metadata={
                "start_index": url_info.get("start_index"),
                "end_index": url_info.get("end_index"),
            },
        ))
    return sources
