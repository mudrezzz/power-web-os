"""Planner-facing source cards and capability validation for live Radar."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from power_web_os.application.connector_profiles import (
    ConnectorProfileRegistry,
    default_connector_profile_registry,
)
from power_web_os.application.radar.shared.source_policy import source_usage_obligation

RadarPlannerSourceUseIntent = Literal[
    "broad_discovery",
    "identity_lookup",
    "enrichment",
    "coverage",
    "signal_evidence",
    "official_evidence",
]
RadarPlannerSourceInputShape = Literal[
    "broad_query",
    "concrete_company",
    "candidate_scope",
    "domain_or_url",
    "official_domain_query",
    "unknown",
]


class RadarPlannerSourceUse(BaseModel):
    source_id: str
    connector_profile_id: str = ""
    intended_use: RadarPlannerSourceUseIntent
    input_shape: RadarPlannerSourceInputShape = "unknown"
    expected_fact_kinds: list[str] = Field(default_factory=list)
    rationale: str = ""

    @field_validator("expected_fact_kinds", mode="before")
    @classmethod
    def _empty_list_for_null(cls, value: Any) -> Any:
        return [] if value is None else value

    @field_validator("connector_profile_id", "rationale", mode="before")
    @classmethod
    def _empty_string_for_null(cls, value: Any) -> Any:
        return "" if value is None else value


class RadarPlannerSourceCard(BaseModel):
    source_id: str
    source_label: str = ""
    connector_profile_id: str = ""
    source_type: str = ""
    runtime_provider_id: str = ""
    usage_obligation: str = "preferred"
    trust_level: str = ""
    best_for: list[str] = Field(default_factory=list)
    not_for: list[str] = Field(default_factory=list)
    required_input_kinds: list[str] = Field(default_factory=list)
    returned_fact_kinds: list[str] = Field(default_factory=list)
    useful_result_criteria: list[str] = Field(default_factory=list)
    accepted_input_shapes: list[str] = Field(default_factory=list)
    bad_input_shapes: list[str] = Field(default_factory=list)
    non_blocking_outcomes: list[str] = Field(default_factory=list)
    language_hints: list[str] = Field(default_factory=list)
    capability_class: str = ""
    supports_lookup: bool = False
    supports_broad_discovery: bool = False
    supports_identity: bool = False
    supports_enrichment: bool = False
    supports_coverage: bool = False
    supports_signal_evidence: bool = False
    requires_concrete_input: bool = False

    @field_validator(
        "best_for",
        "not_for",
        "required_input_kinds",
        "returned_fact_kinds",
        "useful_result_criteria",
        "accepted_input_shapes",
        "bad_input_shapes",
        "non_blocking_outcomes",
        "language_hints",
        mode="before",
    )
    @classmethod
    def _empty_card_list_for_null(cls, value: Any) -> Any:
        return [] if value is None else value

    @field_validator("source_label", "connector_profile_id", "source_type", "runtime_provider_id", "trust_level", "capability_class", mode="before")
    @classmethod
    def _empty_card_string_for_null(cls, value: Any) -> Any:
        return "" if value is None else value


def planner_source_cards_for_policy(
    global_policy: dict[str, Any],
    *,
    connector_profile_registry: ConnectorProfileRegistry | None = None,
) -> list[RadarPlannerSourceCard]:
    registry = connector_profile_registry or default_connector_profile_registry()
    cards: list[RadarPlannerSourceCard] = []
    for source in [dict(item) for item in global_policy.get("sources", []) if isinstance(item, dict)]:
        source_id = str(source.get("source_id") or source.get("reference") or source.get("label") or "").strip()
        if not source_id:
            continue
        capability = registry.capability_for_source(source)
        if capability is None:
            continue
        cards.append(RadarPlannerSourceCard(
            source_id=source_id,
            source_label=str(source.get("label") or capability.display_name or source_id),
            connector_profile_id=capability.profile_id,
            source_type=capability.source_type,
            runtime_provider_id=capability.runtime_provider_id,
            usage_obligation=source_usage_obligation(source),
            trust_level=str(source.get("trust_level") or source.get("trust") or ""),
            best_for=_source_card_best_for(capability),
            not_for=_source_card_not_for(capability),
            required_input_kinds=list(capability.required_input_kinds),
            returned_fact_kinds=list(capability.returned_fact_kinds),
            useful_result_criteria=list(capability.useful_result_criteria),
            accepted_input_shapes=list(capability.accepted_input_shapes),
            bad_input_shapes=list(capability.bad_input_shapes),
            non_blocking_outcomes=list(capability.non_blocking_outcomes),
            language_hints=list(capability.language_hints),
            capability_class=capability.capability_class,
            supports_lookup=capability.supports_lookup,
            supports_broad_discovery=capability.supports_broad_discovery,
            supports_identity=capability.supports_identity,
            supports_enrichment=capability.supports_enrichment,
            supports_coverage=capability.supports_coverage,
            supports_signal_evidence=capability.supports_signal_evidence,
            requires_concrete_input=capability.requires_concrete_input,
        ))
    return cards


def source_card_index(planning_input: Any) -> dict[str, RadarPlannerSourceCard]:
    return {card.source_id: card for card in getattr(planning_input, "source_cards", [])}


def source_use_for_step(
    *,
    step_id: str,
    stage: str,
    source_ids: list[str],
    candidate_scope: list[str],
    planning_input: Any,
) -> list[RadarPlannerSourceUse]:
    cards = source_card_index(planning_input)
    result: list[RadarPlannerSourceUse] = []
    for source_id in source_ids:
        card = cards.get(source_id)
        result.append(RadarPlannerSourceUse(
            source_id=source_id,
            connector_profile_id=card.connector_profile_id if card else "",
            intended_use=_intended_source_use(stage=stage, card=card),
            input_shape=_input_shape_for_step(stage=stage, candidate_scope=candidate_scope),
            expected_fact_kinds=list(card.returned_fact_kinds) if card else [],
            rationale=f"Compatibility source-use projection for {step_id}.",
        ))
    return result


def compatibility_source_use_for_step(*, step: Any, planning_input: Any) -> list[RadarPlannerSourceUse]:
    return source_use_for_step(
        step_id=str(getattr(step, "step_id", "")),
        stage=str(getattr(step, "stage", "")),
        source_ids=list(getattr(step, "source_ids", [])),
        candidate_scope=list(getattr(step, "candidate_scope", [])),
        planning_input=planning_input,
    )


def broad_discovery_source_ids(source_ids: list[str], planning_input: Any) -> list[str]:
    cards = source_card_index(planning_input)
    filtered: list[str] = []
    for source_id in source_ids:
        card = cards.get(source_id)
        if card is None or card.supports_broad_discovery or (card.supports_coverage and not card.requires_concrete_input):
            filtered.append(source_id)
    return filtered


def lookup_only_identity_source_ids(planning_input: Any) -> list[str]:
    return [
        card.source_id
        for card in getattr(planning_input, "source_cards", [])
        if card.usage_obligation != "disabled"
        and card.supports_identity
        and card.requires_concrete_input
        and not card.supports_broad_discovery
    ]


def validate_source_capability_uses(
    *,
    planning_input: Any,
    steps: list[Any],
) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    errors: list[str] = []
    warnings: list[str] = []
    records: list[dict[str, Any]] = []
    cards = source_card_index(planning_input)
    if not cards:
        return errors, warnings, records
    for step in steps:
        source_uses = list(getattr(step, "source_use", [])) or compatibility_source_use_for_step(step=step, planning_input=planning_input)
        if getattr(step, "source_ids", []) and not getattr(step, "source_use", []):
            records.append({
                "type": "source_use_projected",
                "step_id": str(getattr(step, "step_id", "")),
                "source_ids": list(getattr(step, "source_ids", [])),
                "reason": "Legacy source_ids were projected into source_use for capability validation.",
            })
        for source_use in source_uses:
            card = cards.get(source_use.source_id)
            if card is None:
                continue
            compatible, reason = _source_use_is_capability_compatible(source_use=source_use, card=card)
            records.append({
                "type": "source_capability_matched" if compatible else "source_capability_rejected",
                "step_id": str(getattr(step, "step_id", "")),
                "source_id": source_use.source_id,
                "connector_profile_id": card.connector_profile_id,
                "intended_use": source_use.intended_use,
                "input_shape": source_use.input_shape,
                "reason": reason,
            })
            if not compatible:
                errors.append(
                    f"Step {getattr(step, 'step_id', '')} uses source {source_use.source_id} as {source_use.intended_use} "
                    f"with {source_use.input_shape}, but connector profile {card.connector_profile_id} rejects it: {reason}"
                )
    return errors, warnings, records


def _intended_source_use(*, stage: str, card: RadarPlannerSourceCard | None) -> str:
    if stage == "coverage_check":
        return "coverage"
    if stage in {"source_probe", "qualification_gate"}:
        if card and card.supports_lookup and card.supports_identity:
            return "identity_lookup"
        if card and card.supports_enrichment:
            return "enrichment"
        if card and card.source_type == "url":
            return "official_evidence"
        return "coverage"
    if card and card.source_type == "url":
        return "official_evidence"
    return "broad_discovery"


def _input_shape_for_step(*, stage: str, candidate_scope: list[str]) -> str:
    if candidate_scope or stage in {"source_probe", "qualification_gate"}:
        return "candidate_scope"
    return "broad_query"


def _source_use_is_capability_compatible(
    *,
    source_use: RadarPlannerSourceUse,
    card: RadarPlannerSourceCard,
) -> tuple[bool, str]:
    if card.requires_concrete_input and source_use.input_shape == "broad_query" and not card.supports_broad_discovery:
        return False, "source requires concrete company input and cannot execute broad discovery input"
    if source_use.intended_use == "broad_discovery" and not card.supports_broad_discovery:
        return False, "source does not support broad candidate-universe discovery"
    if source_use.intended_use == "identity_lookup" and not (card.supports_identity and card.requires_concrete_input):
        return False, "source does not support concrete legal entity identity lookup"
    if source_use.intended_use == "enrichment" and not card.supports_enrichment:
        return False, "source does not support company enrichment facts"
    if source_use.intended_use == "coverage" and not card.supports_coverage:
        return False, "source does not support coverage evidence"
    if source_use.intended_use == "signal_evidence" and not card.supports_signal_evidence:
        return False, "source does not support intent signal evidence"
    if source_use.intended_use == "official_evidence" and not (card.source_type == "url" or card.supports_coverage):
        return False, "source is not an official-domain or coverage evidence source"
    return True, "source use matches compiled connector capability"


def _source_card_best_for(capability: Any) -> list[str]:
    result: list[str] = []
    if capability.supports_broad_discovery:
        result.append("broad candidate-universe discovery")
    if capability.supports_identity:
        result.append("legal entity identity")
    if capability.supports_enrichment:
        result.append("company enrichment")
    if capability.supports_coverage:
        result.append("coverage evidence and citations")
    if capability.supports_signal_evidence:
        result.append("intent signal evidence")
    return result


def _source_card_not_for(capability: Any) -> list[str]:
    result: list[str] = []
    if capability.requires_concrete_input and not capability.supports_broad_discovery:
        result.append("broad natural-language universe discovery without concrete company input")
    if not capability.supports_signal_evidence:
        result.append("intent signal evidence")
    if not capability.supports_broad_discovery:
        result.append("holding-contour enumeration")
    return result
