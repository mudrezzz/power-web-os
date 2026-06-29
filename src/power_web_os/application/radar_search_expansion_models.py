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
    target_origin: str = "unknown"
    completion_rank_reason: str = ""
    deprioritized_reason: str = ""
    uncovered_baseline_target: bool = False
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
            "target_origin": self.target_origin,
            "completion_rank_reason": self.completion_rank_reason,
            "deprioritized_reason": self.deprioritized_reason,
            "uncovered_baseline_target": self.uncovered_baseline_target,
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
    target_origin: str = "unknown"
    completion_rank_reason: str = ""
    deprioritized_reason: str = ""
    uncovered_baseline_target: bool = False

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
            "target_origin": self.target_origin,
            "completion_rank_reason": self.completion_rank_reason,
            "deprioritized_reason": self.deprioritized_reason,
            "uncovered_baseline_target": self.uncovered_baseline_target,
        }


@dataclass(frozen=True)
class RadarSearchExpansionPlan:
    should_expand: bool
    variants: list[RadarSearchExpansionVariant]
    reason: str
    targets: list[RadarExpansionTarget] = field(default_factory=list)
    selection_summary: dict[str, Any] = field(default_factory=dict)
    selection_diagnostics: list[dict[str, Any]] = field(default_factory=list)

    def to_payload(self) -> dict[str, Any]:
        variants = [item.to_payload() for item in self.variants]
        target_payloads = [item.to_payload() for item in self.targets]
        return {
            "should_expand": self.should_expand,
            "reason": self.reason,
            "targets": target_payloads,
            "targets_by_type": targets_by_type(target_payloads),
            "variants": variants,
            "variants_by_target": variants_by_target(variants),
            "variants_by_target_type": variants_by_target_type(variants),
            "selection_summary": dict(self.selection_summary),
            "selection_diagnostics": [dict(item) for item in self.selection_diagnostics],
            "targets_not_selected": targets_not_selected(target_payloads, variants, self.selection_diagnostics),
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


def variants_by_target_type(variants: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for item in variants:
        target_type = str(item.get("target_type") or "unknown")
        result.setdefault(target_type, []).append(item)
    return result


def targets_by_type(targets: list[dict[str, Any]]) -> dict[str, int]:
    result: dict[str, int] = {}
    for item in targets:
        target_type = str(item.get("target_type") or "unknown")
        result[target_type] = result.get(target_type, 0) + 1
    return result


def targets_not_selected(
    targets: list[dict[str, Any]],
    variants: list[dict[str, Any]],
    diagnostics: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    selected_ids = {str(item.get("target_id") or "") for item in variants if str(item.get("target_id") or "")}
    diagnostics_by_target = {
        str(item.get("target_id") or ""): item
        for item in diagnostics or []
        if str(item.get("target_id") or "")
    }
    result: list[dict[str, Any]] = []
    for item in targets:
        target_id = str(item.get("target_id") or "")
        if not target_id or target_id in selected_ids:
            continue
        diagnostic = diagnostics_by_target.get(target_id, {})
        result.append({
            **item,
            "execution_status": "not_searched",
            "not_searched_reason": str(diagnostic.get("reason") or "not_selected"),
            "selection_diagnostic": dict(diagnostic) if diagnostic else {},
        })
    return result
