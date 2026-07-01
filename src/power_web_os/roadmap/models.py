"""Value objects for the local roadmap slice tracker."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import re
from typing import Any


VALID_STATUSES = {"Backlog", "Ready", "In Progress", "Blocked", "Done"}
DEFAULT_SECTION_ORDER = (
    "Status",
    "Goal",
    "User value",
    "Problem statement",
    "Scope",
    "Out of scope",
    "Implementation notes",
    "Tests",
    "Docs",
    "Demo impact",
    "Acceptance criteria",
    "Risks",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slice_sort_key(slice_id: str) -> str:
    parts = re.findall(r"\d+|[A-Za-z]+", slice_id)
    key_parts: list[str] = []
    for part in parts:
        if part.isdigit():
            key_parts.append(f"{int(part):06d}")
        else:
            key_parts.append(part.lower())
    return ".".join(key_parts)


@dataclass(slots=True)
class RoadmapSlice:
    id: str
    title: str
    status: str = "Backlog"
    track: str = "general"
    parent_id: str | None = None
    sort_key: str | None = None
    sections: dict[str, str] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    def __post_init__(self) -> None:
        if self.sections.get("Status"):
            self.status = self.sections["Status"].strip("` ")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"Invalid slice status: {self.status}")
        if not self.sort_key:
            self.sort_key = slice_sort_key(self.id)
        self.sections["Status"] = self.status

    def to_export_record(self) -> dict[str, Any]:
        ordered_sections = {key: self.sections[key] for key in self.section_order() if key in self.sections}
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "sort_key": self.sort_key,
            "parent_id": self.parent_id,
            "track": self.track,
            "sections": ordered_sections,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_export_record(cls, record: dict[str, Any]) -> "RoadmapSlice":
        return cls(
            id=record["id"],
            title=record["title"],
            status=record.get("status", "Backlog"),
            sort_key=record.get("sort_key"),
            parent_id=record.get("parent_id"),
            track=record.get("track", "general"),
            sections=dict(record.get("sections") or {}),
            created_at=record.get("created_at") or utc_now_iso(),
            updated_at=record.get("updated_at") or utc_now_iso(),
        )

    def section_order(self) -> list[str]:
        ordered = [key for key in DEFAULT_SECTION_ORDER if key in self.sections]
        ordered.extend(key for key in self.sections if key not in ordered)
        return ordered

    def as_json_line(self) -> str:
        return json.dumps(self.to_export_record(), ensure_ascii=False, sort_keys=True)


@dataclass(frozen=True, slots=True)
class SliceEvent:
    slice_id: str
    event_type: str
    note: str
    event_time: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True, slots=True)
class SliceLink:
    slice_id: str
    link_type: str
    target: str
    label: str = ""
