"""Deterministic JSONL export for roadmap slice review."""

from __future__ import annotations

from pathlib import Path

from power_web_os.roadmap.repository import RoadmapRepository


def export_slices_jsonl(repository: RoadmapRepository, output_path: Path) -> str:
    lines = [roadmap_slice.as_json_line() for roadmap_slice in repository.list_slices()]
    text = "\n".join(lines) + ("\n" if lines else "")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    return text


def render_slices_jsonl(repository: RoadmapRepository) -> str:
    lines = [roadmap_slice.as_json_line() for roadmap_slice in repository.list_slices()]
    return "\n".join(lines) + ("\n" if lines else "")
