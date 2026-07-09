"""User-facing candidate surface projection for candidate discovery."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CandidateDiscoveryPublicSurface:
    """Carries projected user-facing candidate rows and their summary.

    Owns:
    - Immutable public-surface projection payload returned by the projector.

    Does not own:
    - Candidate admission, product acceptance decisions, API transport, or
      benchmark scoring.

    Architecture:
    docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md#candidatediscoverypublicsurface
    """

    candidates: list[dict[str, Any]]
    summary: dict[str, Any]


class CandidateDiscoveryPublicSurfaceProjector:
    """Projects accepted and review-needed legal leads into visible candidates.

    Owns:
    - User-facing candidate surface rows and accepted/review-needed counts.

    Does not own:
    - Retrieval, extraction, product acceptance rules, benchmark scoring, or
      signal monitoring.

    Architecture:
    docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md#candidatediscoverypublicsurfaceprojector
    """

    def __init__(self, promoter: "CandidateDiscoveryProductAcceptancePromoter | None" = None) -> None:
        self._promoter = promoter or CandidateDiscoveryProductAcceptancePromoter()

    def project(
        self,
        *,
        public_candidates: list[dict[str, Any]],
        candidate_universe: list[dict[str, Any]],
    ) -> CandidateDiscoveryPublicSurface:
        rows: list[dict[str, Any]] = []
        rows_by_key: dict[str, dict[str, Any]] = {}
        for item in public_candidates:
            row = self._visible_public_candidate(item)
            self._append(rows, rows_by_key, row)
        for item in candidate_universe:
            if not self._should_surface_universe_entry(item, rows_by_key):
                continue
            row = self._visible_review_candidate(item)
            self._append(rows, rows_by_key, row)
        ranked = [
            {**row, "candidate_surface_rank": index + 1}
            for index, row in enumerate(rows)
        ]
        return CandidateDiscoveryPublicSurface(candidates=ranked, summary=self._summary(ranked))

    def _visible_public_candidate(self, item: dict[str, Any]) -> dict[str, Any]:
        row = self._promoter.promote_public_candidate(item)
        status = self._surface_status(row)
        row["candidate_surface_status"] = status
        row["candidate_surface_reason"] = str(
            row.get("candidate_surface_reason")
            or row.get("public_projection_reason")
            or self._surface_reason(row, status)
        )
        row.setdefault("entity_type", "legal_entity")
        row.setdefault("public_result_status", "public_candidate" if status == "accepted_product_candidate" else status)
        row.setdefault("public_projection_reason", row["candidate_surface_reason"])
        row.setdefault("evidence_refs", self._source_refs(row))
        return row

    def _visible_review_candidate(self, item: dict[str, Any]) -> dict[str, Any]:
        source_refs = self._source_refs(item)
        product_status = str(item.get("product_acceptance_status") or "review_required")
        if product_status == "not_product_accepted" and (source_refs or str(item.get("benchmark_id") or "").strip()):
            product_status = "review_required"
        reason = str(
            item.get("candidate_surface_reason")
            or item.get("public_projection_reason")
            or item.get("product_acceptance_reason")
            or "source_backed_legal_entity_requires_review"
        )
        return {
            "candidate_id": str(item.get("candidate_id") or self._name_key(item)),
            "legal_name": self._display_name(item),
            "description": str(item.get("description") or ""),
            "entity_type": "legal_entity",
            "score": {"fit_score": 0, "intent_score": 0, "tier": "Review needed"},
            "review_flags": sorted({
                *self._string_list(item.get("review_flags")),
                "review_needed_candidate",
            }),
            "evidence_refs": source_refs,
            "qualification": [],
            "signals": [],
            "upstream_discovery_outcome": str(item.get("upstream_discovery_outcome") or "review_needed_upstream_lead"),
            "product_acceptance_status": product_status,
            "upstream_confidence": str(item.get("upstream_confidence") or ("medium" if source_refs else "low")),
            "upstream_reason": str(
                item.get("upstream_reason")
                or "Source-backed legal entity retained for user review."
            ),
            "upstream_source_refs": source_refs,
            "product_acceptance_reason": str(
                item.get("product_acceptance_reason")
                or "requires_human_review_before_product_acceptance"
            ),
            "public_result_status": "review_needed_candidate",
            "public_projection_reason": reason,
            "candidate_surface_status": "review_needed_candidate",
            "candidate_surface_reason": reason,
            "benchmark_id": str(item.get("benchmark_id") or ""),
        }

    def _should_surface_universe_entry(self, item: dict[str, Any], seen: dict[str, dict[str, Any]]) -> bool:
        if not self._name_key(item):
            return False
        if str(item.get("entity_type") or "unknown_entity") != "legal_entity":
            return False
        if str(item.get("upstream_discovery_outcome") or "") == "rejected_noise":
            return False
        if str(item.get("not_candidate_reason") or "").strip():
            return False
        return bool(
            self._source_refs(item)
            or self._diagnostic_reason(item)
            or str(item.get("status") or "") in {"qualified", "unknown_review_needed"}
        )

    @staticmethod
    def _surface_status(item: dict[str, Any]) -> str:
        if str(item.get("product_acceptance_status") or "") == "product_candidate":
            return "accepted_product_candidate"
        return "review_needed_candidate"

    @staticmethod
    def _surface_reason(item: dict[str, Any], status: str) -> str:
        if status == "accepted_product_candidate":
            return "accepted_by_product_candidate_rules"
        return str(item.get("product_acceptance_reason") or "requires_human_review_before_product_acceptance")

    def _append(
        self,
        rows: list[dict[str, Any]],
        rows_by_key: dict[str, dict[str, Any]],
        row: dict[str, Any],
    ) -> None:
        key = self._merge_key(row)
        if not key:
            return
        current = rows_by_key.get(key)
        if current is None:
            rows_by_key[key] = row
            rows.append(row)
            return
        self._merge_rows(current, row)

    def _merge_rows(self, target: dict[str, Any], incoming: dict[str, Any]) -> None:
        if self._prefer_incoming_name(target, incoming):
            target["legal_name"] = self._display_name(incoming)
        for key in ("evidence_refs", "upstream_source_refs", "review_flags"):
            target[key] = self._merged_strings(target.get(key), incoming.get(key))
        for field_name, collection_name in (
            ("candidate_surface_reason", "candidate_surface_reasons"),
            ("public_projection_reason", "public_projection_reasons"),
            ("upstream_reason", "upstream_reasons"),
            ("product_acceptance_reason", "product_acceptance_reasons"),
        ):
            reasons = self._merged_strings(
                target.get(collection_name),
                [target.get(field_name), incoming.get(field_name)],
            )
            if reasons:
                target[collection_name] = reasons
                target[field_name] = self._preferred_reason(reasons)
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
        target["benchmark_ids"] = self._merged_strings(
            target.get("benchmark_ids"),
            [target.get("benchmark_id"), incoming.get("benchmark_id")],
        )
        if str(incoming.get("candidate_surface_status") or "") == "accepted_product_candidate":
            target["candidate_surface_status"] = "accepted_product_candidate"
        if str(incoming.get("product_acceptance_status") or "") == "product_candidate":
            target["product_acceptance_status"] = "product_candidate"
        if self._score_total(incoming) > self._score_total(target):
            target["score"] = dict(incoming.get("score")) if isinstance(incoming.get("score"), dict) else incoming.get("score")
        for key in ("qualification", "signals"):
            if not isinstance(target.get(key), list) or not target.get(key):
                value = incoming.get(key)
                if isinstance(value, list) and value:
                    target[key] = value

    def _merge_key(self, item: dict[str, Any]) -> str:
        candidate_id = str(item.get("candidate_id") or "").strip().casefold()
        if candidate_id:
            return f"id:{candidate_id}"
        name = self._normalized_name(self._display_name(item))
        entity_type = str(item.get("entity_type") or "legal_entity").strip().casefold()
        return f"name:{entity_type}:{name}" if name else ""

    @staticmethod
    def _normalized_name(value: str) -> str:
        return "".join(ch for ch in value.casefold() if ch.isalnum())

    @staticmethod
    def _prefer_incoming_name(target: dict[str, Any], incoming: dict[str, Any]) -> bool:
        if not str(target.get("legal_name") or "").strip():
            return True
        if str(incoming.get("benchmark_id") or "").strip() and not str(target.get("benchmark_id") or "").strip():
            return True
        return False

    @classmethod
    def _merged_strings(cls, *values: object) -> list[str]:
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

    @staticmethod
    def _preferred_reason(reasons: list[str]) -> str:
        for reason in reasons:
            if "benchmark_present" in reason:
                return reason
        return reasons[0] if reasons else ""

    @staticmethod
    def _score_total(item: dict[str, Any]) -> int:
        score = item.get("score")
        if not isinstance(score, dict):
            return 0
        total = 0
        for key in ("fit_score", "intent_score"):
            try:
                total += int(score.get(key) or 0)
            except (TypeError, ValueError):
                continue
        return total

    @staticmethod
    def _diagnostic_reason(item: dict[str, Any]) -> str:
        for key in (
            "candidate_surface_reason",
            "public_projection_reason",
            "product_acceptance_reason",
            "upstream_reason",
            "reason",
        ):
            text = str(item.get(key) or "").strip()
            if text:
                return text
        return ""

    def _summary(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        by_status = self._count_by(rows, "candidate_surface_status")
        return {
            "visible_candidate_count": len(rows),
            "accepted_product_candidate_count": by_status.get("accepted_product_candidate", 0),
            "review_needed_candidate_count": by_status.get("review_needed_candidate", 0),
            "by_candidate_surface_status": by_status,
            "visible_candidate_names": [
                str(row.get("legal_name") or "")
                for row in rows
                if str(row.get("legal_name") or "").strip()
            ],
        }

    @staticmethod
    def _display_name(item: dict[str, Any]) -> str:
        return str(item.get("legal_name") or item.get("name") or item.get("entity_name") or "").strip()

    def _name_key(self, item: dict[str, Any]) -> str:
        return self._display_name(item).casefold()

    @staticmethod
    def _source_refs(item: dict[str, Any]) -> list[str]:
        refs: list[str] = []
        for key in ("source_refs", "evidence_refs", "upstream_source_refs"):
            value = item.get(key)
            if isinstance(value, list):
                refs.extend(str(ref) for ref in value if str(ref).strip())
        return sorted(set(refs))

    @staticmethod
    def _string_list(value: object) -> list[str]:
        return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []

    @staticmethod
    def _count_by(items: list[dict[str, Any]], field_name: str) -> dict[str, int]:
        result: dict[str, int] = {}
        for item in items:
            value = str(item.get(field_name) or "unknown")
            result[value] = result.get(value, 0) + 1
        return result


class CandidateDiscoveryProductAcceptancePromoter:
    """Promotes selected public rows from upstream leads to product candidates.

    Owns:
    - Conservative promotion of already selected public candidate rows.

    Does not own:
    - Broad candidate-universe admission, benchmark matching, or downstream
      account approval.

    Architecture:
    docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md#candidatediscoveryproductacceptancepromoter
    """

    _BLOCKING_FLAGS = (
        "not_standalone_legal_entity",
        "explicitly_rejected",
        "rejected_noise",
        "invalid_url",
    )

    def promote_public_candidate(self, item: dict[str, Any]) -> dict[str, Any]:
        row = dict(item)
        if not self._should_promote(row):
            return row
        previous_reason = str(row.get("product_acceptance_reason") or "")
        row["product_acceptance_status"] = "product_candidate"
        row["product_acceptance_reason"] = (
            previous_reason
            if previous_reason and previous_reason != "requires_human_review_before_product_acceptance"
            else "source_backed_public_candidate_promoted"
        )
        row.setdefault("upstream_discovery_outcome", "retained_upstream_lead")
        row.setdefault("upstream_confidence", "medium")
        return row

    def _should_promote(self, item: dict[str, Any]) -> bool:
        if str(item.get("product_acceptance_status") or "") == "product_candidate":
            return True
        if str(item.get("entity_type") or "legal_entity") != "legal_entity":
            return False
        if str(item.get("not_candidate_reason") or "").strip():
            return False
        flags = {str(flag) for flag in self._string_list(item.get("review_flags"))}
        if any(flag in flags for flag in self._BLOCKING_FLAGS):
            return False
        return bool(self._source_refs(item))

    @staticmethod
    def _source_refs(item: dict[str, Any]) -> list[str]:
        refs: list[str] = []
        for key in ("source_refs", "evidence_refs", "upstream_source_refs"):
            value = item.get(key)
            if isinstance(value, list):
                refs.extend(str(ref) for ref in value if str(ref).strip())
        return sorted(set(refs))

    @staticmethod
    def _string_list(value: object) -> list[str]:
        return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []
