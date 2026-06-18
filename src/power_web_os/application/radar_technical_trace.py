"""Sanitized developer trace support for live Radar runs.

The trace is an admin/debug artifact, not a product explanation and not raw
hidden chain-of-thought. It stores bounded, redacted inputs and outputs that help
debug the planner/provider/normalizer pipeline.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Iterator

from power_web_os.application.ports import RadarRunTechnicalTraceRepository
from power_web_os.application.radar_records import RadarRunTechnicalTraceRecord

FORBIDDEN_REASONING_KEYS = {"chain_of_thought", "hidden_reasoning", "internal_thoughts"}
SECRET_MARKERS = ("authorization", "api_key", "token", "bearer", "secret", "password", "openrouter_api_key")
MAX_TRACE_STRING_LENGTH = 12000


class TechnicalTraceRedactionError(ValueError):
    """Raised when a trace payload tries to store forbidden hidden reasoning."""


@dataclass(frozen=True, slots=True)
class RadarRunTechnicalTraceCommand:
    run_id: str
    phase: str
    node_name: str
    trace_type: str
    title: str
    summary: str = ""
    duration_ms: int | None = None
    payload: dict[str, Any] = field(default_factory=dict)


class TechnicalTraceRedactor:
    """Masks secrets and caps payload size before trace persistence."""

    def sanitize(self, payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        report: dict[str, Any] = {
            "masked_paths": [],
            "truncated_paths": [],
            "rejected_reasoning_keys": [],
        }
        sanitized = self._sanitize_value(payload, path="$", report=report)
        if report["rejected_reasoning_keys"]:
            keys = ", ".join(report["rejected_reasoning_keys"])
            raise TechnicalTraceRedactionError(f"Hidden reasoning fields are not allowed in technical traces: {keys}")
        return dict(sanitized), report

    def _sanitize_value(self, value: Any, *, path: str, report: dict[str, Any]) -> Any:
        if isinstance(value, dict):
            result: dict[str, Any] = {}
            for key, item in value.items():
                normalized_key = str(key).lower()
                child_path = f"{path}.{key}"
                if normalized_key in FORBIDDEN_REASONING_KEYS:
                    report["rejected_reasoning_keys"].append(child_path)
                    continue
                if _looks_secret_key(normalized_key):
                    result[str(key)] = "[REDACTED]"
                    report["masked_paths"].append(child_path)
                    continue
                result[str(key)] = self._sanitize_value(item, path=child_path, report=report)
            return result
        if isinstance(value, list):
            return [self._sanitize_value(item, path=f"{path}[{index}]", report=report) for index, item in enumerate(value)]
        if isinstance(value, str):
            if _looks_secret_value(value):
                report["masked_paths"].append(path)
                return "[REDACTED]"
            if len(value) > MAX_TRACE_STRING_LENGTH:
                report["truncated_paths"].append(path)
                return f"{value[:MAX_TRACE_STRING_LENGTH]} [TRUNCATED]"
        return value


class RadarRunTechnicalTracer:
    """Append-only technical trace writer with mandatory redaction."""

    def __init__(
        self,
        *,
        repository: RadarRunTechnicalTraceRepository,
        default_run_id: str | None = None,
        redactor: TechnicalTraceRedactor | None = None,
    ) -> None:
        self._repository = repository
        self._default_run_id = default_run_id
        self._redactor = redactor or TechnicalTraceRedactor()

    def append(self, command: RadarRunTechnicalTraceCommand) -> RadarRunTechnicalTraceRecord:
        run_id = command.run_id or self._default_run_id
        if not run_id:
            raise ValueError("Technical trace run_id is required")
        payload, report = self._redactor.sanitize(command.payload)
        meta, meta_report = self._redactor.sanitize({"title": command.title, "summary": command.summary})
        _merge_report(report, meta_report)
        sequence = self._repository.next_sequence(run_id)
        record = RadarRunTechnicalTraceRecord(
            trace_id=f"{run_id}:trace:{sequence:06d}",
            run_id=run_id,
            sequence=sequence,
            phase=command.phase,
            node_name=command.node_name,
            trace_type=command.trace_type,
            title=str(meta.get("title", "")),
            summary=str(meta.get("summary", "")),
            duration_ms=command.duration_ms,
            payload=payload,
            redaction_report=report,
        )
        return self._repository.append(record)


_current_tracer: ContextVar[RadarRunTechnicalTracer | None] = ContextVar("radar_run_technical_tracer", default=None)


def current_technical_tracer() -> RadarRunTechnicalTracer | None:
    return _current_tracer.get()


@contextmanager
def technical_trace_context(tracer: RadarRunTechnicalTracer | None) -> Iterator[None]:
    token = _current_tracer.set(tracer)
    try:
        yield
    finally:
        _current_tracer.reset(token)


def append_current_trace(command: RadarRunTechnicalTraceCommand) -> None:
    tracer = current_technical_tracer()
    if tracer is None:
        return
    tracer.append(command)


def _looks_secret_key(value: str) -> bool:
    return any(marker in value for marker in SECRET_MARKERS)


def _looks_secret_value(value: str) -> bool:
    lowered = value.lower()
    return (
        "bearer " in lowered
        or "openrouter_api_key" in lowered
        or lowered.startswith(("sk-", "sk_or_"))
        or "authorization:" in lowered
        or "api_key=" in lowered
        or "token=" in lowered
        or "password=" in lowered
    )


def _merge_report(target: dict[str, Any], source: dict[str, Any]) -> None:
    for key, value in source.items():
        if isinstance(value, list):
            target.setdefault(key, []).extend(value)
