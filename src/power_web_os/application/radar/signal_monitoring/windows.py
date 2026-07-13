"""Initial and incremental time-window policy for signal monitoring."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from power_web_os.application.radar.signal_monitoring.contracts import (
    SignalMonitoringInput,
    SignalMonitoringSignalRule,
    SignalMonitoringSourceLane,
    SignalMonitoringWatermark,
    SignalMonitoringWindow,
)


class SignalMonitoringWindowPolicy:
    """Resolve immutable per-candidate, criterion, and source-lane windows.

    Owns:
        Initial lookback precedence, incremental overlap, and watermark lookup.
    Does not own:
        Persistence, source selection, provider calls, or evidence decisions.
    Architecture:
        docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md
    """

    def resolve(
        self,
        *,
        monitoring_input: SignalMonitoringInput,
        candidate_id: str,
        rule: SignalMonitoringSignalRule,
        source_lane: SignalMonitoringSourceLane,
    ) -> SignalMonitoringWindow:
        as_of = _parse_timestamp(monitoring_input.as_of) or datetime.now(UTC)
        watermark = None
        if monitoring_input.lookback_basis != "explicit_override":
            watermark = self._watermark(
                monitoring_input.previous_watermarks,
                candidate_id=candidate_id,
                signal_code=rule.signal_code,
                source_lane=source_lane,
            )
        if watermark is not None:
            searched_through = _parse_timestamp(watermark.searched_through_at)
            if searched_through is not None:
                overlap = max(rule.incremental_overlap_days, 0)
                start = searched_through - timedelta(days=overlap)
                return SignalMonitoringWindow(
                    candidate_id=candidate_id,
                    signal_code=rule.signal_code,
                    source_lane=source_lane,
                    window_start=_iso(start),
                    window_end=_iso(as_of),
                    basis="incremental",
                    lookback_days=max((as_of.date() - start.date()).days, 1),
                    overlap_days=overlap,
                    previous_watermark=watermark.searched_through_at,
                )

        if monitoring_input.lookback_basis == "explicit_override":
            days = monitoring_input.lookback_days or 365
            basis = "explicit_override"
        elif rule.initial_lookback_days:
            days = rule.initial_lookback_days
            basis = "criterion_policy"
        else:
            days = monitoring_input.lookback_days or 365
            basis = monitoring_input.lookback_basis
        return SignalMonitoringWindow(
            candidate_id=candidate_id,
            signal_code=rule.signal_code,
            source_lane=source_lane,
            window_start=_iso(as_of - timedelta(days=days)),
            window_end=_iso(as_of),
            basis=basis,
            lookback_days=days,
        )

    @staticmethod
    def _watermark(
        watermarks: list[SignalMonitoringWatermark],
        *,
        candidate_id: str,
        signal_code: str,
        source_lane: SignalMonitoringSourceLane,
    ) -> SignalMonitoringWatermark | None:
        matches = [
            item
            for item in watermarks
            if item.candidate_id == candidate_id
            and item.signal_code == signal_code
            and item.source_lane == source_lane
        ]
        return max(matches, key=lambda item: item.searched_through_at, default=None)


def _parse_timestamp(value: str) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.replace(tzinfo=parsed.tzinfo or UTC).astimezone(UTC)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
