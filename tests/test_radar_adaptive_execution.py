"""Fast scenario matrix for adaptive Radar checkpoint execution.

This suite is the required no-network gate before a broad live Radar run.
It verifies executed behavior and diagnostic metadata, not only checkpoint
decisions.
"""

from __future__ import annotations

import socket

from power_web_os.application.live_radar_contracts import RadarExecutionPlan, RadarExecutionTask
from power_web_os.application.live_radar_checkpoints import (
    RadarExecutionCheckpointInput,
    RadarExecutionCheckpointService,
)
from power_web_os.application.live_radar_staged_execution import run_staged_radar_execution
from support.radar_adaptive_harness import (
    ScriptedProvider,
    SourceExpansionProvider,
    assert_action_executed,
    assert_no_normal_negative_signal_projection,
    assert_signal_search_ran,
    assert_stopped_for_review,
    base_plan,
    cross_check_supporting_result,
    evidence_linking_failed_result,
    high_coverage_risk_result,
    radar_definition,
    required_source_unavailable_result,
    schema_invalid_result,
    signal_result,
    strong_discovery_with_cross_check_plan,
    source_policy_selected,
    strong_discovery_result,
    weak_result,
)


def test_checkpoint_routes_weak_recall_with_target_hints_to_expansion() -> None:
    decision = RadarExecutionCheckpointService().review(
        RadarExecutionCheckpointInput(
            checkpoint_id="after-discovery",
            phase="after_discovery",
            candidate_scope_count=1,
            linked_source_count=0,
            evidence_linking_issue_count=1,
            extraction_issue_codes=["evidence_linking_failed"],
            uncovered_target_hint_count=3,
        )
    )

    assert decision.action == "expand_sources"
    assert decision.reason_code == "weak_candidate_coverage"


def test_checkpoint_revises_repeated_unlinked_evidence_after_expansion() -> None:
    decision = RadarExecutionCheckpointService().review(
        RadarExecutionCheckpointInput(
            checkpoint_id="after-discovery",
            phase="after_discovery",
            candidate_scope_count=1,
            linked_source_count=0,
            evidence_linking_issue_count=1,
            extraction_issue_codes=["evidence_linking_failed"],
            search_expansion_result_count=1,
        )
    )

    assert decision.action == "revise_plan"
    assert decision.reason_code == "evidence_linking_failed"


def test_checkpoint_keeps_schema_invalid_on_extraction_repair_path() -> None:
    decision = RadarExecutionCheckpointService().review(
        RadarExecutionCheckpointInput(
            checkpoint_id="after-discovery",
            phase="after_discovery",
            candidate_scope_count=0,
            extraction_issue_codes=["extraction_schema_invalid"],
            uncovered_target_hint_count=3,
        )
    )

    assert decision.action == "repair_extraction"


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


def test_schema_failure_applies_extraction_repair_then_continues() -> None:
    provider = ScriptedProvider([schema_invalid_result(), strong_discovery_result(), signal_result()])

    _, _, execution_results = run_staged_radar_execution(
        radar=radar_definition(),
        execution_plan=base_plan(),
        provider=provider,
        max_checkpoint_retries_per_stage=1,
    )

    assert provider.stages == ["qualification_discovery", "qualification_discovery", "signal_search"]
    assert_signal_search_ran(execution_results)
    assert_action_executed(execution_results, "repair_extraction")
    assert not any(
        item.get("action") == "revise_plan" and item.get("outcome") == "executed"
        for item in execution_results["adaptive_actions"]
    )
    assert execution_results["extraction_recovery_records"][-1]["outcome"] == "recovered"


def test_schema_failure_repair_cap_stops_without_blind_fallback() -> None:
    provider = ScriptedProvider([schema_invalid_result(), schema_invalid_result()])

    _, _, execution_results = run_staged_radar_execution(
        radar=radar_definition(),
        execution_plan=base_plan(),
        provider=provider,
        max_checkpoint_retries_per_stage=1,
    )

    assert provider.stages == ["qualification_discovery", "qualification_discovery"]
    assert_stopped_for_review(execution_results, reason="extraction repair")
    assert any(
        item.get("reason_code") == "extraction_repair_exhausted"
        for item in execution_results["checkpoint_decisions"]
    )
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


def test_evidence_linking_failure_with_benchmark_hints_runs_targeted_expansion_first() -> None:
    provider = ScriptedProvider([evidence_linking_failed_result(), strong_discovery_result(), signal_result()])
    radar = radar_definition()
    radar["name"] = "SIBUR benchmark"
    radar["description"] = "Find SIBUR production assets."

    _, _, execution_results = run_staged_radar_execution(
        radar=radar,
        execution_plan=base_plan(source_scope="global", source_ids=["sibur_site"]),
        provider=provider,
        task_context={
            "benchmark_profile": "benchmark_smoke",
            "benchmark_target_hints": [{
                "baseline_id": "candidate-a",
                "canonical_name": "Candidate A",
                "entity_type": "legal_entity",
                "aliases": ["Candidate A"],
            }],
        },
        max_checkpoint_retries_per_stage=1,
    )

    assert provider.stages[:2] == ["qualification_discovery", "coverage_check"]
    assert execution_results["expansion_target_queue"]
    assert execution_results["search_expansion_query_variants"]
    assert_action_executed(execution_results, "expand_sources")
    first_blocking_action = next(
        item["action"]
        for item in execution_results["checkpoint_decisions"]
        if item["action"] != "continue"
    )
    assert first_blocking_action == "expand_sources"
    assert_signal_search_ran(execution_results)


def test_high_coverage_risk_blocks_signal_search_until_recovery_improves_it() -> None:
    provider = ScriptedProvider([strong_discovery_result(), high_coverage_risk_result()])

    _, _, execution_results = run_staged_radar_execution(
        radar=radar_definition(),
        execution_plan=base_plan(include_coverage=True),
        provider=provider,
    )

    assert provider.stages[:2] == ["qualification_discovery", "coverage_check"]
    assert "signal_search" not in provider.stages
    assert execution_results["search_expansion_query_variants"]
    assert execution_results["search_expansion_results"]
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


def test_cross_source_disambiguation_executes_official_web_check() -> None:
    provider = ScriptedProvider([
        strong_discovery_with_cross_check_plan(),
        cross_check_supporting_result(),
        signal_result(),
    ])

    _, _, execution_results = run_staged_radar_execution(
        radar=radar_definition(),
        execution_plan=base_plan(),
        provider=provider,
    )

    assert provider.stages == ["qualification_discovery", "coverage_check", "signal_search"]
    execution = execution_results["cross_source_disambiguation_execution"]
    assert execution[0]["outcome"] == "confirmed_relation"
    assert execution_results["cross_source_disambiguation_tasks"][0]["status"] == "executed"
    assert execution_results["linked_entity_facts"]
    assert_signal_search_ran(execution_results)


def test_cross_source_disambiguation_records_no_supporting_evidence() -> None:
    provider = ScriptedProvider([
        strong_discovery_with_cross_check_plan(),
        # The cross-check ran but returned nothing useful.
        weak_result(),
        signal_result(),
    ])

    _, _, execution_results = run_staged_radar_execution(
        radar=radar_definition(),
        execution_plan=base_plan(),
        provider=provider,
    )

    execution = execution_results["cross_source_disambiguation_execution"]
    assert execution[0]["outcome"] == "no_supporting_evidence"
    assert execution_results["cross_source_disambiguation_tasks"][0]["status"] == "executed"


def test_cross_source_disambiguation_budget_skip_stops_for_review() -> None:
    provider = ScriptedProvider([strong_discovery_with_cross_check_plan()])

    _, _, execution_results = run_staged_radar_execution(
        radar=radar_definition(),
        execution_plan=base_plan(),
        provider=provider,
        max_total_web_tasks_per_run=1,
    )

    execution = execution_results["cross_source_disambiguation_execution"]
    assert execution[0]["outcome"] == "skipped_budget_limited"
    assert execution_results["cross_source_disambiguation_tasks"][0]["status"] == "skipped"
    assert_stopped_for_review(execution_results, reason="budget")


def test_cross_source_disambiguation_executes_when_task_is_created_after_gate() -> None:
    plan = RadarExecutionPlan(
        radar_id="adaptive-harness",
        tasks=[
            RadarExecutionTask(
                task_id="discover-q1",
                stage="qualification_discovery",
                subject_type="qualification",
                subject_id="Q1",
                query="Find candidate universe.",
                purpose="Discover candidates.",
            ),
            RadarExecutionTask(
                task_id="identity-gate-q1",
                stage="qualification_gate",
                subject_type="qualification",
                subject_id="Q1",
                query="Confirm candidate identity.",
                purpose="Confirm candidate identity.",
                candidate_scope=["Candidate A"],
            ),
            RadarExecutionTask(
                task_id="signal-s1",
                stage="signal_search",
                subject_type="signal",
                subject_id="S1",
                query="Find signal.",
                purpose="Search signal.",
                candidate_scope=["Candidate A"],
            ),
        ],
    )
    provider = ScriptedProvider([
        strong_discovery_result(),
        strong_discovery_with_cross_check_plan(query_id="identity-gate-q1"),
        cross_check_supporting_result(),
        signal_result(),
    ])

    _, _, execution_results = run_staged_radar_execution(
        radar=radar_definition(),
        execution_plan=plan,
        provider=provider,
    )

    assert provider.stages == ["qualification_discovery", "qualification_gate", "coverage_check", "signal_search"]
    execution = execution_results["cross_source_disambiguation_execution"]
    assert execution[0]["outcome"] == "confirmed_relation"
    assert execution_results["cross_source_disambiguation_tasks"][0]["status"] == "executed"
