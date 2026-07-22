"""SQLite-backed repository for the local roadmap slice tracker."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from power_web_os.roadmap.models import RoadmapSlice, SliceEvent, SliceLink, VALID_STATUSES, utc_now_iso


class SQLiteRoadmapRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS slices (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    sort_key TEXT NOT NULL,
                    parent_id TEXT,
                    track TEXT NOT NULL,
                    sections_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS slice_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slice_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_time TEXT NOT NULL,
                    note TEXT NOT NULL,
                    FOREIGN KEY(slice_id) REFERENCES slices(id)
                );
                CREATE TABLE IF NOT EXISTS slice_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slice_id TEXT NOT NULL,
                    link_type TEXT NOT NULL,
                    target TEXT NOT NULL,
                    label TEXT NOT NULL DEFAULT '',
                    FOREIGN KEY(slice_id) REFERENCES slices(id)
                );
                CREATE TABLE IF NOT EXISTS roadmap_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """
            )

    def upsert_slice(self, roadmap_slice: RoadmapSlice) -> None:
        self.initialize()
        existing = self.get_slice(roadmap_slice.id)
        created_at = existing.created_at if existing else roadmap_slice.created_at
        updated_at = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO slices (
                    id, title, status, sort_key, parent_id, track, sections_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title,
                    status=excluded.status,
                    sort_key=excluded.sort_key,
                    parent_id=excluded.parent_id,
                    track=excluded.track,
                    sections_json=excluded.sections_json,
                    updated_at=excluded.updated_at
                """,
                (
                    roadmap_slice.id,
                    roadmap_slice.title,
                    roadmap_slice.status,
                    roadmap_slice.sort_key,
                    roadmap_slice.parent_id,
                    roadmap_slice.track,
                    json.dumps(roadmap_slice.sections, ensure_ascii=False, sort_keys=True),
                    created_at,
                    updated_at,
                ),
            )

    def get_slice(self, slice_id: str) -> RoadmapSlice | None:
        self.initialize()
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM slices WHERE id = ?", (slice_id,)).fetchone()
        return self._row_to_slice(row) if row else None

    def list_slices(self, *, status: str | None = None, track: str | None = None) -> list[RoadmapSlice]:
        self.initialize()
        where: list[str] = []
        params: list[str] = []
        if status:
            where.append("status = ?")
            params.append(status)
        if track:
            where.append("track = ?")
            params.append(track)
        query = "SELECT * FROM slices"
        if where:
            query += " WHERE " + " AND ".join(where)
        query += " ORDER BY sort_key, id"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_slice(row) for row in rows]

    def update_status(self, slice_id: str, status: str, *, note: str | None = None) -> None:
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid slice status: {status}")
        roadmap_slice = self.get_slice(slice_id)
        if roadmap_slice is None:
            raise KeyError(f"Unknown slice id: {slice_id}")
        roadmap_slice.status = status
        roadmap_slice.sections["Status"] = status
        roadmap_slice.updated_at = utc_now_iso()
        self.upsert_slice(roadmap_slice)
        self.add_event(SliceEvent(slice_id=slice_id, event_type="status_updated", note=note or status))

    def update_track(self, slice_id: str, track: str) -> None:
        normalized_track = track.strip()
        if not normalized_track:
            raise ValueError("Roadmap track cannot be empty")
        roadmap_slice = self.get_slice(slice_id)
        if roadmap_slice is None:
            raise KeyError(f"Unknown slice id: {slice_id}")
        roadmap_slice.track = normalized_track
        self.upsert_slice(roadmap_slice)
        self.add_event(SliceEvent(slice_id=slice_id, event_type="track_updated", note=normalized_track))

    def set_section(self, slice_id: str, key: str, value: str) -> None:
        roadmap_slice = self.get_slice(slice_id)
        if roadmap_slice is None:
            raise KeyError(f"Unknown slice id: {slice_id}")
        roadmap_slice.sections[key] = value
        self.upsert_slice(roadmap_slice)
        self.add_event(SliceEvent(slice_id=slice_id, event_type="section_updated", note=key))

    def add_event(self, event: SliceEvent) -> None:
        self.initialize()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO slice_events (slice_id, event_type, event_time, note) VALUES (?, ?, ?, ?)",
                (event.slice_id, event.event_type, event.event_time, event.note),
            )

    def add_link(self, link: SliceLink) -> None:
        self.initialize()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO slice_links (slice_id, link_type, target, label) VALUES (?, ?, ?, ?)",
                (link.slice_id, link.link_type, link.target, link.label),
            )

    def set_meta(self, key: str, value: str) -> None:
        self.initialize()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO roadmap_meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )

    def get_meta(self, key: str, default: str = "") -> str:
        self.initialize()
        with self._connect() as conn:
            row = conn.execute("SELECT value FROM roadmap_meta WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _row_to_slice(row: sqlite3.Row) -> RoadmapSlice:
        return RoadmapSlice(
            id=row["id"],
            title=row["title"],
            status=row["status"],
            sort_key=row["sort_key"],
            parent_id=row["parent_id"],
            track=row["track"],
            sections=json.loads(row["sections_json"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
