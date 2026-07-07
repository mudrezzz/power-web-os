"""Qualification contract validation for normalized live Radar candidates."""

from __future__ import annotations

from typing import Any

from power_web_os.application.radar.candidate_discovery.contracts import (
    LiveRadarCandidate,
    QualificationContractIssue,
    RadarSourceEvidence,
)


def validate_live_radar_qualification_contract(
    *,
    candidates: list[LiveRadarCandidate],
    sources: list[RadarSourceEvidence],
    radar: dict[str, Any],
) -> list[QualificationContractIssue]:
    issues: list[QualificationContractIssue] = []
    rule_codes = {str(item.get("code")) for item in radar.get("qualification_criteria", [])}
    source_refs = {source.evidence_ref for source in sources}
    for candidate_index, candidate in enumerate(candidates):
        candidate_path = f"candidates[{candidate_index}]"
        result_codes = {item.criterion_code for item in candidate.qualification}
        missing = sorted(rule_codes - result_codes)
        extra = sorted(result_codes - rule_codes)
        for code in missing:
            issues.append(QualificationContractIssue(
                severity="error",
                path=f"{candidate_path}.qualification.{code}",
                message="Qualification result is missing for radar rule.",
            ))
        for code in extra:
            issues.append(QualificationContractIssue(
                severity="error",
                path=f"{candidate_path}.qualification.{code}",
                message="Qualification result references an unknown radar rule.",
            ))
        for item in candidate.qualification:
            item_path = f"{candidate_path}.qualification.{item.criterion_code}"
            for ref in item.evidence_refs:
                if ref not in source_refs:
                    issues.append(QualificationContractIssue(
                        severity="error",
                        path=f"{item_path}.evidence_refs",
                        message=f"Evidence ref {ref} is not present in sources.",
                    ))
            if item.requirement_level == "required" and item.final_assessment in {"does_not_match", "unknown"}:
                issues.append(QualificationContractIssue(
                    severity="warning",
                    path=item_path,
                    message="Required qualification rule is not satisfied and needs human review.",
                ))
            if item.cross_validation.required and item.cross_validation.status != "passed":
                issues.append(QualificationContractIssue(
                    severity="warning",
                    path=f"{item_path}.cross_validation",
                    message="Cross-validation requirement is not fully satisfied.",
                ))
    return issues
