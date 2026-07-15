"""Pipeline-neutral source usage obligation values."""

from __future__ import annotations

from typing import Any

SourceUsageObligation = str

SOURCE_USAGE_OBLIGATIONS = {
    "required",
    "preferred",
    "optional",
    "fallback",
    "disabled",
    "required_for_identity",
    "required_for_coverage",
    "required_for_signal",
}
REQUIRED_OBLIGATIONS = {"required", "required_for_identity", "required_for_coverage", "required_for_signal"}


def source_usage_obligation(source: dict[str, Any]) -> SourceUsageObligation:
    value = str(source.get("usage_obligation") or source.get("usage_mode") or "preferred").strip().lower()
    return value if value in SOURCE_USAGE_OBLIGATIONS else "preferred"
