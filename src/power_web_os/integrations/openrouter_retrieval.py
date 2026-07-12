"""OpenRouter retrieval-result mapping for live Radar provider traces."""

from __future__ import annotations

from typing import Any

from power_web_os.application.radar.candidate_discovery.retrieval.web_retrieval import (
    RadarRetrievalSourceOutcome,
    RadarRetrievedSource,
    RadarWebRetrievalResult,
)
from power_web_os.integrations.openrouter_annotations import normalized_openrouter_annotations


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
    sources: list[RadarRetrievedSource] = []
    for item in normalized_openrouter_annotations(annotations):
        sources.append(RadarRetrievedSource(
            source_ref=str(item["source_ref"]),
            title=str(item["title"]),
            url=str(item["url"]),
            snippet=str(item["snippet"]),
            rank=int(item["rank"]),
            citation_index=int(item["citation_index"]),
            provider_id=provider_id,
            engine=engine,
            raw_metadata=dict(item["raw_metadata"]),
        ))
    return sources
