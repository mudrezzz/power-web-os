"""Outcome reconciliation for candidate-discovery finalization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from power_web_os.application.radar.candidate_discovery.execution.public_surface import (
    CandidateDiscoveryProductAcceptancePromoter,
    CandidateDiscoveryPublicSurfaceProjector,
)


@dataclass(frozen=True)
class _CandidateDiscoveryOutcomeReconciliation:
    candidate_universe: list[dict[str, Any]]
    user_visible_candidates: list[dict[str, Any]]
    summary: dict[str, Any]
    product_acceptance_ledger: list[dict[str, Any]]


class CandidateDiscoveryOutcomeReconciler:
    """Reconciles upstream discovery output with public candidate rows.

    Owns:
    - Product-safe accounting for public candidate rows, universe-only upstream
      leads, rejected/not-promoted entities, and diagnostic gaps.

    Does not own:
    - Retrieval, extraction, admission decisions, product acceptance policy,
      signal monitoring, or benchmark scoring.

    Architecture:
    docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md#candidatediscoveryoutcomereconciler
    """

    def reconcile(
        self,
        *,
        public_candidates: list[Any],
        candidate_universe: list[dict[str, Any]],
        unresolved_gaps: list[dict[str, Any]],
    ) -> _CandidateDiscoveryOutcomeReconciliation:
        promoter = CandidateDiscoveryProductAcceptancePromoter()
        public_payloads = [promoter.promote_public_candidate(self._payload(item)) for item in public_candidates]
        public_names = {
            self._name_key(item)
            for item in public_payloads
            if self._name_key(item)
        }
        enriched_universe = [
            self._enriched_universe_entry(item, public_names=public_names)
            for item in candidate_universe
        ]
        public_surface = CandidateDiscoveryPublicSurfaceProjector().project(
            public_candidates=public_payloads,
            candidate_universe=enriched_universe,
        )
        enriched_universe = self._apply_visible_surface_metadata(
            enriched_universe,
            user_visible_candidates=public_surface.candidates,
            public_names=public_names,
        )
        ledger = self._ledger(
            public_payloads=public_payloads,
            candidate_universe=enriched_universe,
            unresolved_gaps=unresolved_gaps,
        )
        return _CandidateDiscoveryOutcomeReconciliation(
            candidate_universe=enriched_universe,
            user_visible_candidates=public_surface.candidates,
            summary=self._summary(
                public_payloads=public_payloads,
                user_visible_candidates=public_surface.candidates,
                candidate_universe=enriched_universe,
                unresolved_gaps=unresolved_gaps,
                ledger=ledger,
                public_surface_summary=public_surface.summary,
            ),
            product_acceptance_ledger=ledger,
        )

    def _apply_visible_surface_metadata(
        self,
        candidate_universe: list[dict[str, Any]],
        *,
        user_visible_candidates: list[dict[str, Any]],
        public_names: set[str],
    ) -> list[dict[str, Any]]:
        visible_by_name = {
            self._name_key(item): item
            for item in user_visible_candidates
            if self._name_key(item)
        }
        result = []
        for item in candidate_universe:
            payload = dict(item)
            name_key = self._name_key(payload)
            visible = visible_by_name.get(name_key)
            if visible is not None:
                payload["candidate_surface_status"] = str(visible.get("candidate_surface_status") or "")
                payload["candidate_surface_reason"] = str(visible.get("candidate_surface_reason") or "")
                if name_key not in public_names:
                    payload["public_result_status"] = "review_needed_candidate"
                    payload["public_projection_reason"] = payload["candidate_surface_reason"]
            result.append(payload)
        return result

    def _enriched_universe_entry(
        self,
        item: dict[str, Any],
        *,
        public_names: set[str],
    ) -> dict[str, Any]:
        payload = dict(item)
        outcome = str(payload.get("upstream_discovery_outcome") or self._default_outcome(payload))
        product_status = str(payload.get("product_acceptance_status") or self._default_product_status(payload, outcome))
        public_status = str(payload.get("public_result_status") or "")
        public_reason = str(payload.get("public_projection_reason") or "")
        name_key = self._name_key(payload)
        if name_key and name_key in public_names:
            public_status = "public_candidate"
            public_reason = public_reason or "promoted_to_public_candidate_row"
        elif not public_status:
            public_status = self._default_public_status(payload, outcome)
        if not public_reason:
            public_reason = self._default_public_reason(payload, product_status, public_status)
        payload["upstream_discovery_outcome"] = outcome
        payload["product_acceptance_status"] = product_status
        payload["upstream_confidence"] = str(payload.get("upstream_confidence") or self._default_confidence(payload, outcome))
        payload["upstream_reason"] = str(payload.get("upstream_reason") or self._default_upstream_reason(payload, outcome))
        payload["product_acceptance_reason"] = str(
            payload.get("product_acceptance_reason") or self._default_product_reason(payload, product_status)
        )
        payload["public_result_status"] = public_status
        payload["public_projection_reason"] = public_reason
        return payload

    def _ledger(
        self,
        *,
        public_payloads: list[dict[str, Any]],
        candidate_universe: list[dict[str, Any]],
        unresolved_gaps: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for item in public_payloads:
            row = self._ledger_row(item, collection="public_candidates")
            self._append_row(rows, seen, row)
        for item in candidate_universe:
            row = self._ledger_row(item, collection="candidate_universe")
            self._append_row(rows, seen, row)
        for item in unresolved_gaps:
            if not self._name_key(item):
                continue
            row = self._gap_ledger_row(item)
            self._append_row(rows, seen, row)
        return rows

    def _summary(
        self,
        *,
        public_payloads: list[dict[str, Any]],
        user_visible_candidates: list[dict[str, Any]],
        candidate_universe: list[dict[str, Any]],
        unresolved_gaps: list[dict[str, Any]],
        ledger: list[dict[str, Any]],
        public_surface_summary: dict[str, Any],
    ) -> dict[str, Any]:
        upstream_rows = [
            item for item in ledger
            if str(item.get("upstream_discovery_outcome") or "") != "rejected_noise"
        ]
        public_rows = [item for item in ledger if str(item.get("public_result_status") or "") == "public_candidate"]
        product_rows = [item for item in ledger if str(item.get("product_acceptance_status") or "") == "product_candidate"]
        unexplained = [
            item for item in ledger
            if not str(item.get("public_result_status") or "").strip()
            or not str(item.get("public_projection_reason") or "").strip()
            or not str(item.get("product_acceptance_reason") or "").strip()
        ]
        by_public_status = self._count_by(ledger, "public_result_status")
        by_product_status = self._count_by(ledger, "product_acceptance_status")
        by_upstream_outcome = self._count_by(ledger, "upstream_discovery_outcome")
        product_candidate_count = len({self._name_key(item) for item in product_rows if self._name_key(item)})
        return {
            "raw_upstream_lead_count": len({self._name_key(item) for item in upstream_rows if self._name_key(item)}),
            "public_candidate_count": len({self._name_key(item) for item in public_rows if self._name_key(item)}),
            "visible_candidate_count": int(public_surface_summary.get("visible_candidate_count") or 0),
            "accepted_product_candidate_count": int(
                public_surface_summary.get("accepted_product_candidate_count") or 0
            ),
            "review_needed_candidate_count": int(public_surface_summary.get("review_needed_candidate_count") or 0),
            "candidate_universe_count": len(candidate_universe),
            "unresolved_gap_count": len(unresolved_gaps),
            "ledger_entry_count": len(ledger),
            "product_candidate_count": product_candidate_count,
            "universe_only_count": by_public_status.get("retained_in_candidate_universe", 0),
            "not_promoted_count": by_public_status.get("not_promoted_to_public_candidate", 0),
            "rejected_or_noise_count": by_upstream_outcome.get("rejected_noise", 0),
            "unexplained_drop_count": len(unexplained),
            "by_public_result_status": by_public_status,
            "by_product_acceptance_status": by_product_status,
            "by_upstream_discovery_outcome": by_upstream_outcome,
            "by_candidate_surface_status": dict(public_surface_summary.get("by_candidate_surface_status") or {}),
            "product_candidate_zero_explained": product_candidate_count == 0 and all(
                str(item.get("product_acceptance_reason") or "").strip()
                for item in ledger
                if str(item.get("product_acceptance_status") or "") != "product_candidate"
            ),
            "public_candidate_names": sorted({
                str(item.get("legal_name") or item.get("name") or item.get("entity_name") or "")
                for item in public_payloads
                if self._name_key(item)
            }),
            "visible_candidate_names": [
                str(item.get("legal_name") or "")
                for item in user_visible_candidates
                if self._name_key(item)
            ],
        }

    def _ledger_row(self, item: dict[str, Any], *, collection: str) -> dict[str, Any]:
        source_refs = self._source_refs(item)
        return {
            "candidate_id": str(item.get("candidate_id") or self._name_key(item)),
            "legal_name": self._display_name(item),
            "collection": collection,
            "entity_type": str(item.get("entity_type") or "legal_entity"),
            "source_refs": source_refs,
            "upstream_discovery_outcome": str(item.get("upstream_discovery_outcome") or self._default_outcome(item)),
            "product_acceptance_status": str(item.get("product_acceptance_status") or self._default_product_status(item, "")),
            "product_acceptance_reason": str(
                item.get("product_acceptance_reason")
                or self._default_product_reason(item, str(item.get("product_acceptance_status") or ""))
            ),
            "public_result_status": str(item.get("public_result_status") or "retained_in_candidate_universe"),
            "public_projection_reason": str(
                item.get("public_projection_reason")
                or self._default_public_reason(
                    item,
                    str(item.get("product_acceptance_status") or ""),
                    str(item.get("public_result_status") or ""),
                )
            ),
            "candidate_surface_status": str(item.get("candidate_surface_status") or ""),
            "candidate_surface_reason": str(item.get("candidate_surface_reason") or ""),
            "review_flags": self._string_list(item.get("review_flags")),
            "benchmark_id": str(item.get("benchmark_id") or ""),
        }

    def _gap_ledger_row(self, item: dict[str, Any]) -> dict[str, Any]:
        reason = str(item.get("reason") or item.get("not_candidate_reason") or "diagnostic_gap")
        source_refs = self._source_refs(item)
        return {
            "candidate_id": str(item.get("candidate_id") or self._name_key(item)),
            "legal_name": self._display_name(item),
            "collection": "unresolved_candidate_gaps",
            "entity_type": str(item.get("entity_type") or "unknown_entity"),
            "source_refs": source_refs,
            "upstream_discovery_outcome": str(item.get("upstream_discovery_outcome") or "review_needed_upstream_lead"),
            "product_acceptance_status": str(item.get("product_acceptance_status") or "not_product_accepted"),
            "product_acceptance_reason": str(item.get("product_acceptance_reason") or reason),
            "public_result_status": str(item.get("public_result_status") or "not_promoted_to_public_candidate"),
            "public_projection_reason": str(item.get("public_projection_reason") or reason),
            "review_flags": self._string_list(item.get("review_flags")),
            "benchmark_id": str(item.get("benchmark_id") or ""),
        }

    @staticmethod
    def _append_row(
        rows: list[dict[str, Any]],
        seen: set[tuple[str, str]],
        row: dict[str, Any],
    ) -> None:
        name_key = str(row.get("legal_name") or "").casefold()
        collection = str(row.get("collection") or "")
        if not name_key:
            return
        key = (name_key, collection)
        if key in seen:
            return
        seen.add(key)
        rows.append(row)

    @staticmethod
    def _payload(item: Any) -> dict[str, Any]:
        if isinstance(item, dict):
            return dict(item)
        if hasattr(item, "model_dump"):
            return dict(item.model_dump())
        return {}

    @staticmethod
    def _display_name(item: dict[str, Any]) -> str:
        return str(item.get("legal_name") or item.get("name") or item.get("entity_name") or "").strip()

    def _name_key(self, item: dict[str, Any]) -> str:
        return self._display_name(item).casefold()

    def _default_outcome(self, item: dict[str, Any]) -> str:
        if str(item.get("status") or "") == "rejected" or item.get("rejection_reasons"):
            return "rejected_noise"
        if self._source_refs(item):
            return "review_needed_upstream_lead"
        if str(item.get("status") or "") == "gap":
            return "review_needed_upstream_lead"
        return "review_needed_upstream_lead"

    def _default_product_status(self, item: dict[str, Any], outcome: str) -> str:
        if outcome == "rejected_noise":
            return "not_product_accepted"
        if str(item.get("status") or "") == "qualified" and str(item.get("entity_type") or "legal_entity") == "legal_entity":
            return "review_required"
        if self._source_refs(item):
            return "review_required"
        return "not_product_accepted"

    @staticmethod
    def _default_confidence(item: dict[str, Any], outcome: str) -> str:
        if outcome == "confirmed_upstream_lead":
            return "high"
        if item.get("source_refs") or item.get("evidence_refs"):
            return "medium"
        return "low"

    def _default_upstream_reason(self, item: dict[str, Any], outcome: str) -> str:
        if outcome == "rejected_noise":
            return "Rejected by candidate-discovery qualification or entity-resolution rules."
        if self._source_refs(item):
            return "Source-backed entity retained in upstream candidate universe."
        return "Entity retained as diagnostic candidate-universe gap for review."

    @staticmethod
    def _default_product_reason(item: dict[str, Any], product_status: str) -> str:
        if product_status == "product_candidate":
            return "deterministic_qualification_and_upstream_evidence_passed"
        reason = str(item.get("not_candidate_reason") or item.get("reason") or "")
        if reason:
            return reason
        entity_type = str(item.get("entity_type") or "")
        if entity_type and entity_type not in {"legal_entity", "unknown_entity"}:
            return "review_entity_not_standalone_legal_entity"
        if product_status == "review_required":
            return "requires_human_review_before_product_acceptance"
        return "insufficient_product_acceptance_evidence"

    @staticmethod
    def _default_public_status(item: dict[str, Any], outcome: str) -> str:
        if outcome == "rejected_noise":
            return "not_promoted_to_public_candidate"
        if str(item.get("status") or "") == "gap":
            return "not_promoted_to_public_candidate"
        return "retained_in_candidate_universe"

    @staticmethod
    def _default_public_reason(item: dict[str, Any], product_status: str, public_status: str) -> str:
        reason = str(item.get("reason") or item.get("not_candidate_reason") or "")
        if reason:
            return reason
        if public_status == "public_candidate":
            return "promoted_to_public_candidate_row"
        if product_status == "product_candidate":
            return "product_candidate_retained_outside_public_page"
        entity_type = str(item.get("entity_type") or "")
        if entity_type and entity_type not in {"legal_entity", "unknown_entity"}:
            return "review_entity_not_standalone_legal_entity"
        return "requires_review_before_public_candidate_row"

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
