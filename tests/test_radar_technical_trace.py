from __future__ import annotations

import pytest

from power_web_os.application.radar.lifecycle.technical_trace import (
    MAX_TRACE_STRING_LENGTH,
    RadarRunTechnicalTraceCommand,
    RadarRunTechnicalTracer,
    TechnicalTraceRedactionError,
    TechnicalTraceRedactor,
)


def test_technical_trace_redactor_masks_secrets_and_caps_long_strings() -> None:
    payload, report = TechnicalTraceRedactor().sanitize(
        {
            "Authorization": "Bearer test-secret",
            "nested": {"api_key": "test-secret", "safe": "visible"},
            "long_text": "x" * (MAX_TRACE_STRING_LENGTH + 5),
        }
    )

    assert payload["Authorization"] == "[REDACTED]"
    assert payload["nested"]["api_key"] == "[REDACTED]"
    assert payload["nested"]["safe"] == "visible"
    assert str(payload["long_text"]).endswith("[TRUNCATED]")
    assert "$.Authorization" in report["masked_paths"]
    assert "$.nested.api_key" in report["masked_paths"]
    assert "$.long_text" in report["truncated_paths"]


def test_technical_trace_redactor_rejects_hidden_reasoning_keys() -> None:
    with pytest.raises(TechnicalTraceRedactionError, match="Hidden reasoning fields"):
        TechnicalTraceRedactor().sanitize({"hidden_reasoning": "do not store"})


def test_technical_tracer_appends_sanitized_payload_with_default_run_id() -> None:
    repository = _InMemoryTraceRepository()
    tracer = RadarRunTechnicalTracer(repository=repository, default_run_id="run-1")

    record = tracer.append(
        RadarRunTechnicalTraceCommand(
            run_id="",
            phase="provider",
            node_name="openrouter",
            trace_type="provider_request",
            title="Provider request",
            payload={"token": "secret-value", "model": "test"},
        )
    )

    assert record.run_id == "run-1"
    assert record.sequence == 1
    assert record.payload == {"token": "[REDACTED]", "model": "test"}
    assert repository.records == [record]


class _InMemoryTraceRepository:
    def __init__(self) -> None:
        self.records = []

    def append(self, record):
        self.records.append(record)
        return record

    def list_for_run(self, run_id: str):
        return tuple(record for record in self.records if record.run_id == run_id)

    def next_sequence(self, run_id: str) -> int:
        return len(self.list_for_run(run_id)) + 1
