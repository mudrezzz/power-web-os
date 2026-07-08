"""Candidate-discovery reconciliation helpers for Radar evaluation reports."""

from __future__ import annotations

from typing import Any


def candidate_discovery_reconciliation(dossier: dict[str, Any]) -> dict[str, Any]:
    reconciliation = _dict(dossier.get("candidate_discovery_reconciliation"))
    if reconciliation:
        ledger = product_acceptance_ledger(dossier)
        product_candidate_count = _product_candidate_count(ledger) or int(reconciliation.get("product_candidate_count") or 0)
        normalized = dict(reconciliation)
        normalized["product_candidate_zero_explained"] = product_candidate_count == 0 and bool(
            normalized.get("product_candidate_zero_explained")
        )
        return normalized
    ledger = product_acceptance_ledger(dossier)
    if not ledger:
        return {}
    unexplained = _unexplained_rows(ledger)
    product_candidate_count = _product_candidate_count(ledger)
    return {
        "ledger_entry_count": len(ledger),
        "unexplained_drop_count": len(unexplained),
        "product_candidate_zero_explained": product_candidate_count == 0 and all(
            str(item.get("product_acceptance_reason") or "").strip()
            for item in ledger
            if str(item.get("product_acceptance_status") or "") != "product_candidate"
        ),
    }


def product_acceptance_ledger(dossier: dict[str, Any]) -> list[dict[str, Any]]:
    ledger = _list(dossier.get("product_acceptance_ledger"))
    if ledger:
        return ledger
    rows: list[dict[str, Any]] = []
    for collection_name in ("candidates", "candidate_universe"):
        for item in _list(dossier.get(collection_name)):
            name = _first_string(item, "legal_name", "name", "entity_name")
            if not name:
                continue
            product_status = str(item.get("product_acceptance_status") or "")
            public_status = str(item.get("public_result_status") or "")
            rows.append({
                "legal_name": name,
                "collection": collection_name,
                "upstream_discovery_outcome": str(item.get("upstream_discovery_outcome") or ""),
                "product_acceptance_status": product_status,
                "product_acceptance_reason": str(
                    item.get("product_acceptance_reason") or _fallback_product_acceptance_reason(product_status)
                ),
                "public_result_status": public_status or _fallback_public_result_status(collection_name),
                "public_projection_reason": str(
                    item.get("public_projection_reason")
                    or _fallback_public_projection_reason(collection_name, product_status)
                ),
                "source_refs": sorted(_source_refs(item)),
            })
    return rows


def _unexplained_rows(ledger: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        item for item in ledger
        if not str(item.get("public_result_status") or "").strip()
        or not str(item.get("public_projection_reason") or "").strip()
        or not str(item.get("product_acceptance_reason") or "").strip()
    ]


def _product_candidate_count(ledger: list[dict[str, Any]]) -> int:
    return len({
        str(item.get("legal_name") or "").casefold()
        for item in ledger
        if str(item.get("product_acceptance_status") or "") == "product_candidate"
        and str(item.get("legal_name") or "").strip()
    })


def _fallback_product_acceptance_reason(product_status: str) -> str:
    if product_status == "product_candidate":
        return "deterministic_qualification_and_upstream_evidence_passed"
    if product_status == "review_required":
        return "requires_human_review_before_product_acceptance"
    return "insufficient_product_acceptance_evidence"


def _fallback_public_result_status(collection_name: str) -> str:
    if collection_name == "candidates":
        return "public_candidate"
    return "retained_in_candidate_universe"


def _fallback_public_projection_reason(collection_name: str, product_status: str) -> str:
    if collection_name == "candidates":
        return "promoted_to_public_candidate_row"
    if product_status == "product_candidate":
        return "product_candidate_retained_outside_public_page"
    return "requires_review_before_public_candidate_row"


def _source_refs(payload: Any) -> set[str]:
    refs: set[str] = set()
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in {"source_ref", "source_refs", "evidence_ref", "evidence_refs"}:
                if isinstance(value, str):
                    refs.add(value)
                elif isinstance(value, list):
                    refs.update(str(item) for item in value if item)
            elif isinstance(value, (dict, list)):
                refs.update(_source_refs(value))
    elif isinstance(payload, list):
        for item in payload:
            refs.update(_source_refs(item))
    return refs


def _first_string(payload: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []
