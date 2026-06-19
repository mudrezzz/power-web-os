"""Source URL verification for live Radar provider adapters.

This module owns HTTP reachability checks. Application services consume the
resulting verification metadata but do not import HTTP clients.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from power_web_os.application.live_radar_contracts import RadarSourceEvidence, SourceVerificationMode, SourceVerificationState


@dataclass(frozen=True, slots=True)
class SourceReachabilityResult:
    state: SourceVerificationState
    reason: str
    status_code: int | None = None


ReachabilityCheck = Callable[[str], SourceReachabilityResult]


def normalize_verification_mode(value: str | None) -> SourceVerificationMode:
    normalized = (value or "").strip().lower()
    if normalized in {"strict", "soft", "off"}:
        return normalized  # type: ignore[return-value]
    return "soft"


def verify_sources(
    sources: list[RadarSourceEvidence],
    *,
    mode: SourceVerificationMode,
    reachability_check: ReachabilityCheck | None = None,
) -> list[RadarSourceEvidence]:
    if mode == "off":
        return [
            source.model_copy(update={
                "verification_mode": mode,
                "verification_state": "not_checked",
                "verification_reason": "URL reachability check skipped by source verification mode.",
                "verification_status_code": None,
            })
            for source in sources
        ]
    checker = reachability_check or check_source_url
    verified = []
    for source in sources:
        result = checker(source.url)
        verified.append(source.model_copy(update={
            "verification_mode": mode,
            "verification_state": result.state,
            "verification_reason": result.reason,
            "verification_status_code": result.status_code,
        }))
    return verified


def supports_product_evidence(source: RadarSourceEvidence, *, mode: SourceVerificationMode) -> bool:
    if source.verification_state == "invalid_url":
        return False
    if mode == "strict":
        return source.verification_state == "reachable"
    return source.verification_state in {"reachable", "blocked", "timeout", "unverified_url", "not_checked"}


def source_has_verification_risk(source: RadarSourceEvidence) -> bool:
    return source.verification_state in {"blocked", "timeout", "unverified_url", "not_checked"}


def check_source_url(url: str) -> SourceReachabilityResult:
    if not url.startswith(("http://", "https://")):
        return SourceReachabilityResult(state="invalid_url", reason="Source URL is missing or is not HTTP(S).")
    try:
        import httpx
    except ImportError:  # pragma: no cover - OpenRouter provider already requires httpx.
        return SourceReachabilityResult(state="unverified_url", reason="httpx is unavailable for URL verification.")

    headers = {"User-Agent": "PowerWebOS-LiveRadar/0.7.6.1.7"}
    try:
        with httpx.Client(follow_redirects=True, timeout=12, headers=headers) as client:
            response = client.head(url)
            if response.status_code in {405, 403}:
                response = client.get(url)
            if response.status_code < 400:
                return SourceReachabilityResult(state="reachable", reason="URL returned a successful HTTP status.", status_code=response.status_code)
            if response.status_code in {401, 403, 429}:
                return SourceReachabilityResult(state="blocked", reason=f"URL returned blocking HTTP status {response.status_code}.", status_code=response.status_code)
            return SourceReachabilityResult(state="unverified_url", reason=f"URL returned HTTP status {response.status_code}.", status_code=response.status_code)
    except httpx.TimeoutException:
        return SourceReachabilityResult(state="timeout", reason="URL verification timed out.")
    except httpx.HTTPError as error:
        return SourceReachabilityResult(state="unverified_url", reason=f"URL verification failed: {error.__class__.__name__}.")
