"""Generic source capability and candidate ownership decisions."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from power_web_os.application.radar.signal_monitoring.contracts import (
    SignalMonitoringCandidate,
    SignalSourceBindingDecision,
    SignalSourceCapability,
    SignalSourceRef,
)
from power_web_os.application.radar.signal_monitoring.text_matching import compact, text_matches_entity


class SignalSourceBindingService:
    """Classify provenance without benchmark or company-specific rules."""

    def bind(
        self,
        *,
        candidate: SignalMonitoringCandidate,
        source: SignalSourceRef,
    ) -> SignalSourceBindingDecision:
        capability, capability_basis = classify_source_capability(source)
        if not source.url.strip():
            status, reason, basis, confidence = "no_url", "source_has_no_retrievable_url", "url", "strong"
        elif source.candidate_id:
            if compact(source.candidate_id) == compact(candidate.candidate_id):
                status, reason, basis, confidence = "matched_candidate", "source_candidate_id_matches", "candidate_id", "strong"
            else:
                status, reason, basis, confidence = "cross_entity", "source_candidate_id_mismatch", "candidate_id", "strong"
        elif _matches_candidate(candidate, source):
            status, reason, basis, confidence = "matched_candidate", "candidate_alias_matches_source", "title_snippet_url", "medium"
        else:
            status, reason, basis, confidence = "unknown_owner", "candidate_ownership_not_proven", "title_snippet_url", "weak"
        signal_capable = capability not in {"identity_only", "registry"}
        return SignalSourceBindingDecision(
            candidate_id=candidate.candidate_id,
            source_ref=source.source_ref,
            status=status,  # type: ignore[arg-type]
            capability=capability,
            reason=reason,
            basis=f"{basis};{capability_basis}",
            confidence=confidence,  # type: ignore[arg-type]
            scheduled_as_known_source=status == "matched_candidate" and signal_capable,
        )


def classify_source_capability(source: SignalSourceRef) -> tuple[SignalSourceCapability, str]:
    if not source.url.strip():
        return "registry", "missing_url"
    parsed = urlparse(source.url)
    tokens = {
        token.casefold()
        for token in re.split(r"[^\w]+", f"{parsed.path} {source.title} {source.source_id}")
        if token
    }
    suffix = parsed.path.rsplit(".", 1)[-1].casefold() if "." in parsed.path else ""
    if suffix in {"xls", "xlsx", "csv", "xml", "json"}:
        return "identity_only", "structured_registry_or_disclosure_file"
    if tokens.intersection({"press", "news", "новости", "пресс", "publication", "article"}):
        return "official_press", "news_or_press_path"
    if tokens.intersection({"feed", "rss", "events", "события"}):
        return "event_feed", "event_feed_path"
    if tokens.intersection({"project", "projects", "asset", "history", "история"}):
        return "project_or_asset_history", "project_or_history_path"
    if tokens.intersection({"about", "products", "contacts", "career", "geo", "wiki", "справка", "контакты"}):
        return "identity_only", "identity_or_reference_path"
    if parsed.scheme in {"http", "https"} and parsed.hostname:
        return "generic_web", "retrievable_web_url"
    return "unknown", "unclassified_source"


def apply_capability(source: SignalSourceRef) -> SignalSourceRef:
    capability, basis = classify_source_capability(source)
    return source.model_copy(update={"capability": capability, "capability_basis": basis})


def _matches_candidate(candidate: SignalMonitoringCandidate, source: SignalSourceRef) -> bool:
    return text_matches_entity(
        values=[candidate.candidate_id, candidate.display_name, candidate.legal_name, *candidate.aliases],
        text=" ".join([source.title, source.snippet, source.url]),
    )
