from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

import power_web_os.live_icp_radar as live_facade
from power_web_os.application.live_radar_service import LiveRadarRunService
from power_web_os.application.live_radar_definition_runtime import active_definition_to_live_radar_payload
from power_web_os.application.live_radar_contracts import (
    RadarDiscoveryPlan,
    RadarDiscoveryPlanStep,
    RadarDiscoveryPlanValidationResult,
    RadarDiscoverySourcePolicyDecision,
    RadarExecutionPlan,
    RadarExecutionTask,
    RadarSourceEvidence,
)
from power_web_os.application.live_radar_discovery_planning import (
    DeterministicRadarDiscoveryPlanner,
    RadarDiscoveryPlanValidator,
    build_discovery_planning_input,
    discovery_plan_to_execution_plan,
)
from power_web_os.application.live_radar_plan_acceptance import RadarDiscoveryPlanAcceptanceService
from power_web_os.application.live_radar_execution_plan import compile_radar_execution_plan, execution_task_to_search_plan
from power_web_os.application.live_radar_execution_budget import (
    RadarExecutionBudget,
    RadarExecutionBudgetSettings,
    budget_key,
)
from power_web_os.application.live_radar_entity_resolution import RadarEntityResolutionService
from power_web_os.application.live_radar_normalization import normalize_live_candidate
from power_web_os.application.live_radar_extraction_contract import validate_and_repair_extraction_payload
from power_web_os.application.live_radar_retrieval_plan import retrieval_plan_from_execution_plan, retrieval_plan_to_search_plan
from power_web_os.application.live_radar_staged_execution import run_staged_radar_execution
from power_web_os.application.live_radar_web_retrieval import (
    RadarWebRetrievalResult,
    RadarRetrievedSource,
    RecordedRadarWebRetrievalProvider,
    retrieval_request_from_search_plan,
)
from power_web_os.application.radar_source_providers import RadarSourceRegistry, SourceRegistryWebSearchProvider
from power_web_os.application.radar_records import RadarDefinitionRecord
from power_web_os.demo import build_icp_radar_catalog_from_workbook, generate_live_mini_icp_radar_plan
from power_web_os.integrations.dadata_provider import RecordedDaDataCompanyRegistryProvider
from power_web_os.integrations import live_radar_openrouter
from power_web_os.integrations.live_radar_source_verification import SourceReachabilityResult, verify_sources
from power_web_os.integrations.openrouter_retrieval import retrieval_result_from_openrouter_response
from power_web_os.live_icp_radar import (
    FRAMEWORK_AVAILABLE,
    LiveICPRadarRunState,
    LiveICPRadarRunWorkflow,
    OpenRouterWebSearchProvider,
    OpenRouterDiscoveryPlanner,
    RecordedWebSearchProvider,
    WebSearchProviderResult,
    build_live_mini_radar_artifact,
    build_live_mini_radar_definition,
    build_live_mini_radar_search_plan,
    build_openrouter_request,
    build_openrouter_discovery_planner_request,
    normalize_openrouter_response,
    _filter_result_to_verified_sources,
)
from power_web_os.integrations.openrouter_discovery_planner import _plan_from_response
from power_web_os.workflows import live_icp_radar_workflow


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


def test_live_radar_facade_points_to_extracted_backend_layers() -> None:
    assert live_facade.OpenRouterWebSearchProvider is live_radar_openrouter.OpenRouterWebSearchProvider
    assert live_facade.LiveICPRadarRunWorkflow is live_icp_radar_workflow.LiveICPRadarRunWorkflow
    assert LiveRadarRunService.__module__ == "power_web_os.application.live_radar_service"


def test_live_mini_radar_dry_run_plan_does_not_create_candidates(tmp_path: Path) -> None:
    output_path = tmp_path / "live_plan.json"

    artifact = generate_live_mini_icp_radar_plan(output_path=output_path)

    assert output_path.exists()
    assert artifact["artifact_type"] == "icp_radar_live_search_plan"
    assert artifact["radar"]["radar_id"] == "toir-quick-live"
    assert len(artifact["search_plan"]["queries"]) == 6
    assert [query["stage"] for query in artifact["search_plan"]["queries"][:2]] == [
        "qualification_discovery",
        "qualification_gate",
    ]
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
            "OPENROUTER_MODEL=local/model",
            "OPENROUTER_WEB_MODE=plugin_web",
        ]),
        encoding="utf-8",
    )
    monkeypatch.setenv("OPENROUTER_MODEL", "ambient/model")
    monkeypatch.setenv("OPENROUTER_WEB_MODE", "server_tools")

    provider = OpenRouterWebSearchProvider(env_path=env_file)

    assert provider.model == "local/model"
    assert provider.web_mode == "plugin_web"


def test_openrouter_provider_selects_perplexity_retrieval_engine_from_env(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join([
            "OPENROUTER_API_KEY=test-key",
            "POWER_WEB_OS_RADAR_WEB_RETRIEVAL_PROVIDER=openrouter_perplexity",
        ]),
        encoding="utf-8",
    )

    provider = OpenRouterWebSearchProvider(env_path=env_file)

    assert provider.retrieval_provider == "openrouter_perplexity"
    assert provider.web_search_engine == "perplexity"


def test_openrouter_request_builder_supports_web_modes() -> None:
    radar = build_live_mini_radar_definition()
    plan = build_live_mini_radar_search_plan(radar)

    server_tools = build_openrouter_request(
        radar=radar,
        search_plan=plan,
        model="test/model",
        web_mode="server_tools",
        web_search_engine="perplexity",
    )
    plugin_web = build_openrouter_request(radar=radar, search_plan=plan, model="test/model", web_mode="plugin_web")
    model_native = build_openrouter_request(radar=radar, search_plan=plan, model="test/model", web_mode="model_native")

    assert server_tools["tools"][0]["type"] == "openrouter:web_search"
    assert server_tools["tools"][0]["parameters"]["engine"] == "perplexity"
    assert plugin_web["plugins"][0]["id"] == "web"
    assert "tools" not in model_native
    assert "plugins" not in model_native
    assert model_native["metadata"]["web_mode"] == "model_native"


def test_openrouter_request_builder_scopes_prompt_to_current_task() -> None:
    radar = build_live_mini_radar_definition()
    plan = compile_radar_execution_plan(radar)
    qualification_task = next(task for task in plan.tasks if task.stage == "qualification_discovery")
    signal_task = next(task for task in plan.tasks if task.stage == "signal_search")

    qualification_request = build_openrouter_request(
        radar=radar,
        search_plan=execution_task_to_search_plan(qualification_task, radar_id=plan.radar_id),
        model="test/model",
        web_mode="model_native",
    )
    signal_request = build_openrouter_request(
        radar=radar,
        search_plan=execution_task_to_search_plan(signal_task, radar_id=plan.radar_id),
        model="test/model",
        web_mode="model_native",
    )

    qualification_prompt = json.loads(qualification_request["messages"][1]["content"])
    signal_prompt = json.loads(signal_request["messages"][1]["content"])

    assert set(qualification_prompt) == {"task_card", "response_contract", "constraints"}
    assert qualification_prompt["task_card"]["stage"] == "qualification_discovery"
    assert qualification_prompt["task_card"]["subject_id"] == qualification_task.subject_id
    assert qualification_prompt["response_contract"]["schema_id"] == "qualification_finding_v1"
    assert "intent_signals" not in json.dumps(qualification_prompt)
    assert "search_plan" not in qualification_prompt
    assert "radar" not in qualification_prompt
    assert signal_prompt["task_card"]["stage"] == "signal_search"
    assert signal_prompt["task_card"]["subject_id"] == signal_task.subject_id
    assert signal_prompt["response_contract"]["schema_id"] == "signal_finding_v1"
    assert "qualification_criteria" not in json.dumps(signal_prompt)
    assert "search_plan" not in signal_prompt
    assert "radar" not in signal_prompt


def test_execution_plan_projects_to_retrieval_plan_and_legacy_search_plan() -> None:
    radar = build_live_mini_radar_definition()
    plan = compile_radar_execution_plan(radar)

    retrieval_plan = retrieval_plan_from_execution_plan(plan)
    legacy_plan = retrieval_plan_to_search_plan(retrieval_plan)

    assert retrieval_plan.radar_id == plan.radar_id
    assert [task.task_id for task in retrieval_plan.tasks] == [task.task_id for task in plan.tasks]
    signal_task = next(task for task in retrieval_plan.tasks if task.stage == "signal_search")
    assert signal_task.response_contract.schema_id == "signal_finding_v1"
    assert signal_task.expected_evidence == [signal_task.subject_id]
    assert legacy_plan.model_dump() == build_live_mini_radar_search_plan(radar).model_dump()


def test_web_retrieval_contracts_preserve_ranked_source_material() -> None:
    plan = build_live_mini_radar_search_plan(build_live_mini_radar_definition())
    request = retrieval_request_from_search_plan(
        search_plan=plan,
        provider_id="openrouter_perplexity",
        engine="perplexity",
    )
    result = RadarWebRetrievalResult(
        provider_id="openrouter_perplexity",
        engine="perplexity",
        query=request.query,
        retrieved_sources=[
            RadarRetrievedSource(
                source_ref="retrieved_1",
                title="Result",
                url="https://example.test/result",
                snippet="Perplexity-shaped snippet",
                rank=1,
                provider_id="openrouter_perplexity",
                engine="perplexity",
            )
        ],
    )
    provider = RecordedRadarWebRetrievalProvider(result)

    retrieved = provider.retrieve(request=request)

    assert provider.requests == [request]
    assert retrieved.retrieved_sources[0].url == "https://example.test/result"
    assert retrieved.retrieved_sources[0].rank == 1


def test_openrouter_response_maps_annotations_to_retrieval_result() -> None:
    payload = {
        "choices": [{
            "message": {
                "annotations": [{
                    "url_citation": {
                        "title": "Perplexity source",
                        "url": "https://example.test/perplexity",
                        "content": "Ranked source snippet.",
                    }
                }]
            }
        }]
    }

    result = retrieval_result_from_openrouter_response(
        payload,
        provider_id="openrouter_perplexity",
        engine="perplexity",
        query="test query",
    )

    assert result.provider_id == "openrouter_perplexity"
    assert result.engine == "perplexity"
    assert result.retrieved_sources[0].title == "Perplexity source"
    assert result.source_outcomes[0].outcome == "retrieved"


def test_source_registry_selects_dadata_company_registry_source() -> None:
    radar = {
        "radar_id": "generic-radar",
        "global_search_policy": {
            "sources": [{
                "source_id": "dadata_registry",
                "source_type": "company_registry",
                "provider_id": "dadata",
                "label": "DaData",
                "reference": "company_registry:dadata",
            }]
        },
    }
    task = RadarExecutionTask(
        task_id="discover-q1",
        stage="qualification_discovery",
        subject_type="qualification",
        subject_id="Q1",
        rule_snapshot="Find source-backed legal entities.",
        query="Candidate A",
        purpose="Discover companies.",
        source_ids=["dadata_registry"],
    )
    provider = RecordedDaDataCompanyRegistryProvider(fixtures=[{
        "source_ref": "dadata_candidate_a",
        "legal_name": "Candidate A",
        "inn": "7700000000",
        "status": "ACTIVE",
        "address": "Moscow",
    }])

    result = RadarSourceRegistry(company_registry_providers={"dadata": provider}).lookup_for_task(radar=radar, task=task)

    assert result.sources[0].source_type == "company_registry"
    assert result.sources[0].evidence_ref == "dadata_candidate_a"
    assert result.candidate_observations[0]["legal_name"] == "Candidate A"
    assert result.candidate_observations[0]["entity_type"] == "legal_entity"
    assert result.candidate_observations[0]["entity_resolution_status"] == "resolved"
    assert result.candidate_observations[0]["inn"] == "7700000000"
    assert result.candidate_observations[0]["qualification"][0]["criterion_code"] == "Q1"
    assert result.provider_metadata["source_provider_outcomes"][0]["provider_id"] == "dadata"


def test_source_registry_wrapper_does_not_use_dadata_for_signal_search() -> None:
    radar = {
        "radar_id": "generic-radar",
        "global_search_policy": {
            "sources": [{
                "source_id": "dadata_registry",
                "source_type": "company_registry",
                "provider_id": "dadata",
            }]
        },
    }
    provider = RecordedDaDataCompanyRegistryProvider(fixtures=[{"legal_name": "Candidate A"}])
    web_provider = RecordedWebSearchProvider(WebSearchProviderResult())
    wrapped = SourceRegistryWebSearchProvider(
        web_provider,
        RadarSourceRegistry(company_registry_providers={"dadata": provider}),
    )
    signal_task = RadarExecutionTask(
        task_id="signal-s1",
        stage="signal_search",
        subject_type="signal",
        subject_id="S1",
        query="Candidate A signal",
        purpose="Search signal.",
        source_ids=["dadata_registry"],
        candidate_scope=["Candidate A"],
    )

    wrapped.run_search_plan(radar=radar, search_plan=execution_task_to_search_plan(signal_task, radar_id="generic-radar"))

    assert provider.requests == []
    assert len(web_provider.calls) == 1


def test_execution_budget_keys_are_candidate_scoped_for_gate_and_signal_tasks() -> None:
    gate_task = RadarExecutionTask(
        task_id="gate-q2",
        stage="qualification_gate",
        subject_type="qualification",
        subject_id="Q2",
        query="Check candidate.",
        purpose="Check one candidate.",
        candidate_scope=["Candidate A"],
    )
    signal_task = RadarExecutionTask(
        task_id="signal-s1",
        stage="signal_search",
        subject_type="signal",
        subject_id="S1",
        query="Search signal.",
        purpose="Search one candidate signal.",
        candidate_scope=["Candidate A"],
    )
    budget = RadarExecutionBudget(RadarExecutionBudgetSettings(max_signal_tasks_per_candidate_signal=1))

    assert budget_key(gate_task) == "gate:Q2:Candidate A"
    assert budget_key(signal_task) == "signal:S1:Candidate A"
    assert budget.reserve(signal_task)
    assert not budget.reserve(signal_task)
    assert budget.exhaustion_events[0]["state"] == "not_searched_budget_limited"


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


def test_source_verification_modes_record_reachability_states() -> None:
    sources = [
        RadarSourceEvidence(evidence_ref="ok", title="Ok", url="https://example.test/ok", snippet="Ok source"),
        RadarSourceEvidence(evidence_ref="blocked", title="Blocked", url="https://example.test/blocked", snippet="Blocked source"),
        RadarSourceEvidence(evidence_ref="timeout", title="Timeout", url="https://example.test/timeout", snippet="Timeout source"),
    ]

    def fake_check(url: str) -> SourceReachabilityResult:
        if url.endswith("/ok"):
            return SourceReachabilityResult(state="reachable", reason="http_200", status_code=200)
        if url.endswith("/blocked"):
            return SourceReachabilityResult(state="blocked", reason="http_403", status_code=403)
        return SourceReachabilityResult(state="timeout", reason="timeout", status_code=None)

    verified = verify_sources(sources, mode="soft", reachability_check=fake_check)
    unchecked = verify_sources(sources, mode="off", reachability_check=lambda _: pytest.fail("off mode must not verify URLs"))

    assert [source.verification_state for source in verified] == ["reachable", "blocked", "timeout"]
    assert verified[1].verification_mode == "soft"
    assert verified[1].verification_status_code == 403
    assert {source.verification_state for source in unchecked} == {"not_checked"}


def test_soft_risky_source_keeps_candidate_but_downgrades_confidence() -> None:
    radar = build_live_mini_radar_definition()
    risky_source = RadarSourceEvidence(
        evidence_ref="risky_src",
        title="Risky source",
        url="https://example.invalid/source",
        snippet="Candidate belongs to the target universe and has a relevant signal.",
        verification_state="unverified_url",
        verification_mode="soft",
        verification_reason="http_404",
        verification_status_code=404,
    )

    candidate = normalize_live_candidate(
        {
            "legal_name": "Risky Evidence Candidate",
            "qualification": [
                {"criterion_code": "Q1", "status": "confirmed", "confidence": "high", "evidence_refs": ["risky_src"]},
                {"criterion_code": "Q2", "status": "confirmed", "confidence": "high", "evidence_refs": ["risky_src"]},
            ],
            "signals": [
                {"signal_code": "S1", "status": "observed", "score": 2, "confidence": "high", "evidence_refs": ["risky_src"]}
            ],
        },
        radar=radar,
        sources=[risky_source],
    )

    assert candidate.qualification[0].status == "weak"
    assert candidate.qualification[0].confidence == "low"
    assert candidate.qualification[0].confidence_policy == "hitl_required"
    assert candidate.signals[0].status == "unclear"
    assert candidate.signals[0].score == 0
    assert candidate.score.fit_score == 0
    assert "source_verification_review" in candidate.review_flags


def test_useful_result_budget_retries_weak_discovery_result() -> None:
    radar = build_live_mini_radar_definition()
    provider = _WeakThenUsefulProvider()
    execution_plan = RadarExecutionPlan(
        radar_id="toir-quick-live",
        tasks=[
            RadarExecutionTask(
                task_id="discover-q1",
                stage="qualification_discovery",
                subject_type="qualification",
                subject_id="Q1",
                query="Find candidate universe.",
                purpose="Discovery",
                expected_evidence=["candidate identity", "qualification evidence"],
            )
        ],
    )

    result, events, execution_results = run_staged_radar_execution(
        radar=radar,
        execution_plan=execution_plan,
        provider=provider,
        min_useful_sources_per_discovery_task=1,
        min_candidates_per_discovery_task=1,
        max_discovery_retries_per_task=1,
    )

    assert len(provider.calls) == 2
    assert provider.calls[1].queries[0].query.startswith("Find candidate universe.\nRetry 1")
    assert len(result.candidate_observations) == 2
    assert execution_results["retrieval_plan"]["tasks"][0]["task_id"] == "discover-q1"
    assert execution_results["retrieval_plan"]["tasks"][0]["response_contract"]["schema_id"] == "qualification_finding_v1"
    assert execution_results["useful_result_retry_records"][0]["reason"] == "verification_limited"
    assert execution_results["useful_result_warnings"]
    assert "validation_warning" in [event.event_type for event in events]


def test_extraction_contract_repairs_single_candidate_object_and_reconciles_refs() -> None:
    repair = validate_and_repair_extraction_payload({
        "sources": [
            {
                "evidence_ref": "src_1",
                "title": "Candidate A source",
                "url": "https://example.test/a",
                "snippet": "Candidate A belongs.",
            }
        ],
        "candidates": {
            "legal_name": "Candidate A",
            "evidence_refs": ["https://example.test/a"],
            "qualification": [{"criterion_code": "Q1", "status": "confirmed", "evidence_refs": ["https://example.test/a"]}],
        },
    })

    assert repair.valid
    assert repair.state == "extraction_repair_needed"
    assert repair.payload["candidates"][0]["evidence_refs"] == ["src_1"]
    assert repair.payload["candidates"][0]["qualification"][0]["evidence_refs"] == ["src_1"]
    assert {issue.code for issue in repair.issues} == {"extraction_repair_needed"}


def test_extraction_contract_reports_unresolved_evidence_refs() -> None:
    repair = validate_and_repair_extraction_payload({
        "sources": [{"evidence_ref": "src_1", "title": "A", "url": "https://example.test/a", "snippet": "A"}],
        "candidates": [{"legal_name": "Candidate A", "signals": [{"signal_code": "S1", "evidence_refs": [42, "missing_src"]}]}],
    })

    assert not repair.valid
    assert repair.state == "evidence_linking_failed"
    assert {issue.code for issue in repair.issues} == {"evidence_linking_failed"}


def test_openrouter_normalization_records_extraction_repair_metadata() -> None:
    payload = {
        "id": "resp_1",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": json.dumps({
                        "sources": [{"evidence_ref": "src_1", "title": "A", "url": "https://example.test/a", "snippet": "A"}],
                        "candidates": {"legal_name": "Candidate A", "evidence_refs": ["src_1"]},
                    }),
                    "annotations": [],
                }
            }
        ],
    }

    result = normalize_openrouter_response(payload, fallback_metadata={"provider": "openrouter"})

    assert result.candidate_observations[0]["legal_name"] == "Candidate A"
    assert result.provider_metadata["extraction_validation_results"][0]["state"] == "extraction_repair_needed"
    assert result.provider_metadata["extraction_repair_results"][0]["type"] == "object_wrapped_as_list"


def test_staged_execution_exposes_extraction_schema_failures_in_execution_results() -> None:
    radar = build_live_mini_radar_definition()
    execution_plan = RadarExecutionPlan(
        radar_id="toir-quick-live",
        tasks=[
            RadarExecutionTask(
                task_id="discover-q1",
                stage="qualification_discovery",
                subject_type="qualification",
                subject_id="Q1",
                query="Find candidate universe.",
                purpose="Discovery",
                expected_evidence=["candidate identity"],
            )
        ],
    )

    result, events, execution_results = run_staged_radar_execution(
        radar=radar,
        execution_plan=execution_plan,
        provider=_SchemaInvalidProvider(),
    )

    assert result.candidate_observations == []
    assert execution_results["extraction_contract_state"] == "extraction_schema_invalid"
    assert execution_results["extraction_validation_issues"][0]["code"] == "extraction_schema_invalid"
    assert execution_results["retrieved_sources"][0]["url"] == "https://example.test/retrieved"
    assert any("extraction_schema_invalid" in warning for warning in execution_results["coverage_warnings"])
    assert any(event.node_name == "extraction_contract_gate" for event in events)


def test_live_radar_service_executes_explicit_pipeline_phases() -> None:
    payload = recorded_provider_payload()
    provider = RecordedWebSearchProvider(payload)
    service = LiveRadarRunService(provider)
    state = LiveICPRadarRunState(radar=build_live_mini_radar_definition(), live=False)

    planned = service.build_search_plan(state)
    collected = service.run_web_search(planned)
    normalized = service.normalize_sources(collected)
    extracted = service.extract_candidates(normalized)
    evaluated = service.evaluate_candidates(extracted)
    validated = service.validate_artifact(evaluated)
    shaped = service.shape_artifact(
        state=validated,
        node_name="shape_artifact",
        runtime_mode="local_fallback",
        framework_available=False,
    )

    assert planned.search_plan is not None
    assert len(planned.search_plan["queries"]) == 6
    assert planned.search_plan["queries"][0]["source_scope"] == "global"
    assert planned.search_plan["queries"][0]["source_ids"] == ["sibur.ru"]
    assert planned.execution_plan is not None
    assert len(collected.candidate_observations) == 1
    assert [call.queries[0].stage for call in provider.calls] == [
        "qualification_discovery",
        "qualification_gate",
        "coverage_check",
        "signal_search",
        "signal_search",
        "signal_search",
    ]
    assert len(normalized.sources) == 1
    assert extracted.candidates[0]["legal_name"] == payload["candidate_observations"][0]["legal_name"]
    assert evaluated.candidates[0]["score"]["tier"] == "Tier 1"
    assert validated.contract_validation == []
    assert shaped.artifact is not None
    assert shaped.artifact["artifact_type"] == "icp_radar_live_run"
    event_types = [event["event_type"] for event in shaped.workflow_metadata["pipeline_events"]]
    assert event_types[:4] == ["discovery_plan_requested", "discovery_plan_created", "criterion_roles_inferred", "discovery_plan_validated"]
    assert "plan_created" in event_types
    assert "qualification_discovery_planned" in event_types
    assert "qualification_gate_applied" in event_types
    assert "candidate_universe_discovered" in event_types
    assert "signal_search_planned" in event_types
    assert "source_collected" in event_types
    assert "candidate_extracted" in event_types
    assert "signal_evaluated" in event_types
    assert "self_check_completed" in event_types


def test_discovery_planning_input_and_validator_apply_source_policy() -> None:
    radar = {
        "radar_id": "generic-source-policy",
        "name": "Generic source policy radar",
        "qualification_criteria": [
            {
                "code": "Q1",
                "label": "Revenue threshold",
                "rule": "Revenue exceeds configured threshold.",
                "source_policy": {
                    "use_global_search_policy": True,
                    "allow_additional_sources": False,
                    "source_ids": ["registry"],
                },
            }
        ],
        "global_search_policy": {
            "sources": [{"source_id": "registry", "label": "Company registry"}],
            "allow_system_sources": True,
        },
    }
    planning_input = build_discovery_planning_input(
        radar=radar,
        task_context={"requester": "test", "source": "unit"},
        live=True,
        provider_metadata={"model": "planner/model", "web_mode": "none"},
    )
    invalid_plan = RadarDiscoveryPlan(
        plan_summary="Invalid additional-source plan.",
        steps=[
            RadarDiscoveryPlanStep(
                step_id="discover-q1",
                stage="candidate_universe_discovery",
                subject_rule_ids=["Q1"],
                source_scope="additional",
                query="find companies",
                purpose="Use open web even though policy disables it.",
                expected_evidence=["revenue"],
                acceptance_criteria=["source-backed revenue"],
            )
        ],
        source_policy_decisions=[],
        coverage_hypotheses=[],
    )

    validation = RadarDiscoveryPlanValidator().validate(planning_input=planning_input, plan=invalid_plan)

    assert planning_input.requester == "test"
    assert planning_input.global_search_policy["sources"][0]["source_id"] == "registry"
    assert validation.accepted is False
    assert any("additional sources are disabled" in error for error in validation.errors)
    assert any("Global source registry" in error for error in validation.errors)


def test_discovery_plan_acceptance_repairs_global_source_id_marked_local() -> None:
    radar = _generic_definition(
        radar_id="registry-policy",
        rules=[("Q1", "Registry criterion", "Find companies through a configured registry.")],
        global_sources=[],
    )
    radar["global_search_policy"] = {"sources": [{"source_id": "registry", "label": "Registry"}], "allow_system_sources": True}
    planning_input = build_discovery_planning_input(radar=radar, task_context={}, live=True, provider_metadata={})
    plan = RadarDiscoveryPlan(
        plan_summary="Invalid source scope.",
        steps=[
            RadarDiscoveryPlanStep(
                step_id="discover-q1",
                stage="candidate_universe_discovery",
                subject_rule_ids=["Q1"],
                source_scope="local",
                source_ids=["registry"],
                query="Find companies.",
                purpose="Wrongly mark global source as local.",
                expected_evidence=["Q1"],
                acceptance_criteria=["Q1"],
            ),
            RadarDiscoveryPlanStep(
                step_id="coverage-q1",
                stage="coverage_check",
                subject_rule_ids=[],
                source_scope="additional",
                query="Check coverage.",
                purpose="Check gaps.",
                expected_evidence=["candidate_universe_gaps"],
                acceptance_criteria=["Coverage checked."],
                depends_on=["discover-q1"],
            ),
        ],
        source_policy_decisions=[
            RadarDiscoverySourcePolicyDecision(
                source_id="registry",
                source_label="Registry",
                decision="selected",
                reason="Registry is configured.",
                rule_ids=["Q1"],
            )
        ],
    )

    acceptance = RadarDiscoveryPlanAcceptanceService().accept(planning_input=planning_input, plan=plan)
    validation = acceptance.validation

    assert validation.accepted
    assert acceptance.accepted_plan.steps[0].source_scope == "global"
    assert acceptance.accepted_plan.steps[0].source_base == "global_configured"
    assert acceptance.accepted_plan.steps[0].application_scope == "rule_scope"
    assert any(correction["type"] == "source_scope_corrected" for correction in validation.corrections)


def test_discovery_plan_acceptance_splits_multi_rule_strategic_step() -> None:
    radar = _generic_definition(
        radar_id="multi-rule-strategy",
        rules=[
            ("Q1", "Holding contour", "Find legal entities in the holding."),
            ("Q2", "Industrial profile", "Filter for industrial assets."),
        ],
        global_sources=[{"source_id": "official-site", "label": "Official site"}],
    )
    planning_input = build_discovery_planning_input(radar=radar, task_context={}, live=True, provider_metadata={})
    plan = RadarDiscoveryPlan(
        plan_summary="Strategic multi-rule plan.",
        steps=[
            RadarDiscoveryPlanStep(
                step_id="discover-contour-and-profile",
                stage="candidate_universe_discovery",
                subject_rule_ids=["Q1", "Q2"],
                source_scope="global",
                source_ids=["official-site"],
                query="Find holding legal entities and note industrial profile.",
                purpose="Shared search strategy before executable checks.",
                expected_evidence=["Q1", "Q2"],
                acceptance_criteria=["Q1", "Q2"],
            ),
            RadarDiscoveryPlanStep(
                step_id="coverage-q2",
                stage="coverage_check",
                subject_rule_ids=[],
                source_scope="additional",
                query="Check coverage.",
                purpose="Check gaps.",
                expected_evidence=["candidate_universe_gaps"],
                acceptance_criteria=["Coverage checked."],
                depends_on=["discover-contour-and-profile"],
            ),
        ],
        source_policy_decisions=[
            RadarDiscoverySourcePolicyDecision(
                source_id="official-site",
                source_label="Official site",
                decision="selected",
                reason="Official site is configured and relevant.",
                rule_ids=["Q1", "Q2"],
            )
        ],
    )

    acceptance = RadarDiscoveryPlanAcceptanceService().accept(planning_input=planning_input, plan=plan)
    execution_plan = discovery_plan_to_execution_plan(radar=radar, plan=acceptance.accepted_plan)

    assert acceptance.validation.accepted
    assert [step.subject_rule_ids for step in acceptance.accepted_plan.steps[:2]] == [["Q1"], ["Q2"]]
    assert acceptance.accepted_plan.steps[1].stage == "qualification_gate"
    assert acceptance.accepted_plan.steps[2].depends_on == [acceptance.accepted_plan.steps[1].step_id]
    assert [task.stage for task in execution_plan.tasks[:3]] == ["qualification_discovery", "qualification_gate", "coverage_check"]
    assert any(correction["type"] == "multi_rule_step_split" for correction in acceptance.corrections)


def test_source_obligation_rejects_required_coverage_source_skipped_by_planner() -> None:
    radar = _generic_definition(
        radar_id="required-coverage",
        rules=[("Q1", "Holding contour", "Find legal entities in the holding.")],
        global_sources=[
            {
                "source_id": "open-web",
                "label": "Open web",
                "source_type": "search_engine",
                "usage_obligation": "required_for_coverage",
            }
        ],
    )
    planning_input = build_discovery_planning_input(radar=radar, task_context={}, live=True, provider_metadata={})
    plan = RadarDiscoveryPlan(
        plan_summary="Skipped required coverage source.",
        steps=[
            RadarDiscoveryPlanStep(
                step_id="discover-q1",
                stage="candidate_universe_discovery",
                subject_rule_ids=["Q1"],
                source_scope="additional",
                query="Find candidates.",
                purpose="Discover candidates.",
                expected_evidence=["Q1"],
                acceptance_criteria=["Q1"],
            ),
            RadarDiscoveryPlanStep(
                step_id="coverage-q1",
                stage="coverage_check",
                subject_rule_ids=[],
                source_scope="additional",
                query="Check coverage.",
                purpose="Check gaps.",
                expected_evidence=["candidate_universe_gaps"],
                acceptance_criteria=["Coverage checked."],
                depends_on=["discover-q1"],
            ),
        ],
        source_policy_decisions=[
            RadarDiscoverySourcePolicyDecision(
                source_id="open-web",
                source_label="Open web",
                decision="skipped",
                reason="Planner preferred configured registry.",
                rule_ids=["Q1"],
            )
        ],
    )

    validation = RadarDiscoveryPlanAcceptanceService().accept(planning_input=planning_input, plan=plan).validation

    assert not validation.accepted
    assert any("Required source open-web cannot be skipped" in error for error in validation.errors)
    assert any("required_for_coverage source open-web" in error for error in validation.errors)


def test_source_obligation_allows_preferred_source_skipped_with_rationale() -> None:
    radar = _generic_definition(
        radar_id="preferred-source",
        rules=[("Q1", "Registry criterion", "Find companies through a registry.")],
        global_sources=[
            {
                "source_id": "official-site",
                "label": "Official site",
                "source_type": "url",
                "usage_obligation": "preferred",
            }
        ],
    )
    planning_input = build_discovery_planning_input(radar=radar, task_context={}, live=True, provider_metadata={})
    plan = RadarDiscoveryPlan(
        plan_summary="Preferred source skipped.",
        steps=[
            RadarDiscoveryPlanStep(
                step_id="discover-q1",
                stage="candidate_universe_discovery",
                subject_rule_ids=["Q1"],
                source_scope="additional",
                query="Find candidates.",
                purpose="Discover candidates.",
                expected_evidence=["Q1"],
                acceptance_criteria=["Q1"],
            ),
            RadarDiscoveryPlanStep(
                step_id="coverage-q1",
                stage="coverage_check",
                subject_rule_ids=[],
                source_scope="additional",
                query="Check coverage.",
                purpose="Check gaps.",
                expected_evidence=["candidate_universe_gaps"],
                acceptance_criteria=["Coverage checked."],
                depends_on=["discover-q1"],
            ),
        ],
        source_policy_decisions=[
            RadarDiscoverySourcePolicyDecision(
                source_id="official-site",
                source_label="Official site",
                decision="skipped",
                reason="The official site does not expose the needed registry facts.",
                rule_ids=["Q1"],
            )
        ],
    )

    validation = RadarDiscoveryPlanAcceptanceService().accept(planning_input=planning_input, plan=plan).validation

    assert validation.accepted
    assert any("Preferred source official-site was skipped" in warning for warning in validation.warnings)


def test_source_obligation_rejects_disabled_source_selection_and_early_fallback() -> None:
    radar = _generic_definition(
        radar_id="disabled-and-fallback",
        rules=[("Q1", "Registry criterion", "Find companies through a registry.")],
        global_sources=[
            {"source_id": "disabled-source", "label": "Disabled", "usage_obligation": "disabled"},
            {"source_id": "preferred-source", "label": "Preferred", "usage_obligation": "preferred"},
            {"source_id": "fallback-web", "label": "Fallback web", "usage_obligation": "fallback"},
        ],
    )
    planning_input = build_discovery_planning_input(radar=radar, task_context={}, live=True, provider_metadata={})
    plan = RadarDiscoveryPlan(
        plan_summary="Invalid disabled and fallback source use.",
        steps=[
            RadarDiscoveryPlanStep(
                step_id="discover-q1",
                stage="candidate_universe_discovery",
                subject_rule_ids=["Q1"],
                source_scope="global",
                source_ids=["disabled-source", "fallback-web"],
                query="Find candidates.",
                purpose="Discover candidates.",
                expected_evidence=["Q1"],
                acceptance_criteria=["Q1"],
            ),
            RadarDiscoveryPlanStep(
                step_id="coverage-q1",
                stage="coverage_check",
                subject_rule_ids=[],
                source_scope="additional",
                query="Check coverage.",
                purpose="Check gaps.",
                expected_evidence=["candidate_universe_gaps"],
                acceptance_criteria=["Coverage checked."],
                depends_on=["discover-q1"],
            ),
        ],
        source_policy_decisions=[
            RadarDiscoverySourcePolicyDecision(
                source_id="disabled-source",
                source_label="Disabled",
                decision="selected",
                reason="Invalidly selected.",
                rule_ids=["Q1"],
            ),
            RadarDiscoverySourcePolicyDecision(
                source_id="fallback-web",
                source_label="Fallback web",
                decision="selected",
                reason="Invalidly selected too early.",
                rule_ids=["Q1"],
            ),
            RadarDiscoverySourcePolicyDecision(
                source_id="preferred-source",
                source_label="Preferred",
                decision="skipped",
                reason="",
                rule_ids=["Q1"],
            ),
        ],
    )

    validation = RadarDiscoveryPlanAcceptanceService().accept(planning_input=planning_input, plan=plan).validation

    assert not validation.accepted
    assert any("Disabled source disabled-source" in error for error in validation.errors)
    assert any("Fallback source fallback-web" in error for error in validation.errors)


def test_discovery_plan_accepts_llm_nulls_for_optional_step_fields() -> None:
    plan = RadarDiscoveryPlan.model_validate({
        "plan_summary": "Plan with null optional fields.",
        "steps": [
            {
                "step_id": "discover",
                "stage": "candidate_universe_discovery",
                "subject_rule_ids": None,
                "source_scope": "global",
                "source_ids": None,
                "external_source_hints": None,
                "query": "Find candidates.",
                "purpose": "Build candidate universe.",
                "expected_evidence": None,
                "acceptance_criteria": None,
                "skip_rationale": None,
                "depends_on": None,
                "candidate_scope": None,
            }
        ],
    })

    step = plan.steps[0]
    assert step.skip_rationale == ""
    assert step.subject_rule_ids == []
    assert step.source_ids == []
    assert step.expected_evidence == []
    assert step.depends_on == []


def test_discovery_plan_validator_rejects_unscoped_qualification_steps() -> None:
    radar = _generic_definition(
        radar_id="rule-scoped-plan",
        rules=[("Q1", "First rule", "Find qualified companies.")],
        global_sources=[],
    )
    planning_input = build_discovery_planning_input(radar=radar, task_context={}, live=True, provider_metadata={})
    plan = RadarDiscoveryPlan(
        plan_summary="Unscoped plan.",
        steps=[
            RadarDiscoveryPlanStep(
                step_id="unscoped-discovery",
                stage="candidate_universe_discovery",
                subject_rule_ids=[],
                source_scope="additional",
                query="Find candidates.",
                purpose="No explicit rule scope.",
                expected_evidence=["Q1"],
                acceptance_criteria=["Q1"],
            )
        ],
        source_policy_decisions=[],
        coverage_hypotheses=[],
    )

    validation = RadarDiscoveryPlanValidator().validate(planning_input=planning_input, plan=plan)

    assert not validation.accepted
    assert any("at least one qualification rule" in error for error in validation.errors)


def test_discovery_planner_accepts_three_generic_radar_shapes() -> None:
    planner = DeterministicRadarDiscoveryPlanner()
    validator = RadarDiscoveryPlanValidator()
    definitions = [
        _generic_definition(
            radar_id="holding-contour",
            rules=[
                ("Q1", "Belongs to the target holding", "Find legal entities in the holding."),
                ("Q2", "Industrial asset", "Filter for operating industrial assets."),
            ],
            global_sources=[{"source_id": "official-site", "label": "Official site"}],
        ),
        _generic_definition(
            radar_id="industry-region-revenue",
            rules=[
                ("Q1", "Industry match", "Find companies in the target industries."),
                ("Q2", "Central region", "Filter companies in the central region."),
                ("Q3", "Revenue threshold", "Filter companies with revenue above 10 billion."),
            ],
            global_sources=[{"source_id": "company-registry", "label": "Company registry"}],
        ),
        _generic_definition(
            radar_id="registry-constrained",
            rules=[
                ("Q1", "Registry identity", "Use configured registry source for legal entity identity."),
                ("Q2", "Manufacturing profile", "Confirm manufacturing profile."),
            ],
            global_sources=[{"source_id": "sbis-like-registry", "label": "Registry source"}],
            allow_additional_sources=False,
        ),
    ]

    for definition in definitions:
        planning_input = build_discovery_planning_input(
            radar=definition,
            task_context={"requester": "test"},
            live=False,
            provider_metadata={},
        )
        plan = planner.propose_plan(planning_input=planning_input)
        validation = validator.validate(planning_input=planning_input, plan=plan)
        serialized = json.dumps(plan.model_dump(), ensure_ascii=False)

        assert validation.accepted, validation.errors
        assert plan.steps[0].stage == "candidate_universe_discovery"
        assert all(step.stage != "signal_search" for step in plan.steps)
        assert "SIBUR" not in serialized


def test_live_radar_service_revises_invalid_discovery_plan_once() -> None:
    planner = _RevisionPlanner()
    service = LiveRadarRunService(RecordedWebSearchProvider(recorded_provider_payload()), discovery_planner=planner)
    state = LiveICPRadarRunState(radar=build_live_mini_radar_definition(), live=False)

    planned = service.build_search_plan(state)

    assert planner.calls == 2
    assert planned.discovery_plan is not None
    assert planned.discovery_plan["plan_summary"] == "Accepted revised plan."
    event_types = [event["event_type"] for event in planned.pipeline_events]
    assert "discovery_plan_revised" in event_types


def test_live_radar_service_falls_back_when_revised_discovery_plan_is_invalid() -> None:
    planner = _AlwaysInvalidPlanner()
    service = LiveRadarRunService(RecordedWebSearchProvider(recorded_provider_payload()), discovery_planner=planner)
    state = LiveICPRadarRunState(radar=build_live_mini_radar_definition(), live=False)

    planned = service.build_search_plan(state)

    assert planner.calls == 2
    assert planned.discovery_plan is not None
    assert planned.discovery_plan["plan_summary"].startswith("Discovery plan for")
    assert any(query["stage"] == "coverage_check" for query in planned.search_plan["queries"])
    assert any(
            event["event_type"] == "discovery_plan_fallback_used"
            and "deterministic fallback" in event["summary"]
        for event in planned.pipeline_events
    )


def test_product_output_hides_analyzed_but_unused_sources() -> None:
    payload = recorded_provider_payload()
    payload["sources"] = [
        *payload["sources"],  # type: ignore[index]
        {
            "evidence_ref": "unused_src",
            "title": "Unused source",
            "url": "https://example.test/unused",
            "snippet": "Analyzed but not used.",
            "query_id": "q-unused",
        },
    ]

    artifact = build_live_mini_radar_artifact(
        provider=RecordedWebSearchProvider(payload),
        live=False,
    )

    assert [source["evidence_ref"] for source in artifact["sources"]] == ["src_1"]
    execution_results = artifact["run_metadata"]["execution_results"]
    assert execution_results["analyzed_source_count"] == 1
    assert execution_results["analyzed_sources"][0]["evidence_ref"] == "unused_src"


def test_openrouter_discovery_planner_request_uses_planning_scope_only() -> None:
    planning_input = build_discovery_planning_input(
        radar=build_live_mini_radar_definition(),
        task_context={"requester": "test"},
        live=True,
        provider_metadata={"model": "planner/model"},
    )

    request = build_openrouter_discovery_planner_request(
        planning_input=planning_input,
        model="planner/model",
        previous_validation=None,
    )
    prompt = json.loads(request["messages"][1]["content"])

    assert "discovery plan" in prompt["task"]
    assert "qualification_rules" in prompt["planning_input"]
    assert "intent_signals" not in prompt["planning_input"]
    assert "criterion_role_decisions" in prompt["output_schema"]
    assert "source_base" in prompt["output_schema"]["steps"][0]
    assert "application_scope" in prompt["output_schema"]["steps"][0]
    assert "usage_obligation" in prompt["output_schema"]["source_policy_decisions"][0]
    assert "obligation_status" in prompt["output_schema"]["source_policy_decisions"][0]
    assert prompt["planning_input"]["max_iterations"] == 2
    assert request["metadata"]["planner_role"] == "discovery_strategy"


def test_openrouter_discovery_planner_normalizes_localized_coverage_risk() -> None:
    payload = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "plan_summary": "Plan.",
                        "steps": [],
                        "coverage_hypotheses": [{"summary": "Risk.", "completeness_risk": "низкий"}],
                    }, ensure_ascii=False)
                }
            }
        ]
    }

    plan = _plan_from_response(payload)

    assert plan.coverage_hypotheses[0].completeness_risk == "low"


def test_execution_plan_compilation_is_generic_and_qualification_first() -> None:
    radar = {
        "radar_id": "generic-industrial",
        "name": "Generic industrial Radar",
        "description": "Find group companies and operational intent.",
        "qualification_criteria": [
            {"code": "Q1", "label": "Belongs to target group", "rule": "Find legal entities in the group.", "operator": "AND"},
            {"code": "Q2", "label": "Industrial operation", "rule": "Filter for industrial operating assets.", "operator": "AND"},
        ],
        "intent_signals": [
            {"code": "S1", "label": "Maintenance", "rule": "Find maintenance agenda."},
        ],
    }

    plan = compile_radar_execution_plan(radar)

    assert [task.stage for task in plan.tasks] == [
        "qualification_discovery",
        "qualification_gate",
        "coverage_check",
        "signal_search",
    ]
    assert [task.subject_id for task in plan.tasks] == ["Q1", "Q2", "generic-industrial", "S1"]
    assert plan.tasks[1].depends_on == [plan.tasks[0].task_id]
    assert plan.tasks[2].depends_on == [plan.tasks[1].task_id]
    assert plan.tasks[3].depends_on == [plan.tasks[2].task_id]
    assert "SIBUR" not in json.dumps(plan.model_dump(), ensure_ascii=False)


def test_staged_execution_does_not_search_signals_for_rejected_candidates() -> None:
    provider = _StageAwareProvider()
    service = LiveRadarRunService(provider)
    state = LiveICPRadarRunState(radar=build_live_mini_radar_definition(), live=False)

    collected = service.run_web_search(service.build_search_plan(state))

    assert [call.queries[0].stage for call in provider.calls] == [
        "qualification_discovery",
        "qualification_gate",
        "coverage_check",
    ]
    assert collected.execution_results["signal_task_count"] == 0
    assert collected.execution_results["rejected_candidates"][0]["failed_rules"] == ["Q2"]


def test_staged_execution_expands_candidate_universe_through_coverage_before_signals() -> None:
    provider = _CoverageExpansionProvider()
    service = LiveRadarRunService(provider)
    state = LiveICPRadarRunState(radar=build_live_mini_radar_definition(), live=False)

    collected = service.run_web_search(service.build_search_plan(state))
    extracted = service.extract_candidates(service.normalize_sources(collected))

    stages = [call.queries[0].stage for call in provider.calls]
    signal_calls = [call for call in provider.calls if call.queries[0].stage == "signal_search"]
    universe = {item["legal_name"]: item for item in collected.execution_results["candidate_universe"]}

    assert stages[:3] == ["qualification_discovery", "qualification_gate", "coverage_check"]
    discovery_scopes = [call.queries[0].candidate_scope for call in provider.calls if call.queries[0].stage == "qualification_discovery"]
    assert discovery_scopes == [[], ["Candidate B"]]
    assert any(call.queries[0].stage == "qualification_gate" and "Candidate B" in call.queries[0].candidate_scope for call in provider.calls)
    assert "Candidate B" in [name for call in signal_calls for name in call.queries[0].candidate_scope]
    assert universe["Candidate B"]["status"] == "qualified"
    assert collected.execution_results["coverage_checks"][0]["new_candidate_count"] == 1
    assert collected.execution_results["unresolved_candidate_gaps"] == []
    assert {item["legal_name"] for item in extracted.candidates} == {"Candidate A", "Candidate B"}


def test_signal_stage_new_entities_become_gaps_not_candidates() -> None:
    provider = _SignalGapProvider()
    service = LiveRadarRunService(provider)
    state = LiveICPRadarRunState(radar=build_live_mini_radar_definition(), live=False)

    collected = service.run_web_search(service.build_search_plan(state))
    extracted = service.extract_candidates(service.normalize_sources(collected))

    assert {item["legal_name"] for item in extracted.candidates} == {"Candidate A"}
    assert collected.execution_results["unresolved_candidate_gaps"][0]["legal_name"] == "Candidate C"
    assert "Candidate C" not in {item["legal_name"] for item in collected.candidate_observations}


def test_entity_resolution_links_project_fact_to_legal_entity() -> None:
    service = RadarEntityResolutionService()
    output = service.resolve(
        observations=[
            {
                "legal_name": "АО «Тестовый завод»",
                "inn": "1234567890",
                "evidence_refs": ["src_legal"],
                "qualification": [{"criterion_code": "Q1", "status": "confirmed", "evidence_refs": ["src_legal"]}],
            },
            {
                "legal_name": "EP-600",
                "entity_type": "project",
                "linked_legal_name": "АО «Тестовый завод»",
                "evidence_refs": ["src_project"],
            },
        ],
        sources=[
            RadarSourceEvidence(evidence_ref="src_legal", title="Registry", url="https://example.test/legal", snippet="АО «Тестовый завод», INN 1234567890"),
            RadarSourceEvidence(evidence_ref="src_project", title="Project", url="https://example.test/project", snippet="EP-600 at АО «Тестовый завод»"),
        ],
    )

    assert [item["legal_name"] for item in output.candidate_observations] == ["АО «Тестовый завод»"]
    assert output.candidate_observations[0]["entity_type"] == "legal_entity"
    assert output.candidate_observations[0]["linked_entity_facts"][0]["entity_name"] == "EP-600"
    assert output.provider_metadata["linked_entity_facts"][0]["linked_legal_name"] == "АО «Тестовый завод»"
    assert any(item["resolution_status"] == "linked_to_legal_entity" for item in output.provider_metadata["entity_resolution_results"])
    assert output.provider_metadata["candidate_universe_gaps"] == []


def test_staged_execution_does_not_score_project_as_legal_entity_candidate() -> None:
    class ProjectOnlyProvider:
        runtime_name = "project-only"

        def __init__(self) -> None:
            self.calls = []

        def run_search_plan(self, *, radar, search_plan):
            _ = radar
            self.calls.append(search_plan)
            query = search_plan.queries[0]
            if query.stage == "qualification_discovery":
                return WebSearchProviderResult(
                    sources=[
                        RadarSourceEvidence(
                            evidence_ref="src_ep600",
                            title="EP-600 project",
                            url="https://example.test/ep-600",
                            snippet="EP-600 is a production expansion project.",
                            query_id=query.query_id,
                        )
                    ],
                    candidate_observations=[
                        {
                            "legal_name": "EP-600",
                            "entity_type": "project",
                            "qualification": [{"criterion_code": "Q1", "status": "confirmed", "evidence_refs": ["src_ep600"]}],
                        }
                    ],
                )
            return WebSearchProviderResult()

    provider = ProjectOnlyProvider()
    radar = {
        "radar_id": "entity-resolution-test",
        "qualification_criteria": [{"code": "Q1", "label": "Find legal entities", "requirement_level": "required"}],
        "intent_signals": [{"code": "S1", "label": "Signal", "rule": "Find signal."}],
    }
    plan = RadarExecutionPlan(
        radar_id="entity-resolution-test",
        tasks=[
            RadarExecutionTask(
                task_id="discover-q1",
                stage="qualification_discovery",
                subject_type="qualification",
                subject_id="Q1",
                query="Find projects and companies.",
                purpose="Discover candidate universe.",
            ),
            RadarExecutionTask(
                task_id="signal-s1",
                stage="signal_search",
                subject_type="signal",
                subject_id="S1",
                query="Find signal.",
                purpose="Signal search.",
            ),
        ],
    )

    result, _, execution_results = run_staged_radar_execution(radar=radar, execution_plan=plan, provider=provider)

    assert result.candidate_observations == []
    assert [call.queries[0].stage for call in provider.calls] == ["qualification_discovery"]
    assert execution_results["signal_task_count"] == 0
    assert execution_results["unresolved_candidate_gaps"][0]["legal_name"] == "EP-600"
    assert execution_results["unresolved_candidate_gaps"][0]["reason"] == "entity_type_not_account"
    assert execution_results["entity_resolution_results"][0]["entity_type"] == "project"


def test_staged_execution_searches_each_candidate_signal_when_total_budget_allows() -> None:
    provider = _ManyCandidateProvider(candidate_count=14)
    radar = build_live_mini_radar_definition()
    radar["intent_signals"] = [
        {"code": "S1", "label": "Signal 1", "rule": "Find signal 1."},
        {"code": "S2", "label": "Signal 2", "rule": "Find signal 2."},
        {"code": "S3", "label": "Signal 3", "rule": "Find signal 3."},
    ]
    service = LiveRadarRunService(provider)
    state = LiveICPRadarRunState(radar=radar, live=False)

    collected = service.run_web_search(service.build_search_plan(state))
    signal_calls = [call for call in provider.calls if call.queries[0].stage == "signal_search"]

    assert collected.execution_results["signal_task_count"] == 42
    assert len(signal_calls) == 42
    assert collected.execution_results["max_signal_candidates"] == 14
    assert collected.execution_results["budget_exhaustion_events"] == []
    assert all(item["search_status"] == "searched" for item in collected.execution_results["signal_search_statuses"])
    assert len(collected.execution_results["candidate_universe"]) == 14


def test_compatibility_budget_is_candidate_signal_scoped_not_signal_global() -> None:
    provider = _ManyCandidateProvider(candidate_count=14)
    radar = build_live_mini_radar_definition()
    radar["intent_signals"] = [
        {"code": "S1", "label": "Signal 1", "rule": "Find signal 1."},
        {"code": "S2", "label": "Signal 2", "rule": "Find signal 2."},
        {"code": "S3", "label": "Signal 3", "rule": "Find signal 3."},
    ]
    service = LiveRadarRunService(provider)
    state = LiveICPRadarRunState(
        radar=radar,
        live=False,
        task_context={"max_web_tasks_per_subject": 4},
    )

    collected = service.run_web_search(service.build_search_plan(state))
    signal_subjects = [
        call.queries[0].subject_id
        for call in provider.calls
        if call.queries[0].stage == "signal_search"
    ]

    assert signal_subjects.count("S1") == 14
    assert signal_subjects.count("S2") == 14
    assert signal_subjects.count("S3") == 14
    assert collected.execution_results["max_web_tasks_per_subject"] == 4
    assert collected.execution_results["budget_settings"]["compatibility_max_web_tasks_per_subject"] == 4
    assert collected.execution_results["web_task_counts_by_subject"]["signal:S1:Candidate 01"] == 1
    assert collected.execution_results["web_task_counts_by_subject"]["signal:S3:Candidate 14"] == 1
    assert collected.execution_results["budget_exhaustion_events"] == []


def test_total_budget_marks_remaining_signals_as_not_searched() -> None:
    provider = _ManyCandidateProvider(candidate_count=14)
    radar = build_live_mini_radar_definition()
    radar["intent_signals"] = [{"code": "S1", "label": "Signal 1", "rule": "Find signal 1."}]
    service = LiveRadarRunService(provider)
    state = LiveICPRadarRunState(
        radar=radar,
        live=False,
        task_context={"max_total_web_tasks_per_run": 20},
    )

    collected = service.run_web_search(service.build_search_plan(state))
    extracted = service.extract_candidates(service.normalize_sources(collected))
    signal_calls = [call for call in provider.calls if call.queries[0].stage == "signal_search"]
    statuses = collected.execution_results["signal_search_statuses"]
    not_searched = [item for item in statuses if item["search_status"] == "not_searched_budget_limited"]
    candidate_14 = next(item for item in extracted.candidates if item["legal_name"] == "Candidate 14")
    candidate_14_signal = candidate_14["signals"][0]

    assert len(signal_calls) == 4
    assert collected.execution_results["budget_counters"]["total"] == 20
    assert not_searched
    assert collected.execution_results["budget_exhaustion_events"]
    assert candidate_14_signal["status"] == "unclear"
    assert candidate_14_signal["search_status"] == "not_searched_budget_limited"
    assert candidate_14_signal["not_searched_reason"] == "total_run_budget_exhausted"
    assert candidate_14_signal["score"] == 0
    assert candidate_14_signal["status"] != "not_observed"


def test_openrouter_model_routing_uses_advanced_models_for_planner_and_extractor(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join([
            "OPENROUTER_MODEL=fast/model",
            "OPENROUTER_ADVANCED_MODEL=advanced/model",
            "OPENROUTER_PLANNER_MODEL=planner/model",
            "OPENROUTER_EXTRACTOR_MODEL=extractor/model",
        ]),
        encoding="utf-8",
    )
    provider = OpenRouterWebSearchProvider(env_path=env_file)
    planner = OpenRouterDiscoveryPlanner(env_path=env_file)
    plan = compile_radar_execution_plan(build_live_mini_radar_definition())
    discovery_task = next(task for task in plan.tasks if task.stage == "qualification_discovery")
    signal_task = next(task for task in plan.tasks if task.stage == "signal_search")

    assert provider.model == "fast/model"
    assert provider.extractor_model == "extractor/model"
    assert planner.model == "planner/model"
    assert provider._model_for_search_plan(execution_task_to_search_plan(discovery_task, radar_id=plan.radar_id)) == "extractor/model"
    assert provider._model_for_search_plan(execution_task_to_search_plan(signal_task, radar_id=plan.radar_id)) == "fast/model"


def test_openrouter_model_routing_falls_back_to_advanced_model_for_extractor(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join([
            "OPENROUTER_MODEL=fast/model",
            "OPENROUTER_ADVANCED_MODEL=advanced/model",
        ]),
        encoding="utf-8",
    )

    provider = OpenRouterWebSearchProvider(env_path=env_file)
    planner = OpenRouterDiscoveryPlanner(env_path=env_file)

    assert provider.extractor_model == "advanced/model"
    assert planner.model == "advanced/model"


class _StageAwareProvider:
    runtime_name = "stage-aware"

    def __init__(self) -> None:
        self.calls = []

    def run_search_plan(self, *, radar: dict[str, object], search_plan):
        _ = radar
        self.calls.append(search_plan)
        stage = search_plan.queries[0].stage
        if stage == "qualification_discovery":
            return WebSearchProviderResult(
                sources=[{"evidence_ref": "src_q1", "title": "Group registry", "url": "https://example.test/q1", "snippet": "Candidate A belongs to the group.", "query_id": search_plan.queries[0].query_id}],
                candidate_observations=[{"legal_name": "Candidate A", "qualification": [{"criterion_code": "Q1", "status": "confirmed", "evidence_refs": ["src_q1"]}]}],
                provider_metadata={"provider": "stage-aware"},
            )
        if stage == "qualification_gate":
            return WebSearchProviderResult(
                sources=[{"evidence_ref": "src_q2", "title": "Services registry", "url": "https://example.test/q2", "snippet": "Candidate A is only a service office.", "query_id": search_plan.queries[0].query_id}],
                candidate_observations=[{"legal_name": "Candidate A", "qualification": [{"criterion_code": "Q2", "status": "rejected", "evidence_refs": ["src_q2"]}]}],
                provider_metadata={"provider": "stage-aware"},
            )
        if stage == "coverage_check":
            return WebSearchProviderResult(
                sources=[],
                candidate_observations=[],
                provider_metadata={"provider": "stage-aware", "coverage_findings": [{"summary": "No further candidates.", "completeness_risk": "low"}]},
            )
        raise AssertionError(f"Signal search should not run for rejected candidates: {stage}")


class _WeakThenUsefulProvider:
    runtime_name = "weak-then-useful"

    def __init__(self) -> None:
        self.calls = []

    def run_search_plan(self, *, radar, search_plan):
        _ = radar
        self.calls.append(search_plan)
        query = search_plan.queries[0]
        if len(self.calls) == 1:
            return WebSearchProviderResult(
                sources=[
                    RadarSourceEvidence(
                        evidence_ref="weak_src",
                        title="Weak source",
                        url="https://example.invalid/weak",
                        snippet="Candidate A belongs to the target universe.",
                        query_id=query.query_id,
                        verification_state="unverified_url",
                        verification_mode="soft",
                        verification_reason="http_404",
                        verification_status_code=404,
                    )
                ],
                candidate_observations=[
                    {
                        "legal_name": "Candidate A",
                        "qualification": [
                            {"criterion_code": "Q1", "status": "confirmed", "evidence_refs": ["weak_src"]}
                        ],
                    }
                ],
                provider_metadata={"provider": "weak-then-useful"},
            )
        return WebSearchProviderResult(
            sources=[
                RadarSourceEvidence(
                    evidence_ref="ok_src",
                    title="Verified source",
                    url="https://example.test/ok",
                    snippet="Candidate B belongs to the target universe.",
                    query_id=query.query_id,
                    verification_state="reachable",
                    verification_mode="soft",
                    verification_reason="http_200",
                    verification_status_code=200,
                )
            ],
            candidate_observations=[
                {
                    "legal_name": "Candidate B",
                    "qualification": [
                        {"criterion_code": "Q1", "status": "confirmed", "evidence_refs": ["ok_src"]}
                    ],
                }
            ],
            provider_metadata={"provider": "weak-then-useful"},
        )


class _SchemaInvalidProvider:
    runtime_name = "schema-invalid"

    def run_search_plan(self, *, radar, search_plan):
        _ = radar, search_plan
        return WebSearchProviderResult(
            sources=[],
            candidate_observations=[],
            provider_metadata={
                "provider": "schema-invalid",
                "retrieved_sources": [
                    {
                        "source_ref": "retrieved_1",
                        "title": "Retrieved source",
                        "url": "https://example.test/retrieved",
                        "snippet": "Retrieved but extraction schema failed.",
                    }
                ],
                "extraction_validation_results": [
                    {
                        "valid": False,
                        "state": "extraction_schema_invalid",
                        "repaired": False,
                        "repair_actions": [],
                        "issues": [
                            {
                                "code": "extraction_schema_invalid",
                                "severity": "error",
                                "path": "$.candidates",
                                "message": "Provider output field candidates must be a list.",
                                "details": {"field": "candidates", "actual_type": "object"},
                                "remediation": "Reject dict/list mismatches before normalization.",
                            }
                        ],
                    }
                ],
                "extraction_validation_issues": [
                    {
                        "code": "extraction_schema_invalid",
                        "severity": "error",
                        "path": "$.candidates",
                        "message": "Provider output field candidates must be a list.",
                        "details": {"field": "candidates", "actual_type": "object"},
                        "remediation": "Reject dict/list mismatches before normalization.",
                    }
                ],
                "extraction_repair_results": [],
            },
        )


class _CoverageExpansionProvider:
    runtime_name = "coverage-expansion"

    def __init__(self) -> None:
        self.calls = []

    def run_search_plan(self, *, radar, search_plan):
        _ = radar
        self.calls.append(search_plan)
        query = search_plan.queries[0]
        if query.stage == "qualification_discovery":
            if query.candidate_scope:
                observations = []
                sources = []
                for candidate_name in query.candidate_scope:
                    ref = f"src_{candidate_name[-1].lower()}_q1"
                    sources.append({"evidence_ref": ref, "title": f"Registry {candidate_name}", "url": f"https://example.test/{ref}", "snippet": f"{candidate_name} belongs.", "query_id": query.query_id})
                    observations.append({"legal_name": candidate_name, "qualification": [{"criterion_code": "Q1", "status": "confirmed", "evidence_refs": [ref]}]})
                return WebSearchProviderResult(sources=sources, candidate_observations=observations, provider_metadata={"provider": "coverage-expansion"})
            return WebSearchProviderResult(
                sources=[{"evidence_ref": "src_a_q1", "title": "Registry A", "url": "https://example.test/a-q1", "snippet": "Candidate A belongs.", "query_id": query.query_id}],
                candidate_observations=[{"legal_name": "Candidate A", "qualification": [{"criterion_code": "Q1", "status": "confirmed", "evidence_refs": ["src_a_q1"]}]}],
                provider_metadata={"provider": "coverage-expansion"},
            )
        if query.stage == "qualification_gate":
            observations = []
            sources = []
            for candidate_name in query.candidate_scope:
                ref = f"src_{candidate_name[-1].lower()}_q2"
                sources.append({"evidence_ref": ref, "title": f"Industrial {candidate_name}", "url": f"https://example.test/{ref}", "snippet": f"{candidate_name} is industrial.", "query_id": query.query_id})
                observations.append({"legal_name": candidate_name, "qualification": [{"criterion_code": "Q2", "status": "confirmed", "evidence_refs": [ref]}]})
            return WebSearchProviderResult(sources=sources, candidate_observations=observations, provider_metadata={"provider": "coverage-expansion"})
        if query.stage == "coverage_check":
            return WebSearchProviderResult(
                sources=[{"evidence_ref": "src_b_gap", "title": "Coverage registry", "url": "https://example.test/b-gap", "snippet": "Candidate B is also in scope.", "query_id": query.query_id}],
                candidate_observations=[],
                provider_metadata={
                    "provider": "coverage-expansion",
                    "candidate_universe_gaps": [{"legal_name": "Candidate B", "source_refs": ["src_b_gap"], "reason": "Coverage registry found a missing candidate."}],
                    "coverage_findings": [{"summary": "One missing candidate found.", "completeness_risk": "medium", "warnings": []}],
                },
            )
        if query.stage == "signal_search":
            candidate_name = query.candidate_scope[0]
            return WebSearchProviderResult(
                sources=[{"evidence_ref": f"src_{candidate_name[-1].lower()}_s", "title": f"Signal {candidate_name}", "url": f"https://example.test/{candidate_name[-1].lower()}-s", "snippet": f"{candidate_name} has a signal.", "query_id": query.query_id}],
                candidate_observations=[{"legal_name": candidate_name, "signals": [{"signal_code": query.subject_id, "status": "observed", "score": 1, "evidence_refs": [f"src_{candidate_name[-1].lower()}_s"]}]}],
                provider_metadata={"provider": "coverage-expansion"},
            )
        raise AssertionError(f"Unexpected stage: {query.stage}")


class _SignalGapProvider(_CoverageExpansionProvider):
    runtime_name = "signal-gap"

    def run_search_plan(self, *, radar, search_plan):
        query = search_plan.queries[0]
        if query.stage == "coverage_check":
            self.calls.append(search_plan)
            return WebSearchProviderResult(
                sources=[],
                candidate_observations=[],
                provider_metadata={"provider": "signal-gap", "coverage_findings": [{"summary": "No missing candidates before signal search.", "completeness_risk": "low"}]},
            )
        if query.stage != "signal_search":
            return super().run_search_plan(radar=radar, search_plan=search_plan)
        self.calls.append(search_plan)
        return WebSearchProviderResult(
            sources=[
                {"evidence_ref": "src_a_s", "title": "Signal A", "url": "https://example.test/a-s", "snippet": "Candidate A has a signal.", "query_id": query.query_id},
                {"evidence_ref": "src_c_s", "title": "Signal C", "url": "https://example.test/c-s", "snippet": "Candidate C is mentioned late.", "query_id": query.query_id},
            ],
            candidate_observations=[
                {"legal_name": "Candidate A", "signals": [{"signal_code": query.subject_id, "status": "observed", "score": 1, "evidence_refs": ["src_a_s"]}]},
                {"legal_name": "Candidate C", "signals": [{"signal_code": query.subject_id, "status": "observed", "score": 1, "evidence_refs": ["src_c_s"]}]},
            ],
            provider_metadata={"provider": "signal-gap"},
        )


class _ManyCandidateProvider:
    runtime_name = "many-candidates"

    def __init__(self, *, candidate_count: int) -> None:
        self.candidate_count = candidate_count
        self.calls = []

    def run_search_plan(self, *, radar, search_plan):
        _ = radar
        self.calls.append(search_plan)
        query = search_plan.queries[0]
        if query.stage == "qualification_discovery":
            sources = []
            observations = []
            for index in range(1, self.candidate_count + 1):
                name = f"Candidate {index:02d}"
                ref = f"src_{index:02d}_q1"
                sources.append({
                    "evidence_ref": ref,
                    "title": f"Registry {name}",
                    "url": f"https://example.test/{index:02d}/q1",
                    "snippet": f"{name} belongs to the target group.",
                    "query_id": query.query_id,
                })
                observations.append({
                    "legal_name": name,
                    "qualification": [{"criterion_code": "Q1", "status": "confirmed", "evidence_refs": [ref]}],
                })
            return WebSearchProviderResult(sources=sources, candidate_observations=observations, provider_metadata={"provider": "many-candidates"})
        if query.stage == "qualification_gate":
            sources = []
            observations = []
            for name in query.candidate_scope:
                ref = f"src_{name[-2:]}_q2"
                sources.append({
                    "evidence_ref": ref,
                    "title": f"Industrial {name}",
                    "url": f"https://example.test/{name[-2:]}/q2",
                    "snippet": f"{name} is an industrial enterprise.",
                    "query_id": query.query_id,
                })
                observations.append({
                    "legal_name": name,
                    "qualification": [{"criterion_code": "Q2", "status": "confirmed", "evidence_refs": [ref]}],
                })
            return WebSearchProviderResult(sources=sources, candidate_observations=observations, provider_metadata={"provider": "many-candidates"})
        if query.stage == "coverage_check":
            return WebSearchProviderResult(
                sources=[],
                candidate_observations=[],
                provider_metadata={"provider": "many-candidates", "coverage_findings": [{"summary": "No gaps.", "completeness_risk": "low"}]},
            )
        if query.stage == "signal_search":
            candidate_name = query.candidate_scope[0]
            ref = f"src_{candidate_name[-2:]}_{query.subject_id.lower()}"
            return WebSearchProviderResult(
                sources=[{
                    "evidence_ref": ref,
                    "title": f"{query.subject_id} {candidate_name}",
                    "url": f"https://example.test/{candidate_name[-2:]}/{query.subject_id.lower()}",
                    "snippet": f"{candidate_name} has {query.subject_id}.",
                    "query_id": query.query_id,
                }],
                candidate_observations=[{
                    "legal_name": candidate_name,
                    "signals": [{"signal_code": query.subject_id, "status": "observed", "score": 1, "evidence_refs": [ref]}],
                }],
                provider_metadata={"provider": "many-candidates"},
            )
        raise AssertionError(f"Unexpected stage: {query.stage}")


def _generic_definition(
    *,
    radar_id: str,
    rules: list[tuple[str, str, str]],
    global_sources: list[dict[str, str]],
    allow_additional_sources: bool = True,
) -> dict[str, object]:
    return {
        "radar_id": radar_id,
        "name": radar_id.replace("-", " ").title(),
        "qualification_criteria": [
            {
                "code": code,
                "label": label,
                "rule": rule,
                "operator": "AND",
                "source_policy": {
                    "use_global_search_policy": True,
                    "allow_additional_sources": allow_additional_sources,
                },
            }
            for code, label, rule in rules
        ],
        "global_search_policy": {
            "sources": global_sources,
            "allow_system_sources": allow_additional_sources,
        },
        "intent_signals": [{"code": "S1", "label": "Investment signal", "rule": "Find one buying-intent signal."}],
    }


class _RevisionPlanner(OpenRouterDiscoveryPlanner):
    def __init__(self) -> None:
        self.calls = 0

    def propose_plan(self, *, planning_input, previous_validation: RadarDiscoveryPlanValidationResult | None = None):
        self.calls += 1
        if previous_validation is None:
            return RadarDiscoveryPlan(
                plan_summary="Invalid initial plan.",
                steps=[
                    RadarDiscoveryPlanStep(
                        step_id="invalid-signal",
                        stage="candidate_universe_discovery",
                        subject_rule_ids=["S1"],
                        source_scope="additional",
                        query="Find signal first.",
                        purpose="Invalidly mix signal search into discovery.",
                        expected_evidence=["signal"],
                        acceptance_criteria=["signal"],
                    )
                ],
                source_policy_decisions=[],
                coverage_hypotheses=[],
            )
        return RadarDiscoveryPlan(
            plan_summary="Accepted revised plan.",
            steps=[
                RadarDiscoveryPlanStep(
                    step_id="discover-q1",
                    stage="candidate_universe_discovery",
                    subject_rule_ids=["Q1"],
                    source_scope="additional",
                    query="Find qualified candidates.",
                    purpose="Discover candidate universe.",
                    expected_evidence=["Q1"],
                    acceptance_criteria=["Q1 evidence"],
                ),
                RadarDiscoveryPlanStep(
                    step_id="coverage-q1",
                    stage="coverage_check",
                    subject_rule_ids=[],
                    source_scope="additional",
                    query="Check universe coverage.",
                    purpose="Validate candidate universe coverage before signal search.",
                    expected_evidence=["candidate_universe_gaps"],
                    acceptance_criteria=["Coverage checked."],
                    depends_on=["discover-q1"],
                )
            ],
            source_policy_decisions=[
                RadarDiscoverySourcePolicyDecision(
                    source_id="sibur.ru",
                    source_label="sibur.ru",
                    decision="selected",
                    reason="Configured preferred domain is relevant to qualification discovery.",
                    rule_ids=["Q1"],
                )
            ],
            coverage_hypotheses=[{"summary": "Coverage will be checked before signal search.", "completeness_risk": "medium"}],
        )


class _AlwaysInvalidPlanner(OpenRouterDiscoveryPlanner):
    def __init__(self) -> None:
        self.calls = 0

    def propose_plan(self, *, planning_input, previous_validation: RadarDiscoveryPlanValidationResult | None = None):
        self.calls += 1
        _ = planning_input, previous_validation
        return RadarDiscoveryPlan(
            plan_summary="Still invalid.",
            steps=[
                RadarDiscoveryPlanStep(
                    step_id="single-discovery-without-coverage",
                    stage="candidate_universe_discovery",
                    subject_rule_ids=["Q1"],
                    source_scope="additional",
                    query="Find candidates once.",
                    purpose="Invalidly rely on one broad discovery step.",
                    expected_evidence=["Q1"],
                    acceptance_criteria=["Q1 evidence"],
                )
            ],
            source_policy_decisions=[],
            coverage_hypotheses=[],
        )


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


def test_openrouter_response_parser_ignores_non_json_text_before_fenced_json() -> None:
    payload = {
        "id": "response-2",
        "choices": [
            {
                "message": {
                    "content": (
                        "I will inspect candidates first. {not valid json}\n\n"
                        "```json\n"
                        "{\"sources\":[{\"evidence_ref\":\"src_a\",\"title\":\"Source A\","
                        "\"url\":\"https://example.test/a\",\"snippet\":\"Snippet A\"}],"
                        "\"candidates\":[{\"legal_name\":\"Candidate A\"}]}\n"
                        "```"
                    ),
                    "annotations": [],
                }
            }
        ],
        "usage": {},
    }

    trace_payload = live_radar_openrouter._provider_response_trace_payload(
        payload,
        model="test/model",
        web_mode="server_tools",
    )
    result = normalize_openrouter_response(
        payload,
        fallback_metadata={"provider": "openrouter", "model": "test/model", "web_mode": "server_tools"},
    )

    assert trace_payload["parser_status"] == "json_object"
    assert [source.evidence_ref for source in result.sources] == ["src_a"]
    assert result.candidate_observations == [{"legal_name": "Candidate A"}]


def test_openrouter_response_parser_treats_unparseable_content_as_empty_result() -> None:
    payload = {
        "id": "response-3",
        "choices": [{"message": {"content": "I found something, but returned {broken: payload}.", "annotations": []}}],
        "usage": {},
    }

    trace_payload = live_radar_openrouter._provider_response_trace_payload(
        payload,
        model="test/model",
        web_mode="server_tools",
    )
    result = normalize_openrouter_response(
        payload,
        fallback_metadata={"provider": "openrouter", "model": "test/model", "web_mode": "server_tools"},
    )

    assert trace_payload["parser_status"] == "empty_or_unparseable"
    assert result.sources == []
    assert result.candidate_observations == []


def test_active_definition_adapter_preserves_source_policy_and_runtime_projection() -> None:
    record = _toir_quick_live_definition_record()

    runtime_payload = active_definition_to_live_radar_payload(record)
    plan = compile_radar_execution_plan(runtime_payload)

    assert runtime_payload["definition_id"] == "radar-def-toir-quick-live"
    assert runtime_payload["definition_version"] == record.definition_version
    assert runtime_payload["global_search_policy"]["sources"][0]["source_id"] == "dadata_registry"
    assert runtime_payload["global_search_policy"]["sources"][0]["usage_obligation"] == "required_for_identity"
    assert runtime_payload["global_search_policy"]["sources"][1]["source_id"] == "openrouter_web"
    assert runtime_payload["global_search_policy"]["sources"][1]["usage_obligation"] == "required_for_coverage"
    assert runtime_payload["qualification_criteria"][0]["code"] == "q1-sibur-group"
    assert runtime_payload["qualification_criteria"][0]["source_policy"]["source_ids"][0] == "dadata_registry"
    assert runtime_payload["intent_signals"][0]["code"] == "S1"
    assert plan.tasks[0].source_ids[:2] == ["dadata_registry", "openrouter_web"]
    assert plan.tasks[0].source_base == "global_configured"


def test_source_registry_emits_unavailable_outcome_for_selected_dadata_source() -> None:
    radar = active_definition_to_live_radar_payload(_toir_quick_live_definition_record())
    task = RadarExecutionTask(
        task_id="qualify-discover-q1",
        stage="qualification_discovery",
        subject_type="qualification",
        subject_id="q1-sibur-group",
        query="Find companies in the target holding.",
        purpose="Discover holding legal entities.",
        expected_evidence=["q1-sibur-group"],
        source_scope="global",
        source_ids=["dadata_registry"],
    )

    result = RadarSourceRegistry(company_registry_providers={}).lookup_for_task(radar=radar, task=task)

    outcomes = result.provider_metadata["source_provider_outcomes"]
    assert outcomes[0]["source_id"] == "dadata_registry"
    assert outcomes[0]["provider_id"] == "dadata"
    assert outcomes[0]["outcome"] == "provider_unavailable"


def _toir_quick_live_definition_record() -> RadarDefinitionRecord:
    catalog = build_icp_radar_catalog_from_workbook(Path("demo/fixtures/icp_radar/sibur_icp_pass1.xlsx"))
    for item in catalog["radars"]:
        if item["radar_id"] == "toir-quick-live":
            return RadarDefinitionRecord(
                definition_id=item["definition"]["definition_id"],
                radar_id=item["radar_id"],
                definition_payload=item["definition"],
                definition_version=catalog["artifact_version"],
            )
    raise AssertionError("toir-quick-live fixture is missing")
    assert result.provider_metadata["response_id"] == "response-3"


def test_openrouter_provider_treats_non_json_http_200_as_empty_task_result(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class FakeResponse:
        status_code = 200
        text = "OpenRouter upstream returned a non-JSON envelope"

        def json(self):
            raise json.JSONDecodeError("Expecting value", self.text, 0)

    class FakeClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def post(self, *args, **kwargs):
            return FakeResponse()

    class FakeHttpx:
        Client = FakeClient

        @staticmethod
        def post(*args, **kwargs):
            return FakeResponse()

    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join([
            "OPENROUTER_API_KEY=test-key",
            "OPENROUTER_MODEL=test/model",
            "OPENROUTER_WEB_MODE=server_tools",
        ]),
        encoding="utf-8",
    )
    monkeypatch.setitem(sys.modules, "httpx", FakeHttpx)

    result = OpenRouterWebSearchProvider(env_path=env_file).run_search_plan(
        radar=build_live_mini_radar_definition(),
        search_plan=build_live_mini_radar_search_plan(),
    )

    assert result.sources == []
    assert result.candidate_observations == []
    assert result.provider_metadata["provider_error"]["error_type"] == "JSONDecodeError"


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

    for forbidden in ["OPENROUTER_API_KEY", "Authorization", "Bearer", "test-secret-key"]:
        assert forbidden not in serialized


@pytest.mark.skipif(not FRAMEWORK_AVAILABLE, reason="langgraph-dai is optional")
def test_live_workflow_reports_langgraph_runtime_when_available() -> None:
    workflow = LiveICPRadarRunWorkflow(provider=RecordedWebSearchProvider(WebSearchProviderResult()))
    result = workflow.invoke(LiveICPRadarRunState(radar=build_live_mini_radar_definition()))

    assert result.workflow_metadata["framework_available"] is True
