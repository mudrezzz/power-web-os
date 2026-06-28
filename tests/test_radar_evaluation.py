from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from power_web_os.radar_evaluation import (
    SIBUR_CONTOUR_RADAR_ID,
    RadarEvaluationBaseline,
    RadarEvaluationEntity,
    evaluate_radar_dossier,
    load_evaluation_baseline,
)
from power_web_os.radar_evaluation_runner import resolve_evaluation_run


BASELINE_PATH = Path("demo/fixtures/radar_evaluation/sibur_contour_baseline.json")


def test_load_sibur_baseline_fixture_is_curated_mixed_baseline() -> None:
    baseline = load_evaluation_baseline(BASELINE_PATH)

    assert baseline.baseline_id == "sibur_contour_curated_v1"
    assert baseline.radar_id == SIBUR_CONTOUR_RADAR_ID
    assert 10 <= len(baseline.entities) <= 20
    assert {item.entity_type for item in baseline.entities} >= {"legal_entity", "production_site"}


def test_evaluation_matches_exact_alias_identifier_and_review_needed_site() -> None:
    report = evaluate_radar_dossier(
        run={"run_id": "radar-run-1", "radar_id": SIBUR_CONTOUR_RADAR_ID, "status": "completed"},
        dossier=_sample_dossier(),
        baseline=_sample_baseline(),
    )

    assert report["metrics"]["strict_recall"] == 0.6
    assert report["metrics"]["review_recall"] == 1.0
    assert report["metrics"]["precision"] == 0.6
    assert report["metrics"]["true_positive_count"] == 3
    assert report["metrics"]["false_positive_count"] == 1
    assert report["metrics"]["false_negative_count"] == 1
    assert report["metrics"]["ambiguous_match_count"] == 1
    assert {item["baseline_id"] for item in report["true_positives"]} == {
        "zapsibneftekhim",
        "tomskneftekhim",
        "poliom",
    }
    assert report["review_matches"][0]["baseline_id"] == "gubkinsky-gpp"
    assert report["false_positives"][0]["observed_name"] == "ООО «Нерелевант»"
    assert report["false_negatives"][0]["baseline_id"] == "kazanorgsintez"
    assert report["ambiguous_matches"][0]["baseline_id"] == "rusvinyl"
    assert report["evidence_quality_summary"]["missing"] == 1
    _assert_safe(report)


def test_evaluation_counts_review_needed_sites_from_upstream_universe() -> None:
    baseline = RadarEvaluationBaseline(
        baseline_id="sibur_sites_test",
        version="v1",
        radar_id=SIBUR_CONTOUR_RADAR_ID,
        description="Review recall fixture.",
        entities=(
            RadarEvaluationEntity(
                baseline_id="gubkinsky-gpp",
                canonical_name="Губкинский газоперерабатывающий завод",
                aliases=("Губкинский ГПЗ",),
                entity_type="production_site",
            ),
            RadarEvaluationEntity(
                baseline_id="vyngapurovsky-gpp",
                canonical_name="Вынгапуровский газоперерабатывающий завод",
                aliases=("Вынгапуровский ГПЗ",),
                entity_type="production_site",
            ),
            RadarEvaluationEntity(
                baseline_id="tobolsk-site",
                canonical_name="Тобольская промышленная площадка",
                aliases=("Тобольская площадка",),
                entity_type="production_site",
            ),
        ),
    )
    dossier = {
        "summary": {"execution_outcome": "stopped_for_review", "execution_outcome_reason": "review needed"},
        "source_lifecycle": [{"evidence_ref": "src_sibur", "url": "https://www.sibur.ru/geo", "state": "retrieved"}],
        "candidates": [],
        "candidate_universe": [
            {
                "legal_name": "Губкинский ГПЗ",
                "entity_type": "production_site",
                "resolution_status": "review_needed",
                "source_refs": ["src_sibur"],
                "review_flags": ["requires_human_review", "not_standalone_legal_entity"],
            },
            {
                "legal_name": "Вынгапуровский ГПЗ",
                "entity_type": "production_site",
                "resolution_status": "review_needed",
                "source_refs": ["src_sibur"],
                "review_flags": ["requires_human_review", "not_standalone_legal_entity"],
            },
            {
                "legal_name": "Тобольская площадка",
                "entity_type": "production_site",
                "resolution_status": "review_needed",
                "source_refs": ["src_sibur"],
                "review_flags": ["requires_human_review", "not_standalone_legal_entity"],
            },
        ],
    }

    report = evaluate_radar_dossier(
        run={"run_id": "radar-run-sites", "radar_id": SIBUR_CONTOUR_RADAR_ID, "status": "completed"},
        dossier=dossier,
        baseline=baseline,
    )

    assert report["metrics"]["review_recall"] == 1.0
    assert report["metrics"]["precision"] is None
    assert {item["baseline_id"] for item in report["review_matches"]} == {
        "gubkinsky-gpp",
        "vyngapurovsky-gpp",
        "tobolsk-site",
    }
    assert report["false_positives"] == []


def test_budget_limited_run_still_produces_diagnostic_followups() -> None:
    dossier = _sample_dossier()
    dossier["summary"]["execution_outcome"] = "stopped_for_review"
    dossier["summary"]["execution_outcome_reason"] = "budget exhausted before signal search"

    report = evaluate_radar_dossier(
        run={"run_id": "radar-run-1", "radar_id": SIBUR_CONTOUR_RADAR_ID, "status": "completed"},
        dossier=dossier,
        baseline=_sample_baseline(),
    )

    assert "tune_benchmark_budgets" in report["recommended_followup_buckets"]
    assert "improve_recall" in report["recommended_followup_buckets"]


def test_evaluation_classifies_false_negative_present_in_source_diagnostics() -> None:
    baseline = RadarEvaluationBaseline(
        baseline_id="diagnostic-test",
        version="test",
        radar_id=SIBUR_CONTOUR_RADAR_ID,
        description="False negative diagnostics.",
        entities=(
            RadarEvaluationEntity(
                baseline_id="gubkinsky-gpp",
                canonical_name="Губкинский газоперерабатывающий завод",
                aliases=("Губкинский ГПЗ",),
                entity_type="production_site",
            ),
            RadarEvaluationEntity(
                baseline_id="tobolsk-site",
                canonical_name="Тобольская промышленная площадка",
                aliases=("Тобольская площадка",),
                entity_type="production_site",
            ),
        ),
    )
    dossier = {
        "summary": {"execution_outcome": "stopped_for_review"},
        "candidates": [],
        "candidate_universe": [],
        "source_lifecycle": [
            {
                "evidence_ref": "src_gubkin",
                "title": "СИБУР: Губкинский ГПЗ",
                "snippet": "Губкинский газоперерабатывающий завод связан с производственным контуром.",
            }
        ],
    }

    report = evaluate_radar_dossier(
        run={"run_id": "radar-run-fn", "radar_id": SIBUR_CONTOUR_RADAR_ID, "status": "completed"},
        dossier=dossier,
        baseline=baseline,
    )

    diagnostics = {item["baseline_id"]: item["bucket"] for item in report["false_negative_diagnostics"]}
    assert diagnostics["gubkinsky-gpp"] == "present_not_projected"
    assert diagnostics["tobolsk-site"] == "not_retrieved_in_run"
    assert report["candidate_projection_note"]


def test_evaluation_classifies_false_negative_generated_but_not_selected_for_expansion() -> None:
    baseline = RadarEvaluationBaseline(
        baseline_id="diagnostic-test",
        version="test",
        radar_id=SIBUR_CONTOUR_RADAR_ID,
        description="Expansion diagnostics.",
        entities=(
            RadarEvaluationEntity(
                baseline_id="gubkinsky-gpp",
                canonical_name="Gubkinsky gas processing plant",
                aliases=("Gubkinsky GPP",),
                entity_type="production_site",
            ),
        ),
    )
    dossier = {
        "summary": {"execution_outcome": "stopped_for_review"},
        "candidates": [],
        "candidate_universe": [],
        "expansion_target_queue": [
            {
                "target_id": "production_site_or_branch_target:gubkinsky_gpp",
                "target_label": "Gubkinsky GPP",
                "target_type": "production_site_or_branch_target",
            }
        ],
        "targets_not_searched": [
            {
                "target_id": "production_site_or_branch_target:gubkinsky_gpp",
                "target_label": "Gubkinsky GPP",
                "target_type": "production_site_or_branch_target",
                "not_searched_reason": "not_selected",
            }
        ],
    }

    report = evaluate_radar_dossier(
        run={"run_id": "radar-run-fn", "radar_id": SIBUR_CONTOUR_RADAR_ID, "status": "completed"},
        dossier=dossier,
        baseline=baseline,
    )

    diagnostics = {item["baseline_id"]: item["bucket"] for item in report["false_negative_diagnostics"]}
    assert diagnostics["gubkinsky-gpp"] == "expansion_not_selected"


def test_non_sibur_run_is_rejected_for_sibur_baseline() -> None:
    with pytest.raises(ValueError, match="targets benchmark-sibur-holding-contour"):
        evaluate_radar_dossier(
            run={"run_id": "radar-run-1", "radar_id": "benchmark-mining-toir", "status": "completed"},
            dossier=_sample_dossier(),
            baseline=_sample_baseline(),
        )


def test_latest_run_resolution_uses_api_catalog_without_enqueueing() -> None:
    client = _FakeEvaluationClient()

    run = resolve_evaluation_run(client=client, run_id=None, radar_id=SIBUR_CONTOUR_RADAR_ID, latest=True)

    assert run["run_id"] == "radar-run-latest"
    assert client.paths == ["/api/radars"]


def test_evaluation_module_does_not_reference_provider_credentials_or_hidden_reasoning() -> None:
    text = Path("src/power_web_os/radar_evaluation.py").read_text(encoding="utf-8")

    assert "OpenRouterWebSearchProvider" not in text
    assert "dadata_source_registry_from_env" not in text
    assert "power_web_os.integrations" not in text
    assert "httpx" not in text


class _FakeEvaluationClient:
    def __init__(self) -> None:
        self.paths: list[str] = []

    def get_json(self, path: str) -> dict[str, Any] | list[Any]:
        self.paths.append(path)
        return [
            {
                "radar_id": SIBUR_CONTOUR_RADAR_ID,
                "latest_run": {
                    "run_id": "radar-run-latest",
                    "radar_id": SIBUR_CONTOUR_RADAR_ID,
                    "status": "completed",
                },
            }
        ]


def _sample_baseline() -> RadarEvaluationBaseline:
    return RadarEvaluationBaseline(
        baseline_id="test-sibur",
        version="test",
        radar_id=SIBUR_CONTOUR_RADAR_ID,
        description="Test baseline.",
        entities=(
            RadarEvaluationEntity(
                baseline_id="zapsibneftekhim",
                canonical_name="ООО «ЗапСибНефтехим»",
                entity_type="legal_entity",
                aliases=("ЗапСибНефтехим",),
            ),
            RadarEvaluationEntity(
                baseline_id="tomskneftekhim",
                canonical_name="ООО «Томскнефтехим»",
                entity_type="legal_entity",
                aliases=("ТНХК",),
            ),
            RadarEvaluationEntity(
                baseline_id="poliom",
                canonical_name="ООО «Полиом»",
                entity_type="legal_entity",
                inn="5501085734",
            ),
            RadarEvaluationEntity(
                baseline_id="rusvinyl",
                canonical_name="ООО «РусВинил»",
                entity_type="legal_entity",
            ),
            RadarEvaluationEntity(
                baseline_id="kazanorgsintez",
                canonical_name="ПАО «Казаньоргсинтез»",
                entity_type="legal_entity",
            ),
            RadarEvaluationEntity(
                baseline_id="gubkinsky-gpp",
                canonical_name="Губкинский газоперерабатывающий завод",
                entity_type="production_site",
                aliases=("Губкинский ГПЗ",),
            ),
        ),
    )


def _sample_dossier() -> dict[str, Any]:
    return {
        "summary": {"execution_outcome": "completed_with_candidates", "execution_outcome_reason": ""},
        "sources": [{"evidence_ref": "src_sibur", "url": "https://www.sibur.ru/ru/about/geo/", "state": "used"}],
        "source_lifecycle": [
            {"evidence_ref": "src_sibur", "url": "https://www.sibur.ru/ru/about/geo/", "state": "used", "verification_state": "reachable"},
            {"evidence_ref": "src_review", "url": "https://example.com/gpp", "state": "retrieved", "verification_state": "reachable"},
        ],
        "candidates": [
            {"legal_name": "ООО «ЗапСибНефтехим»", "source_refs": ["src_sibur"]},
            {"legal_name": "ТНХК", "source_refs": ["src_sibur"]},
            {"legal_name": "ООО «Полиом»", "inn": "5501085734", "source_refs": ["src_sibur"]},
            {"legal_name": "РусВинил производство", "source_refs": ["src_review"]},
            {"legal_name": "ООО «Нерелевант»", "source_refs": ["src_review"]},
        ],
        "candidate_universe": [
            {
                "name": "Губкинский газоперерабатывающий завод",
                "entity_type": "production_site",
                "resolution_status": "review_needed",
                "source_refs": ["src_review"],
                "review_flags": ["requires_human_review"],
            }
        ],
    }


def _assert_safe(payload: dict[str, Any]) -> None:
    serialized = json.dumps(payload, ensure_ascii=False)
    forbidden = ("OPENROUTER_API_KEY", "DADATA_API_KEY", "DADATA_SECRET_KEY", "Authorization", "Bearer", "chain_of_thought", "hidden_reasoning", "internal_thoughts")
    assert not any(token in serialized for token in forbidden)
