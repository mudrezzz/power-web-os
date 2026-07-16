"""Deterministic reconciliation of retrieved evidence across signal criteria."""

from __future__ import annotations

import re

from power_web_os.application.radar.signal_monitoring.contracts import (
    SignalCrossCriterionValidationRecord,
    SignalEvidence,
    SignalMonitoringSignalRule,
    SignalObservation,
    SignalSearchTask,
    SignalSourceRef,
)
from power_web_os.application.radar.signal_monitoring.source_binding import apply_capability
from power_web_os.application.radar.signal_monitoring.temporal import SignalTemporalEvidenceService
from power_web_os.application.radar.signal_monitoring.text_matching import text_matches_entity
from power_web_os.application.radar.signal_monitoring.url_identity import canonical_signal_url, signal_source_key


class SignalCrossCriterionEvidenceReconciliationService:
    """Revalidate product-safe evidence for other criteria of the same candidate."""

    def __init__(self, temporal_service: SignalTemporalEvidenceService | None = None) -> None:
        self._temporal = temporal_service or SignalTemporalEvidenceService()

    def reconcile(
        self,
        *,
        tasks: list[SignalSearchTask],
        rules: list[SignalMonitoringSignalRule],
        task_observations: list[SignalObservation],
        previous_source_keys: set[str],
    ) -> tuple[list[SignalObservation], list[SignalCrossCriterionValidationRecord]]:
        rule_by_code = {rule.signal_code: rule for rule in rules}
        target_tasks = _target_tasks(tasks)
        existing = _existing_evidence_keys(task_observations)
        reconciled: list[SignalObservation] = []
        records: list[SignalCrossCriterionValidationRecord] = []

        for origin in list(task_observations):
            if not origin.evidence or not origin.sources:
                continue
            source_by_ref = {source.source_ref: apply_capability(source) for source in origin.sources}
            for target_code, rule in rule_by_code.items():
                if target_code == origin.signal_code:
                    continue
                target = target_tasks.get((origin.candidate_id, target_code))
                if target is None:
                    continue
                for evidence in origin.evidence:
                    source = source_by_ref.get(evidence.source_ref)
                    record, observation = self._validate_target(
                        origin=origin,
                        evidence=evidence,
                        source=source,
                        target=target,
                        rule=rule,
                        previous_source_keys=previous_source_keys,
                        existing=existing,
                    )
                    records.append(record)
                    if observation is not None:
                        reconciled.append(observation)
                        existing.add(_evidence_key(observation.candidate_id, observation.signal_code, source))
        return reconciled, records

    def _validate_target(
        self,
        *,
        origin: SignalObservation,
        evidence: SignalEvidence,
        source: SignalSourceRef | None,
        target: SignalSearchTask,
        rule: SignalMonitoringSignalRule,
        previous_source_keys: set[str],
        existing: set[tuple[str, str, str]],
    ) -> tuple[SignalCrossCriterionValidationRecord, SignalObservation | None]:
        base = {
            "candidate_id": origin.candidate_id,
            "source_ref": evidence.source_ref,
            "origin_task_id": origin.task_id,
            "origin_signal_code": origin.signal_code,
            "target_task_id": target.task_id,
            "target_signal_code": target.signal_code,
        }
        if source is None:
            return SignalCrossCriterionValidationRecord(**base, accepted=False, reason="source_ref_unresolved"), None
        if not _matches_candidate(target, source, evidence):
            return SignalCrossCriterionValidationRecord(**base, accepted=False, reason="target_candidate_mismatch"), None
        matched_terms = _matched_terms(rule.evidence_match_terms, source=source, evidence=evidence)
        if not matched_terms:
            return SignalCrossCriterionValidationRecord(**base, accepted=False, reason="target_criterion_not_supported"), None
        if source.capability in {"identity_only", "registry"}:
            return SignalCrossCriterionValidationRecord(
                **base,
                accepted=False,
                reason="source_capability_not_fresh_signal_capable",
                matched_terms=matched_terms,
            ), None
        key = _evidence_key(origin.candidate_id, target.signal_code, source)
        if key in existing:
            return SignalCrossCriterionValidationRecord(
                **base,
                accepted=False,
                reason="target_evidence_already_present",
                matched_terms=matched_terms,
            ), None

        classified = self._temporal.classify(
            evidence,
            source,
            window_start=target.window_start,
            window_end=target.window_end,
        )
        source_key = signal_source_key(
            candidate_id=origin.candidate_id,
            signal_code=target.signal_code,
            url_or_ref=source.url or source.source_ref,
        )
        duplicate = bool(source_key and source_key in previous_source_keys)
        if classified.temporal_status == "confirmed_in_window":
            search_status = "duplicate_existing_signal" if duplicate else "searched"
            observation_status = "unclear" if duplicate else "observed"
            score = 0 if duplicate else max(origin.score, 1)
            accepted = True
            reason = "cross_criterion_evidence_validated"
        elif classified.temporal_status in {"review_needed_date_unknown", "review_needed_date_conflict"}:
            search_status = "duplicate_existing_review" if duplicate else classified.temporal_status
            observation_status = "unclear"
            score = 0
            accepted = False
            reason = classified.temporal_status
        else:
            search_status = "rejected_out_of_window"
            observation_status = "unclear"
            score = 0
            accepted = False
            reason = "rejected_out_of_window"

        observation = SignalObservation(
            task_id=f"{origin.task_id}::reconcile::{target.signal_code}",
            candidate_id=origin.candidate_id,
            signal_code=target.signal_code,
            observation_status=observation_status,
            search_status=search_status,
            summary=f"Cross-criterion validation from {origin.signal_code}: {origin.summary}",
            score=score,
            evidence=[classified],
            source_refs=[source.source_ref],
            sources=[source],
            fingerprint="|".join([
                origin.candidate_id,
                target.signal_code,
                canonical_signal_url(source.url or source.source_ref),
                classified.event_at or classified.published_at,
            ]),
        )
        return SignalCrossCriterionValidationRecord(
            **base,
            accepted=accepted,
            reason=reason,
            temporal_status=classified.temporal_status,
            matched_terms=matched_terms,
        ), observation


def _target_tasks(tasks: list[SignalSearchTask]) -> dict[tuple[str, str], SignalSearchTask]:
    result: dict[tuple[str, str], SignalSearchTask] = {}
    for task in tasks:
        key = (task.candidate_id, task.signal_code)
        current = result.get(key)
        if current is None or (current.source_lane != "open_web" and task.source_lane == "open_web"):
            result[key] = task
    return result


def _existing_evidence_keys(observations: list[SignalObservation]) -> set[tuple[str, str, str]]:
    return {
        _evidence_key(observation.candidate_id, observation.signal_code, source)
        for observation in observations
        for source in observation.sources
        if any(item.source_ref == source.source_ref for item in observation.evidence)
    }


def _evidence_key(candidate_id: str, signal_code: str, source: SignalSourceRef | None) -> tuple[str, str, str]:
    identity = canonical_signal_url((source.url or source.source_ref) if source else "")
    return candidate_id, signal_code, identity


def _matches_candidate(task: SignalSearchTask, source: SignalSourceRef, evidence: SignalEvidence) -> bool:
    return text_matches_entity(
        values=[task.candidate_id, task.candidate_name, *task.candidate_aliases],
        text=" ".join([source.title, source.snippet, source.url, evidence.fact, evidence.excerpt]),
    )


def _matched_terms(terms: list[str], *, source: SignalSourceRef, evidence: SignalEvidence) -> list[str]:
    text = _normalize(" ".join([source.title, source.snippet, evidence.fact, evidence.excerpt]))
    result: list[str] = []
    for term in terms:
        normalized = _normalize(term)
        tokens = [token for token in normalized.split() if len(token) >= 3]
        if not tokens:
            continue
        if normalized in text or (len(tokens) >= 2 and all(token in text for token in tokens)):
            result.append(term)
        elif len(tokens) == 1 and len(tokens[0]) >= 5 and re.search(rf"\b{re.escape(tokens[0])}\b", text):
            result.append(term)
    return result


def _normalize(value: str) -> str:
    return " ".join(re.sub(r"[^\w]+", " ", value.casefold().replace("ё", "е")).split())
