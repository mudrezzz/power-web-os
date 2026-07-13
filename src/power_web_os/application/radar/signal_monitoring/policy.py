"""Normalization helpers for effective per-signal monitoring policy."""

from __future__ import annotations

from typing import Any

from power_web_os.application.radar.signal_monitoring.contracts import SignalMonitoringSourceLane


def bounded_policy_int(value: Any, *, default: int, low: int, high: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return min(max(parsed, low), high)


def signal_source_lanes(value: Any) -> list[SignalMonitoringSourceLane]:
    allowed: tuple[SignalMonitoringSourceLane, ...] = (
        "known_source", "official_company", "signal_specific", "open_web"
    )
    if not isinstance(value, list):
        return list(allowed)
    return [lane for lane in allowed if lane in value]
