"""Observation and outcome projection for signal monitoring."""

from __future__ import annotations

from typing import Any

from power_web_os.application.radar.signal_monitoring.contracts import (
    SignalEvidence,
    SignalMonitoringDiagnostic,
    SignalMonitoringInput,
    SignalMonitoringOutcome,
    SignalMonitoringSourceStrategyResult,
    SignalObservation,
    SignalProviderAttemptRecord,
    SignalSearchStatus,
    SignalSearchTask,
    SignalSourceRef,
)
from power_web_os.application.radar.signal_monitoring.payloads import (
    ParsedSignalPayload,
    SignalPayloadParseFailure,
)
from power_web_os.application.radar_model_profiles import RadarModelProfile


def observation_from_payload(
    task: SignalSearchTask,
    parsed: ParsedSignalPayload,
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
        return diagnostic_observation(task, "evidence_linking_failed", "Observed signal did not include evidence refs.")
    missing_refs = [ref for ref in evidence_refs if ref not in source_refs]
    if missing_refs:
        return diagnostic_observation(task, "evidence_linking_failed", f"Evidence refs did not resolve: {', '.join(missing_refs)}")
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


def schema_failed(task: SignalSearchTask, reason: str, failure: SignalPayloadParseFailure) -> SignalObservation:
    return diagnostic_observation(task, "schema_recovery_needed", f"{reason}: {failure.message}", path=failure.path)


def diagnostic_observation(
    task: SignalSearchTask,
    status: SignalSearchStatus,
    message: str,
    *,
    path: str = "",
) -> SignalObservation:
    issue = diagnostic(
        status,
        message,
        task_id=task.task_id,
        candidate_id=task.candidate_id,
        signal_code=task.signal_code,
        path=path,
    )
    return SignalObservation(
        task_id=task.task_id,
        candidate_id=task.candidate_id,
        signal_code=task.signal_code,
        observation_status="unclear",
        search_status=status,
        summary=message,
        diagnostics=[issue],
    )


def not_searched(task: SignalSearchTask, status: SignalSearchStatus, message: str) -> SignalObservation:
    return diagnostic_observation(task, status, message)


def diagnostic(
    code: str,
    message: str,
    *,
    task_id: str = "",
    candidate_id: str = "",
    signal_code: str = "",
    path: str = "",
) -> SignalMonitoringDiagnostic:
    return SignalMonitoringDiagnostic(
        code=code,
        message=message,
        task_id=task_id,
        candidate_id=candidate_id,
        signal_code=signal_code,
        path=path,
    )


def outcome(
    monitoring_input: SignalMonitoringInput,
    tasks: list[SignalSearchTask],
    observations: list[SignalObservation],
    diagnostics: list[SignalMonitoringDiagnostic],
    attempts: list[SignalProviderAttemptRecord],
    counters: dict[str, int],
    source_strategy_result: SignalMonitoringSourceStrategyResult,
    model_profile: RadarModelProfile,
) -> SignalMonitoringOutcome:
    return SignalMonitoringOutcome(
        run_id=monitoring_input.run_id,
        radar_id=monitoring_input.radar_id,
        model_profile_id=model_profile.profile_id,
        model_profile_summary=model_profile.to_summary(),
        tasks=tasks,
        observations=observations,
        diagnostics=diagnostics,
        source_strategy_decisions=source_strategy_result.decisions,
        source_strategy_diagnostics=source_strategy_result.diagnostics,
        provider_attempts=attempts,
        budget_counters=counters,
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
