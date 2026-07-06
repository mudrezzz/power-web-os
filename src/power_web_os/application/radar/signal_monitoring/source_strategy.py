"""Source strategy for the standalone Radar signal-monitoring harness.

The strategy is an application-layer selector. It does not call providers,
does not inspect persistence, and does not know runtime adapters. Its only
job is to decide which signal-evidence source lanes are executable before the
recorded executor builds provider tasks.
"""

from __future__ import annotations

from collections.abc import Iterable

from power_web_os.application.radar.shared.source_cards import RadarPlannerSourceCard
from power_web_os.application.radar.signal_monitoring.contracts import (
    SignalMonitoringDiagnostic,
    SignalMonitoringInput,
    SignalMonitoringSourceDecision,
    SignalMonitoringSourceHint,
    SignalMonitoringSourceLane,
    SignalMonitoringSourcePolicy,
    SignalMonitoringSourceStrategyResult,
    SignalSourceRef,
)


class SignalMonitoringSourceStrategy:
    """Select signal source lanes using source policy and compiled capabilities."""

    def select_sources(self, monitoring_input: SignalMonitoringInput) -> SignalMonitoringSourceStrategyResult:
        policy = monitoring_input.source_policy
        cards = {card.source_id: card for card in monitoring_input.source_cards}
        decisions: list[SignalMonitoringSourceDecision] = []
        diagnostics: list[SignalMonitoringDiagnostic] = []

        decisions.extend(_required_source_diagnostics(policy=policy, cards=cards))
        selected_source_ids: set[str] = set()
        selected_refs: set[str] = set()

        if policy.reuse_known_sources:
            for source in _candidate_known_sources(monitoring_input):
                decision = _known_source_decision(
                    source=source,
                    card=cards.get(source.source_id),
                    policy=policy,
                    selected_refs=selected_refs,
                )
                decisions.append(decision)
                if decision.status == "selected":
                    selected_refs.update(decision.source_refs)
                    if decision.source_id:
                        selected_source_ids.add(decision.source_id)
        else:
            decisions.append(_decision(
                lane="known_source",
                status="skipped",
                reason="Known-source reuse is disabled by signal source policy.",
            ))

        for source_id in _ordered_unique(policy.official_source_ids):
            decision = _card_source_decision(
                lane="official_company",
                source_id=source_id,
                card=cards.get(source_id),
                policy=policy,
                selected_source_ids=selected_source_ids,
            )
            decisions.append(decision)
            if decision.status == "selected":
                selected_source_ids.add(source_id)

        explicit_signal_sources = _ordered_unique([
            *policy.required_source_ids,
            *policy.preferred_source_ids,
            *policy.fallback_source_ids,
        ])
        for source_id in explicit_signal_sources:
            if source_id in set(policy.official_source_ids):
                continue
            decision = _card_source_decision(
                lane="signal_specific",
                source_id=source_id,
                card=cards.get(source_id),
                policy=policy,
                selected_source_ids=selected_source_ids,
            )
            decisions.append(decision)
            if decision.status == "selected":
                selected_source_ids.add(source_id)

        for hint in policy.signal_source_hints:
            decision = _hint_source_decision(
                hint=hint,
                card=cards.get(hint.source_id),
                policy=policy,
                selected_source_ids=selected_source_ids,
            )
            decisions.append(decision)
            if decision.status == "selected":
                selected_source_ids.add(hint.source_id)

        if policy.allow_open_web:
            for card in _open_web_cards(cards.values(), policy=policy):
                if card.source_id in selected_source_ids:
                    continue
                decisions.append(_selected_card_decision(
                    lane="open_web",
                    card=card,
                    reason="Open web signal search is allowed by policy and connector capability.",
                ))
                selected_source_ids.add(card.source_id)
        else:
            decisions.append(_decision(
                lane="open_web",
                status="skipped",
                reason="Open web signal search is disabled by signal source policy.",
            ))

        selected = [decision.decision_id for decision in decisions if decision.status == "selected"]
        for decision in decisions:
            if decision.diagnostic_severity in {"warning", "blocking"}:
                diagnostics.append(SignalMonitoringDiagnostic(
                    code=decision.reason,
                    message=_diagnostic_message(decision),
                    details={
                        "decision_id": decision.decision_id,
                        "lane": decision.lane,
                        "source_id": decision.source_id,
                        "source_ref": decision.source_ref,
                    },
                ))
        if not selected:
            diagnostics.append(SignalMonitoringDiagnostic(
                code="no_executable_signal_source_lane",
                message="No executable signal source lane was selected.",
            ))

        return SignalMonitoringSourceStrategyResult(
            decisions=decisions,
            diagnostics=diagnostics,
            selected_decision_ids=selected,
        )


def _required_source_diagnostics(
    *,
    policy: SignalMonitoringSourcePolicy,
    cards: dict[str, RadarPlannerSourceCard],
) -> list[SignalMonitoringSourceDecision]:
    decisions: list[SignalMonitoringSourceDecision] = []
    for source_id in _ordered_unique(policy.required_source_ids):
        card = cards.get(source_id)
        if card is None:
            decisions.append(_decision(
                lane="signal_specific",
                status="rejected",
                source_id=source_id,
                reason="required_signal_source_missing_capability_card",
                required=True,
                severity="blocking",
            ))
        elif not card.supports_signal_evidence:
            decisions.append(_decision(
                lane="signal_specific",
                status="rejected",
                source_id=source_id,
                connector_profile_id=card.connector_profile_id,
                reason="required_signal_source_not_signal_capable",
                supports_signal_evidence=False,
                required=True,
                severity="blocking",
            ))
    return decisions


def _candidate_known_sources(monitoring_input: SignalMonitoringInput) -> list[SignalSourceRef]:
    candidate_ids = {candidate.candidate_id for candidate in monitoring_input.candidates}
    candidate_source_refs = {
        source_ref
        for candidate in monitoring_input.candidates
        for source_ref in candidate.source_refs
        if source_ref
    }
    useful_states = {"used", "retrieved", "analyzed", "verified", "linked", "unknown"}
    result: list[SignalSourceRef] = []
    seen: set[str] = set()
    for source in monitoring_input.known_sources:
        if source.lifecycle_state not in useful_states:
            continue
        if source.source_ref not in candidate_source_refs and source.candidate_id not in candidate_ids:
            continue
        if source.source_ref in seen:
            continue
        seen.add(source.source_ref)
        result.append(source)
    return result


def _known_source_decision(
    *,
    source: SignalSourceRef,
    card: RadarPlannerSourceCard | None,
    policy: SignalMonitoringSourcePolicy,
    selected_refs: set[str],
) -> SignalMonitoringSourceDecision:
    if source.source_ref in selected_refs:
        return _decision(
            lane="known_source",
            status="skipped",
            source_id=source.source_id,
            source_ref=source.source_ref,
            source_refs=[source.source_ref],
            reason="known_source_already_selected",
        )
    if source.source_id and not _source_allowed(source.source_id, policy):
        return _decision(
            lane="known_source",
            status="rejected",
            source_id=source.source_id,
            source_ref=source.source_ref,
            source_refs=[source.source_ref],
            reason="known_source_policy_limited",
            severity="warning",
        )
    if card is not None and not card.supports_signal_evidence:
        return _decision(
            lane="known_source",
            status="rejected",
            source_id=source.source_id,
            source_ref=source.source_ref,
            source_refs=[source.source_ref],
            connector_profile_id=card.connector_profile_id,
            supports_signal_evidence=False,
            reason="known_source_not_signal_capable",
            severity="warning",
        )
    return _decision(
        lane="known_source",
        status="selected",
        source_id=source.source_id,
        source_ref=source.source_ref,
        source_refs=[source.source_ref],
        connector_profile_id=card.connector_profile_id if card else "",
        supports_signal_evidence=card.supports_signal_evidence if card else True,
        reason="Known candidate-discovery source is reusable for signal search.",
    )


def _card_source_decision(
    *,
    lane: SignalMonitoringSourceLane,
    source_id: str,
    card: RadarPlannerSourceCard | None,
    policy: SignalMonitoringSourcePolicy,
    selected_source_ids: set[str],
) -> SignalMonitoringSourceDecision:
    if source_id in selected_source_ids:
        return _decision(lane=lane, status="skipped", source_id=source_id, reason="source_already_selected")
    if not _source_allowed(source_id, policy):
        return _decision(lane=lane, status="rejected", source_id=source_id, reason="source_policy_limited", severity="warning")
    if card is None:
        return _decision(lane=lane, status="rejected", source_id=source_id, reason="source_capability_missing", severity="warning")
    if not card.supports_signal_evidence:
        return _decision(
            lane=lane,
            status="rejected",
            source_id=source_id,
            connector_profile_id=card.connector_profile_id,
            supports_signal_evidence=False,
            reason="source_not_signal_capable",
            severity="warning",
        )
    return _selected_card_decision(
        lane=lane,
        card=card,
        reason="Source selected for signal evidence by source policy and capability.",
    )


def _hint_source_decision(
    *,
    hint: SignalMonitoringSourceHint,
    card: RadarPlannerSourceCard | None,
    policy: SignalMonitoringSourcePolicy,
    selected_source_ids: set[str],
) -> SignalMonitoringSourceDecision:
    decision = _card_source_decision(
        lane="signal_specific",
        source_id=hint.source_id,
        card=card,
        policy=policy,
        selected_source_ids=selected_source_ids,
    )
    if decision.status == "selected":
        return decision.model_copy(update={"reason": f"Signal-specific source hint selected: {hint.label or hint.source_id}."})
    return decision


def _open_web_cards(
    cards: Iterable[RadarPlannerSourceCard],
    *,
    policy: SignalMonitoringSourcePolicy,
) -> list[RadarPlannerSourceCard]:
    ordered_ids = _ordered_unique([
        *policy.preferred_source_ids,
        *policy.fallback_source_ids,
        *policy.allowed_source_ids,
    ])
    card_by_id = {card.source_id: card for card in cards}
    candidates = [card_by_id[source_id] for source_id in ordered_ids if source_id in card_by_id]
    candidates.extend(card for card in cards if card.source_id not in {item.source_id for item in candidates})
    return [
        card
        for card in candidates
        if _source_allowed(card.source_id, policy)
        and card.supports_signal_evidence
        and (card.supports_broad_discovery or card.source_type in {"web", "search", "open_web"})
    ]


def _selected_card_decision(
    *,
    lane: SignalMonitoringSourceLane,
    card: RadarPlannerSourceCard,
    reason: str,
) -> SignalMonitoringSourceDecision:
    return _decision(
        lane=lane,
        status="selected",
        source_id=card.source_id,
        connector_profile_id=card.connector_profile_id,
        supports_signal_evidence=card.supports_signal_evidence,
        reason=reason,
    )


def _source_allowed(source_id: str, policy: SignalMonitoringSourcePolicy) -> bool:
    return not policy.allowed_source_ids or source_id in set(policy.allowed_source_ids)


def _decision(
    *,
    lane: SignalMonitoringSourceLane,
    status: str,
    reason: str,
    source_id: str = "",
    source_ref: str = "",
    source_refs: list[str] | None = None,
    connector_profile_id: str = "",
    supports_signal_evidence: bool = False,
    required: bool = False,
    severity: str = "info",
) -> SignalMonitoringSourceDecision:
    key = source_ref or source_id or "none"
    return SignalMonitoringSourceDecision(
        decision_id=f"{lane}:{status}:{key}:{reason}",
        lane=lane,
        status=status,  # type: ignore[arg-type]
        reason=reason,
        source_id=source_id,
        source_ref=source_ref,
        source_refs=source_refs or [],
        connector_profile_id=connector_profile_id,
        supports_signal_evidence=supports_signal_evidence,
        required=required,
        diagnostic_severity=severity,  # type: ignore[arg-type]
    )


def _diagnostic_message(decision: SignalMonitoringSourceDecision) -> str:
    label = decision.source_id or decision.source_ref or decision.lane
    return f"Signal source {label} was {decision.status}: {decision.reason}."


def _ordered_unique(items: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        value = str(item).strip()
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
