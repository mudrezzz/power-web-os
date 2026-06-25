"""Helpers for source-reference extraction from Radar candidate payloads."""

from __future__ import annotations

from typing import Any


def candidate_source_refs(candidates: list[dict[str, Any]]) -> set[str]:
    refs: set[str] = set()
    for candidate in candidates:
        refs.update(str(ref) for ref in candidate.get("evidence_refs", []) if isinstance(ref, str))
        for section_name in ("qualification", "signals"):
            for item in candidate.get(section_name, []):
                if not isinstance(item, dict):
                    continue
                refs.update(str(ref) for ref in item.get("evidence_refs", []) if isinstance(ref, str))
                refs.update(str(usage.get("source_ref", "")) for usage in item.get("source_usages", []) if isinstance(usage, dict))
                refs.update(str(finding.get("source_ref", "")) for finding in item.get("evidence_findings", []) if isinstance(finding, dict))
    return {ref for ref in refs if ref}
