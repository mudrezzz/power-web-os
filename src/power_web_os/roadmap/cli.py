"""Command line interface for the local roadmap slice tracker."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from power_web_os.roadmap.exporter import export_slices_jsonl, render_slices_jsonl
from power_web_os.roadmap.importer import import_slices_from_markdown
from power_web_os.roadmap.models import RoadmapSlice, SliceLink, VALID_STATUSES
from power_web_os.roadmap.radar_completion_gate import radar_completion_problems
from power_web_os.roadmap.renderer import render_roadmap, write_roadmap
from power_web_os.roadmap.sqlite_repository import SQLiteRoadmapRepository


DEFAULT_DB_PATH = Path("docs/roadmap/roadmap.sqlite")
DEFAULT_EXPORT_PATH = Path("docs/roadmap/slices.export.jsonl")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m power_web_os.roadmap")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init")

    import_parser = subparsers.add_parser("import-current")
    import_parser.add_argument("--from", dest="source", type=Path, default=Path("ROADMAP.md"))

    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--status", choices=sorted(VALID_STATUSES))
    list_parser.add_argument("--track")

    show_parser = subparsers.add_parser("show")
    show_parser.add_argument("slice_id")

    add_parser = subparsers.add_parser("add-slice")
    add_parser.add_argument("--id", required=True)
    add_parser.add_argument("--title", required=True)
    add_parser.add_argument("--status", default="Backlog", choices=sorted(VALID_STATUSES))
    add_parser.add_argument("--track", default="general")
    add_parser.add_argument("--goal", default="")

    status_parser = subparsers.add_parser("update-status")
    status_parser.add_argument("slice_id")
    status_parser.add_argument("status", choices=sorted(VALID_STATUSES))
    status_parser.add_argument("--note", default="")

    track_parser = subparsers.add_parser("update-track")
    track_parser.add_argument("slice_id")
    track_parser.add_argument("track")

    section_parser = subparsers.add_parser("set-section")
    section_parser.add_argument("slice_id")
    section_parser.add_argument("key")
    section_parser.add_argument("value")

    link_parser = subparsers.add_parser("link")
    link_parser.add_argument("slice_id")
    link_parser.add_argument("--type", required=True, dest="link_type")
    link_parser.add_argument("--target", required=True)
    link_parser.add_argument("--label", default="")

    meta_parser = subparsers.add_parser("set-meta")
    meta_parser.add_argument("key")
    meta_parser.add_argument("value")

    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--output", type=Path, default=DEFAULT_EXPORT_PATH)

    render_parser = subparsers.add_parser("render")
    render_parser.add_argument("--output", type=Path, default=Path("ROADMAP.md"))

    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("--roadmap", type=Path, default=Path("ROADMAP.md"))
    check_parser.add_argument("--export", type=Path, default=DEFAULT_EXPORT_PATH)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repository = SQLiteRoadmapRepository(args.db)
    try:
        return _run(args, repository)
    except (KeyError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


def _run(args: argparse.Namespace, repository: SQLiteRoadmapRepository) -> int:
    if args.command == "init":
        repository.initialize()
        print(f"Initialized roadmap tracker at {repository.db_path}")
        return 0
    if args.command == "import-current":
        repository.initialize()
        slices, prefix, suffix = import_slices_from_markdown(args.source)
        for roadmap_slice in slices:
            repository.upsert_slice(roadmap_slice)
        repository.set_meta("legacy_prefix", prefix)
        repository.set_meta("legacy_suffix", suffix)
        repository.set_meta(
            "next_recommended_task",
            "Slice 0.7.6.4.0.1: SQLite slice tracker and generated Roadmap report",
        )
        print(f"Imported {len(slices)} slices from {args.source}")
        return 0
    if args.command == "list":
        for roadmap_slice in repository.list_slices(status=args.status, track=args.track):
            print(f"{roadmap_slice.id}\t{roadmap_slice.status}\t{roadmap_slice.title}")
        return 0
    if args.command == "show":
        roadmap_slice = repository.get_slice(args.slice_id)
        if roadmap_slice is None:
            raise KeyError(f"Unknown slice id: {args.slice_id}")
        print(f"{roadmap_slice.id}: {roadmap_slice.title}")
        for key in roadmap_slice.section_order():
            value = roadmap_slice.sections[key]
            if "\n" in value or value.startswith("- "):
                print(f"{key}:")
                print(value)
            else:
                print(f"{key}: {value}")
        return 0
    if args.command == "add-slice":
        sections = {"Status": args.status}
        if args.goal:
            sections["Goal"] = args.goal
        repository.upsert_slice(
            RoadmapSlice(id=args.id, title=args.title, status=args.status, track=args.track, sections=sections)
        )
        print(f"Added slice {args.id}")
        return 0
    if args.command == "update-status":
        if args.status == "Done":
            roadmap_slice = repository.get_slice(args.slice_id)
            if roadmap_slice is None:
                raise KeyError(f"Unknown slice id: {args.slice_id}")
            problems = radar_completion_problems(roadmap_slice)
            if problems:
                raise ValueError("\n".join(problems))
        repository.update_status(args.slice_id, args.status, note=args.note)
        print(f"Updated {args.slice_id} to {args.status}")
        return 0
    if args.command == "update-track":
        repository.update_track(args.slice_id, args.track)
        print(f"Updated {args.slice_id} track to {args.track}")
        return 0
    if args.command == "set-section":
        repository.set_section(args.slice_id, args.key, args.value)
        print(f"Updated {args.slice_id} section {args.key}")
        return 0
    if args.command == "link":
        repository.add_link(
            SliceLink(slice_id=args.slice_id, link_type=args.link_type, target=args.target, label=args.label)
        )
        print(f"Linked {args.slice_id} -> {args.target}")
        return 0
    if args.command == "set-meta":
        repository.set_meta(args.key, args.value)
        print(f"Set roadmap meta {args.key}")
        return 0
    if args.command == "export":
        export_slices_jsonl(repository, args.output)
        print(f"Exported roadmap slices to {args.output}")
        return 0
    if args.command == "render":
        write_roadmap(repository, args.output)
        print(f"Rendered roadmap to {args.output}")
        return 0
    if args.command == "check":
        expected_roadmap = render_roadmap(repository)
        expected_export = render_slices_jsonl(repository)
        actual_roadmap = args.roadmap.read_text(encoding="utf-8") if args.roadmap.exists() else ""
        actual_export = args.export.read_text(encoding="utf-8") if args.export.exists() else ""
        problems = []
        if actual_roadmap != expected_roadmap:
            problems.append(f"{args.roadmap} is stale")
        if actual_export != expected_export:
            problems.append(f"{args.export} is stale")
        for roadmap_slice in repository.list_slices():
            if roadmap_slice.status == "Done":
                problems.extend(radar_completion_problems(roadmap_slice))
        if problems:
            for problem in problems:
                print(problem, file=sys.stderr)
            return 1
        print("Roadmap tracker artifacts are up to date")
        return 0
    raise ValueError(f"Unknown command: {args.command}")
