from __future__ import annotations

from power_web_os.application.radar.signal_monitoring.contracts import SignalSearchTask, SignalSourceRef
from power_web_os.application.radar.signal_monitoring.evidence import SignalEvidenceValidationService
from power_web_os.application.radar.signal_monitoring.payloads import ParsedSignalPayload, parse_payload
from power_web_os.integrations.openrouter_signal_monitoring import (
    OpenRouterSignalMonitoringProvider,
    _normalized_signal_sources,
    _task_scoped_signal_payload,
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


def test_provider_local_source_refs_are_namespaced_by_task_before_merge() -> None:
    first_task = SignalSearchTask(
        task_id="task-a",
        candidate_id="candidate-a",
        candidate_name="Candidate A",
        signal_code="S1",
        signal_label="Maintenance",
        query="Candidate A maintenance",
        lookback_days=365,
    )
    second_task = first_task.model_copy(update={"task_id": "task-b", "candidate_id": "candidate-b"})
    payload = {
        "sources": [{"source_ref": "source_1", "url": "https://example.test/news"}],
        "observations": [{"evidence_refs": ["source_1"]}],
    }

    first = _task_scoped_signal_payload(payload, task=first_task)
    second = _task_scoped_signal_payload(payload, task=second_task)

    assert first["sources"][0]["source_ref"] == "task-a:source_1"
    assert first["observations"][0]["evidence_refs"] == ["task-a:source_1"]
    assert second["sources"][0]["source_ref"] == "task-b:source_1"
    assert second["observations"][0]["evidence_refs"] == ["task-b:source_1"]
    assert first["sources"][0]["source_ref"] != second["sources"][0]["source_ref"]


def test_task_scoping_preserves_known_source_contract_refs() -> None:
    task = SignalSearchTask(
        task_id="task-known",
        candidate_id="candidate-a",
        candidate_name="Candidate A",
        signal_code="S1",
        signal_label="Maintenance",
        query="Candidate A maintenance",
        lookback_days=365,
        source_contracts=[SignalSourceRef(source_ref="known-a", url="https://example.test/news")],
    )

    result = _task_scoped_signal_payload({
        "sources": [{"source_ref": "known-a", "url": "https://example.test/news"}],
        "observations": [{"evidence_refs": ["known-a"]}],
    }, task=task)

    assert result["sources"][0]["source_ref"] == "known-a"
    assert result["observations"][0]["evidence_refs"] == ["known-a"]


def test_open_web_xlsx_is_review_only() -> None:
    task = SignalSearchTask(
        task_id="task-xlsx",
        candidate_id="candidate-a",
        candidate_name="Candidate A",
        signal_code="maintenance",
        signal_label="Maintenance",
        query="Candidate A maintenance",
        lookback_days=365,
        window_start="2025-07-16T00:00:00Z",
        window_end="2026-07-16T00:00:00Z",
    )
    parsed = parse_payload({
        "sources": [{
            "source_ref": "registry-xlsx",
            "title": "Candidate A registry export",
            "url": "https://example.test/export/candidate-a.xlsx",
            "snippet": "Candidate A maintenance row.",
            "published_at": "2026-06-01",
        }],
        "observations": [{
            "candidate_id": "candidate-a",
            "signal_code": "maintenance",
            "status": "observed",
            "summary": "Candidate A maintenance row.",
            "score": 2,
            "evidence_refs": ["registry-xlsx"],
            "event_at": "2026-06-01",
        }],
    })
    assert isinstance(parsed, ParsedSignalPayload)

    observation, record = SignalEvidenceValidationService().validate(
        task=task,
        parsed=parsed,
        previous_fingerprints=set(),
        previous_source_keys=set(),
    )

    assert record.accepted is False
    assert record.reason == "source_capability_not_fresh_signal_capable"
    assert observation.observation_status == "unclear"
    assert observation.score == 0
