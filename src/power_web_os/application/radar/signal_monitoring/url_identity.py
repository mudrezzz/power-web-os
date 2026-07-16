"""Stable product-safe URL identity for signal evidence and controls."""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit


_TRACKING_KEYS = {"erid", "gclid", "yclid"}


def canonical_signal_url(value: object) -> str:
    """Normalize source identity without collapsing different pages or queries."""

    raw = str(value or "").strip()
    if not raw:
        return ""
    parsed = urlsplit(raw)
    host = (parsed.hostname or "").removeprefix("www.").casefold()
    if not host:
        return raw.casefold().rstrip("/")
    scheme = (parsed.scheme or "https").casefold()
    port = f":{parsed.port}" if parsed.port else ""
    path = parsed.path.rstrip("/").casefold()
    query = urlencode(sorted(
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not _is_tracking_key(key)
    ))
    return f"{scheme}://{host}{port}{path}{f'?{query}' if query else ''}"


def signal_source_key(*, candidate_id: str, signal_code: str, url_or_ref: str) -> str:
    identity = canonical_signal_url(url_or_ref)
    return f"{candidate_id}|{signal_code}|{identity}" if identity else ""


def _is_tracking_key(value: str) -> bool:
    normalized = value.casefold()
    return normalized.startswith("utm_") or normalized in _TRACKING_KEYS
