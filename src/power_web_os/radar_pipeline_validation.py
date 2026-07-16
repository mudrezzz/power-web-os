"""CLI for auditable Radar pipeline slice acceptance."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

import httpx

from power_web_os.application.radar.validation import RadarPipelineSliceValidator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m power_web_os.radar_pipeline_validation")
    parser.add_argument("--pipeline", required=True, choices=["candidate-discovery", "signal-monitoring", "power-web-discovery"])
    parser.add_argument("--slice", required=True, dest="slice_id")
    parser.add_argument("--baseline-run-id", default="")
    parser.add_argument("--first-live-run-id", default="")
    parser.add_argument("--second-live-run-id", default="")
    parser.add_argument("--initial-live-run-id", action="append", default=[])
    parser.add_argument("--incremental-live-run-id", default="")
    parser.add_argument("--restart-verified", action="store_true")
    parser.add_argument("--api-url", default="http://127.0.0.1:8001")
    parser.add_argument("--skip-tests", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest = _manifest_path(args.pipeline, args.slice_id)
    first = _load_report(args.api_url, args.pipeline, args.first_live_run_id)
    second = _load_report(args.api_url, args.pipeline, args.second_live_run_id)
    initial = [_load_report(args.api_url, args.pipeline, item) for item in args.initial_live_run_id]
    incremental = _load_report(args.api_url, args.pipeline, args.incremental_live_run_id)
    report = RadarPipelineSliceValidator().validate(
        manifest_path=manifest,
        first_live_report=first,
        second_live_report=second,
        initial_live_reports=initial,
        incremental_live_report=incremental,
        restart_verified=args.restart_verified,
        baseline_run_id=args.baseline_run_id,
        run_tests=not args.skip_tests,
    )
    print(f"validation_status={report.validation_status}")
    print(f"first_live_run_id={report.first_live_run_id or 'missing'}")
    print(f"second_live_run_id={report.second_live_run_id or 'missing'}")
    print(f"initial_live_run_ids={','.join(report.initial_live_run_ids) or 'missing'}")
    print(f"incremental_live_run_id={report.incremental_live_run_id or 'missing'}")
    for item in report.requirements:
        print(f"{item.requirement_id}={item.status}")
    return 0 if report.validation_status == "PASS" else 1


def _manifest_path(pipeline_id: str, slice_id: str) -> Path:
    prefix = {
        "signal-monitoring": "RADAR_SIGNAL_MONITORING_TO_BE_",
        "power-web-discovery": "RADAR_POWER_WEB_DISCOVERY_TO_BE_",
        "candidate-discovery": "RADAR_SEARCH_PIPELINE_TO_BE_",
    }[pipeline_id]
    folder = {
        "signal-monitoring": Path("docs/radar/pipelines/signal-monitoring/to-be"),
        "power-web-discovery": Path("docs/radar/pipelines/power-web-discovery/to-be"),
        "candidate-discovery": Path("docs/radar/to-be"),
    }[pipeline_id]
    return folder / f"{prefix}{slice_id}.acceptance.json"


def _load_report(api_url: str, pipeline_id: str, run_id: str) -> dict[str, Any]:
    if not run_id:
        return {}
    if pipeline_id != "signal-monitoring":
        raise ValueError(f"Runtime report loading is not implemented for {pipeline_id}.")
    response = httpx.get(
        f"{api_url.rstrip('/')}/api/signal-monitoring-runs/{run_id}/report",
        timeout=60.0,
    )
    response.raise_for_status()
    return dict(response.json())


if __name__ == "__main__":
    sys.exit(main())
