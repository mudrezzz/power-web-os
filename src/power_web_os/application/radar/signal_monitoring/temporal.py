"""Publication/event-time resolution for Signal Monitoring evidence."""

from __future__ import annotations

from datetime import UTC, datetime
import re

from power_web_os.application.radar.signal_monitoring.contracts import (
    SignalEvidence,
    SignalSourceMetadataProvider,
    SignalSourceRef,
    SignalTemporalStatus,
)


class SignalTemporalEvidenceService:
    """Resolve safe source metadata and classify evidence against a task window."""

    def __init__(self, metadata_provider: SignalSourceMetadataProvider | None = None) -> None:
        self._metadata_provider = metadata_provider

    def enrich_sources(self, sources: list[SignalSourceRef]) -> list[SignalSourceRef]:
        enriched: list[SignalSourceRef] = []
        for source in sources:
            base = source.model_copy(update={
                "retrieved_at": source.retrieved_at or source.observed_at,
            })
            if self._metadata_provider is None or not source.url:
                enriched.append(_with_url_date(base))
                continue
            try:
                metadata = self._metadata_provider.resolve(base)
            except Exception:
                enriched.append(_with_url_date(base))
                continue
            enriched.append(_with_url_date(base.model_copy(update={
                "published_at": metadata.published_at or base.published_at,
                "date_basis": metadata.date_basis if metadata.published_at else base.date_basis,
                "date_confidence": metadata.date_confidence if metadata.published_at else base.date_confidence,
                "date_evidence": metadata.date_evidence or base.date_evidence,
                "date_conflict": metadata.conflicting or base.date_conflict,
            })))
        return enriched

    def classify(
        self,
        evidence: SignalEvidence,
        source: SignalSourceRef,
        *,
        window_start: str,
        window_end: str,
    ) -> SignalEvidence:
        evidence = _with_text_event_interval(evidence, source)
        if source.date_conflict:
            return evidence.model_copy(update={
                "published_at": source.published_at,
                "temporal_status": "review_needed_date_conflict",
                "date_basis": source.date_basis,
                "date_confidence": source.date_confidence,
                "date_evidence": source.date_evidence,
            })
        event = _parse(evidence.event_at)
        published = _parse(source.published_at or evidence.published_at)
        lower, upper = _parse(window_start), _parse(window_end)
        if lower is None or upper is None:
            return evidence.model_copy(update={"temporal_status": "review_needed_date_conflict"})
        if (
            event is not None
            and published is not None
            and published < lower
            and lower <= event <= upper
            and not _event_date_is_source_supported(evidence, source)
        ):
            event = None
        in_window = any(value is not None and lower <= value <= upper for value in (event, published))
        if in_window:
            status: SignalTemporalStatus = "confirmed_in_window"
        elif event is None and published is None:
            status = "review_needed_date_unknown"
        else:
            status = "rejected_out_of_window"
        basis = evidence.date_basis if event is not None else source.date_basis
        confidence = evidence.date_confidence if event is not None else source.date_confidence
        date_evidence = evidence.date_evidence if event is not None else source.date_evidence
        return evidence.model_copy(update={
            "published_at": source.published_at or evidence.published_at,
            "temporal_status": status,
            "date_basis": basis,
            "date_confidence": confidence,
            "date_evidence": date_evidence,
        })


def _with_url_date(source: SignalSourceRef) -> SignalSourceRef:
    if source.published_at or not source.url:
        return source
    match = re.search(r"/(20\d{2})/(0[1-9]|1[0-2])/(0[1-9]|[12]\d|3[01])(?:/|$)", source.url)
    if not match:
        return source
    value = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    return source.model_copy(update={
        "published_at": value,
        "date_basis": "url",
        "date_confidence": "medium",
        "date_evidence": value,
    })


def _with_text_event_interval(evidence: SignalEvidence, source: SignalSourceRef) -> SignalEvidence:
    if evidence.event_at:
        return evidence
    text = " ".join([source.title, source.snippet, evidence.fact, evidence.excerpt])
    patterns = (
        (r"(?:перв\w*|\bI\b|\bQ1\b)\s+квартал\w*\s+(20\d{2})", 1),
        (r"(?:втор\w*|\bII\b|\bQ2\b)\s+квартал\w*\s+(20\d{2})", 2),
        (r"(?:трет\w*|\bIII\b|\bQ3\b)\s+квартал\w*\s+(20\d{2})", 3),
        (r"(?:четверт\w*|\bIV\b|\bQ4\b)\s+квартал\w*\s+(20\d{2})", 4),
        (r"(?:first|\bQ1\b)\s+quarter(?:\s+of)?\s+(20\d{2})", 1),
        (r"(?:second|\bQ2\b)\s+quarter(?:\s+of)?\s+(20\d{2})", 2),
        (r"(?:third|\bQ3\b)\s+quarter(?:\s+of)?\s+(20\d{2})", 3),
        (r"(?:fourth|\bQ4\b)\s+quarter(?:\s+of)?\s+(20\d{2})", 4),
    )
    for pattern, quarter in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue
        year = int(match.group(1))
        start_month = (quarter - 1) * 3 + 1
        end_month = start_month + 2
        end_day = 31 if end_month in {3, 12} else 30
        return evidence.model_copy(update={
            "event_at": f"{year:04d}-{start_month:02d}-01",
            "event_end_at": f"{year:04d}-{end_month:02d}-{end_day:02d}",
            "date_basis": "snippet",
            "date_confidence": "medium",
            "date_evidence": match.group(0),
        })
    return evidence


def _event_date_is_source_supported(evidence: SignalEvidence, source: SignalSourceRef) -> bool:
    event_year = str(evidence.event_at or "")[:4]
    if not re.fullmatch(r"20\d{2}", event_year):
        return False
    date_evidence = str(evidence.date_evidence or "").strip()
    if event_year in date_evidence and date_evidence != str(evidence.event_at or "").strip():
        return True
    source_text = " ".join([
        str(evidence.excerpt or ""),
        str(source.title or ""),
        str(source.snippet or ""),
        str(source.date_evidence or ""),
    ]).lower()
    return event_year in source_text


def _parse(value: str) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    normalized = text[:10] if re.fullmatch(r"\d{4}-\d{2}-\d{2}.*", text) else text
    for candidate in (normalized, text):
        try:
            parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
            return parsed.replace(tzinfo=parsed.tzinfo or UTC).astimezone(UTC)
        except ValueError:
            continue
    return None
