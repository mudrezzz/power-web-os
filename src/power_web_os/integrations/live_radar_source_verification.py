"""Source URL verification for live Radar provider adapters.

This module owns HTTP reachability checks. Application services consume the
resulting verification metadata but do not import HTTP clients.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit
from typing import Callable

from power_web_os.application.live_radar_external_budget import reserve_external_call
from power_web_os.application.live_radar_contracts import RadarSourceEvidence, SourceVerificationMode, SourceVerificationState


@dataclass(frozen=True, slots=True)
class SourceReachabilityResult:
    state: SourceVerificationState
    reason: str
    status_code: int | None = None


ReachabilityCheck = Callable[[str], SourceReachabilityResult]


@dataclass(slots=True)
class SourceVerificationCache:
    results_by_url: dict[str, SourceReachabilityResult]
    unique_request_count: int = 0
    cache_hit_count: int = 0
    duplicate_skip_count: int = 0

    def to_metadata(self) -> dict[str, int]:
        return {
            "source_verification_unique_request_count": self.unique_request_count,
            "source_verification_cache_hit_count": self.cache_hit_count,
            "source_verification_duplicate_skip_count": self.duplicate_skip_count,
            "source_verification_cached_url_count": len(self.results_by_url),
        }


_current_verification_cache: ContextVar[SourceVerificationCache | None] = ContextVar(
    "radar_source_verification_cache",
    default=None,
)


@contextmanager
def source_verification_cache_context(cache: SourceVerificationCache | None = None):
    token = _current_verification_cache.set(cache or SourceVerificationCache(results_by_url={}))
    try:
        yield
    finally:
        _current_verification_cache.reset(token)


def current_source_verification_cache() -> SourceVerificationCache | None:
    return _current_verification_cache.get()


def source_verification_cache_metadata() -> dict[str, int]:
    cache = current_source_verification_cache()
    if cache is None:
        return SourceVerificationCache(results_by_url={}).to_metadata()
    return cache.to_metadata()


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
    cache = current_source_verification_cache()
    local_cache = cache or SourceVerificationCache(results_by_url={})
    for source in sources:
        normalized_url = _verification_cache_key(source.url)
        if normalized_url and normalized_url in local_cache.results_by_url:
            local_cache.cache_hit_count += 1
            local_cache.duplicate_skip_count += 1
            result = local_cache.results_by_url[normalized_url]
            verified.append(source.model_copy(update={
                "verification_mode": mode,
                "verification_state": result.state,
                "verification_reason": f"{result.reason} Reused cached verification result for duplicate URL.",
                "verification_status_code": result.status_code,
            }))
            continue
        decision = reserve_external_call(
            "source_verification",
            key=source.evidence_ref or source.url or "source",
            task_id=source.query_id or "",
        )
        if not decision.accepted:
            result = SourceReachabilityResult(
                state="not_checked",
                reason=decision.message or "Source verification skipped by external-call budget.",
                status_code=None,
            )
            if normalized_url:
                local_cache.results_by_url[normalized_url] = result
            verified.append(source.model_copy(update={
                "verification_mode": mode,
                "verification_state": result.state,
                "verification_reason": result.reason,
                "verification_status_code": result.status_code,
            }))
            continue
        result = checker(source.url)
        local_cache.unique_request_count += 1
        if normalized_url:
            local_cache.results_by_url[normalized_url] = result
        verified.append(source.model_copy(update={
            "verification_mode": mode,
            "verification_state": result.state,
            "verification_reason": result.reason,
            "verification_status_code": result.status_code,
        }))
    return verified


def _verification_cache_key(url: str) -> str:
    value = (url or "").strip()
    if not value:
        return ""
    try:
        parsed = urlsplit(value)
    except ValueError:
        return value.casefold()
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return value.casefold()
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, parsed.query, ""))


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
