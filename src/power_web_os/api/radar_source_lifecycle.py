"""Source lifecycle projection helpers for Radar dossier responses."""

from __future__ import annotations

from typing import Any

from power_web_os.api.radar_dtos import (
    RadarRunDossierSourceLifecycleItemResponse,
    RadarRunDossierSourceLifecycleSummaryResponse,
    RadarRunDossierSourceUsageResponse,
)


def source_lifecycle(
    *,
    sources: list[dict[str, Any]],
    execution_results: dict[str, Any],
    source_usage_index: dict[str, list[RadarRunDossierSourceUsageResponse]],
) -> list[RadarRunDossierSourceLifecycleItemResponse]:
    items: dict[str, RadarRunDossierSourceLifecycleItemResponse] = {}
    extraction_state = _extraction_validation_state(execution_results)
    for source in sources:
        evidence_ref = str(source.get("evidence_ref", "")).strip()
        if not evidence_ref:
            continue
        usages = source_usage_index.get(evidence_ref, [])
        reason = "used_by_candidate" if usages else "missing_evidence_ref"
        _upsert_source_lifecycle(
            items,
            _source_lifecycle_item(
                source,
                evidence_ref=evidence_ref,
                state="used" if usages else "parsed",
                reason=reason,
                origin="product_sources",
                usages=usages,
            ),
        )

    for analyzed in _list(execution_results.get("analyzed_sources")):
        evidence_ref = str(analyzed.get("evidence_ref") or analyzed.get("source_ref") or analyzed.get("id") or "").strip()
        if not evidence_ref:
            continue
        reason = _source_lifecycle_reason(str(analyzed.get("reason") or analyzed.get("outcome") or "unknown"))
        _upsert_source_lifecycle(
            items,
            _source_lifecycle_item(
                analyzed,
                evidence_ref=evidence_ref,
                state=_source_lifecycle_state(reason, extraction_state=extraction_state, source=_dict(analyzed)),
                reason=reason,
                origin="analyzed_sources",
                usages=[],
            ),
        )

    for retrieved in _list(execution_results.get("retrieved_sources")):
        evidence_ref = str(retrieved.get("source_ref") or retrieved.get("evidence_ref") or retrieved.get("id") or "").strip()
        if not evidence_ref:
            continue
        _upsert_source_lifecycle(
            items,
            _source_lifecycle_item(
                retrieved,
                evidence_ref=evidence_ref,
                state=_retrieved_source_state(extraction_state),
                reason=_retrieved_source_reason(extraction_state),
                origin="retrieved_sources",
                usages=[],
                default_source_type="web",
            ),
        )

    for outcome in [
        *_list(execution_results.get("source_outcomes")),
        *_list(execution_results.get("retrieval_source_outcomes")),
        *_list(execution_results.get("source_provider_outcomes")),
    ]:
        evidence_ref = str(outcome.get("evidence_ref") or outcome.get("source_ref") or outcome.get("source_id") or outcome.get("id") or "").strip()
        if not evidence_ref:
            continue
        reason = _source_lifecycle_reason(str(outcome.get("outcome") or outcome.get("reason") or "unknown"))
        _upsert_source_lifecycle(
            items,
            _source_lifecycle_item(
                outcome,
                evidence_ref=evidence_ref,
                state=_source_lifecycle_state(reason, extraction_state=extraction_state, source=_dict(outcome)),
                reason=reason,
                origin="source_outcomes",
                usages=[],
            ),
        )

    for verification in _list(execution_results.get("source_verification_results")):
        evidence_ref = str(verification.get("evidence_ref") or verification.get("source_ref") or "").strip()
        if not evidence_ref:
            continue
        state = str(verification.get("verification_state") or "unverified_url")
        _upsert_source_lifecycle(
            items,
            _source_lifecycle_item(
                verification,
                evidence_ref=evidence_ref,
                state="verified" if state == "reachable" else "verification_failed",
                reason=_source_lifecycle_reason(state),
                origin="source_verification",
                usages=[],
            ),
        )

    return sorted(items.values(), key=lambda item: (_source_lifecycle_sort_rank(item.state), item.evidence_ref))


def source_lifecycle_summary(
    items: list[RadarRunDossierSourceLifecycleItemResponse],
) -> RadarRunDossierSourceLifecycleSummaryResponse:
    by_state: dict[str, int] = {}
    by_reason: dict[str, int] = {}
    for item in items:
        by_state[item.state] = by_state.get(item.state, 0) + 1
        by_reason[item.reason] = by_reason.get(item.reason, 0) + 1
    return RadarRunDossierSourceLifecycleSummaryResponse(
        total_count=len(items),
        by_state=by_state,
        by_reason=by_reason,
    )


def _source_lifecycle_item(
    payload: dict[str, Any],
    *,
    evidence_ref: str,
    state: str,
    reason: str,
    origin: str,
    usages: list[RadarRunDossierSourceUsageResponse],
    default_source_type: str = "web",
) -> RadarRunDossierSourceLifecycleItemResponse:
    return RadarRunDossierSourceLifecycleItemResponse(
        evidence_ref=evidence_ref,
        title=str(payload.get("title", "")),
        url=str(payload.get("url", "")),
        query_id=str(payload.get("query_id")) if payload.get("query_id") is not None else None,
        source_type=str(payload.get("source_type", default_source_type)),
        state=state,
        reason=reason,
        origin=origin,
        verification_state=_optional_text(payload.get("verification_state")),
        verification_mode=_optional_text(payload.get("verification_mode")),
        verification_reason=_optional_text(payload.get("verification_reason")),
        verification_status_code=_optional_int(payload.get("verification_status_code")),
        usages=usages,
    )


def _upsert_source_lifecycle(
    items: dict[str, RadarRunDossierSourceLifecycleItemResponse],
    item: RadarRunDossierSourceLifecycleItemResponse,
) -> None:
    current = items.get(item.evidence_ref)
    if current is None or _source_lifecycle_precedence(item.state) > _source_lifecycle_precedence(current.state):
        items[item.evidence_ref] = item


def _source_lifecycle_precedence(state: str) -> int:
    return {
        "used": 100,
        "linked": 90,
        "verification_failed": 85,
        "linking_failed": 80,
        "schema_rejected": 75,
        "analyzed_only": 70,
        "skipped": 60,
        "budget_limited": 55,
        "verified": 50,
        "parsed": 40,
        "retrieved": 10,
    }.get(state, 0)


def _source_lifecycle_sort_rank(state: str) -> int:
    return {
        "used": 0,
        "linked": 1,
        "linking_failed": 2,
        "schema_rejected": 3,
        "verification_failed": 4,
        "analyzed_only": 5,
        "skipped": 6,
        "budget_limited": 7,
        "verified": 8,
        "parsed": 9,
        "retrieved": 10,
    }.get(state, 20)


def _source_lifecycle_state(reason: str, *, extraction_state: str, source: dict[str, Any]) -> str:
    if reason in {"used", "used_by_candidate"}:
        return "used"
    if reason in {"linked", "source_linked", "evidence_linked"}:
        return "linked"
    if reason in {"evidence_linking_failed", "missing_evidence_ref", "unresolved_evidence_ref"}:
        return "linking_failed"
    if extraction_state == "evidence_linking_failed" and reason in {"not_used_by_candidate", "retrieved", "retrieved_not_extracted"}:
        return "linking_failed"
    if extraction_state == "extraction_schema_invalid":
        return "schema_rejected"
    if reason in {"extraction_schema_invalid", "schema_invalid", "schema_rejected"}:
        return "schema_rejected"
    if reason in {"unreachable", "blocked", "timeout", "invalid_url", "unverified_url", "verification_limited"}:
        return "verification_failed"
    if reason in {"policy_skipped", "duplicate", "irrelevant", "skipped"}:
        return "skipped"
    if reason in {"budget_limited", "not_executed_budget_limited"}:
        return "budget_limited"
    if source.get("verification_state") == "reachable":
        return "verified"
    return "analyzed_only"


def _retrieved_source_state(extraction_state: str) -> str:
    if extraction_state == "evidence_linking_failed":
        return "linking_failed"
    if extraction_state == "extraction_schema_invalid":
        return "schema_rejected"
    return "retrieved"


def _retrieved_source_reason(extraction_state: str) -> str:
    if extraction_state in {"evidence_linking_failed", "extraction_schema_invalid"}:
        return extraction_state
    return "retrieved_not_extracted"


def _extraction_validation_state(execution_results: dict[str, Any]) -> str:
    states = {
        str(item.get("state", "")).strip()
        for item in _list(execution_results.get("extraction_validation_results"))
    }
    if "extraction_schema_invalid" in states:
        return "extraction_schema_invalid"
    if "evidence_linking_failed" in states:
        return "evidence_linking_failed"
    return ""


def _source_lifecycle_reason(value: str) -> str:
    normalized = value.strip() or "unknown"
    allowed = {
        "used_by_candidate",
        "used",
        "linked",
        "source_linked",
        "evidence_linked",
        "not_used_by_candidate",
        "unreachable",
        "blocked",
        "timeout",
        "unverified_url",
        "not_checked",
        "verification_limited",
        "provider_empty",
        "provider_empty_or_verification_limited",
        "budget_limited",
        "not_executed_budget_limited",
        "evidence_linking_limited",
        "evidence_linking_failed",
        "missing_evidence_ref",
        "unresolved_evidence_ref",
        "extraction_schema_invalid",
        "schema_invalid",
        "schema_rejected",
        "retrieved",
        "retrieved_not_extracted",
        "invalid_url",
        "policy_skipped",
        "duplicate",
        "irrelevant",
        "insufficient_evidence",
        "provider_metadata_only",
        "provider_recorded_empty",
        "provider_unavailable",
        "unknown",
    }
    return normalized if normalized in allowed else "unknown"


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_int(value: object) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _dict(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}
