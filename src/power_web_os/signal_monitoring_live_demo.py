"""API-driven live Signal Monitoring demo and DoD summary."""

from __future__ import annotations

import json
from pathlib import Path
from time import monotonic, sleep
from typing import Any
from uuid import uuid4

import httpx

from power_web_os.radar_signal_monitoring import generate_recorded_signal_monitoring_report


def configure_signal_monitoring_demo_arguments(parser: Any, *, root: Path) -> None:
    parser.add_argument(
        "--signal-monitoring-fixture",
        type=Path,
        default=root / "demo" / "fixtures" / "radar_signal_monitoring" / "toir_recorded_signal_monitoring.json",
    )
    parser.add_argument(
        "--signal-monitoring-output",
        type=Path,
        default=root / "demo" / "output" / "radar_signal_monitoring_report.json",
    )
    parser.add_argument("--source-run-id", default=None)
    parser.add_argument("--candidate-id", action="append", default=[])
    parser.add_argument("--signal-code", action="append", default=[])
    parser.add_argument("--lookback-days", type=int, default=None)
    parser.add_argument("--monitoring-series-id", default="default")
    parser.add_argument(
        "--signal-monitoring-profile",
        choices=["signal_monitoring_smoke", "signal_monitoring_quality"],
        default="signal_monitoring_smoke",
    )


def run_signal_monitoring_demo_command(args: Any) -> dict[str, Any] | None:
    if args.command == "run-recorded-signal-monitoring":
        return generate_recorded_signal_monitoring_report(
            fixture_path=args.signal_monitoring_fixture,
            output_path=args.signal_monitoring_output,
        )
    if args.command != "run-live-signal-monitoring":
        return None
    return run_live_signal_monitoring(
        api_url=args.api_url,
        radar_id=args.radar_id,
        source_run_id=args.source_run_id,
        candidate_ids=tuple(args.candidate_id),
        signal_codes=tuple(args.signal_code),
        lookback_days=args.lookback_days,
        monitoring_series_id=args.monitoring_series_id,
        run_profile=args.signal_monitoring_profile,
        output_path=args.signal_monitoring_output,
        poll_interval_seconds=args.benchmark_poll_interval_seconds,
        timeout_seconds=args.benchmark_timeout_seconds,
    )


def run_live_signal_monitoring(
    *,
    api_url: str,
    radar_id: str,
    source_run_id: str | None,
    candidate_ids: tuple[str, ...] = (),
    signal_codes: tuple[str, ...] = (),
    lookback_days: int | None = None,
    monitoring_series_id: str = "default",
    run_profile: str = "signal_monitoring_smoke",
    output_path: Path | None = None,
    poll_interval_seconds: float = 3.0,
    timeout_seconds: float = 900.0,
) -> dict[str, Any]:
    with httpx.Client(base_url=api_url.rstrip("/"), timeout=60.0) as client:
        resolved_source_run_id = source_run_id or _latest_completed_candidate_run(client, radar_id)
        selected_candidate_ids = candidate_ids or _default_candidate_scope(client, resolved_source_run_id)
        preflight = _preflight(
            client,
            radar_id=radar_id,
            source_run_id=resolved_source_run_id,
            candidate_ids=selected_candidate_ids,
            signal_codes=signal_codes,
            lookback_days=lookback_days,
            run_profile=run_profile,
            monitoring_series_id=monitoring_series_id,
        )
        if not preflight.get("ready_for_live_run"):
            raise RuntimeError(f"Signal monitoring preflight failed: {preflight.get('issues')}")
        response = client.post(
            f"/api/radars/{radar_id}/signal-monitoring-runs",
            json={
                "source_candidate_run_id": resolved_source_run_id,
                "candidate_scope_mode": "accepted_and_review_needed",
                "candidate_ids": list(selected_candidate_ids),
                "signal_codes": list(signal_codes),
                **({"lookback_days": lookback_days} if lookback_days is not None else {}),
                "run_profile": run_profile,
                "monitoring_series_id": monitoring_series_id,
                "idempotency_key": f"demo-signal:{uuid4()}",
                "requester": "demo-cli",
            },
        )
        response.raise_for_status()
        queued = dict(response.json())
        terminal = _poll_terminal(
            client,
            run_id=str(queued["run_id"]),
            poll_interval_seconds=poll_interval_seconds,
            timeout_seconds=timeout_seconds,
        )
        report_response = _get_with_transport_retries(
            client,
            f"/api/signal-monitoring-runs/{queued['run_id']}/report",
        )
        report_response.raise_for_status()
        report = dict(report_response.json())

    result = {
        "artifact_type": "signal_monitoring_live_demo_result",
        "radar_id": radar_id,
        "source_candidate_run_id": resolved_source_run_id,
        "signal_run_id": queued["run_id"],
        "pipeline_id": terminal.get("pipeline_id"),
        "status": terminal.get("status"),
        "preflight": preflight,
        "closeout": signal_monitoring_closeout(report),
        "report": report,
    }
    _assert_product_safe(result)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def signal_monitoring_closeout(report: dict[str, Any]) -> dict[str, Any]:
    summary = _dict(report.get("summary"))
    budgets = _dict(report.get("budgets"))
    counters = _dict(budgets.get("counters")) or _dict(report.get("budget_counters"))
    attempts = _list(report.get("provider_attempts"))
    observations = _list(report.get("observations"))
    status_counts: dict[str, int] = {}
    for item in observations:
        key = str(item.get("observation_status") or "unknown")
        status_counts[key] = status_counts.get(key, 0) + 1
    return {
        "pipeline_id": report.get("pipeline_id"),
        "signal_run_id": report.get("signal_run_id") or report.get("run_id"),
        "source_candidate_run_id": report.get("source_candidate_run_id"),
        "completion_state": report.get("completion_state"),
        "candidate_count": summary.get("candidate_count"),
        "task_count": summary.get("task_count"),
        "provider_call_count": counters.get("provider_calls", len(attempts)),
        "retry_count": counters.get("retries", 0),
        "observation_status_counts": status_counts,
        "search_status_counts": summary.get("observations_by_search_status", {}),
        "not_searched_count": sum(
            count
            for key, count in _dict(summary.get("observations_by_search_status")).items()
            if key.startswith("not_searched")
        ),
        "budget_exhaustion_events": budgets.get("exhaustion_events", report.get("budget_exhaustion_events", [])),
    }


def _latest_completed_candidate_run(client: httpx.Client, radar_id: str) -> str:
    response = client.get(f"/api/radars/{radar_id}/runs", params={"limit": 20})
    response.raise_for_status()
    for run in response.json():
        if run.get("pipeline_id") == "candidate_discovery" and run.get("status") == "completed" and run.get("output"):
            return str(run["run_id"])
    raise RuntimeError(f"No completed candidate-discovery run found for Radar {radar_id}.")


def _default_candidate_scope(client: httpx.Client, source_run_id: str) -> tuple[str, ...]:
    response = client.get(f"/api/radar-runs/{source_run_id}/candidates")
    response.raise_for_status()
    candidates = [item for item in response.json().get("candidates", []) if isinstance(item, dict)]
    accepted = [str(item["candidate_id"]) for item in candidates if item.get("product_acceptance_status") == "product_candidate"]
    review = [str(item["candidate_id"]) for item in candidates if item.get("product_acceptance_status") == "review_required"]
    selected = accepted[:2] + review[:1]
    if len(selected) < 3:
        selected.extend(
            str(item["candidate_id"])
            for item in candidates
            if str(item.get("candidate_id") or "") not in selected
        )
    if not selected:
        raise RuntimeError(f"Candidate run {source_run_id} has no monitorable public candidates.")
    return tuple(selected[:3])


def _preflight(
    client: httpx.Client,
    *,
    radar_id: str,
    source_run_id: str,
    candidate_ids: tuple[str, ...],
    signal_codes: tuple[str, ...],
    lookback_days: int | None,
    run_profile: str,
    monitoring_series_id: str,
) -> dict[str, Any]:
    params: list[tuple[str, str | int]] = [
        ("source_candidate_run_id", source_run_id),
        ("run_profile", run_profile),
        ("monitoring_series_id", monitoring_series_id),
    ]
    if lookback_days is not None:
        params.append(("lookback_days", lookback_days))
    params.extend(("candidate_ids", item) for item in candidate_ids)
    params.extend(("signal_codes", item) for item in signal_codes)
    response = client.get(f"/api/radars/{radar_id}/signal-monitoring/preflight", params=params)
    response.raise_for_status()
    return dict(response.json())


def _poll_terminal(
    client: httpx.Client,
    *,
    run_id: str,
    poll_interval_seconds: float,
    timeout_seconds: float,
) -> dict[str, Any]:
    deadline = monotonic() + timeout_seconds
    while monotonic() < deadline:
        try:
            response = client.get(f"/api/signal-monitoring-runs/{run_id}")
        except httpx.TransportError:
            sleep(poll_interval_seconds)
            continue
        response.raise_for_status()
        run = dict(response.json())
        if run.get("status") in {"completed", "failed"}:
            return run
        sleep(poll_interval_seconds)
    raise TimeoutError(f"Signal monitoring run did not reach terminal state within {timeout_seconds} seconds: {run_id}")


def _get_with_transport_retries(
    client: httpx.Client,
    path: str,
    *,
    attempts: int = 3,
    delay_seconds: float = 1.0,
) -> httpx.Response:
    last_error: httpx.TransportError | None = None
    for attempt in range(attempts):
        try:
            return client.get(path)
        except httpx.TransportError as exc:
            last_error = exc
            if attempt + 1 < attempts:
                sleep(delay_seconds)
    assert last_error is not None
    raise last_error


def _dict(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _list(value: object) -> list[dict[str, Any]]:
    return [dict(item) for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _assert_product_safe(payload: dict[str, Any]) -> None:
    serialized = json.dumps(payload, ensure_ascii=False)
    if any(token in serialized for token in ("Authorization", "Bearer ", "sk-or-")):
        raise RuntimeError("Refusing to expose secret-like Signal Monitoring output.")
