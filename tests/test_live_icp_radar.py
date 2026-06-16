from __future__ import annotations

import json
from pathlib import Path

import pytest

from power_web_os.demo import generate_live_mini_icp_radar_plan
from power_web_os.live_icp_radar import (
    FRAMEWORK_AVAILABLE,
    LiveICPRadarRunState,
    LiveICPRadarRunWorkflow,
    OpenRouterWebSearchProvider,
    RecordedWebSearchProvider,
    WebSearchProviderResult,
    build_live_mini_radar_artifact,
    build_live_mini_radar_definition,
    build_live_mini_radar_search_plan,
    build_openrouter_request,
    normalize_openrouter_response,
    _filter_result_to_verified_sources,
)


def recorded_provider_payload() -> dict[str, object]:
    return {
        "sources": [
            {
                "evidence_ref": "src_1",
                "title": "СИБУР модернизирует производство",
                "url": "https://www.sibur.ru/example-modernization",
                "snippet": "СИБУР сообщает о модернизации производственной площадки и цифровой диагностике.",
                "query_id": "q2-modernization-investment",
            }
        ],
        "candidate_observations": [
            {
                "legal_name": "ПАО «Нижнекамскнефтехим»",
                "description": "Производственный актив группы СИБУР.",
                "qualification": [
                    {
                        "criterion_code": "Q1",
                        "status": "confirmed",
                        "confidence": "high",
                        "rationale": "Источник относит компанию к группе СИБУР.",
                        "evidence_refs": ["src_1"],
                        "evidence_findings": [
                            {
                                "source_ref": "src_1",
                                "fact": "Source states the candidate belongs to the SIBUR group.",
                                "excerpt": "production asset of the SIBUR group",
                                "excerpt_type": "quote",
                                "why_it_matches_rule": "The excerpt supports group affiliation.",
                                "evidence_strength": "strong",
                                "contradicts_rule": False,
                            }
                        ],
                    },
                    {
                        "criterion_code": "Q2",
                        "status": "confirmed",
                        "confidence": "high",
                        "rationale": "Источник описывает производственную площадку.",
                        "evidence_refs": ["src_1"],
                    },
                ],
                "signals": [
                    {
                        "signal_code": "S1",
                        "status": "observed",
                        "score": 1,
                        "confidence": "medium",
                        "summary": "Есть ремонтная и reliability-повестка.",
                        "evidence_refs": ["src_1"],
                        "evidence_findings": [
                            {
                                "source_ref": "src_1",
                                "fact": "Source mentions repair and reliability agenda.",
                                "excerpt": "repair and reliability agenda",
                                "excerpt_type": "quote",
                                "why_it_matches_signal": "Repair and reliability wording matches S1.",
                                "why_score_applies": "The observation is relevant but not a direct TOIR platform purchase.",
                                "evidence_strength": "medium",
                                "contradicts_signal": False,
                            }
                        ],
                        "score_evaluation": {
                            "scale": "0-2",
                            "applied_score": 1,
                            "max_score": 2,
                            "rule_snapshot": "1: weak or indirect source-backed signal.",
                            "explanation": "Repair/reliability context supports a weak intent score.",
                        },
                    },
                    {
                        "signal_code": "S2",
                        "status": "observed",
                        "score": 2,
                        "confidence": "high",
                        "summary": "Есть модернизация и инвестиционный сигнал.",
                        "evidence_refs": ["src_1"],
                    },
                    {
                        "signal_code": "S3",
                        "status": "unclear",
                        "score": 1,
                        "confidence": "low",
                        "summary": "Цифровая диагностика требует проверки.",
                        "evidence_refs": ["src_1"],
                    },
                ],
                "review_flags": ["digitalization_signal_requires_check"],
            }
        ],
        "provider_metadata": {
            "provider": "recorded",
            "model": "recorded-model",
            "web_mode": "recorded",
        },
    }


def test_live_mini_radar_dry_run_plan_does_not_create_candidates(tmp_path: Path) -> None:
    output_path = tmp_path / "live_plan.json"

    artifact = generate_live_mini_icp_radar_plan(output_path=output_path)

    assert output_path.exists()
    assert artifact["artifact_type"] == "icp_radar_live_search_plan"
    assert artifact["radar"]["radar_id"] == "toir-quick-live"
    assert len(artifact["search_plan"]["queries"]) == 3
    assert "candidates" not in artifact


def test_openrouter_provider_refuses_live_without_key(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    provider = OpenRouterWebSearchProvider(env_path=tmp_path / ".env")

    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
        provider.run_search_plan(
            radar=build_live_mini_radar_definition(),
            search_plan=build_live_mini_radar_search_plan(),
        )


def test_openrouter_provider_prefers_local_env_file_over_ambient_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join([
            "OPENROUTER_API_KEY=sk-or-v1-local",
            "OPENROUTER_MODEL=local/model",
            "OPENROUTER_WEB_MODE=plugin_web",
        ]),
        encoding="utf-8",
    )
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-stale")
    monkeypatch.setenv("OPENROUTER_MODEL", "ambient/model")
    monkeypatch.setenv("OPENROUTER_WEB_MODE", "server_tools")

    provider = OpenRouterWebSearchProvider(env_path=env_file)

    assert provider.model == "local/model"
    assert provider.web_mode == "plugin_web"
    assert provider._api_key == "sk-or-v1-local"


def test_openrouter_request_builder_supports_web_modes() -> None:
    radar = build_live_mini_radar_definition()
    plan = build_live_mini_radar_search_plan(radar)

    server_tools = build_openrouter_request(radar=radar, search_plan=plan, model="test/model", web_mode="server_tools")
    plugin_web = build_openrouter_request(radar=radar, search_plan=plan, model="test/model", web_mode="plugin_web")
    model_native = build_openrouter_request(radar=radar, search_plan=plan, model="test/model", web_mode="model_native")

    assert server_tools["tools"][0]["type"] == "openrouter:web_search"
    assert plugin_web["plugins"][0]["id"] == "web"
    assert "tools" not in model_native
    assert "plugins" not in model_native
    assert model_native["metadata"]["web_mode"] == "model_native"


def test_recorded_response_normalizes_sources_candidates_and_scores() -> None:
    artifact = build_live_mini_radar_artifact(
        provider=RecordedWebSearchProvider(recorded_provider_payload()),
        live=False,
    )

    assert artifact["artifact_type"] == "icp_radar_live_run"
    assert artifact["artifact_version"] == "0.6.3.4"
    assert artifact["radar"]["radar_id"] == "toir-quick-live"
    assert artifact["run_metadata"]["runtime"] == "recorded"
    assert len(artifact["sources"]) == 1
    assert artifact["candidates"][0]["legal_name"] == "ПАО «Нижнекамскнефтехим»"
    assert artifact["candidates"][0]["score"]["fit_score"] == 2
    assert artifact["candidates"][0]["score"]["intent_score"] == 3
    assert artifact["candidates"][0]["score"]["tier"] == "Tier 1"
    assert "signal_requires_human_review" in artifact["candidates"][0]["review_flags"]
    qualification = artifact["candidates"][0]["qualification"][0]
    assert qualification["operator"] == "AND"
    assert qualification["requirement_level"] == "required"
    assert qualification["final_assessment"] == "matches"
    assert qualification["source_usages"][0]["source_origin"] == "additional"
    assert qualification["source_usages"][0]["trust_policy"] == "trusted"
    assert qualification["evidence_findings"][0]["source_ref"] == "src_1"
    assert qualification["evidence_findings"][0]["excerpt_type"] == "quote"
    assert qualification["evidence_findings"][0]["excerpt"]
    assert qualification["requirement_evaluation"]["satisfied"] is True
    fallback_qualification = artifact["candidates"][0]["qualification"][1]
    assert fallback_qualification["evidence_findings"][0]["excerpt_type"] == "not_available"
    signal = artifact["candidates"][0]["signals"][0]
    assert signal["source_usages"][0]["source_ref"] == "src_1"
    assert signal["evidence_findings"][0]["source_ref"] == "src_1"
    assert signal["evidence_findings"][0]["excerpt_type"] == "quote"
    assert signal["evidence_findings"][0]["why_score_applies"]
    assert signal["score_evaluation"]["applied_score"] == 1
    fallback_signal = artifact["candidates"][0]["signals"][1]
    assert fallback_signal["evidence_findings"][0]["excerpt_type"] == "not_available"
    assert fallback_signal["score_evaluation"]["scale"] == "0-2"
    assert artifact["contract_validation"] == []


def test_openrouter_response_parser_handles_json_content_and_annotations() -> None:
    payload = {
        "id": "response-1",
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "sources": [
                            {
                                "evidence_ref": "src_a",
                                "title": "Source A",
                                "url": "https://example.test/a",
                                "snippet": "Snippet A",
                            }
                        ],
                        "candidates": [{"legal_name": "Candidate A"}],
                    }),
                    "annotations": [
                        {
                            "url_citation": {
                                "url": "https://example.test/b",
                                "title": "Source B",
                                "content": "Snippet B",
                            }
                        }
                    ],
                }
            }
        ],
        "usage": {"prompt_tokens": 10},
    }

    result = normalize_openrouter_response(
        payload,
        fallback_metadata={"provider": "openrouter", "model": "test/model", "web_mode": "server_tools"},
    )

    assert [source.evidence_ref for source in result.sources] == ["src_a", "citation_2"]
    assert result.candidate_observations == [{"legal_name": "Candidate A"}]
    assert result.provider_metadata["response_id"] == "response-1"


def test_unverified_live_sources_do_not_support_candidates(monkeypatch: pytest.MonkeyPatch) -> None:
    result = WebSearchProviderResult(
        sources=[
            {
                "evidence_ref": "bad_src",
                "title": "Unverified source",
                "url": "https://example.invalid/missing",
                "snippet": "Model-supplied snippet",
            }
        ],
        candidate_observations=[
            {
                "legal_name": "Candidate with fake source",
                "qualification": [{"criterion_code": "Q1", "evidence_refs": ["bad_src"]}],
                "signals": [{"signal_code": "S1", "evidence_refs": ["bad_src"]}],
            }
        ],
    )
    monkeypatch.setattr("power_web_os.live_icp_radar._source_url_is_reachable", lambda _: False)

    filtered = _filter_result_to_verified_sources(result)

    assert filtered.sources == []
    assert filtered.candidate_observations == []
    assert filtered.provider_metadata["discarded_source_count"] == 1


def test_live_run_artifact_does_not_contain_secret_markers() -> None:
    artifact = build_live_mini_radar_artifact(
        provider=RecordedWebSearchProvider(recorded_provider_payload()),
        live=False,
    )
    serialized = json.dumps(artifact, ensure_ascii=False)

    for forbidden in ["OPENROUTER_API_KEY", "Authorization", "Bearer", "sk-or-"]:
        assert forbidden not in serialized


@pytest.mark.skipif(not FRAMEWORK_AVAILABLE, reason="langgraph-dai is optional")
def test_live_workflow_reports_langgraph_runtime_when_available() -> None:
    workflow = LiveICPRadarRunWorkflow(provider=RecordedWebSearchProvider(WebSearchProviderResult()))
    result = workflow.invoke(LiveICPRadarRunState(radar=build_live_mini_radar_definition()))

    assert result.workflow_metadata["framework_available"] is True
