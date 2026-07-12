"""Provider-neutral signal evidence validation."""

from __future__ import annotations

from urllib.parse import urlparse

from power_web_os.application.radar.signal_monitoring.contracts import (
    SignalEvidence,
    SignalEvidenceValidationRecord,
    SignalObservation,
    SignalSearchTask,
    SignalSourceRef,
)
from power_web_os.application.radar.signal_monitoring.payloads import ParsedSignalPayload
from power_web_os.application.radar.signal_monitoring.projection import (
    observation_from_payload,
)
from power_web_os.application.radar.signal_monitoring.source_binding import apply_capability
from power_web_os.application.radar.signal_monitoring.temporal import SignalTemporalEvidenceService
from power_web_os.application.radar.signal_monitoring.text_matching import text_matches_entity


class SignalEvidenceValidationService:
    """Validate entity, criterion, date, source linkage, and lane constraints."""

    def __init__(self, temporal_service: SignalTemporalEvidenceService | None = None) -> None:
        self._temporal = temporal_service or SignalTemporalEvidenceService()

    def validate(
        self,
        *,
        task: SignalSearchTask,
        parsed: ParsedSignalPayload,
        previous_fingerprints: set[str],
        previous_source_keys: set[str] | None = None,
        source_refs_to_enrich: set[str] | None = None,
    ) -> tuple[SignalObservation, SignalEvidenceValidationRecord]:
        parsed = ParsedSignalPayload(
            sources=self._enriched_sources(parsed.sources, source_refs_to_enrich),
            observations=parsed.observations,
            repaired=parsed.repaired,
        )
        observation = observation_from_payload(
            task,
            parsed,
            previous_fingerprints,
            previous_source_keys or set(),
        )
        if observation.observation_status != "observed":
            return observation, self._record(task, True, "no_positive_evidence_to_validate", observation.source_refs)
        sources = [apply_capability(source) for source in observation.sources]
        source_by_ref = {source.source_ref: source for source in sources}
        evidence = [
            self._temporal.classify(
                item,
                source_by_ref.get(item.source_ref, SignalSourceRef(source_ref=item.source_ref)),
                window_start=task.window_start,
                window_end=task.window_end,
            )
            for item in observation.evidence
        ]
        observation = observation.model_copy(update={"sources": sources, "evidence": evidence})

        if task.source_lane == "known_source" and not any(
            _source_matches_candidate(task, source)
            and _matches_requested_known_url(task, source)
            for source in sources
        ):
            return self._rejected(task, observation, "known_source_evidence_url_mismatch")
        if not any(_source_matches_candidate(task, source) for source in sources):
            return self._rejected(task, observation, "observed_evidence_candidate_mismatch")
        if task.source_lane == "official_company" and task.domain_restrictions:
            allowed = set(task.domain_restrictions)
            returned = {
                (urlparse(item.url).hostname or "").removeprefix("www.").lower()
                for item in sources
                if item.url
            }
            if not returned or not all(any(host == domain or host.endswith(f".{domain}") for domain in allowed) for host in returned):
                return self._rejected(task, observation, "official_evidence_domain_mismatch")

        non_signal_sources = [
            source for source in sources if source.capability in {"identity_only", "registry"}
        ]
        if non_signal_sources and len(non_signal_sources) == len(sources):
            return self._rejected(task, observation, "source_capability_not_fresh_signal_capable")

        source_keys = {_source_key(task, source) for source in sources if _source_key(task, source)}
        duplicate = bool(source_keys.intersection(previous_source_keys or set()))
        confirmed = [item for item in evidence if item.temporal_status == "confirmed_in_window"]
        conflicts = [item for item in evidence if item.temporal_status == "review_needed_date_conflict"]
        unknown = [item for item in evidence if item.temporal_status == "review_needed_date_unknown"]
        out_of_window = [item for item in evidence if item.temporal_status == "rejected_out_of_window"]
        if confirmed:
            confirmed_refs = [item.source_ref for item in confirmed]
            retained_review_refs = {
                item.source_ref
                for item in [*conflicts, *unknown, *out_of_window]
            }
            confirmed_sources = [source for source in sources if source.source_ref in set(confirmed_refs)]
            retained_review_sources = [
                source
                for source in sources
                if source.source_ref in retained_review_refs and source.source_ref not in set(confirmed_refs)
            ]
            status = "duplicate_existing_signal" if duplicate else "searched"
            return observation.model_copy(update={
                "search_status": status,
                "score": max(1, observation.score),
                "source_refs": confirmed_refs,
                "sources": [*confirmed_sources, *retained_review_sources],
                "evidence": [*confirmed, *conflicts, *unknown, *out_of_window],
            }), self._record(
                task,
                True,
                "duplicate_existing_signal" if duplicate else "evidence_validated",
                confirmed_refs,
                temporal_status="confirmed_in_window",
            )
        if conflicts:
            return self._temporal_review(task, observation, "review_needed_date_conflict", conflicts, duplicate)
        if unknown:
            return self._temporal_review(task, observation, "review_needed_date_unknown", unknown, duplicate)
        if out_of_window:
            return self._temporal_review(task, observation, "rejected_out_of_window", out_of_window, duplicate)
        return self._temporal_review(task, observation, "review_needed_date_unknown", evidence, duplicate)

    def _rejected(
        self,
        task: SignalSearchTask,
        observation: SignalObservation,
        reason: str,
    ) -> tuple[SignalObservation, SignalEvidenceValidationRecord]:
        return observation.model_copy(update={
            "observation_status": "unclear",
            "search_status": "review_needed",
            "summary": reason,
            "score": 0,
        }), self._record(task, False, reason, observation.source_refs)

    def _temporal_review(
        self,
        task: SignalSearchTask,
        observation: SignalObservation,
        search_status: str,
        evidence: list[SignalEvidence],
        duplicate: bool,
    ) -> tuple[SignalObservation, SignalEvidenceValidationRecord]:
        status = "duplicate_existing_review" if duplicate and search_status in {
            "review_needed_date_unknown",
            "review_needed_date_conflict",
        } else search_status
        projected = observation.model_copy(update={
            "observation_status": "unclear",
            "search_status": status,
            "summary": _temporal_summary(status),
            "score": 0,
            "evidence": evidence or observation.evidence,
        })
        temporal_status = evidence[0].temporal_status if evidence else "review_needed_date_unknown"
        return projected, self._record(
            task,
            False,
            status,
            observation.source_refs,
            temporal_status=temporal_status,
        )

    @staticmethod
    def _record(
        task: SignalSearchTask,
        accepted: bool,
        reason: str,
        source_refs: list[str],
        *,
        temporal_status: str = "not_applicable",
        details: dict[str, object] | None = None,
    ) -> SignalEvidenceValidationRecord:
        return SignalEvidenceValidationRecord(
            task_id=task.task_id,
            candidate_id=task.candidate_id,
            signal_code=task.signal_code,
            accepted=accepted,
            reason=reason,
            source_refs=list(source_refs),
            temporal_status=temporal_status,  # type: ignore[arg-type]
            details=details or {},
        )

    def _enriched_sources(
        self,
        sources: list[SignalSourceRef],
        source_refs_to_enrich: set[str] | None,
    ) -> list[SignalSourceRef]:
        if source_refs_to_enrich is None:
            return self._temporal.enrich_sources(sources)
        targets = {str(item) for item in source_refs_to_enrich if str(item)}
        target_sources = [source for source in sources if source.source_ref in targets]
        enriched_by_ref = {source.source_ref: source for source in self._temporal.enrich_sources(target_sources)}
        return [enriched_by_ref.get(source.source_ref, apply_capability(source)) for source in sources]


def _source_matches_candidate(task: SignalSearchTask, source: object) -> bool:
    source_ref = str(getattr(source, "source_ref", "") or "")
    url = str(getattr(source, "url", "") or "")
    return text_matches_entity(
        values=[task.candidate_id, task.candidate_name, *task.candidate_aliases],
        text=" ".join([
            source_ref,
            str(getattr(source, "title", "") or ""),
            str(getattr(source, "snippet", "") or ""),
            url,
        ]),
    )


def _matches_requested_known_url(task: SignalSearchTask, source: object) -> bool:
    source_url = _canonical_url(str(getattr(source, "url", "") or ""))
    requested = [_canonical_url(item.url) for item in task.source_contracts if item.url]
    return bool(source_url and any(source_url == value or source_url.startswith(f"{value}/") for value in requested))


def _canonical_url(value: str) -> str:
    parsed = urlparse(value.strip())
    host = (parsed.hostname or "").removeprefix("www.").lower()
    path = parsed.path.rstrip("/").lower()
    return f"{host}{path}" if host else ""


def _source_key(task: SignalSearchTask, source: SignalSourceRef) -> str:
    value = (source.url or source.source_ref).strip().lower().rstrip("/")
    return f"{task.candidate_id}|{task.signal_code}|{value}" if value else ""


def _temporal_summary(status: str) -> str:
    return {
        "review_needed_date_unknown": "Relevant signal evidence was found, but publication or event date is unknown.",
        "review_needed_date_conflict": "Relevant signal evidence has conflicting publication or event dates.",
        "rejected_out_of_window": "Relevant signal evidence is outside the monitoring window.",
        "duplicate_existing_review": "Relevant review-needed evidence was already retained by a previous run.",
    }.get(status, status)
