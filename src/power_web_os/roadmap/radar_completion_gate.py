"""Roadmap completion gate for behavior-changing Radar pipeline slices."""

from __future__ import annotations

import json
from pathlib import Path

from power_web_os.application.radar.validation import RadarPipelineAcceptanceManifest
from power_web_os.roadmap.models import RoadmapSlice


def radar_completion_problems(roadmap_slice: RoadmapSlice, *, root: Path = Path(".")) -> list[str]:
    if roadmap_slice.sections.get("Behavior change", "").strip().lower() != "true":
        return []
    pipeline_id = roadmap_slice.sections.get("Pipeline", "").strip()
    if not pipeline_id:
        return [f"{roadmap_slice.id}: behavior-changing Radar slice has no Pipeline section"]
    manifest_value = roadmap_slice.sections.get("Acceptance manifest", "").strip()
    if not manifest_value:
        return [f"{roadmap_slice.id}: acceptance manifest is not registered"]
    manifest_path = root / manifest_value
    if not manifest_path.exists():
        return [f"{roadmap_slice.id}: missing acceptance manifest {manifest_value}"]
    manifest = RadarPipelineAcceptanceManifest.load(manifest_path)
    problems: list[str] = []
    for value in (manifest.to_be_markdown, manifest.to_be_pdf, manifest.as_is_markdown, manifest.as_is_pdf):
        if not (root / value).exists():
            problems.append(f"{roadmap_slice.id}: missing required pipeline artifact {value}")
    validation_path = root / manifest.validation_json
    if not validation_path.exists():
        problems.append(f"{roadmap_slice.id}: missing validation report {manifest.validation_json}")
        return problems
    payload = json.loads(validation_path.read_text(encoding="utf-8"))
    if payload.get("validation_status") != "PASS":
        problems.append(f"{roadmap_slice.id}: validation_status is not PASS")
    failed = [
        item.get("requirement_id")
        for item in payload.get("requirements", [])
        if item.get("status") != "PASS"
    ]
    if failed:
        problems.append(f"{roadmap_slice.id}: failed or missing requirements: {', '.join(map(str, failed))}")
    to_be = (root / manifest.to_be_markdown).read_text(encoding="utf-8")
    as_is = (root / manifest.as_is_markdown).read_text(encoding="utf-8")
    if "Status: Implemented" not in to_be:
        problems.append(f"{roadmap_slice.id}: TO BE status is not Implemented")
    if roadmap_slice.id not in as_is:
        problems.append(f"{roadmap_slice.id}: AS IS has no finalized slice change record")
    return problems
