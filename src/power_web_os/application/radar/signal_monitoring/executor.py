"""No-network executor for Radar signal-monitoring contract tests.

The executor is intentionally provider-neutral. It calls a scripted provider
port supplied by tests, validates payload shape, applies bounded retry/backup
recovery, and returns explicit diagnostic states without touching HTTP,
persistence, Redis, Celery, or API routes.
"""

from __future__ import annotations

from power_web_os.application.radar.signal_monitoring.budgets import SignalMonitoringBudgetTracker
from power_web_os.application.radar.signal_monitoring.contracts import (
    SignalAttemptRole,
    SignalMonitoringDiagnostic,
    SignalMonitoringEvidenceProvider,
    SignalMonitoringInput,
    SignalMonitoringOutcome,
    SignalMonitoringProviderResult,
    SignalObservation,
    SignalProviderAttemptRecord,
    SignalSearchTask,
)
from power_web_os.application.radar.signal_monitoring.payloads import ParsedSignalPayload, parse_payload
from power_web_os.application.radar.signal_monitoring.planning import SignalMonitoringTaskPlanner
from power_web_os.application.radar.signal_monitoring.projection import (
    diagnostic,
    not_searched,
    observation_from_payload,
    outcome,
    schema_failed,
)
from power_web_os.application.radar.signal_monitoring.source_strategy import SignalMonitoringSourceStrategy
from power_web_os.application.radar_model_profiles import (
    RadarModelProfileRegistry,
    default_model_profile_registry,
)


class SignalMonitoringExecutor:
    """Execute the recorded signal-monitoring harness against a fake provider."""

    def __init__(
        self,
        provider: SignalMonitoringEvidenceProvider,
        *,
        backup_provider: SignalMonitoringEvidenceProvider | None = None,
        source_strategy: SignalMonitoringSourceStrategy | None = None,
        task_planner: SignalMonitoringTaskPlanner | None = None,
        model_profile_registry: RadarModelProfileRegistry | None = None,
    ) -> None:
        self.provider = provider
        self.backup_provider = backup_provider
        self.source_strategy = source_strategy or SignalMonitoringSourceStrategy()
        self.task_planner = task_planner or SignalMonitoringTaskPlanner()
        self.model_profile_registry = model_profile_registry or default_model_profile_registry()

    def run(self, monitoring_input: SignalMonitoringInput) -> SignalMonitoringOutcome:
        model_profile = monitoring_input.model_profile or self.model_profile_registry.require(monitoring_input.model_profile_id)
        source_strategy_result = self.source_strategy.select_sources(monitoring_input)
        tasks = self.task_planner.build_tasks(monitoring_input, source_strategy_result)
        observations: list[SignalObservation] = []
        diagnostics: list[SignalMonitoringDiagnostic] = list(source_strategy_result.diagnostics)
        attempts: list[SignalProviderAttemptRecord] = []
        budget = SignalMonitoringBudgetTracker(monitoring_input, task_count=len(tasks))

        if not monitoring_input.candidates:
            diagnostics.append(diagnostic("not_searched_missing_candidate_scope", "No candidates were provided."))
        if not monitoring_input.source_policy.enabled:
            for task in tasks:
                observations.append(not_searched(task, "not_searched_policy_limited", "Signal source policy is disabled."))
            return outcome(monitoring_input, tasks, observations, diagnostics, attempts, budget.counters, source_strategy_result, model_profile)
        if not source_strategy_result.selected_decision_ids:
            for task in tasks:
                observations.append(not_searched(task, "not_searched_policy_limited", "No executable signal source lane was selected."))
            return outcome(monitoring_input, tasks, observations, diagnostics, attempts, budget.counters, source_strategy_result, model_profile)

        previous = set(monitoring_input.previous_signal_fingerprints)
        for task in tasks:
            candidate = next((item for item in monitoring_input.candidates if item.candidate_id == task.candidate_id), None)
            if candidate is None or not candidate.monitorable:
                observations.append(not_searched(task, "not_searched_missing_candidate_scope", "Candidate is not monitorable."))
                continue
            if budget.task_budget_exhausted():
                observations.append(not_searched(task, "not_searched_budget_limited", "Signal task budget exhausted."))
                continue
            if budget.lookback_budget_exhausted():
                observations.append(not_searched(task, "not_searched_budget_limited", "Signal lookback query budget exhausted."))
                continue

            budget.record_lookback_query()
            result = self._execute_with_recovery(task, monitoring_input, budget, attempts, previous)
            observations.append(result)
            if result.search_status == "searched":
                budget.record_searched_task()

        return outcome(monitoring_input, tasks, observations, diagnostics, attempts, budget.counters, source_strategy_result, model_profile)

    def _execute_with_recovery(
        self,
        task: SignalSearchTask,
        monitoring_input: SignalMonitoringInput,
        budget: SignalMonitoringBudgetTracker,
        attempts: list[SignalProviderAttemptRecord],
        previous_fingerprints: set[str],
    ) -> SignalObservation:
        if budget.provider_budget_exhausted():
            return not_searched(task, "not_searched_budget_limited", "Signal provider-call budget exhausted.")

        primary = self._attempt(task, "primary", budget, attempts)
        parsed = parse_payload(primary.payload)
        if isinstance(parsed, ParsedSignalPayload):
            return observation_from_payload(task, parsed, previous_fingerprints)

        if budget.provider_budget_exhausted():
            return schema_failed(task, "budget_exhausted_before_retry", parsed)

        if budget.retry_budget_available():
            budget.record_primary_retry()
            retry = self._attempt(task, "primary_retry", budget, attempts)
            parsed = parse_payload(retry.payload)
            if isinstance(parsed, ParsedSignalPayload):
                return observation_from_payload(task, parsed, previous_fingerprints)
        else:
            return schema_failed(task, "signal_extraction_retry_budget_exhausted", parsed)

        if not monitoring_input.budget.allow_backup_retry or self.backup_provider is None:
            return schema_failed(task, "backup_not_configured", parsed)
        if budget.provider_budget_exhausted():
            return schema_failed(task, "budget_exhausted_before_backup", parsed)

        budget.record_backup_retry()
        backup = self._attempt(task, "backup_retry", budget, attempts)
        parsed = parse_payload(backup.payload)
        if isinstance(parsed, ParsedSignalPayload):
            return observation_from_payload(task, parsed, previous_fingerprints)
        return schema_failed(task, "backup_schema_invalid", parsed)

    def _attempt(
        self,
        task: SignalSearchTask,
        attempt_role: SignalAttemptRole,
        budget: SignalMonitoringBudgetTracker,
        attempts: list[SignalProviderAttemptRecord],
    ) -> SignalMonitoringProviderResult:
        provider = self.backup_provider if attempt_role == "backup_retry" and self.backup_provider else self.provider
        budget.record_provider_call()
        result = provider.run_signal_task(task=task, attempt_role=attempt_role)
        parse_result = parse_payload(result.payload)
        attempts.append(SignalProviderAttemptRecord(
            task_id=task.task_id,
            attempt_role=attempt_role,
            outcome="accepted" if isinstance(parse_result, ParsedSignalPayload) else parse_result.code,
            message="" if isinstance(parse_result, ParsedSignalPayload) else parse_result.message,
        ))
        return result
