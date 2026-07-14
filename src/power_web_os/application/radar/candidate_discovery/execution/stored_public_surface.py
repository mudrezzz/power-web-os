"""Canonical public candidate surface for persisted discovery outputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class _StoredCandidatePublicSurface:
    rows: tuple[dict[str, Any], ...]
    candidate_ids: tuple[str, ...]
    accepted_count: int
    review_needed_count: int
    diagnostics: tuple[dict[str, str], ...]

    @property
    def candidate_count(self) -> int:
        return len(self.rows)


class StoredCandidatePublicSurfaceProjector:
    """Project one duplicate-safe public surface from a persisted output.

    Owns: persisted candidate source precedence, dedupe and binary public status.
    Does not own: candidate discovery, acceptance promotion, API transport or SQL.
    Architecture:
    docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md#storedcandidatepublicsurfaceprojector
    """

    def project(
        self,
        *,
        artifact_payload: dict[str, Any] | None,
        candidates_payload: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
    ) -> _StoredCandidatePublicSurface:
        artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
        execution_results = _dict(_dict(artifact.get("run_metadata")).get("execution_results"))
        candidates = (
            _list(execution_results.get("user_visible_candidates"))
            or _list(artifact.get("candidates"))
            or [dict(item) for item in candidates_payload if isinstance(item, dict)]
        )

        rows: list[dict[str, Any]] = []
        rows_by_key: dict[str, dict[str, Any]] = {}
        diagnostics: list[dict[str, str]] = []
        for candidate in candidates:
            row = dict(candidate)
            key = _candidate_merge_key(row)
            if not key:
                diagnostics.append(_diagnostic(row, "invalid_public_candidate_identity"))
                continue
            if _is_rejected(row):
                diagnostics.append(_diagnostic(row, "explicitly_rejected_public_candidate"))
                continue
            current = rows_by_key.get(key)
            if current is None:
                _normalize_public_status(row)
                rows_by_key[key] = row
                rows.append(row)
                continue
            _merge_candidate_row(current, row)
            _normalize_public_status(current)

        ranked_rows = tuple(
            {**row, "candidate_surface_rank": index + 1}
            for index, row in enumerate(rows)
        )
        accepted_count = sum(_is_accepted(row) for row in ranked_rows)
        review_needed_count = len(ranked_rows) - accepted_count
        return _StoredCandidatePublicSurface(
            rows=ranked_rows,
            candidate_ids=tuple(_public_candidate_id(row) for row in ranked_rows),
            accepted_count=accepted_count,
            review_needed_count=review_needed_count,
            diagnostics=tuple(diagnostics),
        )


def _normalize_public_status(candidate: dict[str, Any]) -> None:
    if _is_accepted(candidate):
        candidate["candidate_surface_status"] = "accepted_product_candidate"
        candidate["product_acceptance_status"] = "product_candidate"
        return
    candidate["candidate_surface_status"] = "review_needed_candidate"
    if str(candidate.get("product_acceptance_status") or "") != "not_product_accepted":
        candidate["product_acceptance_status"] = "review_required"


def _is_accepted(candidate: dict[str, Any]) -> bool:
    return (
        str(candidate.get("candidate_surface_status") or "") == "accepted_product_candidate"
        or str(candidate.get("product_acceptance_status") or "") == "product_candidate"
    )


def _is_rejected(candidate: dict[str, Any]) -> bool:
    statuses = {
        str(candidate.get("candidate_surface_status") or "").strip(),
        str(candidate.get("upstream_discovery_outcome") or "").strip(),
        str(candidate.get("public_result_status") or "").strip(),
    }
    return bool(statuses & {"rejected", "rejected_noise"}) or bool(
        str(candidate.get("not_candidate_reason") or "").strip()
    )


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
        reasons = _merged_strings(
            target.get(collection_name),
            [target.get(field_name), incoming.get(field_name)],
        )
        if reasons:
            target[collection_name] = reasons
            target[field_name] = _preferred_reason(reasons)
    for key in (
        "benchmark_id",
        "inn",
        "ogrn",
        "okved",
        "provider_id",
        "source_id",
        "lookup_query",
        "match_quality",
    ):
        if not str(target.get(key) or "").strip() and str(incoming.get(key) or "").strip():
            target[key] = incoming.get(key)
    target["benchmark_ids"] = _merged_strings(
        target.get("benchmark_ids"),
        [target.get("benchmark_id"), incoming.get("benchmark_id")],
    )
    if _is_accepted(incoming):
        target["candidate_surface_status"] = "accepted_product_candidate"
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
    name = _normalized_name(_display_name(candidate))
    entity_type = str(candidate.get("entity_type") or "legal_entity").strip().casefold()
    return f"name:{entity_type}:{name}" if name else ""


def _public_candidate_id(candidate: dict[str, Any]) -> str:
    candidate_id = str(candidate.get("candidate_id") or "").strip()
    if candidate_id:
        return candidate_id
    entity_type = str(candidate.get("entity_type") or "legal_entity").strip().casefold()
    return f"{entity_type}:{_normalized_name(_display_name(candidate))}"


def _diagnostic(candidate: dict[str, Any], reason: str) -> dict[str, str]:
    return {
        "candidate_id": str(candidate.get("candidate_id") or ""),
        "legal_name": _display_name(candidate),
        "reason": reason,
    }


def _prefer_incoming_name(target: dict[str, Any], incoming: dict[str, Any]) -> bool:
    if not str(target.get("legal_name") or "").strip():
        return True
    return bool(str(incoming.get("benchmark_id") or "").strip()) and not bool(
        str(target.get("benchmark_id") or "").strip()
    )


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
    return next((reason for reason in reasons if "benchmark_present" in reason), reasons[0])


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


def _display_name(candidate: dict[str, Any]) -> str:
    for key in ("legal_name", "name", "candidate_name", "canonical_name"):
        value = str(candidate.get(key) or "").strip()
        if value:
            return value
    return ""


def _normalized_name(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())


def _dict(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _list(value: object) -> list[dict[str, Any]]:
    return [dict(item) for item in value if isinstance(item, dict)] if isinstance(value, list) else []
