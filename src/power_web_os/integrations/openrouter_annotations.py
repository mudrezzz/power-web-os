"""Provider-neutral normalization of product-safe OpenRouter URL citations."""

from __future__ import annotations

from typing import Any


def normalized_openrouter_annotations(
    annotations: Any,
    *,
    source_ref_prefix: str = "retrieved",
) -> list[dict[str, Any]]:
    if not isinstance(annotations, list):
        return []
    result: list[dict[str, Any]] = []
    for rank, annotation in enumerate(annotations, start=1):
        if not isinstance(annotation, dict):
            continue
        url_info = annotation.get("url_citation") or annotation
        if not isinstance(url_info, dict) or not url_info.get("url"):
            continue
        result.append({
            "source_ref": f"{source_ref_prefix}_{rank}",
            "title": str(url_info.get("title") or url_info.get("url") or ""),
            "url": str(url_info.get("url") or ""),
            "snippet": str(url_info.get("content") or url_info.get("snippet") or ""),
            "rank": rank,
            "citation_index": rank,
            "raw_metadata": {
                "start_index": url_info.get("start_index"),
                "end_index": url_info.get("end_index"),
            },
        })
    return result
