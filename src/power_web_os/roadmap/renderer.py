"""Markdown renderer for the generated Roadmap report."""

from __future__ import annotations

from pathlib import Path
import re

from power_web_os.roadmap.models import RoadmapSlice
from power_web_os.roadmap.repository import RoadmapRepository


GENERATED_NOTE = """<!--
Generated Roadmap section.
Source database: docs/roadmap/roadmap.sqlite
Review export: docs/roadmap/slices.export.jsonl
Render command: python -m power_web_os.roadmap render --output ROADMAP.md
Manual edits to generated slice sections should be temporary; update the tracker and render again.
-->
"""


def render_roadmap(repository: RoadmapRepository) -> str:
    prefix = repository.get_meta("legacy_prefix")
    suffix = repository.get_meta("legacy_suffix")
    next_task = repository.get_meta("next_recommended_task")
    managed = "\n\n".join(render_slice(roadmap_slice) for roadmap_slice in repository.list_slices(track="radar"))
    rendered = prefix.rstrip()
    if GENERATED_NOTE not in rendered:
        rendered = rendered.replace("# ROADMAP.md", "# ROADMAP.md\n\n" + GENERATED_NOTE, 1)
    if managed:
        rendered += "\n\n" + managed
    if suffix:
        suffix_text = suffix.lstrip()
        if next_task:
            suffix_text = _replace_next_recommended_task(suffix_text, next_task)
        rendered += "\n\n" + suffix_text
    elif next_task:
        rendered += "\n\n## Next Recommended Task\n\n" + next_task.strip() + "\n"
    return rendered.rstrip() + "\n"


def render_slice(roadmap_slice: RoadmapSlice) -> str:
    lines = [f"### Slice {roadmap_slice.id}: {roadmap_slice.title}", ""]
    for section in roadmap_slice.section_order():
        value = roadmap_slice.sections.get(section, "").strip()
        if not value:
            continue
        if value.startswith("- "):
            lines.append(f"- {section}:")
            lines.extend(_indent_section_lines(value))
            continue
        if "\n" in value:
            first, rest = value.split("\n", 1)
            lines.append(f"- {section}: {first}".rstrip())
            lines.extend(rest.splitlines())
        else:
            lines.append(f"- {section}: {value}")
    return "\n".join(lines).rstrip()


def _indent_section_lines(value: str) -> list[str]:
    rendered: list[str] = []
    for line in value.splitlines():
        if line.startswith("- "):
            rendered.append("  " + line)
        else:
            rendered.append(line)
    return rendered


def write_roadmap(repository: RoadmapRepository, output_path: Path) -> str:
    text = render_roadmap(repository)
    output_path.write_text(text, encoding="utf-8")
    return text


def _replace_next_recommended_task(text: str, next_task: str) -> str:
    replacement = "## Next Recommended Task\n\n" + next_task.strip() + "\n"
    pattern = re.compile(r"## Next Recommended Task\n\n.*\Z", re.DOTALL)
    if pattern.search(text):
        return pattern.sub(replacement.rstrip(), text)
    return text.rstrip() + "\n\n" + replacement.rstrip()
