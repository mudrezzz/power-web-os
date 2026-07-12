"""Argument and dispatch helpers for Radar benchmark demo commands."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from power_web_os.radar_benchmark import generate_radar_benchmark_report
from power_web_os.radar_coverage_probe import generate_radar_coverage_probe_report
from power_web_os.radar_evaluation_runner import generate_radar_evaluation_report


def configure_benchmark_demo_arguments(parser: Any, *, root: Path) -> None:
    parser.add_argument("--benchmark-output", type=Path, default=root / "demo" / "output" / "radar_benchmark_report.json")
    parser.add_argument("--benchmark-poll-interval-seconds", type=float, default=5.0)
    parser.add_argument("--benchmark-timeout-seconds", type=float, default=2400.0)
    parser.add_argument(
        "--benchmark-profile",
        choices=("benchmark_smoke", "benchmark_live", "blind_benchmark"),
        default="benchmark_smoke",
    )
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--latest", action="store_true")
    parser.add_argument(
        "--baseline",
        type=Path,
        default=root / "demo" / "fixtures" / "radar_evaluation" / "sibur_contour_baseline.json",
    )
    parser.add_argument("--evaluation-output", type=Path, default=root / "demo" / "output" / "radar_evaluation_report.json")
    parser.add_argument("--coverage-output", type=Path, default=root / "demo" / "output" / "radar_coverage_probe_report.json")
    parser.add_argument("--probe-limit", type=int, default=5)


def run_benchmark_demo_command(args: Any) -> dict[str, Any] | None:
    if args.command == "run-radar-benchmark":
        profile = args.profile if args.profile in {"benchmark_smoke", "benchmark_live", "blind_benchmark"} else args.benchmark_profile
        return generate_radar_benchmark_report(
            api_url=args.api_url,
            profile=profile,
            radar_id=args.radar_id,
            output_path=args.benchmark_output,
            poll_interval_seconds=args.benchmark_poll_interval_seconds,
            timeout_seconds=args.benchmark_timeout_seconds,
        )
    if args.command == "evaluate-radar-benchmark":
        return generate_radar_evaluation_report(
            api_url=args.api_url,
            run_id=args.run_id,
            radar_id=args.radar_id,
            latest=args.latest,
            baseline_path=args.baseline,
            output_path=args.evaluation_output,
        )
    if args.command == "probe-radar-coverage":
        return generate_radar_coverage_probe_report(
            api_url=args.api_url,
            run_id=args.run_id,
            radar_id=args.radar_id,
            latest=args.latest,
            baseline_path=args.baseline,
            output_path=args.coverage_output,
            probe_limit=args.probe_limit,
        )
    return None
