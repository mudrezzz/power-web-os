"""Observation and outcome projection for signal monitoring."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from power_web_os.application.radar.signal_monitoring.contracts import (
    SignalEvidence,
    SignalMonitoringDiagnostic,
    SignalMonitoringInput,
    SignalMonitoringOutcome,
    SignalMonitoringCheckpointDecision,
    SignalMonitoringPlan,
    SignalMonitoringPlanAcceptance,
    SignalMonitoringSourceStrategyResult,
    SignalMonitoringWatermark,
    SignalEvidenceValidationRecord,
    SignalObservation,
    SignalProviderAttemptRecord,
    SignalSearchStatus,
    SignalSearchTask,
    SignalSearchExecutionReceipt,
    SignalSourceBindingDecision,
    SignalSourceLaneLedgerEntry,
    SignalSourceLifecycleRecord,
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
    previous_source_keys: set[str] | None = None,
) -> SignalObservation:
    parsed_sources, evidence_refs = _normalize_evidence_refs(parsed.sources, parsed.observations)
    source_refs = {source.source_ref: source for source in parsed_sources}
    raw = next(
        (
            item
            for item in parsed.observations
            if str(item.get("candidate_id")) == task.candidate_id and str(item.get("signal_code")) == task.signal_code
        ),
        None,
    )
    if raw is None:
        searched_sources = list(source_refs.values())
        return SignalObservation(
            task_id=task.task_id,
            candidate_id=task.candidate_id,
            signal_code=task.signal_code,
            observation_status="not_observed",
            search_status="searched",
            summary="Signal was searched and not observed.",
            source_refs=[item.source_ref for item in searched_sources],
            sources=searched_sources,
        )
    status = str(raw.get("status") or raw.get("observation_status") or "unclear")
    evidence_refs = evidence_refs.get(id(raw), [])
    if status == "not_observed":
        searched_sources = list(source_refs.values())
        return SignalObservation(
            task_id=task.task_id,
            candidate_id=task.candidate_id,
            signal_code=task.signal_code,
            observation_status="not_observed",
            search_status="searched",
            summary=str(raw.get("summary") or "Signal was searched and not observed."),
            source_refs=[item.source_ref for item in searched_sources],
            sources=searched_sources,
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
            event_at=str(raw.get("event_at") or raw.get("event_date") or ""),
            event_end_at=str(raw.get("event_end_at") or raw.get("event_end_date") or ""),
            published_at=str(raw.get("published_at") or ""),
            date_basis="provider_extracted" if raw.get("event_at") or raw.get("event_date") or raw.get("published_at") else "none",
            date_confidence=_confidence(raw.get("date_confidence") or raw.get("confidence")),
            date_evidence=str(raw.get("date_evidence") or raw.get("event_at") or raw.get("event_date") or raw.get("published_at") or ""),
            confidence=_confidence(raw.get("confidence")),
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
            sources=[source_refs[ref] for ref in evidence_refs],
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
        sources=[source_refs[ref] for ref in evidence_refs],
        fingerprint=fingerprint,
    )


def _normalize_evidence_refs(
    sources: list[SignalSourceRef],
    observations: list[dict[str, Any]],
) -> tuple[list[SignalSourceRef], dict[int, list[str]]]:
    by_ref = {source.source_ref: source for source in sources}
    normalized_by_observation: dict[int, list[str]] = {}
    for raw in observations:
        refs: list[str] = []
        for item in raw.get("evidence_refs", []):
            ref, source = _evidence_ref_and_source(item, by_ref)
            if not ref:
                continue
            refs.append(ref)
            if source is not None and ref not in by_ref:
                by_ref[ref] = source
        normalized_by_observation[id(raw)] = refs
    return list(by_ref.values()), normalized_by_observation


def _evidence_ref_and_source(
    value: object,
    existing_sources: dict[str, SignalSourceRef],
) -> tuple[str, SignalSourceRef | None]:
    if isinstance(value, dict):
        raw_ref = str(
            value.get("source_ref")
            or value.get("evidence_ref")
            or value.get("ref")
            or value.get("id")
            or ""
        ).strip()
        url = str(value.get("url") or "").strip()
        ref = raw_ref or url
        if url and raw_ref:
            existing = existing_sources.get(raw_ref)
            if existing is not None and _canonical_url(existing.url) != _canonical_url(url):
                ref = f"{raw_ref}::{_url_slug(url)}"
            elif raw_ref.startswith("configured:"):
                ref = f"{raw_ref}::{_url_slug(url)}"
        if not ref:
            return "", None
        source = SignalSourceRef(
            source_ref=ref,
            title=str(value.get("title") or value.get("label") or ref),
            url=url,
            snippet=str(value.get("snippet") or value.get("excerpt") or ""),
            source_id=str(value.get("source_id") or ""),
            retrieved_at=str(value.get("retrieved_at") or ""),
            published_at=str(value.get("published_at") or ""),
            date_basis=str(value.get("date_basis") or "none"),  # type: ignore[arg-type]
            date_confidence=str(value.get("date_confidence") or "weak"),  # type: ignore[arg-type]
            date_evidence=str(value.get("date_evidence") or ""),
        )
        return ref, source
    ref = str(value or "").strip()
    if not ref:
        return "", None
    if ref.startswith(("http://", "https://")):
        return ref, SignalSourceRef(source_ref=ref, title=ref, url=ref)
    return ref, None


def _url_slug(value: str) -> str:
    parsed = urlparse(value)
    basis = parsed.path.strip("/") or parsed.netloc or value
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", basis).strip("-").lower()
    return slug[:120] or "url"


def _canonical_url(value: str) -> str:
    parsed = urlparse(value.strip())
    host = (parsed.hostname or "").removeprefix("www.").lower()
    path = parsed.path.rstrip("/").lower()
    return f"{host}{path}" if host else value.strip().lower().rstrip("/")


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
    budget_settings: dict[str, Any],
    budget_exhaustion_events: list[dict[str, Any]],
    source_strategy_result: SignalMonitoringSourceStrategyResult,
    model_profile: RadarModelProfile,
    *,
    search_plan: SignalMonitoringPlan | None = None,
    plan_acceptance: SignalMonitoringPlanAcceptance | None = None,
    task_observations: list[SignalObservation] | None = None,
    source_lane_ledger: list[SignalSourceLaneLedgerEntry] | None = None,
    search_execution_receipts: list[SignalSearchExecutionReceipt] | None = None,
    source_lifecycle: list[SignalSourceLifecycleRecord] | None = None,
    watermarks_before: list[SignalMonitoringWatermark] | None = None,
    watermarks_after: list[SignalMonitoringWatermark] | None = None,
    evidence_validation_records: list[SignalEvidenceValidationRecord] | None = None,
    checkpoint_decisions: list[SignalMonitoringCheckpointDecision] | None = None,
    source_binding_decisions: list[SignalSourceBindingDecision] | None = None,
) -> SignalMonitoringOutcome:
    return SignalMonitoringOutcome(
        run_id=monitoring_input.run_id,
        radar_id=monitoring_input.radar_id,
        source_candidate_run_id=monitoring_input.source_candidate_run_id,
        candidate_scope_mode=monitoring_input.candidate_scope_mode,
        completion_state=_completion_state(observations),
        model_profile_id=model_profile.profile_id,
        model_profile_summary=model_profile.to_summary(),
        tasks=tasks,
        observations=observations,
        sources=_dedupe_sources(observations),
        diagnostics=diagnostics,
        source_strategy_decisions=source_strategy_result.decisions,
        source_strategy_diagnostics=source_strategy_result.diagnostics,
        provider_attempts=attempts,
        search_plan=search_plan,
        plan_acceptance=plan_acceptance,
        task_observations=task_observations or [],
        source_lane_ledger=source_lane_ledger or [],
        search_execution_receipts=search_execution_receipts or [],
        source_lifecycle=source_lifecycle or [],
        watermarks_before=watermarks_before or [],
        watermarks_after=watermarks_after or [],
        evidence_validation_records=evidence_validation_records or [],
        checkpoint_decisions=checkpoint_decisions or [],
        source_binding_decisions=source_binding_decisions or list(monitoring_input.source_binding_decisions),
        budget_counters=counters,
        budget_settings=budget_settings,
        budget_exhaustion_events=budget_exhaustion_events,
    )


def _completion_state(observations: list[SignalObservation]) -> str:
    limited = {
        "not_searched_budget_limited",
        "not_searched_policy_limited",
        "not_searched_missing_candidate_scope",
        "schema_recovery_needed",
        "evidence_linking_failed",
        "review_needed",
    }
    return "completed_with_limits" if any(item.search_status in limited for item in observations) else "completed"


def _dedupe_sources(observations: list[SignalObservation]) -> list[SignalSourceRef]:
    by_ref: dict[str, SignalSourceRef] = {}
    for observation in observations:
        for source in observation.sources:
            by_ref.setdefault(source.source_ref, source)
    return list(by_ref.values())


def _fingerprint(task: SignalSearchTask, raw: dict[str, Any], sources: list[SignalSourceRef]) -> str:
    source_key = "|".join(sorted((source.url or source.source_ref).strip().lower().rstrip("/") for source in sources))
    return "|".join([
        task.candidate_id,
        task.signal_code,
        source_key,
        str(raw.get("event_at") or raw.get("event_date") or raw.get("published_at") or "").strip().lower(),
        str(raw.get("summary") or raw.get("fact") or "").strip().lower(),
    ])


def _confidence(value: object) -> str:
    normalized = str(value or "medium").strip().lower()
    return {
        "high": "strong",
        "strong": "strong",
        "medium": "medium",
        "moderate": "medium",
        "low": "weak",
        "weak": "weak",
    }.get(normalized, "medium")
