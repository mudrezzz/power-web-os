"""Provider-neutral execution for the standalone signal-monitoring pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from power_web_os.application.radar.signal_monitoring.budgets import SignalMonitoringBudgetTracker
from power_web_os.application.radar.signal_monitoring.checkpoints import SignalMonitoringCheckpointService
from power_web_os.application.radar.signal_monitoring.cross_criterion import (
    SignalCrossCriterionEvidenceReconciliationService,
)
from power_web_os.application.radar.signal_monitoring.contracts import (
    SignalAttemptRole,
    SignalEvidenceValidationRecord,
    SignalMonitoringDiagnostic,
    SignalMonitoringEvidenceProvider,
    SignalMonitoringInput,
    SignalMonitoringOutcome,
    SignalMonitoringProviderResult,
    SignalMonitoringWatermark,
    SignalObservation,
    SignalProviderAttemptRecord,
    SignalSearchExecutionReceipt,
    SignalSearchTask,
    SignalSourceLaneLedgerEntry,
    SignalSourceLifecycleRecord,
)
from power_web_os.application.radar.signal_monitoring.evidence import SignalEvidenceValidationService
from power_web_os.application.radar.signal_monitoring.payloads import (
    ParsedSignalPayload,
    SignalPayloadParseFailure,
    parse_payload,
)
from power_web_os.application.radar.signal_monitoring.planning import SignalMonitoringPlanningPipeline
from power_web_os.application.radar.signal_monitoring.projection import (
    diagnostic,
    diagnostic_observation,
    not_searched,
    outcome,
    schema_failed,
)
from power_web_os.application.radar.signal_monitoring.receipts import SignalSearchReceiptFactory
from power_web_os.application.radar.signal_monitoring.revisions import SignalMonitoringQueryRevisionService
from power_web_os.application.radar.signal_monitoring.source_strategy import SignalMonitoringSourceStrategy
from power_web_os.application.radar.configuration.model_profiles import (
    RadarModelProfileRegistry,
    default_model_profile_registry,
)


@dataclass(frozen=True, slots=True)
class _TaskResult:
    observation: SignalObservation
    receipt: SignalSearchExecutionReceipt
    validation: SignalEvidenceValidationRecord | None = None


@dataclass(frozen=True, slots=True)
class _AttemptResult:
    parsed: ParsedSignalPayload | SignalPayloadParseFailure | None
    receipt: SignalSearchExecutionReceipt
    observation: SignalObservation | None = None


class SignalMonitoringExecutor:
    """Execute accepted multi-lane signal work under pipeline-owned policy."""

    def __init__(
        self,
        provider: SignalMonitoringEvidenceProvider,
        *,
        backup_provider: SignalMonitoringEvidenceProvider | None = None,
        source_strategy: SignalMonitoringSourceStrategy | None = None,
        planning_pipeline: SignalMonitoringPlanningPipeline | None = None,
        evidence_validator: SignalEvidenceValidationService | None = None,
        checkpoint_service: SignalMonitoringCheckpointService | None = None,
        receipt_factory: SignalSearchReceiptFactory | None = None,
        query_revision_service: SignalMonitoringQueryRevisionService | None = None,
        cross_criterion_service: SignalCrossCriterionEvidenceReconciliationService | None = None,
        model_profile_registry: RadarModelProfileRegistry | None = None,
    ) -> None:
        self.provider = provider
        self.backup_provider = backup_provider
        self.source_strategy = source_strategy or SignalMonitoringSourceStrategy()
        self.planning_pipeline = planning_pipeline or SignalMonitoringPlanningPipeline()
        self.evidence_validator = evidence_validator or SignalEvidenceValidationService()
        self.checkpoint_service = checkpoint_service or SignalMonitoringCheckpointService()
        self.receipt_factory = receipt_factory or SignalSearchReceiptFactory()
        self.query_revision_service = query_revision_service or SignalMonitoringQueryRevisionService()
        self.cross_criterion_service = (
            cross_criterion_service or SignalCrossCriterionEvidenceReconciliationService()
        )
        self.model_profile_registry = model_profile_registry or default_model_profile_registry()

    def run(self, monitoring_input: SignalMonitoringInput) -> SignalMonitoringOutcome:
        model_profile = monitoring_input.model_profile or self.model_profile_registry.require(monitoring_input.model_profile_id)
        strategy = self.source_strategy.select_sources(monitoring_input)
        execution_plan = self.planning_pipeline.build(monitoring_input, strategy)
        scheduled_tasks = execution_plan.schedule.tasks
        ledger = list(execution_plan.schedule.ledger)
        diagnostics: list[SignalMonitoringDiagnostic] = list(strategy.diagnostics)
        attempts: list[SignalProviderAttemptRecord] = []
        task_observations: list[SignalObservation] = []
        receipts: list[SignalSearchExecutionReceipt] = []
        validations: list[SignalEvidenceValidationRecord] = []
        lifecycle: list[SignalSourceLifecycleRecord] = [
            self.receipt_factory.planned(task) for task in execution_plan.search_plan.tasks
        ]
        budget = SignalMonitoringBudgetTracker(monitoring_input, task_count=len(execution_plan.search_plan.tasks))

        if execution_plan.acceptance.errors:
            diagnostics.extend(diagnostic("signal_plan_rejected", message) for message in execution_plan.acceptance.errors)
        executable = bool(strategy.selected_decision_ids) and execution_plan.acceptance.accepted and monitoring_input.source_policy.enabled
        previous = set(monitoring_input.previous_signal_fingerprints)
        previous_source_keys = set(monitoring_input.previous_signal_source_keys)
        if executable:
            for task in scheduled_tasks:
                candidate = next(
                    (item for item in monitoring_input.candidates if item.candidate_id == task.candidate_id),
                    None,
                )
                if candidate is None or not candidate.monitorable:
                    task_observations.append(not_searched(
                        task,
                        "not_searched_missing_candidate_scope",
                        "Candidate is not monitorable.",
                    ))
                    continue
                if budget.task_budget_exhausted():
                    budget.record_exhaustion(budget="signal_tasks", task_id=task.task_id, limit=budget.max_signal_tasks())
                    task_observations.append(not_searched(task, "not_searched_budget_limited", "Signal task budget exhausted."))
                    continue
                if budget.lookback_budget_exhausted():
                    limit = monitoring_input.budget.max_signal_lookback_queries or 0
                    budget.record_exhaustion(budget="signal_lookback_queries", task_id=task.task_id, limit=limit)
                    task_observations.append(not_searched(task, "not_searched_budget_limited", "Signal lookback query budget exhausted."))
                    continue
                budget.record_lookback_query()
                lifecycle.append(self.receipt_factory.requested(task))
                result = self._execute_with_recovery(
                    task, monitoring_input, budget, attempts, previous, previous_source_keys
                )
                task_observations.append(result.observation)
                receipts.append(result.receipt)
                lifecycle.extend(self.receipt_factory.lifecycle(result.receipt))
                if result.validation is not None:
                    validations.append(result.validation)
                    if result.validation.accepted and result.observation.observation_status == "observed":
                        lifecycle.extend(self.receipt_factory.accepted_evidence(task, result.observation.source_refs))
                ledger = [
                    item.model_copy(update={"status": "executed", "reason": result.receipt.outcome})
                    if item.task_id == task.task_id else item
                    for item in ledger
                ]
                if result.observation.search_status in {"searched", "duplicate_existing_signal"}:
                    budget.record_searched_task()
        else:
            message = "Signal source policy is disabled." if not monitoring_input.source_policy.enabled else "No accepted executable signal-search plan is available."
            task_observations.extend(
                not_searched(task, "not_searched_policy_limited", message) for task in scheduled_tasks
            )
            ledger = [item.model_copy(update={"status": "policy_limited", "reason": message}) for item in ledger]

        observations, checkpoints = self.checkpoint_service.review(
            tasks=execution_plan.search_plan.tasks,
            task_observations=task_observations,
            ledger=ledger,
            receipts=receipts,
        )
        revision_tasks = self.query_revision_service.build(
            decisions=checkpoints,
            tasks=execution_plan.search_plan.tasks,
            max_revisions_per_pair=monitoring_input.budget.max_query_revisions_per_candidate_signal,
            allow_open_web=monitoring_input.source_policy.allow_open_web,
        )
        for task in revision_tasks:
            if budget.task_budget_exhausted() or budget.provider_budget_exhausted():
                task_observations.append(not_searched(
                    task, "not_searched_budget_limited", "Signal query revision budget exhausted."
                ))
                ledger.append(_revision_ledger(task, "not_scheduled_budget_limited", "revision_budget_limited"))
                continue
            budget.record_lookback_query()
            lifecycle.extend([self.receipt_factory.planned(task), self.receipt_factory.requested(task)])
            result = self._execute_with_recovery(
                task, monitoring_input, budget, attempts, previous, previous_source_keys
            )
            scheduled_tasks.append(task)
            execution_plan.search_plan.tasks.append(task)
            task_observations.append(result.observation)
            receipts.append(result.receipt)
            lifecycle.extend(self.receipt_factory.lifecycle(result.receipt))
            if result.validation is not None:
                validations.append(result.validation)
                if result.validation.accepted and result.observation.observation_status == "observed":
                    lifecycle.extend(self.receipt_factory.accepted_evidence(task, result.observation.source_refs))
            ledger.append(_revision_ledger(task, "executed", result.receipt.outcome))
            if result.observation.search_status in {"searched", "duplicate_existing_signal"}:
                budget.record_searched_task()
        reconciled, cross_criterion_records = self.cross_criterion_service.reconcile(
            tasks=execution_plan.search_plan.tasks,
            rules=monitoring_input.signal_rules,
            task_observations=task_observations,
            previous_source_keys=previous_source_keys,
        )
        task_observations.extend(reconciled)
        observations, checkpoints = self.checkpoint_service.review(
            tasks=execution_plan.search_plan.tasks,
            task_observations=task_observations,
            ledger=ledger,
            receipts=receipts,
        )
        watermarks_after = _advanced_watermarks(monitoring_input, receipts)
        return outcome(
            monitoring_input,
            scheduled_tasks,
            observations,
            diagnostics,
            attempts,
            budget.counters,
            budget.settings_payload(),
            budget.exhaustion_events,
            strategy,
            model_profile,
            search_plan=execution_plan.search_plan,
            plan_acceptance=execution_plan.acceptance,
            task_observations=task_observations,
            source_lane_ledger=ledger,
            search_execution_receipts=receipts,
            source_lifecycle=lifecycle,
            watermarks_before=monitoring_input.previous_watermarks,
            watermarks_after=watermarks_after,
            evidence_validation_records=validations,
            cross_criterion_validation_records=cross_criterion_records,
            checkpoint_decisions=checkpoints,
        )

    def _execute_with_recovery(
        self,
        task: SignalSearchTask,
        monitoring_input: SignalMonitoringInput,
        budget: SignalMonitoringBudgetTracker,
        attempts: list[SignalProviderAttemptRecord],
        previous_fingerprints: set[str],
        previous_source_keys: set[str],
    ) -> _TaskResult:
        if budget.provider_budget_exhausted():
            budget.record_exhaustion(budget="signal_provider_calls", task_id=task.task_id, limit=budget.max_signal_provider_calls())
            receipt = self._receipt(task, [], "budget_limited", _now(), provider=self.provider)
            return _TaskResult(not_searched(task, "not_searched_budget_limited", "Signal provider-call budget exhausted."), receipt)

        attempt = self._attempt_safely(task, "primary", budget, attempts)
        if attempt.observation is not None:
            return _TaskResult(attempt.observation, attempt.receipt)
        if isinstance(attempt.parsed, ParsedSignalPayload):
            observation, validation = self._validate_evidence(
                task, attempt.parsed, previous_fingerprints, previous_source_keys, budget
            )
            return _TaskResult(observation, attempt.receipt, validation)
        failure = attempt.parsed or SignalPayloadParseFailure("schema_invalid", "Provider payload was unavailable.")

        if budget.retry_budget_available(task.task_id) and not budget.provider_budget_exhausted():
            budget.record_primary_retry(task.task_id)
            retry = self._attempt_safely(task, "primary_retry", budget, attempts)
            if retry.observation is not None:
                return _TaskResult(retry.observation, retry.receipt)
            if isinstance(retry.parsed, ParsedSignalPayload):
                observation, validation = self._validate_evidence(
                    task, retry.parsed, previous_fingerprints, previous_source_keys, budget
                )
                return _TaskResult(observation, retry.receipt, validation)
            failure, attempt = retry.parsed or failure, retry
        else:
            return _TaskResult(
                _failure_observation(task, "signal_extraction_retry_budget_exhausted", failure),
                attempt.receipt,
            )

        if (
            monitoring_input.budget.allow_backup_retry
            and self.backup_provider is not None
            and budget.backup_retry_budget_available()
            and not budget.provider_budget_exhausted()
        ):
            budget.record_backup_retry()
            backup = self._attempt_safely(task, "backup_retry", budget, attempts)
            if backup.observation is not None:
                return _TaskResult(backup.observation, backup.receipt)
            if isinstance(backup.parsed, ParsedSignalPayload):
                observation, validation = self._validate_evidence(
                    task, backup.parsed, previous_fingerprints, previous_source_keys, budget
                )
                return _TaskResult(observation, backup.receipt, validation)
            failure, attempt = backup.parsed or failure, backup
        reason = "backup_not_configured" if self.backup_provider is None else "signal_schema_recovery_exhausted"
        return _TaskResult(_failure_observation(task, reason, failure), attempt.receipt)

    def _validate_evidence(
        self,
        task: SignalSearchTask,
        parsed: ParsedSignalPayload,
        previous_fingerprints: set[str],
        previous_source_keys: set[str],
        budget: SignalMonitoringBudgetTracker,
    ) -> tuple[SignalObservation, SignalEvidenceValidationRecord]:
        verification_refs = {
            str(ref)
            for observation in parsed.observations
            if str(observation.get("candidate_id") or "") == task.candidate_id
            and str(observation.get("signal_code") or "") == task.signal_code
            and str(observation.get("status") or observation.get("observation_status") or "") == "observed"
            for ref in observation.get("evidence_refs", [])
            if str(ref)
        }
        verification_count = len(verification_refs)
        if not budget.source_verification_budget_available(verification_count):
            limit = budget.monitoring_input.budget.max_signal_source_verifications or 0
            budget.record_exhaustion(budget="signal_source_verifications", task_id=task.task_id, limit=limit)
            return (
                diagnostic_observation(task, "review_needed", "Signal source-verification budget exhausted."),
                SignalEvidenceValidationRecord(
                    task_id=task.task_id,
                    candidate_id=task.candidate_id,
                    signal_code=task.signal_code,
                    accepted=False,
                    reason="source_verification_budget_exhausted",
                ),
            )
        budget.record_source_verifications(verification_count)
        return self.evidence_validator.validate(
            task=task,
            parsed=parsed,
            previous_fingerprints=previous_fingerprints,
            previous_source_keys=previous_source_keys,
            source_refs_to_enrich=verification_refs,
        )

    def _attempt_safely(
        self,
        task: SignalSearchTask,
        role: SignalAttemptRole,
        budget: SignalMonitoringBudgetTracker,
        attempts: list[SignalProviderAttemptRecord],
    ) -> _AttemptResult:
        provider = self.backup_provider if role == "backup_retry" and self.backup_provider else self.provider
        started = _now()
        try:
            budget.record_provider_call()
            result = provider.run_signal_task(task=task, attempt_role=role)
            parsed = parse_payload(result.payload)
            sources = parsed.sources if isinstance(parsed, ParsedSignalPayload) else []
            receipt = result.execution_receipt or self._receipt(
                task,
                sources,
                "retrieved" if sources else ("no_results" if isinstance(parsed, ParsedSignalPayload) else "schema_invalid"),
                started,
                provider=provider,
            )
            attempts.append(SignalProviderAttemptRecord(
                task_id=task.task_id,
                attempt_role=role,
                outcome="accepted" if isinstance(parsed, ParsedSignalPayload) else parsed.code,
                message="" if isinstance(parsed, ParsedSignalPayload) else parsed.message,
                provider_runtime=result.runtime_name or getattr(provider, "runtime_name", ""),
                model_id=result.model_id or getattr(provider, "model_id", ""),
                attempt_index=len([item for item in attempts if item.task_id == task.task_id]) + 1,
            ))
            return _AttemptResult(parsed=parsed, receipt=receipt)
        except Exception as exc:
            failure = SignalPayloadParseFailure("provider_error", f"Signal provider failed: {type(exc).__name__}.")
            attempts.append(SignalProviderAttemptRecord(
                task_id=task.task_id,
                attempt_role=role,
                outcome="provider_error",
                message=str(exc),
                provider_runtime=getattr(provider, "runtime_name", ""),
                model_id=getattr(provider, "model_id", ""),
                attempt_index=len([item for item in attempts if item.task_id == task.task_id]) + 1,
            ))
            receipt = self._receipt(task, [], "provider_error", started, provider=provider)
            return _AttemptResult(parsed=failure, receipt=receipt)

    def _receipt(self, task, sources, outcome_name, started, *, provider):
        return self.receipt_factory.create(
            task=task,
            sources=sources,
            engine=str(getattr(provider, "web_search_engine", getattr(provider, "runtime_name", ""))),
            outcome=outcome_name,
            started_at=started,
        )


def _advanced_watermarks(
    monitoring_input: SignalMonitoringInput,
    receipts: list[SignalSearchExecutionReceipt],
) -> list[SignalMonitoringWatermark]:
    by_key = {
        (item.candidate_id, item.signal_code, item.source_lane): item
        for item in monitoring_input.previous_watermarks
    }
    for receipt in receipts:
        if receipt.outcome not in {"retrieved", "no_results"}:
            continue
        key = (receipt.candidate_id, receipt.signal_code, receipt.source_lane)
        by_key[key] = SignalMonitoringWatermark(
            candidate_id=receipt.candidate_id,
            signal_code=receipt.signal_code,
            source_lane=receipt.source_lane,
            searched_through_at=receipt.window_end,
            source_task_id=receipt.task_id,
        )
    return sorted(by_key.values(), key=lambda item: (item.candidate_id, item.signal_code, item.source_lane))


def _failure_observation(
    task: SignalSearchTask,
    reason: str,
    failure: SignalPayloadParseFailure,
) -> SignalObservation:
    if failure.code == "provider_error":
        return diagnostic_observation(task, "review_needed", f"{reason}: {failure.message}")
    return schema_failed(task, reason, failure)


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _revision_ledger(task: SignalSearchTask, status: str, reason: str) -> SignalSourceLaneLedgerEntry:
    return SignalSourceLaneLedgerEntry(
        task_id=task.task_id,
        candidate_id=task.candidate_id,
        signal_code=task.signal_code,
        source_lane=task.source_lane,
        required=False,
        status=status,
        reason=reason,
    )
