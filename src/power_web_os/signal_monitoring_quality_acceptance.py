"""Frozen A/B/incremental live acceptance for Signal Monitoring quality."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from time import monotonic, sleep
from typing import Any
from uuid import uuid4

import httpx

from power_web_os.application.radar.validation import RadarPipelineSliceValidator
from power_web_os.application.radar.validation.acceptance_freeze import (
    verify_acceptance_freeze,
    write_acceptance_freeze,
)
from power_web_os.application.radar.validation.contracts import RadarPipelineAcceptanceManifest
from power_web_os.application.radar.validation.signal_monitoring_quality import control_match_summary


DEFAULT_MANIFEST = Path(
    "docs/radar/pipelines/signal-monitoring/to-be/"
    "RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.19.1.acceptance.json"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m power_web_os.signal_monitoring_quality_acceptance")
    parser.add_argument("command", choices=["prepare", "run", "retry-second", "verify"])
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--api-url", default="http://127.0.0.1:8001")
    parser.add_argument("--poll-interval-seconds", type=float, default=3.0)
    parser.add_argument("--timeout-seconds", type=float, default=1800.0)
    parser.add_argument("--failed-run-id", default="")
    parser.add_argument("--skip-tests", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest_path = args.manifest.resolve()
    manifest = RadarPipelineAcceptanceManifest.load(manifest_path)
    freeze_path = Path(manifest.freeze_record).resolve()
    if args.command == "prepare":
        commit = _git_commit()
        record = write_acceptance_freeze(
            manifest_path=manifest_path,
            output_path=freeze_path,
            git_commit=commit,
        )
        record["slice_id"] = manifest.slice_id
        record["acceptance_session_id"] = uuid4().hex[:12]
        _write_json(freeze_path, record)
        print(f"manifest_sha256={record['manifest_sha256']}")
        print(f"freeze_record={freeze_path}")
        return 0
    freeze = verify_acceptance_freeze(manifest_path=manifest_path, freeze_path=freeze_path)
    if args.command == "retry-second":
        _reset_second_attempt(
            freeze=freeze,
            freeze_path=freeze_path,
            failed_run_id=args.failed_run_id,
        )
        print(f"retained_initial_run_id={freeze['initial_live_run_ids'][0]}")
        print(f"replacement_series_id={freeze['monitoring_series_ids'][1]}")
        return 0
    if args.command == "run":
        if freeze.get("incremental_live_run_id"):
            raise RuntimeError("Acceptance session is already complete; use verify or prepare a new session.")
        _run_session(
            manifest=manifest,
            freeze=freeze,
            freeze_path=freeze_path,
            api_url=args.api_url,
            poll_interval=args.poll_interval_seconds,
            timeout=args.timeout_seconds,
        )
        return 0
    return _verify_session(
        manifest=manifest,
        manifest_path=manifest_path,
        freeze=freeze,
        api_url=args.api_url,
        run_tests=not args.skip_tests,
    )


def _reset_second_attempt(
    *,
    freeze: dict[str, Any],
    freeze_path: Path,
    failed_run_id: str = "",
) -> None:
    initial_ids = [str(item) for item in freeze.get("initial_live_run_ids", [])]
    series_ids = [str(item) for item in freeze.get("monitoring_series_ids", [])]
    if len(series_ids) != 2 or len(initial_ids) not in {1, 2}:
        raise RuntimeError("A retained initial run and a second series are required before replacing B.")
    if len(initial_ids) == 1 and not failed_run_id:
        raise RuntimeError("--failed-run-id is required when B stopped before producing a report.")
    second_run_id = initial_ids[1] if len(initial_ids) == 2 else failed_run_id
    superseded = list(freeze.get("superseded_live_attempts") or [])
    superseded.append({
        "initial_run_id": second_run_id,
        "incremental_run_id": str(freeze.get("incremental_live_run_id") or ""),
        "monitoring_series_id": series_ids[1],
        "reason": "second_initial_run_failed_frozen_reproducibility_gate",
        "recorded_at": _now(),
    })
    suffix = re.search(r"-b(\d+)?$", series_ids[1])
    current_number = int(suffix.group(1) or "1") if suffix else 1
    replacement_number = max(len(superseded) + 1, current_number + 1)
    session_id = str(freeze.get("acceptance_session_id") or uuid4().hex[:12])
    freeze["superseded_live_attempts"] = superseded
    freeze["monitoring_series_ids"] = [series_ids[0], f"sm-{session_id}-b{replacement_number}"]
    freeze["initial_live_run_ids"] = [initial_ids[0]]
    freeze["incremental_live_run_id"] = ""
    freeze["pre_restart_report_sha256"] = {}
    partial = dict(freeze.get("partial_report_sha256") or {})
    freeze["partial_report_sha256"] = {
        initial_ids[0]: partial.get(initial_ids[0], ""),
    }
    _write_json(freeze_path, freeze)


def _run_session(
    *,
    manifest: RadarPipelineAcceptanceManifest,
    freeze: dict[str, Any],
    freeze_path: Path,
    api_url: str,
    poll_interval: float,
    timeout: float,
) -> None:
    live = manifest.live_acceptance
    source_run_id = str(live["source_candidate_run_id"])
    session_id = str(freeze.get("acceptance_session_id") or uuid4().hex[:12])
    with httpx.Client(base_url=api_url.rstrip("/"), timeout=60.0) as client:
        source = _get(client, f"/api/radar-runs/{source_run_id}")
        radar_id = str(source["radar_id"])
        series_ids = list(freeze.get("monitoring_series_ids") or [f"sm-{session_id}-a", f"sm-{session_id}-b"])
        existing_ids = [str(item) for item in freeze.get("initial_live_run_ids", [])]
        if len(series_ids) != 2 or len(existing_ids) > 2:
            raise RuntimeError("Frozen acceptance session contains an invalid A/B state.")
        initial = [_get(client, f"/api/signal-monitoring-runs/{run_id}") for run_id in existing_ids]
        initial_reports = [
            _get(client, f"/api/signal-monitoring-runs/{run_id}/report") for run_id in existing_ids
        ]
        if initial_reports:
            _assert_initial_quality_gate(report=initial_reports[0], live=live)
        for index in range(len(initial), 2):
            series_id = series_ids[index]
            preflight = _preflight(client, radar_id=radar_id, live=live, series_id=series_id, lookback_days=365)
            if not preflight.get("ready_for_live_run"):
                raise RuntimeError(f"Initial preflight failed for {series_id}: {preflight.get('issues')}")
            if preflight.get("previous_source_key_count") or preflight.get("previous_watermark_count"):
                raise RuntimeError(f"Initial series {series_id} is contaminated by previous history.")
            completed = _queue_and_wait(
                client,
                radar_id=radar_id,
                live=live,
                series_id=series_id,
                lookback_days=365,
                poll_interval=poll_interval,
                timeout=timeout,
            )
            initial.append(completed)
            report = _get(client, f"/api/signal-monitoring-runs/{completed['run_id']}/report")
            initial_reports.append(report)
            freeze["radar_id"] = radar_id
            freeze["monitoring_series_ids"] = series_ids
            freeze["initial_live_run_ids"] = [str(item["run_id"]) for item in initial]
            freeze["partial_report_sha256"] = {
                _report_run_id(item): _report_sha256(item) for item in initial_reports
            }
            _write_json(freeze_path, freeze)
            _assert_initial_quality_gate(report=report, live=live)
        _assert_initial_aggregate_gate(reports=initial_reports, live=live)
        incremental_preflight = _preflight(
            client,
            radar_id=radar_id,
            live=live,
            series_id=series_ids[1],
            lookback_days=None,
        )
        if not incremental_preflight.get("previous_source_key_count"):
            raise RuntimeError("Incremental preflight did not load B-series source history.")
        incremental = _queue_and_wait(
            client,
            radar_id=radar_id,
            live=live,
            series_id=series_ids[1],
            lookback_days=None,
            poll_interval=poll_interval,
            timeout=timeout,
        )
        reports = [
            *initial_reports,
            _get(client, f"/api/signal-monitoring-runs/{incremental['run_id']}/report"),
        ]
    freeze["radar_id"] = radar_id
    freeze["monitoring_series_ids"] = series_ids
    freeze["initial_live_run_ids"] = [str(item["run_id"]) for item in initial]
    freeze["incremental_live_run_id"] = str(incremental["run_id"])
    freeze["pre_restart_report_sha256"] = {
        _report_run_id(report): _report_sha256(report) for report in reports
    }
    freeze["live_completed_at"] = _now()
    _write_json(freeze_path, freeze)
    print(f"initial_live_run_ids={','.join(freeze['initial_live_run_ids'])}")
    print(f"incremental_live_run_id={freeze['incremental_live_run_id']}")
    print("restart_required=true")


def _assert_initial_quality_gate(*, report: dict[str, Any], live: dict[str, Any]) -> None:
    positive = control_match_summary(report, list(live.get("positive_controls", [])), expected="confirmed")
    expected = len(live.get("positive_controls", []))
    policy = dict(live.get("reproducibility_policy") or {})
    minimum = int(policy.get("minimum_positive_controls_per_initial_run") or expected)
    if int(positive.get("matched", 0)) < minimum:
        missing = [str(item) for item in positive.get("missing", [])]
        raise RuntimeError(
            "Initial run failed the frozen per-run positive-control gate; "
            f"matched={positive.get('matched', 0)}/{expected}, minimum={minimum}, "
            f"missing={','.join(missing)}. B and C were not queued."
        )


def _assert_initial_aggregate_gate(*, reports: list[dict[str, Any]], live: dict[str, Any]) -> None:
    controls = list(live.get("positive_controls", []))
    expected_ids = {str(item.get("id")) for item in controls}
    summaries = [control_match_summary(report, controls, expected="confirmed") for report in reports]
    matched_ids = {
        str(control_id)
        for summary in summaries
        for control_id in summary.get("matched_ids", [])
    }
    policy = dict(live.get("reproducibility_policy") or {})
    accepted_drift_ids = {
        str(item)
        for item in policy.get("accepted_provider_search_drift_control_ids", [])
    }
    missing_ids = {
        str(control_id)
        for summary in summaries
        for control_id in summary.get("missing", [])
    }
    one_complete = any(int(summary.get("matched", 0)) == len(controls) for summary in summaries)
    if (
        matched_ids != expected_ids
        or (policy.get("require_one_complete_initial_run", False) and not one_complete)
        or not missing_ids <= accepted_drift_ids
    ):
        raise RuntimeError(
            "Initial runs failed the frozen aggregate reproducibility gate; "
            f"aggregate={len(matched_ids)}/{len(controls)}, one_complete={one_complete}, "
            f"unapproved_missing={','.join(sorted(missing_ids - accepted_drift_ids))}. "
            "Incremental C was not queued."
        )


def _verify_session(
    *,
    manifest: RadarPipelineAcceptanceManifest,
    manifest_path: Path,
    freeze: dict[str, Any],
    api_url: str,
    run_tests: bool,
) -> int:
    initial_ids = [str(item) for item in freeze.get("initial_live_run_ids", [])]
    incremental_id = str(freeze.get("incremental_live_run_id") or "")
    with httpx.Client(base_url=api_url.rstrip("/"), timeout=60.0) as client:
        reports = {
            run_id: _get(client, f"/api/signal-monitoring-runs/{run_id}/report")
            for run_id in [*initial_ids, *([incremental_id] if incremental_id else [])]
        }
    expected_hashes = dict(freeze.get("pre_restart_report_sha256") or {})
    expected_run_ids = [*initial_ids, *([incremental_id] if incremental_id else [])]
    restart_verified = len(initial_ids) == 2 and bool(incremental_id) and all(
        expected_hashes.get(run_id) == _report_sha256(report)
        for run_id, report in reports.items()
    ) and set(expected_hashes) == set(expected_run_ids)
    report = RadarPipelineSliceValidator().validate(
        manifest_path=manifest_path,
        initial_live_reports=[reports[item] for item in initial_ids],
        incremental_live_report=reports.get(incremental_id, {}),
        restart_verified=restart_verified,
        run_tests=run_tests,
    )
    print(f"validation_status={report.validation_status}")
    print(f"restart_verified={restart_verified}")
    for item in report.requirements:
        print(f"{item.requirement_id}={item.status}")
    return 0 if report.validation_status == "PASS" else 1


def _preflight(
    client: httpx.Client,
    *,
    radar_id: str,
    live: dict[str, Any],
    series_id: str,
    lookback_days: int | None,
) -> dict[str, Any]:
    params: list[tuple[str, str | int]] = [
        ("source_candidate_run_id", str(live["source_candidate_run_id"])),
        ("run_profile", "signal_monitoring_quality"),
        ("monitoring_series_id", series_id),
    ]
    if lookback_days is not None:
        params.append(("lookback_days", lookback_days))
    params.extend(("candidate_ids", str(item)) for item in live["candidate_ids"])
    params.extend(("signal_codes", str(item)) for item in live["signal_codes"])
    return _request_json(
        client,
        "GET",
        f"/api/radars/{radar_id}/signal-monitoring/preflight",
        params=params,
    )


def _queue_and_wait(
    client: httpx.Client,
    *,
    radar_id: str,
    live: dict[str, Any],
    series_id: str,
    lookback_days: int | None,
    poll_interval: float,
    timeout: float,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "source_candidate_run_id": live["source_candidate_run_id"],
        "candidate_scope_mode": "accepted_and_review_needed",
        "candidate_ids": list(live["candidate_ids"]),
        "signal_codes": list(live["signal_codes"]),
        "run_profile": "signal_monitoring_quality",
        "monitoring_series_id": series_id,
        "idempotency_key": f"acceptance:{series_id}:{'initial' if lookback_days else 'incremental'}",
        "requester": "signal-monitoring-quality-acceptance",
    }
    if lookback_days is not None:
        payload["lookback_days"] = lookback_days
    queued = _request_json(
        client,
        "POST",
        f"/api/radars/{radar_id}/signal-monitoring-runs",
        json=payload,
    )
    deadline = monotonic() + timeout
    while monotonic() < deadline:
        run = _get(client, f"/api/signal-monitoring-runs/{queued['run_id']}")
        if run.get("status") == "completed":
            return run
        if run.get("status") == "failed":
            raise RuntimeError(f"Signal run failed: {run.get('error_message')}")
        sleep(poll_interval)
    raise TimeoutError(f"Signal run did not finish in {timeout} seconds: {queued['run_id']}")


def _get(client: httpx.Client, path: str) -> dict[str, Any]:
    return _request_json(client, "GET", path)


def _request_json(client: httpx.Client, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
    delays = (1.0, 2.0, 4.0, 8.0, 15.0)
    for attempt, delay in enumerate(delays, start=1):
        try:
            response = client.request(method, path, **kwargs)
            response.raise_for_status()
            return dict(response.json())
        except httpx.TransportError:
            if attempt == len(delays):
                raise
            sleep(delay)
    raise AssertionError("unreachable")


def _report_sha256(report: dict[str, Any]) -> str:
    payload = json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _report_run_id(report: dict[str, Any]) -> str:
    return str(report.get("run_id") or report.get("signal_run_id") or "")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _git_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else ""


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    sys.exit(main())
