"""CLI for live Radar root-namespace regression proof."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from time import monotonic, sleep
from typing import Any

import httpx

from power_web_os.application.radar.validation.namespace_closure import (
    RadarNamespaceClosureValidator,
)
from power_web_os.radar_evaluation import evaluate_radar_dossier, load_evaluation_baseline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m power_web_os.radar_namespace_validation")
    parser.add_argument("--slice", dest="slice_id", default="0.7.6.4.19")
    parser.add_argument("--candidate-baseline-run-id", required=True)
    parser.add_argument("--candidate-live-run-id", required=True)
    parser.add_argument("--signal-baseline-initial-run-id", required=True)
    parser.add_argument("--signal-baseline-incremental-run-id", required=True)
    parser.add_argument("--signal-live-initial-run-id", required=True)
    parser.add_argument("--signal-live-incremental-run-id", required=True)
    parser.add_argument("--api-url", default="http://127.0.0.1:8001")
    parser.add_argument(
        "--candidate-baseline",
        type=Path,
        default=Path("demo/fixtures/radar_evaluation/sibur_contour_baseline.json"),
    )
    parser.add_argument(
        "--signal-acceptance",
        type=Path,
        default=Path(
            "docs/radar/pipelines/signal-monitoring/to-be/"
            "RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.2.acceptance.json"
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/radar/pipelines/validation/0.7.6.4.19"),
    )
    parser.add_argument("--skip-service-restart", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.slice_id != "0.7.6.4.19":
        raise ValueError("Radar namespace validator only supports slice 0.7.6.4.19.")
    controls = _dict(_read_json(args.signal_acceptance).get("live_acceptance"))
    with httpx.Client(base_url=args.api_url.rstrip("/"), timeout=90.0) as client:
        candidate_baseline = _candidate_evaluation(
            client, args.candidate_baseline_run_id, args.candidate_baseline
        )
        candidate_live = _candidate_evaluation(
            client, args.candidate_live_run_id, args.candidate_baseline
        )
        candidate_run = _get(client, f"/api/radar-runs/{args.candidate_live_run_id}")
        candidate_rows = _list(
            _get(client, f"/api/radar-runs/{args.candidate_live_run_id}/candidates").get("candidates")
        )
        baseline_trace = _get(
            client, f"/api/radar-runs/{args.candidate_baseline_run_id}/technical-trace"
        )
        live_trace = _get(
            client, f"/api/radar-runs/{args.candidate_live_run_id}/technical-trace"
        )
        signal_baseline_initial = _signal_report(client, args.signal_baseline_initial_run_id)
        signal_baseline_incremental = _signal_report(client, args.signal_baseline_incremental_run_id)
        signal_live_initial = _signal_report(client, args.signal_live_initial_run_id)
        signal_live_incremental = _signal_report(client, args.signal_live_incremental_run_id)
        latest_candidate_run_id = _latest_candidate_run_id(
            client, str(candidate_run.get("radar_id") or "")
        )

    restart_round_trip = {
        "candidate_run": False,
        "candidate_trace": False,
        "signal_initial": False,
        "signal_incremental": False,
    }
    if not args.skip_service_restart:
        _restart_services()
        _wait_for_api(args.api_url)
        with httpx.Client(base_url=args.api_url.rstrip("/"), timeout=90.0) as client:
            restart_round_trip = {
                "candidate_run": _get(client, f"/api/radar-runs/{args.candidate_live_run_id}").get(
                    "run_id"
                )
                == args.candidate_live_run_id,
                "candidate_trace": _get(
                    client, f"/api/radar-runs/{args.candidate_live_run_id}/technical-trace"
                ).get("run_id")
                == args.candidate_live_run_id,
                "signal_initial": _signal_report(client, args.signal_live_initial_run_id).get(
                    "signal_run_id"
                )
                == args.signal_live_initial_run_id,
                "signal_incremental": _signal_report(
                    client, args.signal_live_incremental_run_id
                ).get("signal_run_id")
                == args.signal_live_incremental_run_id,
            }

    report = RadarNamespaceClosureValidator().validate(
        candidate_baseline_evaluation=candidate_baseline,
        candidate_live_evaluation=candidate_live,
        candidate_baseline_trace=baseline_trace,
        candidate_live_trace=live_trace,
        candidate_live_run=candidate_run,
        candidate_live_rows=candidate_rows,
        signal_baseline_initial=signal_baseline_initial,
        signal_baseline_incremental=signal_baseline_incremental,
        signal_live_initial=signal_live_initial,
        signal_live_incremental=signal_live_incremental,
        signal_controls=controls,
        latest_candidate_run_id=latest_candidate_run_id,
        restart_round_trip=restart_round_trip,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "candidate_live_evaluation.json").write_text(
        json.dumps(candidate_live, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    RadarNamespaceClosureValidator.write(report, output_dir=args.output_dir)
    print(f"validation_status={report['validation_status']}")
    for key, value in _dict(report.get("run_ids")).items():
        print(f"{key}={value}")
    return 0 if report["validation_status"] == "PASS" else 1


def _candidate_evaluation(
    client: httpx.Client,
    run_id: str,
    baseline_path: Path,
) -> dict[str, Any]:
    run = _get(client, f"/api/radar-runs/{run_id}")
    dossier = _get(client, f"/api/radar-runs/{run_id}/dossier")
    return evaluate_radar_dossier(
        run=run,
        dossier=dossier,
        baseline=load_evaluation_baseline(baseline_path),
    )


def _signal_report(client: httpx.Client, run_id: str) -> dict[str, Any]:
    return _get(client, f"/api/signal-monitoring-runs/{run_id}/report")


def _latest_candidate_run_id(client: httpx.Client, radar_id: str) -> str:
    response = client.get(f"/api/radars/{radar_id}/runs", params={"limit": 20})
    response.raise_for_status()
    for item in response.json():
        if item.get("pipeline_id") == "candidate_discovery" and item.get("status") == "completed":
            return str(item.get("run_id") or "")
    return ""


def _get(client: httpx.Client, path: str) -> dict[str, Any]:
    response = client.get(path)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError(f"Expected object response from {path}.")
    return dict(payload)


def _restart_services() -> None:
    completed = subprocess.run(
        ["docker", "compose", "restart", "api", "worker"],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr or completed.stdout)


def _wait_for_api(api_url: str, *, timeout_seconds: float = 120.0) -> None:
    deadline = monotonic() + timeout_seconds
    while monotonic() < deadline:
        try:
            response = httpx.get(f"{api_url.rstrip('/')}/health", timeout=5.0)
            if response.status_code == 200:
                return
        except httpx.TransportError:
            pass
        sleep(2.0)
    raise TimeoutError("Radar API did not recover after service restart.")


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected object JSON in {path}.")
    return dict(payload)


def _dict(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _list(value: object) -> list[dict[str, Any]]:
    return [dict(item) for item in value if isinstance(item, dict)] if isinstance(value, list) else []


if __name__ == "__main__":
    sys.exit(main())
