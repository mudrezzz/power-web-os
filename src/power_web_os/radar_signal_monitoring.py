"""Recorded demo runner for the standalone Radar signal-monitoring pipeline."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from power_web_os.application.live_radar_source_cards import RadarPlannerSourceCard
from power_web_os.application.signal_monitoring_contracts import (
    SignalAttemptRole,
    SignalMonitoringBudget,
    SignalMonitoringCandidate,
    SignalMonitoringInput,
    SignalMonitoringProviderResult,
    SignalMonitoringSignalRule,
    SignalMonitoringSourcePolicy,
    SignalSearchTask,
    SignalSourceRef,
)
from power_web_os.application.signal_monitoring_executor import SignalMonitoringExecutor


SIGNAL_MONITORING_REPORT_VERSION = "0.7.6.4.5"


@dataclass(slots=True)
class RecordedSignalMonitoringProvider:
    """Scripted provider keyed by generated task id.

    The provider is deliberately tiny and deterministic: it is a no-network
    adapter for demo fixtures, not a runtime provider integration.
    """

    scripted_payloads: dict[str, Any]
    default_payload: dict[str, Any]
    runtime_name: str = "recorded-signal-monitoring-provider"

    def run_signal_task(
        self,
        *,
        task: SignalSearchTask,
        attempt_role: SignalAttemptRole,
    ) -> SignalMonitoringProviderResult:
        payload = self.scripted_payloads.get(task.task_id, self.default_payload)
        return SignalMonitoringProviderResult(payload=payload)


def generate_recorded_signal_monitoring_report(*, fixture_path: Path, output_path: Path) -> dict[str, Any]:
    report = run_recorded_signal_monitoring(fixture_path=fixture_path)
    _assert_no_secrets(report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def run_recorded_signal_monitoring(*, fixture_path: Path) -> dict[str, Any]:
    fixture = _load_fixture(fixture_path)
    monitoring_input = _monitoring_input_from_fixture(fixture)
    provider = RecordedSignalMonitoringProvider(
        scripted_payloads=dict(fixture.get("provider_payloads", {})),
        default_payload=_dict(fixture.get("default_provider_payload")),
    )
    outcome = SignalMonitoringExecutor(provider).run(monitoring_input)
    return _report_from_outcome(fixture=fixture, fixture_path=fixture_path, outcome=outcome)


def _load_fixture(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid recorded signal-monitoring fixture {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Recorded signal-monitoring fixture must be a JSON object: {path}")
    return payload


def _monitoring_input_from_fixture(fixture: dict[str, Any]) -> SignalMonitoringInput:
    return SignalMonitoringInput(
        run_id=str(fixture.get("run_id") or "recorded-signal-monitoring-run"),
        radar_id=str(fixture.get("radar_id") or "recorded-toir-signal-monitoring"),
        model_profile_id=str(fixture.get("model_profile_id") or "signal_monitoring_default"),
        candidates=[SignalMonitoringCandidate.model_validate(item) for item in _list(fixture.get("candidates"))],
        signal_rules=[SignalMonitoringSignalRule.model_validate(item) for item in _list(fixture.get("signal_rules"))],
        known_sources=[SignalSourceRef.model_validate(item) for item in _list(fixture.get("known_sources"))],
        source_policy=SignalMonitoringSourcePolicy.model_validate(_dict(fixture.get("source_policy"))),
        source_cards=[RadarPlannerSourceCard.model_validate(item) for item in _list(fixture.get("source_cards"))],
        budget=SignalMonitoringBudget.model_validate(_dict(fixture.get("budget"))),
        lookback_days=int(fixture.get("lookback_days") or 7),
        previous_signal_fingerprints=[str(item) for item in _list(fixture.get("previous_signal_fingerprints"))],
    )


def _report_from_outcome(*, fixture: dict[str, Any], fixture_path: Path, outcome: Any) -> dict[str, Any]:
    observations = [item.model_dump(mode="json") for item in outcome.observations]
    tasks = [item.model_dump(mode="json") for item in outcome.tasks]
    search_status_counts = Counter(item["search_status"] for item in observations)
    observation_status_counts = Counter(item["observation_status"] for item in observations)
    signal_code_counts = Counter(item["signal_code"] for item in observations)
    return {
        "artifact_type": "radar_signal_monitoring_report",
        "artifact_version": SIGNAL_MONITORING_REPORT_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "fixture_path": str(fixture_path),
        "fixture_kind": str(fixture.get("fixture_kind") or "recorded_fake"),
        "recorded_provider": True,
        "live_provider_calls": 0,
        "run_id": outcome.run_id,
        "radar_id": outcome.radar_id,
        "model_profile_id": outcome.model_profile_id,
        "model_profile_summary": outcome.model_profile_summary,
        "lookback_days": int(fixture.get("lookback_days") or 7),
        "summary": {
            "candidate_count": len(_list(fixture.get("candidates"))),
            "signal_rule_count": len(_list(fixture.get("signal_rules"))),
            "task_count": len(tasks),
            "observation_count": len(observations),
            "new_signal_count": search_status_counts.get("searched", 0) - observation_status_counts.get("not_observed", 0),
            "repeated_signal_count": search_status_counts.get("duplicate_existing_signal", 0),
            "searched_negative_count": observation_status_counts.get("not_observed", 0),
            "not_searched_budget_limited_count": search_status_counts.get("not_searched_budget_limited", 0),
            "observations_by_search_status": dict(sorted(search_status_counts.items())),
            "observations_by_observation_status": dict(sorted(observation_status_counts.items())),
            "observations_by_signal_code": dict(sorted(signal_code_counts.items())),
        },
        "candidates": _safe_candidates(fixture),
        "signal_rules": _safe_signal_rules(fixture),
        "tasks": tasks,
        "observations": observations,
        "source_strategy_decisions": [item.model_dump(mode="json") for item in outcome.source_strategy_decisions],
        "source_strategy_diagnostics": [item.model_dump(mode="json") for item in outcome.source_strategy_diagnostics],
        "provider_attempts": [item.model_dump(mode="json") for item in outcome.provider_attempts],
        "budget_counters": dict(outcome.budget_counters),
        "diagnostics": [item.model_dump(mode="json") for item in outcome.diagnostics],
    }


def _safe_candidates(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": str(item.get("candidate_id") or ""),
            "display_name": str(item.get("display_name") or ""),
            "legal_name": str(item.get("legal_name") or ""),
            "entity_type": str(item.get("entity_type") or ""),
            "monitorable": bool(item.get("monitorable", True)),
            "review_flags": [str(flag) for flag in _list(item.get("review_flags"))],
        }
        for item in _list(fixture.get("candidates"))
        if isinstance(item, dict)
    ]


def _safe_signal_rules(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "signal_code": str(item.get("signal_code") or ""),
            "label": str(item.get("label") or ""),
            "description": str(item.get("description") or ""),
            "expected_evidence": [str(value) for value in _list(item.get("expected_evidence"))],
        }
        for item in _list(fixture.get("signal_rules"))
        if isinstance(item, dict)
    ]


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _assert_no_secrets(payload: dict[str, Any]) -> None:
    serialized = json.dumps(payload, ensure_ascii=False)
    forbidden = (
        "OPENROUTER_API_KEY",
        "DADATA_API_KEY",
        "DADATA_SECRET_KEY",
        "Authorization",
        "Bearer ",
        "sk-or-",
        "chain_of_thought",
        "hidden_reasoning",
        "internal_thoughts",
    )
    if any(token in serialized for token in forbidden):
        raise RuntimeError("Refusing to write signal-monitoring report containing secret-like content")
