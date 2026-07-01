"""Best-effort importer from the current Markdown Roadmap into structured slices."""

from __future__ import annotations

import re
from pathlib import Path

from power_web_os.roadmap.models import RoadmapSlice


SLICE_HEADING_RE = re.compile(r"^### Slice (?P<id>[0-9A-Za-z_.-]+): (?P<title>.+)$")
FIELD_RE = re.compile(r"^- (?P<name>[A-Z][A-Za-z ]+):(?P<value>.*)$")


def import_slices_from_markdown(
    path: Path,
    *,
    start_id: str = "0.7.6.4.0",
    end_before_id: str = "0.7",
    track: str = "radar",
) -> tuple[list[RoadmapSlice], str, str]:
    text = path.read_text(encoding="utf-8")
    sections = _slice_sections(text)
    selected: list[tuple[str, str, str]] = []
    collecting = False
    for slice_id, title, body in sections:
        if slice_id == start_id:
            collecting = True
        if collecting and slice_id == end_before_id:
            break
        if collecting:
            selected.append((slice_id, title, body))
    slices = [RoadmapSlice(id=slice_id, title=title, track=track, sections=_parse_sections(body)) for slice_id, title, body in selected]
    return slices, _legacy_prefix(text, start_id), _legacy_suffix(text, end_before_id)


def _slice_sections(text: str) -> list[tuple[str, str, str]]:
    lines = text.splitlines()
    headings: list[tuple[int, str, str]] = []
    for index, line in enumerate(lines):
        match = SLICE_HEADING_RE.match(line)
        if match:
            headings.append((index, match.group("id"), match.group("title")))
    result: list[tuple[str, str, str]] = []
    for pos, (line_index, slice_id, title) in enumerate(headings):
        next_index = headings[pos + 1][0] if pos + 1 < len(headings) else len(lines)
        body = "\n".join(lines[line_index + 1 : next_index]).strip()
        result.append((slice_id, title, body))
    return result


def _parse_sections(body: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in body.splitlines():
        match = FIELD_RE.match(line)
        if match:
            current = match.group("name")
            sections[current] = [match.group("value").strip()]
            continue
        if current is not None:
            sections[current].append(line)
    parsed = {name: "\n".join(lines).strip() for name, lines in sections.items()}
    if "Status" not in parsed:
        parsed["Status"] = "Backlog"
    return parsed


def _legacy_prefix(text: str, start_id: str) -> str:
    marker = f"### Slice {start_id}:"
    index = text.find(marker)
    return text[:index].rstrip() if index >= 0 else text.rstrip()


def _legacy_suffix(text: str, end_before_id: str) -> str:
    marker = f"### Slice {end_before_id}:"
    index = text.find(marker)
    return text[index:].lstrip() if index >= 0 else ""
