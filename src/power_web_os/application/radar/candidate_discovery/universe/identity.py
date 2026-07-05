"""Candidate identity helpers for candidate-discovery universe records."""

from __future__ import annotations

import re
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


def candidate_name_set(observations: list[dict[str, Any]]) -> set[str]:
    return {name.lower() for item in observations for name in [candidate_name(item)] if name}


def candidate_name(item: dict[str, Any]) -> str:
    return str(item.get("legal_name") or item.get("name") or "").strip()


def first_task_id(tasks: list[Any]) -> str:
    return str(tasks[0].task_id) if tasks else ""


def source_refs(item: dict[str, Any]) -> list[str]:
    return [str(ref) for ref in item.get("source_refs", []) if str(ref).strip()] if isinstance(item.get("source_refs"), list) else []


def stable_id(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9а-яА-ЯёЁ]+", "-", value.lower()).strip("-")
    return normalized or "candidate"
