"""Reconcile persisted Radar output summaries with the canonical public surface."""

from __future__ import annotations

from dataclasses import dataclass

from power_web_os.application.ports import RadarRunOutputRepository
from power_web_os.application.radar.candidate_discovery.execution.stored_public_surface import (
    StoredCandidatePublicSurfaceProjector,
)


@dataclass(frozen=True, slots=True)
class RadarOutputSummaryReconciliationResult:
    scanned: int = 0
    updated: int = 0
    unchanged: int = 0
    invalid: int = 0

    def to_payload(self) -> dict[str, int]:
        return {
            "scanned": self.scanned,
            "updated": self.updated,
            "unchanged": self.unchanged,
            "invalid": self.invalid,
        }


class RadarOutputSummaryReconciliationService:
    def __init__(self, repository: RadarRunOutputRepository) -> None:
        self._repository = repository
        self._projector = StoredCandidatePublicSurfaceProjector()

    def reconcile(self) -> RadarOutputSummaryReconciliationResult:
        scanned = updated = unchanged = invalid = 0
        for output in self._repository.list_all():
            scanned += 1
            try:
                surface = self._projector.project(
                    artifact_payload=output.artifact_payload,
                    candidates_payload=output.candidates_payload,
                )
                summary = self._repository.get_summary(output.run_id)
                legacy_reader = getattr(self._repository, "get_legacy_summary", None)
                legacy_summary = legacy_reader(output.run_id) if legacy_reader else summary
                expected = (
                    surface.candidate_count,
                    surface.candidate_count,
                    surface.accepted_count,
                    surface.review_needed_count,
                )
                actual = (
                    summary.candidate_count,
                    summary.visible_candidate_count,
                    summary.accepted_candidate_count,
                    summary.review_needed_candidate_count,
                ) if summary else None
                legacy_actual = (
                    legacy_summary.candidate_count,
                    legacy_summary.visible_candidate_count,
                    legacy_summary.accepted_candidate_count,
                    legacy_summary.review_needed_candidate_count,
                ) if legacy_summary else None
                if actual == expected and legacy_actual == expected:
                    unchanged += 1
                    continue
                self._repository.upsert(output)
                updated += 1
            except (TypeError, ValueError, KeyError):
                invalid += 1
        return RadarOutputSummaryReconciliationResult(
            scanned=scanned,
            updated=updated,
            unchanged=unchanged,
            invalid=invalid,
        )

    def reconcile_fast_if_complete(self) -> RadarOutputSummaryReconciliationResult:
        coverage = getattr(self._repository, "summary_coverage", lambda: (0, -1))()
        if coverage[0] == coverage[1] and coverage[0] > 0:
            return RadarOutputSummaryReconciliationResult(scanned=coverage[0], unchanged=coverage[0])
        return self.reconcile()
