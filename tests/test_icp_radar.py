from __future__ import annotations

import json
from pathlib import Path

from power_web_os.demo import generate_icp_radar_artifact, generate_icp_radar_catalog_artifact
from power_web_os.icp_radar import (
    CRITERION_CODES,
    AtomicRule,
    ICPRadar,
    RadarDefinition,
    RadarDefinitionValidator,
    RuleGroup,
    SourcePolicy,
)
from power_web_os.icp_radar_xlsx import REQUIRED_SHEETS, load_icp_radar_workbook


WORKBOOK = Path("demo/fixtures/icp_radar/sibur_icp_pass1.xlsx")


def test_icp_radar_importer_reads_required_sheets() -> None:
    artifact = load_icp_radar_workbook(WORKBOOK)

    assert artifact.workflow_metadata["sheet_names"][:4] == list(REQUIRED_SHEETS)
    assert artifact.workflow_metadata["candidate_count"] == len(artifact.candidates)
    assert artifact.workflow_metadata["source_count"] == len(artifact.sources)


def test_icp_radar_importer_parses_exactly_twenty_criteria() -> None:
    artifact = load_icp_radar_workbook(WORKBOOK)

    assert len(artifact.criteria) == 20
    assert artifact.criteria[0].code == "C1"
    assert artifact.criteria[-1].code == "C20"
    assert len(artifact.definition.intent_signals) == 20
    assert artifact.definition.intent_signals[0].code == "C1"
    assert artifact.definition.intent_signals[-1].scoring_rubric.scale == (0, 1, 2)


def test_icp_radar_definition_has_rule_signal_source_model() -> None:
    artifact = load_icp_radar_workbook(WORKBOOK)
    definition = artifact.definition

    assert definition.metadata.name == "ТОиР / SIBUR"
    assert definition.global_search_policy.sources
    assert definition.global_search_policy.allow_system_sources is True
    assert definition.account_qualification.rule_group.operator == "AND"
    assert definition.account_qualification.rule_group.name
    assert all(rule.description for rule in definition.account_qualification.rule_group.rules)
    assert {rule.target_field for rule in definition.account_qualification.rule_group.rules} >= {
        "holding",
        "industry",
        "revenue_billion_rub",
    }
    assert definition.intent_signals[0].trigger_rule_group.rules
    assert definition.scoring_model.fit_model["formula_preset"] == "weighted_average"
    assert definition.scoring_model.intent_model["formula_preset"] == "weighted_average"
    assert not hasattr(definition.scoring_model, "trigger_formula")
    assert not hasattr(definition.scoring_model, "total_formula")
    assert not definition.validation_report.errors
    assert definition.validation_report.info


def test_icp_radar_definition_validator_catches_structural_issues() -> None:
    artifact = load_icp_radar_workbook(WORKBOOK)
    definition = artifact.definition
    bad_rule = AtomicRule(
        rule_id="bad-required",
        description="Bad required rule",
        target_field="revenue_billion_rub",
        comparison_operator="greater_than",
        value="10",
        requirement_level="required",
        source_policy=SourcePolicy(
            source_ids=(),
            source_logic="AND",
            use_global_search_policy=False,
            allow_additional_sources=False,
            fallback_confidence="none",
        ),
    )
    contradictory = AtomicRule(
        rule_id="bad-upper",
        description="Contradicting upper bound",
        target_field="revenue_billion_rub",
        comparison_operator="less_than",
        value="5",
        requirement_level="recommended",
        source_policy=SourcePolicy(
            source_ids=("sbis",),
            source_logic="OR",
            use_global_search_policy=True,
            allow_additional_sources=True,
            fallback_confidence="low",
        ),
    )
    bad_definition = RadarDefinition(
        definition_id=definition.definition_id,
        metadata=definition.metadata,
        global_search_policy=definition.global_search_policy,
        account_qualification=type(definition.account_qualification)(
            rule_group=RuleGroup(
                group_id="bad-root",
                name="Bad root",
                operator="AND",
                rules=(*definition.account_qualification.rule_group.rules, bad_rule, contradictory),
            )
        ),
        intent_signals=definition.intent_signals,
        monitoring_policy=definition.monitoring_policy,
        scoring_model=definition.scoring_model,
        validation_report=definition.validation_report,
    )

    report = RadarDefinitionValidator().validate(bad_definition)
    assert {issue.code for issue in report.errors} >= {"required_rule_without_source"}
    assert {issue.code for issue in report.warnings} >= {
        "source_and_without_crosscheck",
        "obvious_numeric_contradiction",
    }


def test_icp_radar_definition_validator_catches_description_first_policy_and_formula_issues() -> None:
    artifact = load_icp_radar_workbook(WORKBOOK)
    definition = artifact.definition
    empty_policy_rule = AtomicRule(
        rule_id="empty-source-policy",
        name="No source choice",
        description="Rule without source policy choices.",
        target_field="",
        comparison_operator="",
        value="",
        requirement_level="recommended",
        source_policy=SourcePolicy(
            source_ids=(),
            source_logic="OR",
            use_global_search_policy=False,
            allow_additional_sources=False,
            fallback_confidence="none",
        ),
    )
    bad_scoring_model = type(definition.scoring_model)(
        fit_model={
            "formula_preset": "custom",
            "description": "Custom fit model.",
            "custom_formula": "unknown_rule + qualification-revenue",
            "uses": [],
        },
        intent_model={
            "formula_preset": "not_a_preset",
            "description": "Bad intent model.",
            "custom_formula": "",
            "uses": [],
        },
        tier_model=definition.scoring_model.tier_model,
        tier_thresholds=definition.scoring_model.tier_thresholds,
        confidence_penalties=definition.scoring_model.confidence_penalties,
    )
    bad_definition = RadarDefinition(
        definition_id=definition.definition_id,
        metadata=definition.metadata,
        global_search_policy=definition.global_search_policy,
        account_qualification=type(definition.account_qualification)(
            rule_group=RuleGroup(
                group_id="bad-root",
                name="Bad root",
                operator="AND",
                rules=(*definition.account_qualification.rule_group.rules, empty_policy_rule),
            )
        ),
        intent_signals=definition.intent_signals,
        monitoring_policy=definition.monitoring_policy,
        scoring_model=bad_scoring_model,
        validation_report=definition.validation_report,
    )

    report = RadarDefinitionValidator().validate(bad_definition)
    error_codes = {issue.code for issue in report.errors}
    assert error_codes >= {
        "missing_source_policy_choice",
        "invalid_formula_preset",
        "invalid_custom_formula_reference",
    }


def test_icp_radar_score_formula_matches_workbook_values() -> None:
    artifact = load_icp_radar_workbook(WORKBOOK)
    candidates = {item.legal_name: item for item in artifact.candidates}

    assert candidates["ПАО «Нижнекамскнефтехим»"].score.fit_score == 13
    assert candidates["ПАО «Нижнекамскнефтехим»"].score.intent_score == 25
    assert candidates["ПАО «Нижнекамскнефтехим»"].score.trigger_score == 8
    assert candidates["ПАО «Нижнекамскнефтехим»"].score.total_score == 46
    assert candidates["ПАО «Нижнекамскнефтехим»"].score.tier == "Tier 1"

    assert candidates["АО «Воронежсинтезкаучук»"].score.total_score == 36
    assert candidates["АО «Воронежсинтезкаучук»"].score.tier == "Tier 2"

    assert candidates["АО «СИБУР-РТ»"].score.total_score == 7
    assert candidates["АО «СИБУР-РТ»"].score.tier == "Monitor"


def test_icp_radar_ranking_sort_order_is_stable() -> None:
    artifact = load_icp_radar_workbook(WORKBOOK)
    candidate_names = [item.legal_name for item in artifact.candidates]
    candidate_ids = [item.account_id for item in artifact.candidates]

    assert candidate_names[:4] == [
        "ПАО «Нижнекамскнефтехим»",
        "ООО «СИБУР»",
        "ООО «ЗапСибНефтехим»",
        "ПАО «Казаньоргсинтез»",
    ]
    assert candidate_names[-1] == "АО «СИБУР-РТ»"

    assert candidate_ids[:5] == [
        "icp-sibur-024",
        "icp-sibur-030",
        "icp-sibur-012",
        "icp-sibur-023",
        "icp-sibur-001",
    ]

    sorted_again = ICPRadar().rank(list(artifact.candidates))
    assert [item.legal_name for item in sorted_again] == candidate_names


def test_icp_radar_attaches_criterion_evidence_for_all_criteria() -> None:
    artifact = load_icp_radar_workbook(WORKBOOK)

    for candidate in artifact.candidates:
        assert tuple(candidate.criteria_evidence) == CRITERION_CODES
        assert len(candidate.criteria_evidence) == 20
        for code, explanation in candidate.criteria_evidence.items():
            assert explanation.criterion_code == code
            assert explanation.score == candidate.criteria_scores[code]


def test_icp_radar_top_candidates_have_synthetic_supported_evidence() -> None:
    artifact = load_icp_radar_workbook(WORKBOOK)

    for candidate in artifact.candidates[:5]:
        supported = [
            item for item in candidate.criteria_evidence.values()
            if item.evidence_status == "supported"
        ]
        assert len(supported) >= 8
        assert all(item.evidence_origin == "synthetic_demo_annotation" for item in supported)
        assert all(item.facts for item in supported)

    first_candidate = artifact.candidates[0]
    for code in ["C1", "C2", "C5", "C12", "C13", "C14", "C18", "C19"]:
        assert first_candidate.criteria_evidence[code].evidence_status == "supported"


def test_icp_radar_criterion_evidence_fallback_statuses() -> None:
    artifact = load_icp_radar_workbook(WORKBOOK)
    statuses = {
        explanation.evidence_status
        for candidate in artifact.candidates
        for explanation in candidate.criteria_evidence.values()
    }

    assert {"supported", "inferred", "not_observed"}.issubset(statuses)

    inferred = next(
        explanation
        for candidate in artifact.candidates
        for explanation in candidate.criteria_evidence.values()
        if explanation.evidence_status == "inferred"
    )
    assert inferred.score > 0
    assert inferred.evidence_origin == "workbook_score_fallback"

    not_observed = next(
        explanation
        for candidate in artifact.candidates
        for explanation in candidate.criteria_evidence.values()
        if explanation.evidence_status == "not_observed"
    )
    assert not_observed.score == 0
    assert not_observed.confidence == "none"


def test_generate_icp_radar_writes_backend_frontend_and_normalized_artifacts(tmp_path: Path) -> None:
    output_path = tmp_path / "output" / "icp_radar.json"
    frontend_output_path = tmp_path / "frontend" / "public" / "demo" / "icp_radar.json"
    normalized_output_path = tmp_path / "fixtures" / "toir_sibur_icp_radar.json"

    artifact = generate_icp_radar_artifact(
        input_path=WORKBOOK,
        output_path=output_path,
        frontend_output_path=frontend_output_path,
        normalized_output_path=normalized_output_path,
    )

    assert output_path.exists()
    assert frontend_output_path.exists()
    assert normalized_output_path.exists()
    assert artifact["artifact_type"] == "icp_radar"
    assert artifact["artifact_version"] == "0.6.5.2"
    assert artifact["criteria_evidence_contract_version"] == "0.6.2.3"
    assert artifact["radar"]["definition"]["definition_id"] == "radar-def-toir-sibur"
    assert len(artifact["radar"]["definition"]["intent_signals"]) == 20
    assert artifact["radar"]["definition"]["account_qualification"]["rule_group"]["operator"] == "AND"
    assert artifact["radar"]["definition"]["global_search_policy"]["sources"]
    assert artifact["radar"]["definition"]["scoring_model"]["fit_model"]["formula_preset"] == "weighted_average"
    assert "trigger_formula" not in artifact["radar"]["definition"]["scoring_model"]
    assert "total_formula" not in artifact["radar"]["definition"]["scoring_model"]
    assert not artifact["radar"]["definition"]["validation_report"]["errors"]

    payload = json.loads(frontend_output_path.read_text(encoding="utf-8"))
    assert len(payload["radar"]["definition"]["intent_signals"]) == 20
    assert payload["candidates"][0]["evidence_refs"]
    assert len(payload["candidates"][0]["criteria_evidence"]) == 20


def test_generate_icp_radar_catalog_writes_portfolio_artifact(tmp_path: Path) -> None:
    output_path = tmp_path / "output" / "icp_radars.json"
    frontend_output_path = tmp_path / "frontend" / "public" / "demo" / "icp_radars.json"

    artifact = generate_icp_radar_catalog_artifact(
        input_path=WORKBOOK,
        output_path=output_path,
        frontend_output_path=frontend_output_path,
    )

    assert output_path.exists()
    assert frontend_output_path.exists()
    assert artifact["artifact_type"] == "icp_radar_catalog"
    assert artifact["artifact_version"] == "0.6.5.2"
    assert len(artifact["radars"]) >= 3

    fixture_backed = [item for item in artifact["radars"] if item["artifact_path"] == "/demo/icp_radar.json"]
    assert len(fixture_backed) == 1
    assert fixture_backed[0]["radar_id"] == "toir-sibur"
    assert fixture_backed[0]["summary"]["candidate_count"] > 0
    assert fixture_backed[0]["definition"]["intent_signals"]

    configured_only = [item for item in artifact["radars"] if item["artifact_path"] is None]
    assert len(configured_only) == 2
    assert all(item["definition"]["validation_report"] for item in configured_only)
