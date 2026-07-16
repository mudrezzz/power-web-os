"""Series-scoped incremental history for Signal Monitoring."""

from __future__ import annotations

import re
from typing import Iterable

from power_web_os.application.radar.signal_monitoring.contracts import SignalMonitoringWatermark
from power_web_os.application.radar.signal_monitoring.url_identity import canonical_signal_url
from power_web_os.application.radar.lifecycle.records import SignalMonitoringRunOutputRecord


def normalize_monitoring_series_id(value: str) -> str:
    normalized = str(value or "default").strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", normalized):
        raise ValueError("monitoring_series_id must be 1..128 safe ASCII characters.")
    return normalized


def outputs_for_series(
    outputs: Iterable[SignalMonitoringRunOutputRecord],
    series_id: str,
) -> list[SignalMonitoringRunOutputRecord]:
    return [
        output
        for output in outputs
        if str(output.artifact_payload.get("monitoring_series_id") or "default") == series_id
    ]


def previous_fingerprints(outputs: Iterable[SignalMonitoringRunOutputRecord]) -> list[str]:
    return sorted({
        fingerprint
        for output in outputs
        for observation in _dict_list(output.artifact_payload.get("observations"))
        if (fingerprint := str(observation.get("fingerprint") or "").strip())
    })


def previous_watermarks(outputs: Iterable[SignalMonitoringRunOutputRecord]) -> list[SignalMonitoringWatermark]:
    by_key: dict[tuple[str, str, str], SignalMonitoringWatermark] = {}
    for output in outputs:
        for raw in _dict_list(output.artifact_payload.get("watermarks_after")):
            try:
                item = SignalMonitoringWatermark.model_validate(raw)
            except ValueError:
                continue
            key = (item.candidate_id, item.signal_code, item.source_lane)
            previous = by_key.get(key)
            if previous is None or item.searched_through_at > previous.searched_through_at:
                by_key[key] = item
    return sorted(by_key.values(), key=lambda item: (item.candidate_id, item.signal_code, item.source_lane))


def previous_source_keys(outputs: Iterable[SignalMonitoringRunOutputRecord]) -> list[str]:
    keys: set[str] = set()
    for output in outputs:
        observations = [
            *_dict_list(output.artifact_payload.get("observations")),
            *_dict_list(output.artifact_payload.get("task_observations")),
        ]
        for observation in observations:
            search_status = str(observation.get("search_status") or "")
            observation_status = str(observation.get("observation_status") or "")
            if observation_status != "observed" and search_status not in {
                "review_needed_date_unknown",
                "review_needed_date_conflict",
                "duplicate_existing_review",
            }:
                continue
            candidate_id = str(observation.get("candidate_id") or "")
            signal_code = str(observation.get("signal_code") or "")
            for source in _dict_list(observation.get("sources")):
                url = canonical_signal_url(str(source.get("url") or ""))
                if candidate_id and signal_code and url:
                    keys.add(f"{candidate_id}|{signal_code}|{url}")
    return sorted(keys)


def _dict_list(value: object) -> list[dict[str, object]]:
    return [dict(item) for item in value if isinstance(item, dict)] if isinstance(value, list) else []
