"""API-backed Radar evaluation runner for persisted benchmark runs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import httpx

from power_web_os.radar_evaluation import (
    evaluate_radar_dossier,
    load_evaluation_baseline,
    write_evaluation_report,
)


class RadarEvaluationHttpClient(Protocol):
    def get_json(self, path: str) -> dict[str, Any] | list[Any]: ...


@dataclass(slots=True)
class HttpxRadarEvaluationClient:
    api_url: str
    timeout_seconds: float = 30.0

    def get_json(self, path: str) -> dict[str, Any] | list[Any]:
        with httpx.Client(base_url=self.api_url.rstrip("/"), timeout=self.timeout_seconds) as client:
            response = client.get(path)
            response.raise_for_status()
            return response.json()


def generate_radar_evaluation_report(
    *,
    api_url: str,
    run_id: str | None,
    radar_id: str,
    latest: bool,
    baseline_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    client = HttpxRadarEvaluationClient(api_url=api_url)
    resolved_run = resolve_evaluation_run(client=client, run_id=run_id, radar_id=radar_id, latest=latest)
    dossier = client.get_json(f"/api/radar-runs/{resolved_run['run_id']}/dossier")
    if not isinstance(dossier, dict):
        raise ValueError("Radar dossier endpoint returned a non-object payload.")
    report = evaluate_radar_dossier(run=resolved_run, dossier=dossier, baseline=load_evaluation_baseline(baseline_path))
    write_evaluation_report(output_path, report)
    return report


def resolve_evaluation_run(
    *,
    client: RadarEvaluationHttpClient,
    run_id: str | None,
    radar_id: str,
    latest: bool,
) -> dict[str, Any]:
    if run_id:
        run = client.get_json(f"/api/radar-runs/{run_id}")
        if not isinstance(run, dict):
            raise ValueError(f"Radar run {run_id} was not found.")
        return dict(run)
    if not latest:
        raise ValueError("Provide --run-id or --latest with --radar-id.")
    radars = client.get_json("/api/radars")
    if not isinstance(radars, list):
        raise ValueError("Radar catalog endpoint returned a non-list payload.")
    for radar in radars:
        if isinstance(radar, dict) and radar.get("radar_id") == radar_id:
            latest_run = radar.get("latest_run")
            if not isinstance(latest_run, dict):
                raise ValueError(f"Radar {radar_id} has no latest run to evaluate.")
            return dict(latest_run)
    raise ValueError(f"Radar {radar_id} was not found.")
