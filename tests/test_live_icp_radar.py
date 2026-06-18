from __future__ import annotations

import json
from pathlib import Path

import pytest

import power_web_os.live_icp_radar as live_facade
from power_web_os.application.live_radar_service import LiveRadarRunService
from power_web_os.application.live_radar_contracts import (
    RadarDiscoveryPlan,
    RadarDiscoveryPlanStep,
    RadarDiscoveryPlanValidationResult,
    RadarDiscoverySourcePolicyDecision,
)
from power_web_os.application.live_radar_discovery_planning import (
    DeterministicRadarDiscoveryPlanner,
    RadarDiscoveryPlanValidator,
    build_discovery_planning_input,
)
from power_web_os.application.live_radar_execution_plan import compile_radar_execution_plan, execution_task_to_search_plan
from power_web_os.demo import generate_live_mini_icp_radar_plan
from power_web_os.integrations import live_radar_openrouter
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
    assert len(artifact["search_plan"]["queries"]) == 5
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

    assert qualification_prompt["current_task"]["stage"] == "qualification_discovery"
    assert len(qualification_prompt["radar"]["qualification_criteria"]) == 1
    assert qualification_prompt["radar"]["intent_signals"] == []
    assert signal_prompt["current_task"]["stage"] == "signal_search"
    assert signal_prompt["radar"]["qualification_criteria"] == []
    assert len(signal_prompt["radar"]["intent_signals"]) == 1


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
    assert len(planned.search_plan["queries"]) == 5
    assert planned.search_plan["queries"][0]["source_scope"] == "global"
    assert planned.search_plan["queries"][0]["source_ids"] == ["sibur.ru"]
    assert planned.execution_plan is not None
    assert len(collected.candidate_observations) == 1
    assert [call.queries[0].stage for call in provider.calls] == [
        "qualification_discovery",
        "qualification_gate",
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
    assert event_types[:3] == ["discovery_plan_requested", "discovery_plan_created", "discovery_plan_validated"]
    assert "plan_created" in event_types
    assert "qualification_discovery_planned" in event_types
    assert "qualification_gate_applied" in event_types
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
    assert prompt["planning_input"]["max_iterations"] == 2
    assert request["metadata"]["planner_role"] == "discovery_strategy"


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
        "signal_search",
    ]
    assert [task.subject_id for task in plan.tasks] == ["Q1", "Q2", "S1"]
    assert plan.tasks[1].depends_on == [plan.tasks[0].task_id]
    assert plan.tasks[2].depends_on == [plan.tasks[1].task_id]
    assert "SIBUR" not in json.dumps(plan.model_dump(), ensure_ascii=False)


def test_staged_execution_does_not_search_signals_for_rejected_candidates() -> None:
    provider = _StageAwareProvider()
    service = LiveRadarRunService(provider)
    state = LiveICPRadarRunState(radar=build_live_mini_radar_definition(), live=False)

    collected = service.run_web_search(service.build_search_plan(state))

    assert [call.queries[0].stage for call in provider.calls] == [
        "qualification_discovery",
        "qualification_gate",
    ]
    assert collected.execution_results["signal_task_count"] == 0
    assert collected.execution_results["rejected_candidates"][0]["failed_rules"] == ["Q2"]


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
        raise AssertionError(f"Signal search should not run for rejected candidates: {stage}")


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
