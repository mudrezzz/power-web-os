from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from power_web_os.application.radar.signal_monitoring.contracts import (
    SignalMonitoringCandidate,
    SignalMonitoringInput,
    SignalMonitoringSignalRule,
    SignalMonitoringSourceDecision,
    SignalMonitoringSourceStrategyResult,
    SignalMonitoringWatermark,
)
from power_web_os.application.radar.signal_monitoring.planning import (
    SignalMonitoringPlanningInput,
    SignalMonitoringSearchPlanner,
)
from power_web_os.application.radar.signal_monitoring.windows import SignalMonitoringWindowPolicy
from power_web_os.icp_radar import SignalMonitoringCriterionPolicy, intent_signal_to_payload
from power_web_os.icp_radar_catalog import _intent_signal_from_payload
from power_web_os.icp_radar_xlsx import load_icp_radar_workbook


def test_per_signal_policy_round_trip() -> None:
    definition = load_icp_radar_workbook(Path("demo/fixtures/icp_radar/sibur_icp_pass1.xlsx")).definition
    signal = replace(definition.intent_signals[0], monitoring_policy=SignalMonitoringCriterionPolicy(
        enabled=True,
        initial_lookback_days=90,
        incremental_overlap_days=7,
        cadence="weekly",
        source_lanes=("known_source", "signal_specific"),
    ))

    restored = _intent_signal_from_payload(intent_signal_to_payload(signal))

    assert restored.monitoring_policy == signal.monitoring_policy


def test_effective_signal_policy_precedence_is_auditable() -> None:
    rule = SignalMonitoringSignalRule(signal_code="S1", label="Repair", initial_lookback_days=90)
    monitoring = _monitoring_input(rule=rule, lookback_days=180, lookback_basis="explicit_override")

    window = SignalMonitoringWindowPolicy().resolve(
        monitoring_input=monitoring,
        candidate_id="candidate-a",
        rule=rule,
        source_lane="open_web",
    )

    assert window.lookback_days == 180
    assert window.basis == "explicit_override"


def test_per_signal_source_lanes_limit_planning() -> None:
    rule = SignalMonitoringSignalRule(
        signal_code="S1",
        label="Repair",
        source_lanes=["official_company", "open_web"],
    )
    decisions = [
        SignalMonitoringSourceDecision(
            decision_id=f"decision-{lane}",
            candidate_id="candidate-a",
            lane=lane,
            status="selected",
            reason="test",
            required=True,
        )
        for lane in ("known_source", "official_company", "signal_specific", "open_web")
    ]

    plan = SignalMonitoringSearchPlanner().plan(SignalMonitoringPlanningInput(
        _monitoring_input(rule=rule),
        SignalMonitoringSourceStrategyResult(decisions=decisions),
    ))

    assert {task.source_lane for task in plan.tasks} == {"official_company", "open_web"}


def test_cadence_is_policy_only() -> None:
    rule = SignalMonitoringSignalRule(signal_code="S1", label="Repair", cadence="daily")
    monitoring = _monitoring_input(rule=rule)

    assert monitoring.signal_rules[0].cadence == "daily"
    assert not hasattr(monitoring, "scheduled_job_id")


def test_per_signal_overlap_controls_incremental_window() -> None:
    rule = SignalMonitoringSignalRule(
        signal_code="S1",
        label="Repair",
        incremental_overlap_days=7,
    )
    monitoring = _monitoring_input(
        rule=rule,
        lookback_basis="radar_policy",
        previous_watermarks=[SignalMonitoringWatermark(
            candidate_id="candidate-a",
            signal_code="S1",
            source_lane="open_web",
            searched_through_at="2026-07-01T00:00:00Z",
        )],
    )

    window = SignalMonitoringWindowPolicy().resolve(
        monitoring_input=monitoring,
        candidate_id="candidate-a",
        rule=rule,
        source_lane="open_web",
    )

    assert window.basis == "incremental"
    assert window.overlap_days == 7
    assert window.window_start == "2026-06-24T00:00:00Z"


def _monitoring_input(
    *,
    rule: SignalMonitoringSignalRule,
    lookback_days: int = 365,
    lookback_basis: str = "radar_policy",
    previous_watermarks: list[SignalMonitoringWatermark] | None = None,
) -> SignalMonitoringInput:
    return SignalMonitoringInput(
        run_id="signal-run-settings",
        radar_id="radar-settings",
        source_candidate_run_id="candidate-run",
        candidates=[SignalMonitoringCandidate(candidate_id="candidate-a", display_name="Candidate A")],
        signal_rules=[rule],
        lookback_days=lookback_days,
        lookback_basis=lookback_basis,
        as_of="2026-07-10T00:00:00Z",
        previous_watermarks=previous_watermarks or [],
    )
