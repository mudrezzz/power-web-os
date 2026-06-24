from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


CRITERION_CODES = tuple(f"C{index}" for index in range(1, 21))
FIT_CRITERIA = tuple(f"C{index}" for index in range(13, 18))
INTENT_CRITERIA = tuple([*(f"C{index}" for index in range(1, 10)), "C18", "C19"])
TRIGGER_CRITERIA = ("C10", "C11", "C12", "C20")


@dataclass(frozen=True, slots=True)
class ICPProfile:
    profile_id: str
    name: str
    product: str
    holding: str
    run_mode: str
    source_workbook: str
    scoring_formula: dict[str, Any]


@dataclass(frozen=True, slots=True)
class SignalCriterion:
    code: str
    name: str
    description: str
    scoring_guidance: str


@dataclass(frozen=True, slots=True)
class EvidenceSource:
    source_id: str
    url: str
    usage: str


@dataclass(frozen=True, slots=True)
class RadarMetadata:
    name: str
    description: str
    owner: str
    status: str


@dataclass(frozen=True, slots=True)
class SourceDefinition:
    source_id: str
    source_type: str
    label: str
    reference: str
    trust_level: str
    usage_obligation: str = "preferred"


@dataclass(frozen=True, slots=True)
class SourcePolicy:
    source_ids: tuple[str, ...]
    source_logic: str
    allow_additional_sources: bool
    fallback_confidence: str
    use_global_search_policy: bool = True
    local_sources: tuple[SourceDefinition, ...] = ()


@dataclass(frozen=True, slots=True)
class AtomicRule:
    rule_id: str
    description: str
    target_field: str
    comparison_operator: str
    value: str
    requirement_level: str
    source_policy: SourcePolicy
    name: str = ""


@dataclass(frozen=True, slots=True)
class RuleGroup:
    group_id: str
    operator: str
    rules: tuple[AtomicRule, ...]
    groups: tuple["RuleGroup", ...] = ()
    name: str = ""


@dataclass(frozen=True, slots=True)
class GlobalSearchPolicy:
    sources: tuple[SourceDefinition, ...]
    keywords: tuple[str, ...]
    exclusions: tuple[str, ...]
    allow_system_sources: bool


@dataclass(frozen=True, slots=True)
class AccountQualificationModel:
    rule_group: RuleGroup


@dataclass(frozen=True, slots=True)
class SignalScoreRule:
    score: int
    description: str
    rule_group: RuleGroup


@dataclass(frozen=True, slots=True)
class SignalScoringRubric:
    scale: tuple[int, ...]
    rules: tuple[SignalScoreRule, ...]


@dataclass(frozen=True, slots=True)
class IntentSignalDefinition:
    signal_id: str
    code: str
    name: str
    description: str
    trigger_rule_group: RuleGroup
    source_policy: SourcePolicy
    scoring_rubric: SignalScoringRubric


@dataclass(frozen=True, slots=True)
class MonitoringPolicy:
    cadence: str
    lookback_window: str
    run_mode: str
    deduplication: str
    stale_after: str


@dataclass(frozen=True, slots=True)
class RadarScoringModel:
    fit_model: dict[str, Any]
    intent_model: dict[str, Any]
    tier_model: dict[str, Any]
    tier_thresholds: dict[str, str]
    confidence_penalties: dict[str, str]


@dataclass(frozen=True, slots=True)
class RadarValidationIssue:
    level: str
    code: str
    message: str
    path: str


@dataclass(frozen=True, slots=True)
class RadarValidationReport:
    errors: tuple[RadarValidationIssue, ...]
    warnings: tuple[RadarValidationIssue, ...]
    info: tuple[RadarValidationIssue, ...]


@dataclass(frozen=True, slots=True)
class RadarDefinition:
    definition_id: str
    metadata: RadarMetadata
    global_search_policy: GlobalSearchPolicy
    account_qualification: AccountQualificationModel
    intent_signals: tuple[IntentSignalDefinition, ...]
    monitoring_policy: MonitoringPolicy
    scoring_model: RadarScoringModel
    validation_report: RadarValidationReport


@dataclass(frozen=True, slots=True)
class ICPRadarScore:
    fit_score: int
    intent_score: int
    trigger_score: int
    total_score: int
    tier: str


@dataclass(frozen=True, slots=True)
class SignalValidationDecision:
    signal_code: str
    status: str
    original_score: int
    adjusted_score: int | None = None
    confidence: str | None = None
    corrected_summary: str | None = None
    evidence_refs: tuple[str, ...] = ()
    comment: str = ""
    reviewed_at: str = ""


@dataclass(frozen=True, slots=True)
class ValidatedSignalScore:
    signal_code: str
    original_score: int
    effective_score: int
    delta: int
    status: str


@dataclass(frozen=True, slots=True)
class ValidatedCandidateScore:
    original_score: ICPRadarScore
    effective_score: ICPRadarScore
    signal_scores: dict[str, ValidatedSignalScore]
    status_counts: dict[str, int]


@dataclass(frozen=True, slots=True)
class CriterionEvidenceFact:
    evidence_ref: str
    source_url: str
    fact: str
    why_it_matters: str


@dataclass(frozen=True, slots=True)
class CriterionEvidenceExplanation:
    criterion_code: str
    score: int
    evidence_origin: str
    evidence_status: str
    confidence: str
    rationale: str
    evidence_refs: tuple[str, ...]
    source_urls: tuple[str, ...]
    facts: tuple[CriterionEvidenceFact, ...]


@dataclass(frozen=True, slots=True)
class ICPRadarCandidate:
    rank: int
    account_id: str
    ppo: str
    legal_name: str
    account_type: str
    description: str
    inn: str
    revenue: str
    site: str
    confidence: str
    signal_summary: str
    main_signal: str
    comment: str
    source_urls: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    criteria_scores: dict[str, int]
    criteria_evidence: dict[str, CriterionEvidenceExplanation]
    score: ICPRadarScore


@dataclass(frozen=True, slots=True)
class ICPRadarArtifact:
    profile: ICPProfile
    criteria: tuple[SignalCriterion, ...]
    sources: tuple[EvidenceSource, ...]
    definition: RadarDefinition
    candidates: tuple[ICPRadarCandidate, ...]
    workflow_metadata: dict[str, Any]


class ICPRadar:
    def build_score(self, criteria_scores: dict[str, int]) -> ICPRadarScore:
        normalized = {code: int(criteria_scores.get(code, 0)) for code in CRITERION_CODES}
        fit_score = sum(normalized[code] for code in FIT_CRITERIA)
        intent_score = sum(normalized[code] for code in INTENT_CRITERIA)
        trigger_score = sum(normalized[code] for code in TRIGGER_CRITERIA)
        total_score = sum(normalized.values())
        return ICPRadarScore(
            fit_score=fit_score,
            intent_score=intent_score,
            trigger_score=trigger_score,
            total_score=total_score,
            tier=self._tier(total_score),
        )

    def rank(self, candidates: list[ICPRadarCandidate]) -> tuple[ICPRadarCandidate, ...]:
        ranked = sorted(
            candidates,
            key=lambda item: (-item.score.total_score, -item.score.intent_score, item.legal_name),
        )
        return tuple(
            ICPRadarCandidate(
                rank=index,
                account_id=item.account_id,
                ppo=item.ppo,
                legal_name=item.legal_name,
                account_type=item.account_type,
                description=item.description,
                inn=item.inn,
                revenue=item.revenue,
                site=item.site,
                confidence=item.confidence,
                signal_summary=item.signal_summary,
                main_signal=item.main_signal,
                comment=item.comment,
                source_urls=item.source_urls,
                evidence_refs=item.evidence_refs,
                criteria_scores=item.criteria_scores,
                criteria_evidence=item.criteria_evidence,
                score=item.score,
            )
            for index, item in enumerate(ranked, start=1)
        )

    @staticmethod
    def _tier(total_score: int) -> str:
        if total_score >= 38:
            return "Tier 1"
        if total_score >= 25:
            return "Tier 2"
        if total_score >= 15:
            return "Tier 3"
        return "Monitor"


class ICPRadarValidationScorer:
    supported_statuses = {"unreviewed", "confirmed", "corrected", "rejected", "stale"}

    def __init__(self, radar: ICPRadar | None = None) -> None:
        self._radar = radar or ICPRadar()

    def score(
        self,
        *,
        criteria_scores: dict[str, int],
        decisions: dict[str, SignalValidationDecision] | None = None,
    ) -> ValidatedCandidateScore:
        decisions = decisions or {}
        normalized = {code: int(criteria_scores.get(code, 0)) for code in CRITERION_CODES}
        effective_scores: dict[str, int] = {}
        signal_scores: dict[str, ValidatedSignalScore] = {}
        status_counts = {status: 0 for status in self.supported_statuses}

        for code in CRITERION_CODES:
            original_score = normalized[code]
            decision = decisions.get(code)
            status = self._normalize_status(decision.status if decision else "unreviewed")
            status_counts[status] += 1
            effective_score = self._effective_score(original_score, decision, status)
            effective_scores[code] = effective_score
            signal_scores[code] = ValidatedSignalScore(
                signal_code=code,
                original_score=original_score,
                effective_score=effective_score,
                delta=effective_score - original_score,
                status=status,
            )

        return ValidatedCandidateScore(
            original_score=self._radar.build_score(normalized),
            effective_score=self._radar.build_score(effective_scores),
            signal_scores=signal_scores,
            status_counts=status_counts,
        )

    @classmethod
    def _normalize_status(cls, status: str) -> str:
        return status if status in cls.supported_statuses else "unreviewed"

    @staticmethod
    def _effective_score(
        original_score: int,
        decision: SignalValidationDecision | None,
        status: str,
    ) -> int:
        if status == "corrected":
            return max(0, int(decision.adjusted_score if decision and decision.adjusted_score is not None else original_score))
        if status in {"rejected", "stale"}:
            return 0
        return original_score


class RadarDefinitionValidator:
    allowed_group_operators = {"AND", "OR", "NOT"}
    allowed_source_logic = {"AND", "OR"}
    allowed_requirement_levels = {"required", "recommended"}
    allowed_formula_presets = {"arithmetic_mean", "weighted_average", "maximum_signal", "capped_sum", "custom"}
    allowed_comparison_operators = {
        "equals",
        "not_equals",
        "contains",
        "greater_than",
        "less_than",
        "exists",
        "not_exists",
        "in",
    }

    def validate(self, definition: RadarDefinition) -> RadarValidationReport:
        errors: list[RadarValidationIssue] = []
        warnings: list[RadarValidationIssue] = []
        info: list[RadarValidationIssue] = []
        source_ids = {source.source_id for source in definition.global_search_policy.sources}

        self._require(definition.metadata.name, "metadata.name", "radar_name_required", errors)
        self._require(definition.metadata.description, "metadata.description", "radar_description_required", warnings)
        self._require(definition.metadata.owner, "metadata.owner", "radar_owner_required", errors)
        self._validate_source_ids(definition.global_search_policy.sources, errors)
        self._validate_rule_group(
            definition.account_qualification.rule_group,
            path="account_qualification.rule_group",
            source_ids=source_ids,
            errors=errors,
            warnings=warnings,
            parent_has_positive=False,
        )
        self._validate_simple_contradictions(
            definition.account_qualification.rule_group,
            path="account_qualification.rule_group",
            warnings=warnings,
        )
        self._validate_signal_ids(definition.intent_signals, errors)
        for signal in definition.intent_signals:
            signal_path = f"intent_signals.{signal.signal_id}"
            self._validate_source_policy(signal.source_policy, f"{signal_path}.source_policy", source_ids, errors, warnings)
            self._validate_rule_group(
                signal.trigger_rule_group,
                path=f"{signal_path}.trigger_rule_group",
                source_ids=source_ids,
                errors=errors,
                warnings=warnings,
                parent_has_positive=False,
            )
            rubric_scores = {rule.score for rule in signal.scoring_rubric.rules}
            expected_scores = set(signal.scoring_rubric.scale)
            if rubric_scores != expected_scores:
                errors.append(
                    RadarValidationIssue(
                        level="error",
                        code="signal_rubric_incomplete",
                        message=f"Signal {signal.code} must define rubric rules for {sorted(expected_scores)}.",
                        path=f"{signal_path}.scoring_rubric",
                    )
                )
        self._validate_scoring_model(definition, errors)
        if definition.intent_signals:
            info.append(
                RadarValidationIssue(
                    level="info",
                    code="validator_scope",
                    message="Validator checks structure and obvious contradictions; semantic industry dictionaries are out of scope.",
                    path="validation_report",
                )
            )
        return RadarValidationReport(errors=tuple(errors), warnings=tuple(warnings), info=tuple(info))

    @staticmethod
    def _require(
        value: str,
        path: str,
        code: str,
        issues: list[RadarValidationIssue],
    ) -> None:
        if not value.strip():
            issues.append(
                RadarValidationIssue(
                    level="error",
                    code=code,
                    message=f"{path} is required.",
                    path=path,
                )
            )

    def _validate_source_ids(
        self,
        sources: tuple[SourceDefinition, ...],
        errors: list[RadarValidationIssue],
    ) -> None:
        seen: set[str] = set()
        for index, source in enumerate(sources):
            path = f"global_search_policy.sources.{index}"
            if source.source_id in seen:
                errors.append(RadarValidationIssue("error", "duplicate_source_id", source.source_id, path))
            seen.add(source.source_id)
            self._require(source.source_id, f"{path}.source_id", "source_id_required", errors)
            self._require(source.label, f"{path}.label", "source_label_required", errors)
            self._require(source.reference, f"{path}.reference", "source_reference_required", errors)

    def _validate_signal_ids(
        self,
        signals: tuple[IntentSignalDefinition, ...],
        errors: list[RadarValidationIssue],
    ) -> None:
        seen_ids: set[str] = set()
        seen_codes: set[str] = set()
        for index, signal in enumerate(signals):
            path = f"intent_signals.{index}"
            if signal.signal_id in seen_ids:
                errors.append(RadarValidationIssue("error", "duplicate_signal_id", signal.signal_id, path))
            if signal.code in seen_codes:
                errors.append(RadarValidationIssue("error", "duplicate_signal_code", signal.code, path))
            seen_ids.add(signal.signal_id)
            seen_codes.add(signal.code)
            self._require(signal.name, f"{path}.name", "signal_name_required", errors)

    def _validate_rule_group(
        self,
        group: RuleGroup,
        *,
        path: str,
        source_ids: set[str],
        errors: list[RadarValidationIssue],
        warnings: list[RadarValidationIssue],
        parent_has_positive: bool,
    ) -> None:
        if group.operator not in self.allowed_group_operators:
            errors.append(RadarValidationIssue("error", "invalid_group_operator", group.operator, f"{path}.operator"))
        if not group.rules and not group.groups:
            errors.append(RadarValidationIssue("error", "empty_rule_group", "Rule group must contain at least one rule.", path))
        has_positive = parent_has_positive or group.operator != "NOT"
        if group.operator == "NOT" and not parent_has_positive:
            warnings.append(RadarValidationIssue("warning", "not_without_positive_sibling", "NOT should refine a positive rule group.", path))

        rule_ids: set[str] = set()
        for index, rule in enumerate(group.rules):
            rule_path = f"{path}.rules.{index}"
            if rule.rule_id in rule_ids:
                errors.append(RadarValidationIssue("error", "duplicate_rule_id", rule.rule_id, rule_path))
            rule_ids.add(rule.rule_id)
            self._validate_atomic_rule(rule, rule_path, source_ids, errors, warnings)
        for index, child in enumerate(group.groups):
            self._validate_rule_group(
                child,
                path=f"{path}.groups.{index}",
                source_ids=source_ids,
                errors=errors,
                warnings=warnings,
                parent_has_positive=has_positive,
            )

    def _validate_atomic_rule(
        self,
        rule: AtomicRule,
        path: str,
        source_ids: set[str],
        errors: list[RadarValidationIssue],
        warnings: list[RadarValidationIssue],
    ) -> None:
        self._require(rule.description, f"{path}.description", "rule_description_required", errors)
        if rule.target_field and rule.comparison_operator not in self.allowed_comparison_operators:
            errors.append(RadarValidationIssue("error", "invalid_comparison_operator", rule.comparison_operator, f"{path}.comparison_operator"))
        if rule.requirement_level not in self.allowed_requirement_levels:
            errors.append(RadarValidationIssue("error", "invalid_requirement_level", rule.requirement_level, f"{path}.requirement_level"))
        self._validate_source_policy(rule.source_policy, f"{path}.source_policy", source_ids, errors, warnings)
        if (
            rule.requirement_level == "required"
            and not rule.source_policy.source_ids
            and not rule.source_policy.local_sources
            and not rule.source_policy.use_global_search_policy
            and not rule.source_policy.allow_additional_sources
        ):
            errors.append(RadarValidationIssue("error", "required_rule_without_source", "Required rule needs a trusted source or fallback.", path))

    def _validate_source_policy(
        self,
        policy: SourcePolicy,
        path: str,
        source_ids: set[str],
        errors: list[RadarValidationIssue],
        warnings: list[RadarValidationIssue],
    ) -> None:
        if policy.source_logic not in self.allowed_source_logic:
            errors.append(RadarValidationIssue("error", "invalid_source_logic", policy.source_logic, f"{path}.source_logic"))
        source_count = len(policy.source_ids) + len(policy.local_sources)
        if source_count == 0 and not policy.use_global_search_policy and not policy.allow_additional_sources:
            errors.append(RadarValidationIssue("error", "missing_source_policy_choice", "Select at least one source policy option.", path))
        if policy.source_logic == "AND" and source_count < 2:
            warnings.append(RadarValidationIssue("warning", "source_and_without_crosscheck", "AND source logic needs at least two sources.", path))
        for source_id in policy.source_ids:
            if source_id not in source_ids:
                errors.append(RadarValidationIssue("error", "unknown_source_id", source_id, f"{path}.source_ids"))

    def _validate_simple_contradictions(
        self,
        group: RuleGroup,
        *,
        path: str,
        warnings: list[RadarValidationIssue],
    ) -> None:
        by_field: dict[str, dict[str, float]] = {}
        for rule in self._iter_rules(group):
            if rule.comparison_operator not in {"greater_than", "less_than"}:
                continue
            try:
                value = float(rule.value.replace(" ", "").replace(",", "."))
            except ValueError:
                continue
            field_limits = by_field.setdefault(rule.target_field, {})
            existing = field_limits.get(rule.comparison_operator)
            if existing is None or (
                rule.comparison_operator == "greater_than" and value > existing
            ) or (
                rule.comparison_operator == "less_than" and value < existing
            ):
                field_limits[rule.comparison_operator] = value
            lower = field_limits.get("greater_than")
            upper = field_limits.get("less_than")
            if lower is not None and upper is not None and lower >= upper:
                warnings.append(
                    RadarValidationIssue(
                        level="warning",
                        code="obvious_numeric_contradiction",
                        message=f"{rule.target_field} has incompatible lower and upper bounds.",
                        path=path,
                    )
                )

    def _validate_scoring_model(
        self,
        definition: RadarDefinition,
        errors: list[RadarValidationIssue],
    ) -> None:
        fit_refs = {rule.rule_id for rule in self._iter_rules(definition.account_qualification.rule_group)}
        intent_refs = {signal.code for signal in definition.intent_signals}
        self._validate_formula_model(definition.scoring_model.fit_model, fit_refs, "scoring_model.fit_model", errors)
        self._validate_formula_model(definition.scoring_model.intent_model, intent_refs, "scoring_model.intent_model", errors)

    def _validate_formula_model(
        self,
        model: dict[str, Any],
        allowed_refs: set[str],
        path: str,
        errors: list[RadarValidationIssue],
    ) -> None:
        preset = str(model.get("formula_preset", "")).strip()
        if preset not in self.allowed_formula_presets:
            errors.append(RadarValidationIssue("error", "invalid_formula_preset", preset, f"{path}.formula_preset"))
            return
        if preset != "custom":
            return
        formula = str(model.get("custom_formula", "")).strip()
        if not formula:
            errors.append(RadarValidationIssue("error", "custom_formula_required", "Custom formula requires an expression.", f"{path}.custom_formula"))
            return
        known_words = {"and", "or", "not", "min", "max", "sum", "avg", "mean", "weighted", "capped"}
        for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]*", formula):
            if token.lower() in known_words:
                continue
            if token not in allowed_refs:
                errors.append(RadarValidationIssue("error", "invalid_custom_formula_reference", token, f"{path}.custom_formula"))

    def _iter_rules(self, group: RuleGroup) -> tuple[AtomicRule, ...]:
        rules = list(group.rules)
        for child in group.groups:
            rules.extend(self._iter_rules(child))
        return tuple(rules)


def icp_radar_artifact_to_payload(artifact: ICPRadarArtifact) -> dict[str, Any]:
    criteria_alias = tuple(
        SignalCriterion(
            code=signal.code,
            name=signal.name,
            description=signal.description,
            scoring_guidance=_signal_scoring_guidance(signal),
        )
        for signal in artifact.definition.intent_signals
    )
    return {
        "artifact_type": "icp_radar",
        "artifact_version": "0.6.5.2",
        "criteria_evidence_contract_version": "0.6.2.3",
        "radar": {
            "profile": profile_to_payload(artifact.profile),
            "definition": radar_definition_to_payload(artifact.definition),
        },
        "criteria": [criterion_to_payload(item) for item in criteria_alias],
        "candidates": [candidate_to_payload(item) for item in artifact.candidates],
        "workflow_metadata": artifact.workflow_metadata,
    }


def _signal_scoring_guidance(signal: IntentSignalDefinition) -> str:
    return " | ".join(
        f"{rule.score}: {rule.description}"
        for rule in sorted(signal.scoring_rubric.rules, key=lambda item: item.score)
    )


def profile_to_payload(profile: ICPProfile) -> dict[str, Any]:
    return {
        "profile_id": profile.profile_id,
        "name": profile.name,
        "product": profile.product,
        "holding": profile.holding,
        "run_mode": profile.run_mode,
        "source_workbook": profile.source_workbook,
        "scoring_formula": profile.scoring_formula,
    }


def criterion_to_payload(criterion: SignalCriterion) -> dict[str, Any]:
    return {
        "code": criterion.code,
        "name": criterion.name,
        "description": criterion.description,
        "scoring_guidance": criterion.scoring_guidance,
    }


def source_to_payload(source: EvidenceSource) -> dict[str, Any]:
    return {
        "source_id": source.source_id,
        "url": source.url,
        "usage": source.usage,
    }


def radar_definition_to_payload(definition: RadarDefinition) -> dict[str, Any]:
    return {
        "definition_id": definition.definition_id,
        "metadata": metadata_to_payload(definition.metadata),
        "global_search_policy": global_search_policy_to_payload(definition.global_search_policy),
        "account_qualification": account_qualification_to_payload(definition.account_qualification),
        "intent_signals": [intent_signal_to_payload(item) for item in definition.intent_signals],
        "monitoring_policy": monitoring_policy_to_payload(definition.monitoring_policy),
        "scoring_model": scoring_model_to_payload(definition.scoring_model),
        "validation_report": validation_report_to_payload(definition.validation_report),
    }


def metadata_to_payload(metadata: RadarMetadata) -> dict[str, Any]:
    return {
        "name": metadata.name,
        "description": metadata.description,
        "owner": metadata.owner,
        "status": metadata.status,
    }


def source_definition_to_payload(source: SourceDefinition) -> dict[str, Any]:
    return {
        "source_id": source.source_id,
        "source_type": source.source_type,
        "label": source.label,
        "reference": source.reference,
        "trust_level": source.trust_level,
        "usage_obligation": source.usage_obligation,
    }


def source_policy_to_payload(policy: SourcePolicy) -> dict[str, Any]:
    return {
        "source_ids": list(policy.source_ids),
        "source_logic": policy.source_logic,
        "use_global_search_policy": policy.use_global_search_policy,
        "allow_additional_sources": policy.allow_additional_sources,
        "fallback_confidence": policy.fallback_confidence,
        "local_sources": [source_definition_to_payload(source) for source in policy.local_sources],
    }


def atomic_rule_to_payload(rule: AtomicRule) -> dict[str, Any]:
    return {
        "rule_id": rule.rule_id,
        "name": rule.name or rule.description,
        "description": rule.description,
        "generated_target_field": rule.target_field,
        "generated_comparison_operator": rule.comparison_operator,
        "generated_value": rule.value,
        "requirement_level": rule.requirement_level,
        "source_policy": source_policy_to_payload(rule.source_policy),
    }


def rule_group_to_payload(group: RuleGroup) -> dict[str, Any]:
    return {
        "group_id": group.group_id,
        "name": group.name or group.group_id,
        "operator": group.operator,
        "rules": [atomic_rule_to_payload(rule) for rule in group.rules],
        "groups": [rule_group_to_payload(child) for child in group.groups],
    }


def global_search_policy_to_payload(policy: GlobalSearchPolicy) -> dict[str, Any]:
    return {
        "sources": [source_definition_to_payload(item) for item in policy.sources],
        "keywords": list(policy.keywords),
        "exclusions": list(policy.exclusions),
        "allow_system_sources": policy.allow_system_sources,
    }


def account_qualification_to_payload(model: AccountQualificationModel) -> dict[str, Any]:
    return {
        "rule_group": rule_group_to_payload(model.rule_group),
    }


def score_rule_to_payload(rule: SignalScoreRule) -> dict[str, Any]:
    return {
        "score": rule.score,
        "description": rule.description,
        "rule_group": rule_group_to_payload(rule.rule_group),
    }


def scoring_rubric_to_payload(rubric: SignalScoringRubric) -> dict[str, Any]:
    return {
        "scale": list(rubric.scale),
        "rules": [score_rule_to_payload(item) for item in rubric.rules],
    }


def intent_signal_to_payload(signal: IntentSignalDefinition) -> dict[str, Any]:
    return {
        "signal_id": signal.signal_id,
        "code": signal.code,
        "name": signal.name,
        "description": signal.description,
        "trigger_rule_group": rule_group_to_payload(signal.trigger_rule_group),
        "source_policy": source_policy_to_payload(signal.source_policy),
        "scoring_rubric": scoring_rubric_to_payload(signal.scoring_rubric),
    }


def monitoring_policy_to_payload(policy: MonitoringPolicy) -> dict[str, Any]:
    return {
        "cadence": policy.cadence,
        "lookback_window": policy.lookback_window,
        "run_mode": policy.run_mode,
        "deduplication": policy.deduplication,
        "stale_after": policy.stale_after,
    }


def scoring_model_to_payload(model: RadarScoringModel) -> dict[str, Any]:
    return {
        "fit_model": model.fit_model,
        "intent_model": model.intent_model,
        "tier_model": model.tier_model,
        "tier_thresholds": model.tier_thresholds,
        "confidence_penalties": model.confidence_penalties,
    }


def validation_issue_to_payload(issue: RadarValidationIssue) -> dict[str, Any]:
    return {
        "level": issue.level,
        "code": issue.code,
        "message": issue.message,
        "path": issue.path,
    }


def validation_report_to_payload(report: RadarValidationReport) -> dict[str, Any]:
    return {
        "errors": [validation_issue_to_payload(item) for item in report.errors],
        "warnings": [validation_issue_to_payload(item) for item in report.warnings],
        "info": [validation_issue_to_payload(item) for item in report.info],
    }


def candidate_to_payload(candidate: ICPRadarCandidate) -> dict[str, Any]:
    return {
        "rank": candidate.rank,
        "account_id": candidate.account_id,
        "ppo": candidate.ppo,
        "legal_name": candidate.legal_name,
        "account_type": candidate.account_type,
        "description": candidate.description,
        "inn": candidate.inn,
        "revenue": candidate.revenue,
        "site": candidate.site,
        "confidence": candidate.confidence,
        "signal_summary": candidate.signal_summary,
        "main_signal": candidate.main_signal,
        "comment": candidate.comment,
        "source_urls": list(candidate.source_urls),
        "evidence_refs": list(candidate.evidence_refs),
        "criteria_scores": dict(candidate.criteria_scores),
        "criteria_evidence": {
            code: criterion_evidence_to_payload(item)
            for code, item in sorted(candidate.criteria_evidence.items())
        },
        "score": score_to_payload(candidate.score),
    }


def criterion_evidence_to_payload(explanation: CriterionEvidenceExplanation) -> dict[str, Any]:
    return {
        "criterion_code": explanation.criterion_code,
        "score": explanation.score,
        "evidence_origin": explanation.evidence_origin,
        "evidence_status": explanation.evidence_status,
        "confidence": explanation.confidence,
        "rationale": explanation.rationale,
        "evidence_refs": list(explanation.evidence_refs),
        "source_urls": list(explanation.source_urls),
        "facts": [criterion_evidence_fact_to_payload(item) for item in explanation.facts],
    }


def criterion_evidence_fact_to_payload(fact: CriterionEvidenceFact) -> dict[str, Any]:
    return {
        "evidence_ref": fact.evidence_ref,
        "source_url": fact.source_url,
        "fact": fact.fact,
        "why_it_matters": fact.why_it_matters,
    }


def score_to_payload(score: ICPRadarScore) -> dict[str, Any]:
    return {
        "fit_score": score.fit_score,
        "intent_score": score.intent_score,
        "trigger_score": score.trigger_score,
        "total_score": score.total_score,
        "tier": score.tier,
    }
