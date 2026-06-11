from __future__ import annotations

import json
from pathlib import Path

from power_web_os.demo import generate_icp_radar_artifact
from power_web_os.icp_radar import CRITERION_CODES, ICPRadar
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
    assert artifact["artifact_version"] == "0.6.2.3"
    assert artifact["criteria_evidence_contract_version"] == "0.6.2.3"

    payload = json.loads(frontend_output_path.read_text(encoding="utf-8"))
    assert len(payload["radar"]["criteria"]) == 20
    assert payload["candidates"][0]["evidence_refs"]
    assert len(payload["candidates"][0]["criteria_evidence"]) == 20
