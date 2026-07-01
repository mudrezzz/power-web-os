from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from power_web_os.roadmap.exporter import export_slices_jsonl, render_slices_jsonl
from power_web_os.roadmap.importer import import_slices_from_markdown
from power_web_os.roadmap.models import RoadmapSlice, SliceLink
from power_web_os.roadmap.renderer import render_roadmap
from power_web_os.roadmap.sqlite_repository import SQLiteRoadmapRepository


SAMPLE_ROADMAP = """# ROADMAP.md

## Slice Backlog

### Slice 0.7.6.4.0: Done slice

- Status: `Done`
- Goal: Already done.
- User value: Clear history.

### Slice 0.7.6.4.0.1: Tracker slice

- Status: `Ready`
- Goal: Add tracker.
- User value:
  - Agent queries structured data.
- Tests:
  - import works.

### Slice 0.7.6.4.1: Next slice

- Status: `Backlog`
- Goal: Continue.

### Slice 0.7: Old backlog

- Status: `Backlog`
- Goal: Preserve old text.
"""


def test_sqlite_repository_crud_and_ordering(tmp_path: Path) -> None:
    repository = SQLiteRoadmapRepository(tmp_path / "roadmap.sqlite")
    repository.upsert_slice(
        RoadmapSlice(
            id="0.7.6.4.1",
            title="Signal monitoring",
            status="Backlog",
            track="radar",
            sections={"Status": "Backlog", "Goal": "Design signal monitoring."},
        )
    )
    repository.upsert_slice(
        RoadmapSlice(
            id="0.7.6.4.0.1",
            title="Tracker",
            status="Ready",
            track="radar",
            sections={"Status": "Ready", "Goal": "Add tracker."},
        )
    )

    assert [item.id for item in repository.list_slices(track="radar")] == ["0.7.6.4.0.1", "0.7.6.4.1"]
    assert repository.get_slice("0.7.6.4.0.1") is not None

    repository.update_status("0.7.6.4.1", "Done", note="validated")
    assert repository.get_slice("0.7.6.4.1").status == "Done"  # type: ignore[union-attr]

    repository.add_link(SliceLink(slice_id="0.7.6.4.1", link_type="doc", target="docs/example.md"))
    repository.set_meta("next_recommended_task", "Slice 0.7.6.4.1")
    assert repository.get_meta("next_recommended_task") == "Slice 0.7.6.4.1"


def test_importer_preserves_active_chain_and_legacy_suffix(tmp_path: Path) -> None:
    roadmap = tmp_path / "ROADMAP.md"
    roadmap.write_text(SAMPLE_ROADMAP, encoding="utf-8")

    slices, prefix, suffix = import_slices_from_markdown(roadmap)

    assert [item.id for item in slices] == ["0.7.6.4.0", "0.7.6.4.0.1", "0.7.6.4.1"]
    assert slices[1].status == "Ready"
    assert "Agent queries structured data" in slices[1].sections["User value"]
    assert "## Slice Backlog" in prefix
    assert suffix.startswith("### Slice 0.7: Old backlog")


def test_renderer_and_export_are_deterministic(tmp_path: Path) -> None:
    roadmap = tmp_path / "ROADMAP.md"
    roadmap.write_text(SAMPLE_ROADMAP, encoding="utf-8")
    repository = SQLiteRoadmapRepository(tmp_path / "roadmap.sqlite")
    slices, prefix, suffix = import_slices_from_markdown(roadmap)
    for item in slices:
        repository.upsert_slice(item)
    repository.set_meta("legacy_prefix", prefix)
    repository.set_meta("legacy_suffix", suffix)
    repository.set_meta("next_recommended_task", "Slice 0.7.6.4.0.1")

    first_markdown = render_roadmap(repository)
    second_markdown = render_roadmap(repository)
    assert first_markdown == second_markdown
    assert "Source database: docs/roadmap/roadmap.sqlite" in first_markdown
    assert "### Slice 0.7.6.4.0.1: Tracker slice" in first_markdown
    assert "### Slice 0.7: Old backlog" in first_markdown
    assert "## Next Recommended Task" in first_markdown
    assert "Slice 0.7.6.4.0.1" in first_markdown

    export_path = tmp_path / "slices.export.jsonl"
    first_export = export_slices_jsonl(repository, export_path)
    second_export = render_slices_jsonl(repository)
    assert first_export == second_export
    assert '"id": "0.7.6.4.1"' in first_export


def test_cli_import_list_show_render_and_check(tmp_path: Path) -> None:
    roadmap = tmp_path / "ROADMAP.md"
    roadmap.write_text(SAMPLE_ROADMAP, encoding="utf-8")
    db_path = tmp_path / "roadmap.sqlite"
    export_path = tmp_path / "slices.export.jsonl"

    def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "power_web_os.roadmap", "--db", str(db_path), *args],
            check=True,
            text=True,
            capture_output=True,
        )

    run_cli("init")
    run_cli("import-current", "--from", str(roadmap))
    listing = run_cli("list", "--track", "radar").stdout
    assert "0.7.6.4.0.1" in listing
    assert "Tracker slice" in run_cli("show", "0.7.6.4.0.1").stdout

    run_cli("export", "--output", str(export_path))
    run_cli("render", "--output", str(roadmap))
    assert run_cli("check", "--roadmap", str(roadmap), "--export", str(export_path)).returncode == 0
    run_cli("set-meta", "next_recommended_task", "Slice 0.7.6.4.1")


def test_current_roadmap_tracker_artifacts_are_up_to_date() -> None:
    db_path = Path("docs/roadmap/roadmap.sqlite")
    export_path = Path("docs/roadmap/slices.export.jsonl")
    assert db_path.exists()
    assert export_path.exists()

    repository = SQLiteRoadmapRepository(db_path)
    ids = {item.id for item in repository.list_slices(track="radar")}
    for expected in [
        "0.7.6.4.0",
        "0.7.6.4.0.1",
        "0.7.6.4.1",
        "0.7.6.4.2",
        "0.7.6.4.3",
        "0.7.6.4.4",
        "0.7.6.4.5",
        "0.7.6.4.6",
    ]:
        assert expected in ids

    assert render_slices_jsonl(repository) == export_path.read_text(encoding="utf-8")
    assert render_roadmap(repository) == Path("ROADMAP.md").read_text(encoding="utf-8")
