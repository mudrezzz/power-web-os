"""Bounded product-safe publication metadata extraction for signal sources."""

from __future__ import annotations

from html import unescape
import json
import re
from typing import Any

import httpx

from power_web_os.application.radar.signal_monitoring.contracts import (
    SignalSourceRef,
    SignalSourceTemporalMetadata,
)


class HttpSignalSourceMetadataProvider:
    """Fetch one page and return dates only, never raw HTML or headers."""

    def __init__(self, *, timeout_seconds: float = 8.0) -> None:
        self._timeout = timeout_seconds

    def resolve(self, source: SignalSourceRef) -> SignalSourceTemporalMetadata:
        response = httpx.get(
            source.url,
            timeout=self._timeout,
            follow_redirects=True,
            headers={"User-Agent": "PowerWebOS-SignalMetadata/1.0"},
        )
        response.raise_for_status()
        candidates = _date_candidates(response.text)
        if not candidates:
            return SignalSourceTemporalMetadata(source_ref=source.source_ref)
        top_priority = min(item[0] for item in candidates)
        preferred = [item for item in candidates if item[0] == top_priority]
        unique = list(dict.fromkeys(item[1] for item in preferred))
        basis = preferred[0][2]
        if len(unique) > 1:
            return SignalSourceTemporalMetadata(
                source_ref=source.source_ref,
                date_basis=basis,  # type: ignore[arg-type]
                date_evidence="; ".join(unique[:3]),
                conflicting=True,
            )
        return SignalSourceTemporalMetadata(
            source_ref=source.source_ref,
            published_at=unique[0],
            date_basis=basis,  # type: ignore[arg-type]
            date_confidence="strong" if top_priority <= 2 else "medium",
            date_evidence=unique[0],
        )


def _date_candidates(html: str) -> list[tuple[int, str, str]]:
    result: list[tuple[int, str, str]] = []
    for raw in re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        try:
            payload = json.loads(unescape(raw).strip())
        except (json.JSONDecodeError, ValueError):
            continue
        for value in _json_values(payload, "datePublished"):
            if normalized := _normalize_date(value):
                result.append((1, normalized, "json_ld"))
    for match in re.finditer(r'<meta\s+([^>]+)>', html, flags=re.IGNORECASE):
        attrs = match.group(1)
        key = _attribute(attrs, "property") or _attribute(attrs, "name")
        if str(key).casefold() not in {"article:published_time", "date", "datepublished", "publish_date"}:
            continue
        if normalized := _normalize_date(_attribute(attrs, "content")):
            result.append((2, normalized, "open_graph"))
    for match in re.finditer(r'<time\s+([^>]+)>', html, flags=re.IGNORECASE):
        if normalized := _normalize_date(_attribute(match.group(1), "datetime")):
            result.append((3, normalized, "html_time"))
    if not result:
        class_date = re.search(
            r'class=["\'][^"\']*(?:article-date|info-date|publish-date|news-date)[^"\']*["\'][^>]*>\s*([^<]{6,40})',
            html,
            flags=re.IGNORECASE,
        )
        if class_date and (normalized := _normalize_date(class_date.group(1))):
            result.append((4, normalized, "html_time"))
    return result


def _json_values(value: Any, key: str) -> list[str]:
    result: list[str] = []
    if isinstance(value, dict):
        for item_key, item in value.items():
            if item_key == key and isinstance(item, str):
                result.append(item)
            else:
                result.extend(_json_values(item, key))
    elif isinstance(value, list):
        for item in value:
            result.extend(_json_values(item, key))
    return result


def _attribute(attrs: str, name: str) -> str:
    match = re.search(rf'\b{name}\s*=\s*["\']([^"\']*)["\']', attrs, flags=re.IGNORECASE)
    return unescape(match.group(1)).strip() if match else ""


def _normalize_date(value: object) -> str:
    text = str(value or "").strip()
    match = re.search(r"(20\d{2})-(0[1-9]|1[0-2])-([0-2]\d|3[01])", text)
    if match:
        return "-".join(match.groups())
    match = re.search(r"([0-2]?\d|3[01])\.(0?[1-9]|1[0-2])\.(20\d{2})", text)
    if match:
        return f"{match.group(3)}-{int(match.group(2)):02d}-{int(match.group(1)):02d}"
    month_names = {
        name.casefold(): index
        for index, name in enumerate(
            ("", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
        )
        if name
    }
    match = re.search(r"([0-2]?\d|3[01])-([A-Za-z]{3})-(20\d{2})", text)
    if match and match.group(2).casefold() in month_names:
        return f"{match.group(3)}-{month_names[match.group(2).casefold()]:02d}-{int(match.group(1)):02d}"
    return ""
