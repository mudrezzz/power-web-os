"""No-network executor for Radar signal-monitoring contract tests.

The executor is intentionally provider-neutral. It calls a scripted provider
port supplied by tests, validates payload shape, applies bounded retry/backup
recovery, and returns explicit diagnostic states without touching HTTP,
persistence, Redis, Celery, or API routes.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from power_web_os.application.signal_monitoring_contracts import (
    SignalAttemptRole,
    SignalEvidence,
    SignalMonitoringDiagnostic,
    SignalMonitoringEvidenceProvider,
    SignalMonitoringInput,
    SignalMonitoringOutcome,
    SignalMonitoringProviderResult,
    SignalMonitoringSourceStrategyResult,
    SignalObservation,
    SignalProviderAttemptRecord,
    SignalSearchStatus,
    SignalSearchTask,
    SignalSourceRef,
)
from power_web_os.application.signal_monitoring_source_strategy import SignalMonitoringSourceStrategy


@dataclass(frozen=True)
class _ParsedSignalPayload:
    sources: list[SignalSourceRef]
    observations: list[dict[str, Any]]
    repaired: bool = False


@dataclass(frozen=True)
class _ParseFailure:
    code: str
    message: str
    path: str = "$"


class SignalMonitoringExecutor:
    """Execute the recorded signal-monitoring harness against a fake provider."""

    def __init__(
        self,
        provider: SignalMonitoringEvidenceProvider,
        *,
        backup_provider: SignalMonitoringEvidenceProvider | None = None,
        source_strategy: SignalMonitoringSourceStrategy | None = None,
    ) -> None:
        self.provider = provider
        self.backup_provider = backup_provider
        self.source_strategy = source_strategy or SignalMonitoringSourceStrategy()

    def run(self, monitoring_input: SignalMonitoringInput) -> SignalMonitoringOutcome:
        source_strategy_result = self.source_strategy.select_sources(monitoring_input)
        tasks = _build_tasks(monitoring_input, source_strategy_result)
        observations: list[SignalObservation] = []
        diagnostics: list[SignalMonitoringDiagnostic] = list(source_strategy_result.diagnostics)
        attempts: list[SignalProviderAttemptRecord] = []
        counters = {"tasks_built": len(tasks), "tasks_executed": 0, "provider_calls": 0, "retries": 0, "backup_retries": 0}

        if not monitoring_input.candidates:
            diagnostics.append(_diagnostic("not_searched_missing_candidate_scope", "No candidates were provided."))
        if not monitoring_input.source_policy.enabled:
            for task in tasks:
                observations.append(_not_searched(task, "not_searched_policy_limited", "Signal source policy is disabled."))
            return _outcome(monitoring_input, tasks, observations, diagnostics, attempts, counters, source_strategy_result)
        if not source_strategy_result.selected_decision_ids:
            for task in tasks:
                observations.append(_not_searched(task, "not_searched_policy_limited", "No executable signal source lane was selected."))
            return _outcome(monitoring_input, tasks, observations, diagnostics, attempts, counters, source_strategy_result)

        previous = set(monitoring_input.previous_signal_fingerprints)
        for task in tasks:
            candidate = next((item for item in monitoring_input.candidates if item.candidate_id == task.candidate_id), None)
            if candidate is None or not candidate.monitorable:
                observations.append(_not_searched(task, "not_searched_missing_candidate_scope", "Candidate is not monitorable."))
                continue
            if counters["tasks_executed"] >= monitoring_input.budget.max_tasks:
                observations.append(_not_searched(task, "not_searched_budget_limited", "Signal task budget exhausted."))
                continue

            result = self._execute_with_recovery(task, monitoring_input, counters, attempts, previous)
            observations.append(result)
            if result.search_status == "searched":
                counters["tasks_executed"] += 1

        return _outcome(monitoring_input, tasks, observations, diagnostics, attempts, counters, source_strategy_result)

    def _execute_with_recovery(
        self,
        task: SignalSearchTask,
        monitoring_input: SignalMonitoringInput,
        counters: dict[str, int],
        attempts: list[SignalProviderAttemptRecord],
        previous_fingerprints: set[str],
    ) -> SignalObservation:
        if counters["provider_calls"] >= monitoring_input.budget.max_provider_calls:
            return _not_searched(task, "not_searched_budget_limited", "Signal provider-call budget exhausted.")

        primary = self._attempt(task, "primary", counters, attempts)
        parsed = _parse_payload(primary.payload)
        if isinstance(parsed, _ParsedSignalPayload):
            return _observation_from_payload(task, parsed, previous_fingerprints)

        if counters["provider_calls"] >= monitoring_input.budget.max_provider_calls:
            return _schema_failed(task, "budget_exhausted_before_retry", parsed)

        if monitoring_input.budget.max_retries_per_task > 0:
            counters["retries"] += 1
            retry = self._attempt(task, "primary_retry", counters, attempts)
            parsed = _parse_payload(retry.payload)
            if isinstance(parsed, _ParsedSignalPayload):
                return _observation_from_payload(task, parsed, previous_fingerprints)

        if not monitoring_input.budget.allow_backup_retry or self.backup_provider is None:
            return _schema_failed(task, "backup_not_configured", parsed)
        if counters["provider_calls"] >= monitoring_input.budget.max_provider_calls:
            return _schema_failed(task, "budget_exhausted_before_backup", parsed)

        counters["backup_retries"] += 1
        backup = self._attempt(task, "backup_retry", counters, attempts)
        parsed = _parse_payload(backup.payload)
        if isinstance(parsed, _ParsedSignalPayload):
            return _observation_from_payload(task, parsed, previous_fingerprints)
        return _schema_failed(task, "backup_schema_invalid", parsed)

    def _attempt(
        self,
        task: SignalSearchTask,
        attempt_role: SignalAttemptRole,
        counters: dict[str, int],
        attempts: list[SignalProviderAttemptRecord],
    ) -> SignalMonitoringProviderResult:
        provider = self.backup_provider if attempt_role == "backup_retry" and self.backup_provider else self.provider
        counters["provider_calls"] += 1
        result = provider.run_signal_task(task=task, attempt_role=attempt_role)
        parse_result = _parse_payload(result.payload)
        attempts.append(SignalProviderAttemptRecord(
            task_id=task.task_id,
            attempt_role=attempt_role,
            outcome="accepted" if isinstance(parse_result, _ParsedSignalPayload) else parse_result.code,
            message="" if isinstance(parse_result, _ParsedSignalPayload) else parse_result.message,
        ))
        return result


def _build_tasks(
    monitoring_input: SignalMonitoringInput,
    source_strategy_result: SignalMonitoringSourceStrategyResult,
) -> list[SignalSearchTask]:
    tasks = []
    selected_decisions = [decision for decision in source_strategy_result.decisions if decision.status == "selected"]
    if not selected_decisions:
        selected_decisions = []
    for candidate in monitoring_input.candidates:
        for rule in monitoring_input.signal_rules:
            decisions = selected_decisions or [None]
            for index, decision in enumerate(decisions, start=1):
                query = rule.query_template.format(candidate=candidate.display_name, signal=rule.label)
                suffix = f"-{decision.lane}-{index}" if decision else "-no-source"
                tasks.append(SignalSearchTask(
                    task_id=f"signal-{candidate.candidate_id}-{rule.signal_code}{suffix}",
                    candidate_id=candidate.candidate_id,
                    candidate_name=candidate.display_name,
                    signal_code=rule.signal_code,
                    signal_label=rule.label,
                    query=" ".join(query.split()),
                    lookback_days=monitoring_input.lookback_days,
                    known_source_refs=list(candidate.source_refs),
                    source_lane=decision.lane if decision else "open_web",
                    source_ids=[decision.source_id] if decision and decision.source_id else [],
                    source_refs=list(decision.source_refs) if decision else [],
                    source_decision_ids=[decision.decision_id] if decision else [],
                ))
    return tasks


def _parse_payload(payload: Any) -> _ParsedSignalPayload | _ParseFailure:
    payload, repaired_json = _payload_object(payload)
    if not isinstance(payload, dict):
        return _ParseFailure("schema_invalid", "Provider payload must be a JSON object.")
    sources, sources_repaired = _list_field(payload, "sources", SignalSourceRef)
    if isinstance(sources, _ParseFailure):
        return sources
    raw_observations = _raw_list_field(payload, "observations")
    if isinstance(raw_observations, _ParseFailure):
        return raw_observations
    observations, observations_repaired = raw_observations
    return _ParsedSignalPayload(sources=sources, observations=observations, repaired=repaired_json or sources_repaired or observations_repaired)


def _payload_object(payload: Any) -> tuple[Any, bool]:
    if not isinstance(payload, str):
        return payload, False
    stripped = payload.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?", "", stripped).strip()
        stripped = re.sub(r"```$", "", stripped).strip()
    try:
        return json.loads(stripped), True
    except json.JSONDecodeError:
        return payload, False


def _list_field(payload: dict[str, Any], field_name: str, model_type: type[SignalSourceRef]) -> tuple[list[SignalSourceRef], bool] | _ParseFailure:
    raw = payload.get(field_name, [])
    if isinstance(raw, dict):
        raw = [raw]
        repaired = True
    else:
        repaired = False
    if not isinstance(raw, list):
        return _ParseFailure("schema_invalid", f"{field_name} must be a list.", f"$.{field_name}")
    try:
        return [model_type.model_validate(item) for item in raw if isinstance(item, dict)], repaired
    except Exception as exc:  # pragma: no cover - pydantic message is not stable enough for exact assertions
        return _ParseFailure("schema_invalid", f"{field_name} item is invalid: {exc}", f"$.{field_name}")


def _raw_list_field(payload: dict[str, Any], field_name: str) -> tuple[list[dict[str, Any]], bool] | _ParseFailure:
    raw = payload.get(field_name, [])
    if isinstance(raw, dict):
        raw = [raw]
        repaired = True
    else:
        repaired = False
    if not isinstance(raw, list):
        return _ParseFailure("schema_invalid", f"{field_name} must be a list.", f"$.{field_name}")
    if not all(isinstance(item, dict) for item in raw):
        return _ParseFailure("schema_invalid", f"{field_name} items must be objects.", f"$.{field_name}")
    return raw, repaired


def _observation_from_payload(
    task: SignalSearchTask,
    parsed: _ParsedSignalPayload,
    previous_fingerprints: set[str],
) -> SignalObservation:
    source_refs = {source.source_ref: source for source in parsed.sources}
    raw = next(
        (
            item
            for item in parsed.observations
            if str(item.get("candidate_id")) == task.candidate_id and str(item.get("signal_code")) == task.signal_code
        ),
        None,
    )
    if raw is None:
        return SignalObservation(
            task_id=task.task_id,
            candidate_id=task.candidate_id,
            signal_code=task.signal_code,
            observation_status="not_observed",
            search_status="searched",
            summary="Signal was searched and not observed.",
        )
    status = str(raw.get("status") or raw.get("observation_status") or "unclear")
    evidence_refs = [str(item) for item in raw.get("evidence_refs", []) if str(item)]
    if status == "not_observed":
        return SignalObservation(
            task_id=task.task_id,
            candidate_id=task.candidate_id,
            signal_code=task.signal_code,
            observation_status="not_observed",
            search_status="searched",
            summary=str(raw.get("summary") or "Signal was searched and not observed."),
        )
    if status == "observed" and not evidence_refs:
        return _diagnostic_observation(task, "evidence_linking_failed", "Observed signal did not include evidence refs.")
    missing_refs = [ref for ref in evidence_refs if ref not in source_refs]
    if missing_refs:
        return _diagnostic_observation(task, "evidence_linking_failed", f"Evidence refs did not resolve: {', '.join(missing_refs)}")
    evidence = [
        SignalEvidence(
            source_ref=ref,
            fact=str(raw.get("fact") or raw.get("summary") or "Signal evidence found."),
            excerpt=str(raw.get("excerpt") or ""),
            observed_at=str(raw.get("observed_at") or ""),
            confidence=str(raw.get("confidence") or "medium"),  # type: ignore[arg-type]
        )
        for ref in evidence_refs
    ]
    fingerprint = _fingerprint(task, raw, [source_refs[ref] for ref in evidence_refs])
    if fingerprint in previous_fingerprints:
        return SignalObservation(
            task_id=task.task_id,
            candidate_id=task.candidate_id,
            signal_code=task.signal_code,
            observation_status="unclear",
            search_status="duplicate_existing_signal",
            summary=str(raw.get("summary") or "Signal was already observed before this monitoring window."),
            score=0,
            evidence=evidence,
            source_refs=evidence_refs,
            fingerprint=fingerprint,
        )
    return SignalObservation(
        task_id=task.task_id,
        candidate_id=task.candidate_id,
        signal_code=task.signal_code,
        observation_status="observed" if status == "observed" else "unclear",
        search_status="searched",
        summary=str(raw.get("summary") or "Signal evidence found."),
        score=int(raw.get("score") or 1 if status == "observed" else 0),
        evidence=evidence,
        source_refs=evidence_refs,
        fingerprint=fingerprint,
    )


def _fingerprint(task: SignalSearchTask, raw: dict[str, Any], sources: list[SignalSourceRef]) -> str:
    source_key = "|".join(sorted((source.url or source.source_ref).strip().lower().rstrip("/") for source in sources))
    return "|".join([
        task.candidate_id,
        task.signal_code,
        source_key,
        str(raw.get("observed_at") or "").strip().lower(),
        str(raw.get("summary") or raw.get("fact") or "").strip().lower(),
    ])


def _schema_failed(task: SignalSearchTask, reason: str, failure: _ParseFailure) -> SignalObservation:
    return _diagnostic_observation(task, "schema_recovery_needed", f"{reason}: {failure.message}", path=failure.path)


def _diagnostic_observation(task: SignalSearchTask, status: SignalSearchStatus, message: str, *, path: str = "") -> SignalObservation:
    diagnostic = _diagnostic(status, message, task_id=task.task_id, candidate_id=task.candidate_id, signal_code=task.signal_code, path=path)
    return SignalObservation(
        task_id=task.task_id,
        candidate_id=task.candidate_id,
        signal_code=task.signal_code,
        observation_status="unclear",
        search_status=status,
        summary=message,
        diagnostics=[diagnostic],
    )


def _not_searched(task: SignalSearchTask, status: SignalSearchStatus, message: str) -> SignalObservation:
    return _diagnostic_observation(task, status, message)


def _diagnostic(
    code: str,
    message: str,
    *,
    task_id: str = "",
    candidate_id: str = "",
    signal_code: str = "",
    path: str = "",
) -> SignalMonitoringDiagnostic:
    return SignalMonitoringDiagnostic(code=code, message=message, task_id=task_id, candidate_id=candidate_id, signal_code=signal_code, path=path)


def _outcome(
    monitoring_input: SignalMonitoringInput,
    tasks: list[SignalSearchTask],
    observations: list[SignalObservation],
    diagnostics: list[SignalMonitoringDiagnostic],
    attempts: list[SignalProviderAttemptRecord],
    counters: dict[str, int],
    source_strategy_result: SignalMonitoringSourceStrategyResult,
) -> SignalMonitoringOutcome:
    return SignalMonitoringOutcome(
        run_id=monitoring_input.run_id,
        radar_id=monitoring_input.radar_id,
        tasks=tasks,
        observations=observations,
        diagnostics=diagnostics,
        source_strategy_decisions=source_strategy_result.decisions,
        source_strategy_diagnostics=source_strategy_result.diagnostics,
        provider_attempts=attempts,
        budget_counters=counters,
    )
