from __future__ import annotations

from typing import Any

from power_web_os.application.radar.shared.source_cards import RadarPlannerSourceCard
from power_web_os.application.radar.signal_monitoring.contracts import (
    SignalAttemptRole,
    SignalMonitoringBudget,
    SignalMonitoringCandidate,
    SignalMonitoringInput,
    SignalMonitoringPlan,
    SignalMonitoringProviderResult,
    SignalMonitoringRun,
    SignalMonitoringSignalRule,
    SignalMonitoringSourcePolicy,
    SignalSearchTask,
)
from power_web_os.application.radar.signal_monitoring.executor import SignalMonitoringExecutor


class ScriptedSignalProvider:
    runtime_name = "scripted-signal-provider"

    def __init__(self, payloads: list[Any]) -> None:
        self.payloads = list(payloads)
        self.calls: list[tuple[str, SignalAttemptRole]] = []

    def run_signal_task(
        self,
        *,
        task: SignalSearchTask,
        attempt_role: SignalAttemptRole,
    ) -> SignalMonitoringProviderResult:
        self.calls.append((task.task_id, attempt_role))
        payload = self.payloads.pop(0) if self.payloads else searched_negative_payload()
        return SignalMonitoringProviderResult(payload=payload)


def base_input(**overrides: Any) -> SignalMonitoringInput:
    payload: dict[str, Any] = {
        "run_id": "signal-run-1",
        "radar_id": "signal-radar",
        "candidates": [
            SignalMonitoringCandidate(
                candidate_id="candidate-a",
                display_name="Candidate A",
                legal_name="Candidate A LLC",
                source_refs=["known-src-a"],
            )
        ],
        "signal_rules": [
            SignalMonitoringSignalRule(
                signal_code="toir_tender",
                label="TOIR tender",
                description="Find fresh TOIR procurement signals.",
                query_template="{candidate} {signal} last week",
            )
        ],
        "source_cards": [
            source_card(
                source_id="openrouter_web",
                connector_profile_id="openrouter_web",
                source_type="open_web",
                supports_signal_evidence=True,
                supports_broad_discovery=True,
            )
        ],
        "budget": SignalMonitoringBudget(max_tasks=10, max_provider_calls=10, max_retries_per_task=1),
    }
    payload.update(overrides)
    return SignalMonitoringInput(**payload)


def source_card(
    *,
    source_id: str,
    connector_profile_id: str,
    source_type: str = "web",
    supports_signal_evidence: bool,
    supports_broad_discovery: bool = False,
) -> RadarPlannerSourceCard:
    return RadarPlannerSourceCard(
        source_id=source_id,
        source_label=source_id,
        connector_profile_id=connector_profile_id,
        source_type=source_type,
        supports_signal_evidence=supports_signal_evidence,
        supports_broad_discovery=supports_broad_discovery,
    )


def observed_payload(*, summary: str = "New TOIR tender", observed_at: str = "2026-06-30") -> dict[str, Any]:
    return {
        "sources": [
            {
                "source_ref": "src-signal",
                "title": "Tender",
                "url": "https://example.test/signal",
                "snippet": "Candidate A posted a TOIR tender.",
            }
        ],
        "observations": [
            {
                "candidate_id": "candidate-a",
                "signal_code": "toir_tender",
                "status": "observed",
                "summary": summary,
                "score": 2,
                "evidence_refs": ["src-signal"],
                "observed_at": observed_at,
            }
        ],
    }


def searched_negative_payload() -> dict[str, Any]:
    return {
        "sources": [{"source_ref": "src-empty", "title": "Search result", "url": "https://example.test/empty"}],
        "observations": [
            {
                "candidate_id": "candidate-a",
                "signal_code": "toir_tender",
                "status": "not_observed",
                "summary": "Searched the allowed sources and found no fresh signal.",
            }
        ],
    }


def test_signal_found_projects_observed_and_searched_state() -> None:
    provider = ScriptedSignalProvider([observed_payload()])

    outcome = SignalMonitoringExecutor(provider).run(base_input())

    observation = outcome.observations[0]
    assert observation.observation_status == "observed"
    assert observation.search_status == "searched"
    assert observation.source_refs == ["src-signal"]
    assert outcome.budget_counters["provider_calls"] == 1
    assert outcome.budget_counters["signal_provider_calls"] == 1
    assert outcome.budget_counters["signal_tasks_executed"] == 1
    assert outcome.model_profile_id == "signal_monitoring_default"
    assert outcome.model_profile_summary["pipeline_id"] == "signal-monitoring"
    assert provider.calls == [("signal-candidate-a-toir_tender-open_web-1", "primary")]


def test_run_and_plan_contracts_wrap_input_and_tasks() -> None:
    monitoring_input = base_input()
    provider = ScriptedSignalProvider([observed_payload()])

    outcome = SignalMonitoringExecutor(provider).run(monitoring_input)
    run = SignalMonitoringRun(
        run_id=monitoring_input.run_id,
        radar_id=monitoring_input.radar_id,
        status="completed",
        monitoring_input=monitoring_input,
        plan=SignalMonitoringPlan(radar_id=monitoring_input.radar_id, tasks=outcome.tasks),
    )

    assert run.plan is not None
    assert run.plan.tasks[0].signal_code == "toir_tender"
    assert run.monitoring_input is not None


def test_searched_negative_is_not_observed_only_after_search() -> None:
    provider = ScriptedSignalProvider([searched_negative_payload()])

    outcome = SignalMonitoringExecutor(provider).run(base_input())

    observation = outcome.observations[0]
    assert observation.observation_status == "not_observed"
    assert observation.search_status == "searched"


def test_budget_limited_task_is_not_projected_as_not_observed() -> None:
    provider = ScriptedSignalProvider([observed_payload()])
    monitoring_input = base_input(budget=SignalMonitoringBudget(max_signal_tasks=0, max_provider_calls=10))

    outcome = SignalMonitoringExecutor(provider).run(monitoring_input)

    observation = outcome.observations[0]
    assert observation.observation_status == "unclear"
    assert observation.search_status == "not_searched_budget_limited"
    assert provider.calls == []


def test_signal_provider_call_budget_blocks_provider_call() -> None:
    provider = ScriptedSignalProvider([observed_payload()])
    monitoring_input = base_input(budget=SignalMonitoringBudget(max_signal_provider_calls=0))

    outcome = SignalMonitoringExecutor(provider).run(monitoring_input)

    observation = outcome.observations[0]
    assert observation.observation_status == "unclear"
    assert observation.search_status == "not_searched_budget_limited"
    assert outcome.budget_counters["signal_provider_calls"] == 0
    assert provider.calls == []


def test_policy_limited_task_is_not_executed() -> None:
    provider = ScriptedSignalProvider([observed_payload()])
    monitoring_input = base_input(source_policy=SignalMonitoringSourcePolicy(enabled=False))

    outcome = SignalMonitoringExecutor(provider).run(monitoring_input)

    observation = outcome.observations[0]
    assert observation.search_status == "not_searched_policy_limited"
    assert observation.observation_status == "unclear"
    assert provider.calls == []


def test_no_executable_source_lane_does_not_emit_not_observed() -> None:
    provider = ScriptedSignalProvider([observed_payload()])
    monitoring_input = base_input(
        source_cards=[
            source_card(
                source_id="registry",
                connector_profile_id="registry_identity_only",
                supports_signal_evidence=False,
            )
        ],
        source_policy=SignalMonitoringSourcePolicy(allowed_source_ids=["registry"], allow_open_web=False),
    )

    outcome = SignalMonitoringExecutor(provider).run(monitoring_input)

    assert outcome.observations[0].observation_status == "unclear"
    assert outcome.observations[0].search_status == "not_searched_policy_limited"
    assert outcome.source_strategy_diagnostics[0].code == "no_executable_signal_source_lane"
    assert provider.calls == []


def test_malformed_payload_retries_primary_then_backup_model() -> None:
    primary = ScriptedSignalProvider(["not json", {"sources": [], "observations": "bad"}])
    backup = ScriptedSignalProvider([observed_payload()])

    outcome = SignalMonitoringExecutor(primary, backup_provider=backup).run(base_input())

    assert outcome.observations[0].observation_status == "observed"
    assert [attempt.attempt_role for attempt in outcome.provider_attempts] == [
        "primary",
        "primary_retry",
        "backup_retry",
    ]
    assert outcome.budget_counters["retries"] == 1
    assert outcome.budget_counters["signal_extraction_retries"] == 1
    assert outcome.budget_counters["backup_retries"] == 1
    assert outcome.budget_counters["signal_backup_retries"] == 1


def test_signal_retry_budget_exhaustion_stops_before_backup() -> None:
    primary = ScriptedSignalProvider(["not json"])
    backup = ScriptedSignalProvider([observed_payload()])

    outcome = SignalMonitoringExecutor(primary, backup_provider=backup).run(
        base_input(budget=SignalMonitoringBudget(max_signal_extraction_retries=0, allow_backup_retry=True))
    )

    observation = outcome.observations[0]
    assert observation.search_status == "schema_recovery_needed"
    assert "signal_extraction_retry_budget_exhausted" in observation.summary
    assert outcome.budget_counters["signal_extraction_retries"] == 0
    assert backup.calls == []


def test_repairable_payload_is_fixed_without_backup() -> None:
    repairable = {
        "sources": {
            "source_ref": "src-signal",
            "title": "Tender",
            "url": "https://example.test/signal",
        },
        "observations": {
            "candidate_id": "candidate-a",
            "signal_code": "toir_tender",
            "status": "observed",
            "summary": "New TOIR tender",
            "evidence_refs": ["src-signal"],
        },
    }
    primary = ScriptedSignalProvider([repairable])
    backup = ScriptedSignalProvider([observed_payload(summary="Backup should not run")])

    outcome = SignalMonitoringExecutor(primary, backup_provider=backup).run(base_input())

    assert outcome.observations[0].observation_status == "observed"
    assert [attempt.attempt_role for attempt in outcome.provider_attempts] == ["primary"]
    assert backup.calls == []


def test_repeated_schema_failure_returns_diagnostic_state() -> None:
    provider = ScriptedSignalProvider(["not json", {"sources": [], "observations": "bad"}])

    outcome = SignalMonitoringExecutor(provider).run(base_input())

    observation = outcome.observations[0]
    assert observation.observation_status == "unclear"
    assert observation.search_status == "schema_recovery_needed"
    assert "backup_not_configured" in observation.summary


def test_unresolved_evidence_ref_does_not_become_observed_signal() -> None:
    payload = observed_payload()
    payload["observations"][0]["evidence_refs"] = ["missing-src"]
    provider = ScriptedSignalProvider([payload])

    outcome = SignalMonitoringExecutor(provider).run(base_input())

    observation = outcome.observations[0]
    assert observation.observation_status == "unclear"
    assert observation.search_status == "evidence_linking_failed"


def test_duplicate_old_signal_is_not_reported_as_new() -> None:
    previous = "candidate-a|toir_tender|https://example.test/signal|2026-06-30|new toir tender"
    provider = ScriptedSignalProvider([observed_payload()])

    outcome = SignalMonitoringExecutor(provider).run(base_input(previous_signal_fingerprints=[previous]))

    observation = outcome.observations[0]
    assert observation.observation_status == "unclear"
    assert observation.search_status == "duplicate_existing_signal"
    assert observation.score == 0


def test_unmonitorable_candidate_is_explicit_missing_scope() -> None:
    provider = ScriptedSignalProvider([observed_payload()])
    monitoring_input = base_input(
        candidates=[
            SignalMonitoringCandidate(
                candidate_id="candidate-a",
                display_name="Candidate A",
                monitorable=False,
                review_flags=["requires_human_review"],
            )
        ]
    )

    outcome = SignalMonitoringExecutor(provider).run(monitoring_input)

    assert outcome.observations[0].search_status == "not_searched_missing_candidate_scope"
    assert provider.calls == []


def test_outcome_does_not_expose_raw_provider_secrets_or_hidden_reasoning() -> None:
    payload = observed_payload()
    payload["Authorization"] = "Bearer should-not-leak"
    payload["hidden_reasoning"] = "private reasoning"
    provider = ScriptedSignalProvider([payload])

    outcome = SignalMonitoringExecutor(provider).run(base_input())

    serialized = outcome.model_dump_json()
    assert "Authorization" not in serialized
    assert "Bearer" not in serialized
    assert "hidden_reasoning" not in serialized
