"""Signal execution mode contract for candidate-discovery runs."""

from __future__ import annotations

from typing import Any, Literal

CandidateDiscoverySignalExecutionMode = Literal["handoff", "inline_compatibility"]


def _normalize_signal_execution_mode(value: Any) -> CandidateDiscoverySignalExecutionMode:
    text = str(value or "").strip().lower()
    if text == "inline_compatibility":
        return "inline_compatibility"
    return "handoff"
