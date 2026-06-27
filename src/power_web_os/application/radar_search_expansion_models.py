from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RadarExpansionTarget:
    target_id: str
    target_label: str
    target_type: str
    source_refs: list[str]
    why_target_exists: str
    priority: int
    allowed_source_ids: list[str]
    expected_fact_kinds: list[str]
    budget_reserve_key: str
    execution_status: str = "planned"
    not_searched_reason: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "target_id": self.target_id,
            "target_label": self.target_label,
            "target_type": self.target_type,
            "source_refs": list(self.source_refs),
            "why_target_exists": self.why_target_exists,
            "priority": self.priority,
            "allowed_source_ids": list(self.allowed_source_ids),
            "expected_fact_kinds": list(self.expected_fact_kinds),
            "budget_reserve_key": self.budget_reserve_key,
            "execution_status": self.execution_status,
            "not_searched_reason": self.not_searched_reason,
        }


@dataclass(frozen=True)
class RadarSearchExpansionVariant:
    query: str
    source_ids: list[str]
    source_scope: str
    reason: str
    expected_fact_kinds: list[str] = field(default_factory=list)
    target_id: str = ""
    target_type: str = ""
    budget_reserve_key: str = "recall_expansion"
    priority: int = 100

    def to_payload(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "source_ids": list(self.source_ids),
            "source_scope": self.source_scope,
            "reason": self.reason,
            "expected_fact_kinds": list(self.expected_fact_kinds),
            "target_id": self.target_id,
            "target_type": self.target_type,
            "budget_reserve_key": self.budget_reserve_key,
            "priority": self.priority,
        }


@dataclass(frozen=True)
class RadarSearchExpansionPlan:
    should_expand: bool
    variants: list[RadarSearchExpansionVariant]
    reason: str
    targets: list[RadarExpansionTarget] = field(default_factory=list)

    def to_payload(self) -> dict[str, Any]:
        variants = [item.to_payload() for item in self.variants]
        return {
            "should_expand": self.should_expand,
            "reason": self.reason,
            "targets": [item.to_payload() for item in self.targets],
            "variants": variants,
            "variants_by_target": variants_by_target(variants),
        }


@dataclass(frozen=True)
class _ExpansionSource:
    source_id: str
    source_type: str
    reference: str
    domain: str
    supports_official: bool
    supports_open_web: bool
    returned_fact_kinds: list[str]




def variants_by_target(variants: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for item in variants:
        target_id = str(item.get("target_id") or "unclassified")
        result.setdefault(target_id, []).append(item)
    return result
