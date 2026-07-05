"""Candidate-universe projection helpers for final execution results."""

from __future__ import annotations

from power_web_os.application.radar.candidate_discovery.contracts import (
    LiveRadarCandidate,
    RadarCandidateUniverseEntry,
)


def candidate_universe_entries(
    *,
    candidates: list[LiveRadarCandidate],
    completed_qualification_ids: list[str],
    origin_task_id: str,
    gap_names: set[str],
) -> list[RadarCandidateUniverseEntry]:
    entries: list[RadarCandidateUniverseEntry] = []
    for candidate in candidates:
        rejection_reasons = [
            item.criterion_code
            for item in candidate.qualification
            if item.criterion_code in completed_qualification_ids
            and item.requirement_level == "required"
            and item.final_assessment == "does_not_match"
        ]
        completed_rules = [item for item in candidate.qualification if item.criterion_code in completed_qualification_ids]
        if rejection_reasons:
            status = "rejected"
        elif any(item.final_assessment in {"unknown", "partially_matches"} for item in completed_rules):
            status = "unknown_review_needed"
        elif completed_rules:
            status = "qualified"
        elif candidate.legal_name in gap_names:
            status = "gap"
        else:
            status = "discovered"
        entries.append(RadarCandidateUniverseEntry(
            candidate_id=candidate.candidate_id,
            legal_name=candidate.legal_name,
            status=status,  # type: ignore[arg-type]
            origin_task_id=origin_task_id,
            source_refs=list(candidate.evidence_refs),
            gate_results=[
                {
                    "criterion_code": item.criterion_code,
                    "final_assessment": item.final_assessment,
                    "confidence": item.confidence,
                    "evidence_refs": list(item.evidence_refs),
                }
                for item in candidate.qualification
                if item.criterion_code in completed_qualification_ids
            ],
            rejection_reasons=rejection_reasons,
            coverage_flags=[flag for flag in candidate.review_flags if "candidate_universe" in flag or "coverage" in flag],
        ))
    return entries
