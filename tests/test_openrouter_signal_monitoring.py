from __future__ import annotations

from power_web_os.application.radar.signal_monitoring.contracts import SignalSearchTask, SignalSourceRef
from power_web_os.integrations.openrouter_signal_monitoring import (
    OpenRouterSignalMonitoringProvider,
    _normalized_signal_sources,
)


def test_openrouter_signal_request_exposes_lane_window_and_safe_source_contract() -> None:
    provider = OpenRouterSignalMonitoringProvider(model_id="test/model", api_key="test-key")
    task = SignalSearchTask(
        task_id="task-known",
        candidate_id="candidate-a",
        candidate_name="Candidate A",
        signal_code="S1",
        signal_label="Modernization",
        query="Candidate A modernization https://candidate.test/news",
        lookback_days=365,
        source_lane="known_source",
        source_contracts=[SignalSourceRef(
            source_ref="known-a",
            source_id="candidate-site",
            title="Candidate news",
            url="https://candidate.test/news",
            snippet="Official company news archive.",
        )],
        window_start="2025-07-10T00:00:00Z",
        window_end="2026-07-10T00:00:00Z",
    )

    request = provider._request(task=task, attempt_role="primary")
    task_card = request["messages"][1]["content"]

    assert "https://candidate.test/news" in task_card
    assert "Candidate news" in task_card
    assert "known_source" in task_card
    assert "2025-07-10T00:00:00Z" in task_card
    assert "event_at" in task_card
    assert "published_at" in task_card
    assert "retrieved_at only for retrieval audit" in task_card
    assert "test-key" not in task_card


def test_openrouter_signal_sources_normalize_nullable_provider_fields() -> None:
    sources = _normalized_signal_sources([{
        "source_ref": "source-a",
        "title": "News",
        "url": "https://example.test/news",
        "source_id": None,
    }])

    assert sources[0].source_ref == "source-a"
    assert sources[0].source_id == ""
