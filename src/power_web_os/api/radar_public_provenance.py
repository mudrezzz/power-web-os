"""Public provenance projection for Radar candidate responses."""

from __future__ import annotations

from typing import Any


def public_candidate_rows(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return duplicate-safe public candidate rows for stored run outputs."""

    rows: list[dict[str, Any]] = []
    rows_by_key: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        row = dict(candidate)
        key = _candidate_merge_key(row)
        if not key:
            continue
        current = rows_by_key.get(key)
        if current is None:
            rows_by_key[key] = row
            rows.append(row)
            continue
        _merge_candidate_row(current, row)
    return [
        {**row, "candidate_surface_rank": index + 1}
        for index, row in enumerate(rows)
    ]


def public_candidate_sources(
    *,
    artifact_sources: list[dict[str, Any]],
    execution_results: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return source-like records that explain every public candidate ref."""

    sources_by_ref: dict[str, dict[str, Any]] = {}
    for source in artifact_sources:
        ref = str(source.get("evidence_ref") or "").strip()
        if ref:
            sources_by_ref[ref] = dict(source)

    wanted_refs = _candidate_refs(candidates)
    provenance_records = [
        *_list(execution_results.get("review_needed_upstream_entities")),
        *_list(execution_results.get("candidate_universe")),
        *_list(execution_results.get("product_acceptance_ledger")),
        *_list(execution_results.get("unresolved_candidate_gaps")),
        *_list(execution_results.get("retrieved_sources")),
        *_list(execution_results.get("analyzed_sources")),
        *_list(execution_results.get("source_outcomes")),
        *_list(execution_results.get("retrieval_source_outcomes")),
        *_list(execution_results.get("source_provider_outcomes")),
    ]

    for record in provenance_records:
        for ref in _source_refs(record):
            if ref not in wanted_refs or ref in sources_by_ref:
                continue
            sources_by_ref[ref] = _provenance_source(ref, record)

    for candidate in candidates:
        for ref in _source_refs(candidate):
            if ref in sources_by_ref:
                continue
            sources_by_ref[ref] = _fallback_candidate_source(ref, candidate)

    return [
        sources_by_ref[ref]
        for ref in sorted(sources_by_ref)
        if ref in wanted_refs or ref in _artifact_refs(artifact_sources)
    ]


def _merge_candidate_row(target: dict[str, Any], incoming: dict[str, Any]) -> None:
    if _prefer_incoming_name(target, incoming):
        target["legal_name"] = _display_name(incoming)
    for key in ("evidence_refs", "upstream_source_refs", "review_flags"):
        target[key] = _merged_strings(target.get(key), incoming.get(key))
    for field_name, collection_name in (
        ("candidate_surface_reason", "candidate_surface_reasons"),
        ("public_projection_reason", "public_projection_reasons"),
        ("upstream_reason", "upstream_reasons"),
        ("product_acceptance_reason", "product_acceptance_reasons"),
    ):
        reasons = _merged_strings(target.get(collection_name), [target.get(field_name), incoming.get(field_name)])
        if reasons:
            target[collection_name] = reasons
            target[field_name] = _preferred_reason(reasons)
    for key in ("benchmark_id", "inn", "ogrn", "okved", "provider_id", "source_id", "lookup_query", "match_quality"):
        if not str(target.get(key) or "").strip() and str(incoming.get(key) or "").strip():
            target[key] = incoming.get(key)
    target["benchmark_ids"] = _merged_strings(
        target.get("benchmark_ids"),
        [target.get("benchmark_id"), incoming.get("benchmark_id")],
    )
    if str(incoming.get("candidate_surface_status") or "") == "accepted_product_candidate":
        target["candidate_surface_status"] = "accepted_product_candidate"
    if str(incoming.get("product_acceptance_status") or "") == "product_candidate":
        target["product_acceptance_status"] = "product_candidate"
    if _score_total(incoming) > _score_total(target):
        score = incoming.get("score")
        target["score"] = dict(score) if isinstance(score, dict) else score
    for key in ("qualification", "signals"):
        if not isinstance(target.get(key), list) or not target.get(key):
            value = incoming.get(key)
            if isinstance(value, list) and value:
                target[key] = value


def _candidate_merge_key(candidate: dict[str, Any]) -> str:
    candidate_id = str(candidate.get("candidate_id") or "").strip().casefold()
    if candidate_id:
        return f"id:{candidate_id}"
    name = "".join(ch for ch in _display_name(candidate).casefold() if ch.isalnum())
    entity_type = str(candidate.get("entity_type") or "legal_entity").strip().casefold()
    return f"name:{entity_type}:{name}" if name else ""


def _prefer_incoming_name(target: dict[str, Any], incoming: dict[str, Any]) -> bool:
    if not str(target.get("legal_name") or "").strip():
        return True
    if str(incoming.get("benchmark_id") or "").strip() and not str(target.get("benchmark_id") or "").strip():
        return True
    return False


def _merged_strings(*values: object) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        items = value if isinstance(value, list) else [value]
        for item in items:
            text = str(item or "").strip()
            if not text or text in seen:
                continue
            seen.add(text)
            result.append(text)
    return result


def _preferred_reason(reasons: list[str]) -> str:
    for reason in reasons:
        if "benchmark_present" in reason:
            return reason
    return reasons[0] if reasons else ""


def _score_total(candidate: dict[str, Any]) -> int:
    score = candidate.get("score")
    if not isinstance(score, dict):
        return 0
    total = 0
    for key in ("fit_score", "intent_score"):
        try:
            total += int(score.get(key) or 0)
        except (TypeError, ValueError):
            continue
    return total


def _provenance_source(ref: str, record: dict[str, Any]) -> dict[str, Any]:
    if _is_registry_record(ref, record):
        return {
            "evidence_ref": ref,
            "title": f"Registry evidence: {_display_name(record) or ref}",
            "url": "",
            "snippet": _registry_snippet(record),
            "query_id": _optional_text(record.get("lookup_query")),
            "source_type": "registry",
        }
    if _is_benchmark_record(record):
        return {
            "evidence_ref": ref,
            "title": f"Benchmark projection evidence: {_display_name(record) or ref}",
            "url": "",
            "snippet": _diagnostic_snippet(record, default="Benchmark target was present in product-safe source diagnostics."),
            "query_id": _optional_text(record.get("origin_task_id")),
            "source_type": "projection",
        }
    return {
        "evidence_ref": ref,
        "title": str(record.get("title") or f"Diagnostic evidence: {_display_name(record) or ref}"),
        "url": str(record.get("url") or ""),
        "snippet": str(record.get("snippet") or _diagnostic_snippet(record, default="Diagnostic provenance retained for review.")),
        "query_id": _optional_text(record.get("query_id") or record.get("lookup_query") or record.get("origin_task_id")),
        "source_type": str(record.get("source_type") or "diagnostic"),
    }


def _fallback_candidate_source(ref: str, candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "evidence_ref": ref,
        "title": f"Public candidate reason: {_display_name(candidate) or ref}",
        "url": "",
        "snippet": _diagnostic_snippet(
            candidate,
            default="Candidate is visible because the public surface recorded an explicit review reason.",
        ),
        "query_id": None,
        "source_type": "diagnostic",
    }


def _registry_snippet(record: dict[str, Any]) -> str:
    parts = [
        _display_name(record),
        _labeled("INN", record.get("inn")),
        _labeled("OGRN", record.get("ogrn")),
        _labeled("provider", record.get("provider_id") or record.get("source_id")),
        _labeled("lookup", record.get("lookup_query")),
        _labeled("match quality", record.get("match_quality")),
        _diagnostic_snippet(record, default="Registry identity retained for human review."),
    ]
    return "; ".join(part for part in parts if part)


def _diagnostic_snippet(record: dict[str, Any], *, default: str) -> str:
    for key in (
        "reason",
        "candidate_surface_reason",
        "public_projection_reason",
        "product_acceptance_reason",
        "upstream_reason",
        "outcome",
    ):
        text = str(record.get(key) or "").strip()
        if text:
            return text
    flags = [str(flag) for flag in record.get("review_flags", []) if isinstance(flag, str)]
    return ", ".join(flags) if flags else default


def _candidate_refs(candidates: list[dict[str, Any]]) -> set[str]:
    refs: set[str] = set()
    for candidate in candidates:
        refs.update(_source_refs(candidate))
        for qualification in _list(candidate.get("qualification")):
            refs.update(_source_refs(qualification))
        for signal in _list(candidate.get("signals")):
            refs.update(_source_refs(signal))
    refs.discard("")
    return refs


def _artifact_refs(sources: list[dict[str, Any]]) -> set[str]:
    return {str(source.get("evidence_ref") or "").strip() for source in sources}


def _source_refs(record: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in ("source_refs", "evidence_refs", "upstream_source_refs"):
        value = record.get(key)
        if isinstance(value, list):
            refs.extend(str(item).strip() for item in value if str(item).strip())
    return sorted(set(refs))


def _is_registry_record(ref: str, record: dict[str, Any]) -> bool:
    return (
        ref.startswith("dadata_")
        or str(record.get("source_id") or "") == "dadata_registry"
        or str(record.get("provider_id") or "") == "dadata"
        or bool(str(record.get("inn") or "").strip())
    )


def _is_benchmark_record(record: dict[str, Any]) -> bool:
    return bool(
        str(record.get("benchmark_id") or "").strip()
        or "benchmark_present" in str(record.get("public_projection_reason") or "")
        or "benchmark_present" in " ".join(str(flag) for flag in record.get("review_flags", []))
    )


def _display_name(record: dict[str, Any]) -> str:
    return str(record.get("legal_name") or record.get("entity_name") or record.get("name") or "").strip()


def _labeled(label: str, value: object) -> str:
    text = str(value or "").strip()
    return f"{label}: {text}" if text else ""


def _optional_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]
