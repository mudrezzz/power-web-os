"""Structured acceptance evidence for one Radar pipeline slice."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


class RadarPipelineRequirement(BaseModel):
    id: str
    mandatory: bool = True
    description: str
    test_node_ids: list[str] = Field(default_factory=list)


class RadarPipelineAcceptanceManifest(BaseModel):
    schema_version: str = "radar_pipeline_acceptance.v1"
    slice_id: str
    pipeline_id: str
    behavior_change: bool = True
    to_be_markdown: str
    to_be_pdf: str
    as_is_markdown: str
    as_is_pdf: str
    baseline_diagnostic: str = ""
    validation_json: str
    validation_markdown: str
    freeze_record: str = ""
    requirements: list[RadarPipelineRequirement]
    recorded_acceptance: dict[str, Any] = Field(default_factory=dict)
    live_acceptance: dict[str, Any] = Field(default_factory=dict)
    retrospective: list[dict[str, Any]] = Field(default_factory=list)

    @classmethod
    def load(cls, path: Path) -> "RadarPipelineAcceptanceManifest":
        return cls.model_validate_json(path.read_text(encoding="utf-8"))


class RadarPipelineRequirementResult(BaseModel):
    requirement_id: str
    status: Literal["PASS", "FAIL", "MISSING"]
    evidence: list[str] = Field(default_factory=list)
    message: str = ""


class RadarPipelineValidationReport(BaseModel):
    schema_version: str = "radar_pipeline_validation.v1"
    slice_id: str
    pipeline_id: str
    validation_status: Literal["PASS", "FAIL"]
    generated_at: str
    baseline_run_id: str = ""
    first_live_run_id: str = ""
    second_live_run_id: str = ""
    initial_live_run_ids: list[str] = Field(default_factory=list)
    incremental_live_run_id: str = ""
    acceptance_manifest_sha256: str = ""
    control_matrix: dict[str, Any] = Field(default_factory=dict)
    restart_verified: bool = False
    test_exit_code: int | None = None
    requirements: list[RadarPipelineRequirementResult]
    runtime_summary: dict[str, Any] = Field(default_factory=dict)
    deviations: list[dict[str, Any]] = Field(default_factory=list)
