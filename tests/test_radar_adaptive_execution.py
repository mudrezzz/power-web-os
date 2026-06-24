"""Fast scenario matrix for adaptive Radar checkpoint execution.

This suite is the required no-network gate before a broad live Radar run.
It verifies executed behavior and diagnostic metadata, not only checkpoint
decisions.
"""

from __future__ import annotations

import socket

from power_web_os.application.live_radar_staged_execution import run_staged_radar_execution
from support.radar_adaptive_harness import (
    ScriptedProvider,
    SourceExpansionProvider,
    assert_action_executed,
    assert_no_normal_negative_signal_projection,
    assert_signal_search_ran,
    assert_stopped_for_review,
    base_plan,
    evidence_linking_failed_result,
    high_coverage_risk_result,
    radar_definition,
    required_source_unavailable_result,
    schema_invalid_result,
    signal_result,
    source_policy_selected,
    strong_discovery_result,
    weak_result,
)


def test_unrecovered_weak_discovery_does_not_start_signal_search() -> None:
    provider = ScriptedProvider([weak_result(), weak_result()])

    _, events, execution_results = run_staged_radar_execution(
        radar=radar_definition(),
        execution_plan=base_plan(),
        provider=provider,
    )

    assert provider.stages == ["qualification_discovery", "qualification_discovery"]
    assert_stopped_for_review(execution_results, reason="retry")
    assert_no_normal_negative_signal_projection(execution_results)
    assert "execution_stopped_for_review" in [event.event_type for event in events]


def test_weak_discovery_retries_same_source_then_continues_to_signal_search() -> None:
    provider = ScriptedProvider([weak_result(), strong_discovery_result(), signal_result()])

    _, events, execution_results = run_staged_radar_execution(
        radar=radar_definition(),
        execution_plan=base_plan(),
        provider=provider,
        max_checkpoint_retries_per_stage=1,
    )

    assert provider.stages == ["qualification_discovery", "qualification_discovery", "signal_search"]
    assert_signal_search_ran(execution_results)
    assert_action_executed(execution_results, "retry_same_source")
    assert "execution_checkpoint_action_selected" in [event.event_type for event in events]


def test_weak_global_source_expands_allowed_additional_source_then_continues() -> None:
    provider = SourceExpansionProvider()

    _, _, execution_results = run_staged_radar_execution(
        radar=radar_definition(),
        execution_plan=base_plan(source_scope="global", source_ids=["sibur_site"]),
        provider=provider,
        max_checkpoint_retries_per_stage=1,
    )

    discovery_calls = [call.queries[0] for call in provider.calls if call.queries[0].stage == "qualification_discovery"]
    assert [query.source_scope for query in discovery_calls] == ["global", "additional"]
    assert_signal_search_ran(execution_results)
    assert_action_executed(execution_results, "expand_sources")


def test_required_source_unavailable_stops_before_signal_search() -> None:
    provider = ScriptedProvider([required_source_unavailable_result()])

    _, _, execution_results = run_staged_radar_execution(
        radar=radar_definition(required_source=True),
        execution_plan=base_plan(source_scope="global", source_ids=["required_web"], include_coverage=True),
        provider=provider,
        source_policy_decisions=source_policy_selected("required_web"),
    )

    assert provider.stages == ["qualification_discovery", "coverage_check"]
    assert execution_results["signal_task_count"] == 0
    assert execution_results["checkpoint_decisions"][-1]["action"] == "fail_hard"
    assert execution_results["source_obligation_summary"]["blocking_count"] == 1
    assert_no_normal_negative_signal_projection(execution_results)


def test_schema_failure_applies_revision_style_recovery_then_continues() -> None:
    provider = ScriptedProvider([schema_invalid_result(), strong_discovery_result(), signal_result()])

    _, _, execution_results = run_staged_radar_execution(
        radar=radar_definition(),
        execution_plan=base_plan(),
        provider=provider,
        max_checkpoint_revisions_per_run=1,
    )

    assert provider.stages == ["qualification_discovery", "qualification_discovery", "signal_search"]
    assert_signal_search_ran(execution_results)
    assert_action_executed(execution_results, "revise_plan")


def test_schema_failure_revision_cap_stops_without_blind_fallback() -> None:
    provider = ScriptedProvider([schema_invalid_result(), schema_invalid_result(), schema_invalid_result()])

    _, _, execution_results = run_staged_radar_execution(
        radar=radar_definition(),
        execution_plan=base_plan(),
        provider=provider,
        max_checkpoint_revisions_per_run=2,
    )

    assert provider.stages == ["qualification_discovery", "qualification_discovery", "qualification_discovery"]
    assert_stopped_for_review(execution_results, reason="revision")
    assert_no_normal_negative_signal_projection(execution_results)


def test_unresolved_evidence_refs_do_not_start_signal_search() -> None:
    provider = ScriptedProvider([evidence_linking_failed_result(), evidence_linking_failed_result()])

    _, _, execution_results = run_staged_radar_execution(
        radar=radar_definition(),
        execution_plan=base_plan(),
        provider=provider,
        max_checkpoint_revisions_per_run=1,
    )

    assert provider.stages == ["qualification_discovery", "qualification_discovery"]
    assert_stopped_for_review(execution_results, reason="revision")
    assert "evidence_linking_failed" in str(execution_results["checkpoint_decisions"])
    assert_no_normal_negative_signal_projection(execution_results)


def test_high_coverage_risk_blocks_signal_search_until_recovery_improves_it() -> None:
    provider = ScriptedProvider([strong_discovery_result(), high_coverage_risk_result()])

    _, _, execution_results = run_staged_radar_execution(
        radar=radar_definition(),
        execution_plan=base_plan(include_coverage=True),
        provider=provider,
    )

    assert provider.stages == ["qualification_discovery", "coverage_check"]
    assert_stopped_for_review(execution_results)
    assert execution_results["checkpoint_decisions"][-1]["reason_code"] == "coverage_risk_high"
    assert_no_normal_negative_signal_projection(execution_results)


def test_total_run_budget_exhausted_during_recovery_stops_review_needed() -> None:
    provider = ScriptedProvider([weak_result()])

    _, _, execution_results = run_staged_radar_execution(
        radar=radar_definition(),
        execution_plan=base_plan(),
        provider=provider,
        max_total_web_tasks_per_run=1,
        max_checkpoint_retries_per_stage=1,
    )

    assert provider.stages == ["qualification_discovery"]
    assert_stopped_for_review(execution_results, reason="retry")
    assert execution_results["budget_exhaustion_events"]
    assert execution_results["budget_exhaustion_events"][0]["state"] == "not_searched_budget_limited"
    assert_no_normal_negative_signal_projection(execution_results)


def test_adaptive_suite_uses_fake_providers_without_network(monkeypatch) -> None:
    def fail_network(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("Adaptive harness must not open network sockets.")

    monkeypatch.setattr(socket, "create_connection", fail_network)
    provider = ScriptedProvider([weak_result(), strong_discovery_result(), signal_result()])

    _, _, execution_results = run_staged_radar_execution(
        radar=radar_definition(),
        execution_plan=base_plan(),
        provider=provider,
        max_checkpoint_retries_per_stage=1,
    )

    assert_signal_search_ran(execution_results)
