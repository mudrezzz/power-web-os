from __future__ import annotations

from collections import Counter
from typing import Any

from power_web_os.application.live_radar_contracts import (
    RadarExecutionPlan,
    RadarExecutionTask,
    RadarSourceEvidence,
    WebSearchProviderResult,
)
from power_web_os.application.live_radar_external_budget import (
    RadarExternalCallBudget,
    RadarExternalCallBudgetSettings,
)
from power_web_os.application.live_radar_external_budget_context import (
    external_call_budget_context,
)
from power_web_os.application.live_radar_staged_execution import run_staged_radar_execution
from power_web_os.application.radar_registry_lookup_terms import RegistryLookupTermGenerator
from power_web_os.application.radar_search_expansion import RadarSearchExpansionService
from power_web_os.application.radar_search_expansion_models import RadarSearchExpansionVariant
from power_web_os.application.radar_search_expansion_scheduler import schedule_guaranteed_expansion_variants
from power_web_os.application.radar_search_expansion_selection import select_guaranteed_variants
from power_web_os.application.radar_source_obligations import obligation_decisions_from_plan, source_obligation_summary
from power_web_os.application.radar_source_providers import CompanyLookupRequest, RadarSourceRegistry
from power_web_os.integrations.dadata_provider import RecordedDaDataCompanyRegistryProvider


def test_search_expansion_generates_official_and_open_web_query_variants() -> None:
    service = RadarSearchExpansionService(max_variants=8)

    plan = service.plan_expansion(
        radar=_radar_with_sources(),
        candidate_scope=["Губкинский газоперерабатывающий завод"],
        provider_metadata={},
        coverage_checks=[{"completeness_risk": "high"}],
        unresolved_candidate_gaps=[],
    )

    queries = [item.query for item in plan.variants]
    assert plan.should_expand is True
    assert "site:sibur.ru Губкинский газоперерабатывающий завод" in queries
    assert "Губкинский газоперерабатывающий завод СИБУР" in queries
    assert "Губкинский газоперерабатывающий завод ИНН ОГРН" in queries
    assert "Губкинский газоперерабатывающий завод завод ГПЗ площадка филиал" in queries
    assert any("sibur_site" in item.source_ids for item in plan.variants)
    assert any("openrouter_web" in item.source_ids for item in plan.variants)


def test_search_expansion_respects_disabled_sources() -> None:
    radar = _radar_with_sources()
    radar["global_search_policy"]["sources"][2]["usage_obligation"] = "disabled"

    plan = RadarSearchExpansionService(max_variants=8).plan_expansion(
        radar=radar,
        candidate_scope=["Губкинский газоперерабатывающий завод"],
        provider_metadata={},
        coverage_checks=[{"completeness_risk": "medium"}],
        unresolved_candidate_gaps=[],
    )

    assert plan.should_expand is True
    assert all("openrouter_web" not in item.source_ids for item in plan.variants)
    assert any(item.query.startswith("site:sibur.ru") for item in plan.variants)


def test_search_expansion_builds_prioritized_target_queue_from_source_backed_gaps() -> None:
    plan = RadarSearchExpansionService(max_variants=30).plan_expansion(
        radar=_radar_with_sources(),
        candidate_scope=[],
        provider_metadata={
            "candidate_universe_gaps": [
                {
                    "legal_name": "Губкинский газоперерабатывающий завод",
                    "entity_type": "production_site",
                    "source_refs": ["src_gubkin"],
                    "reason": "Found in retrieved source but not linked.",
                },
                {
                    "legal_name": 'АО "ПОЛИЭФ"',
                    "entity_type": "legal_entity",
                    "source_refs": ["src_polief"],
                },
            ],
        },
        coverage_checks=[{"completeness_risk": "high"}],
        unresolved_candidate_gaps=[],
    )

    targets = plan.to_payload()["targets"]
    assert targets[0]["target_type"] in {"known_subsidiary_or_legal_entity_target", "production_site_or_branch_target"}
    assert {item["target_label"] for item in targets} >= {"Губкинский газоперерабатывающий завод", 'АО "ПОЛИЭФ"'}
    assert any(item["budget_reserve_key"] == "production_site_coverage_probe" for item in targets)
    variants_by_target = plan.to_payload()["variants_by_target"]
    assert variants_by_target
    assert any(
        "site:sibur.ru Губкинский газоперерабатывающий завод" in item["query"]
        for variants in variants_by_target.values()
        for item in variants
    )


def test_search_expansion_uses_benchmark_target_hints_only_for_benchmark_profile() -> None:
    radar = _radar_with_sources()
    radar["task_context"] = {
        "benchmark_profile": "benchmark_smoke",
        "benchmark_target_hints": [{
            "baseline_id": "gubkinsky-gpp",
            "canonical_name": "Р“СѓР±РєРёРЅСЃРєРёР№ Р“РџР—",
            "entity_type": "production_site",
        }],
    }

    plan = RadarSearchExpansionService(max_variants=8).plan_expansion(
        radar=radar,
        candidate_scope=[],
        provider_metadata={},
        coverage_checks=[{"completeness_risk": "high"}],
        unresolved_candidate_gaps=[],
    )

    assert any(target.target_label == "Р“СѓР±РєРёРЅСЃРєРёР№ Р“РџР—" for target in plan.targets)
    assert any(target.target_type == "production_site_or_branch_target" for target in plan.targets)

    radar["task_context"]["benchmark_profile"] = ""
    non_benchmark_plan = RadarSearchExpansionService(max_variants=8).plan_expansion(
        radar=radar,
        candidate_scope=[],
        provider_metadata={},
        coverage_checks=[{"completeness_risk": "high"}],
        unresolved_candidate_gaps=[],
    )

    assert all(target.target_label != "Р“СѓР±РєРёРЅСЃРєРёР№ Р“РџР—" for target in non_benchmark_plan.targets)


def test_search_expansion_uses_source_profile_capabilities_not_hardcoded_dadata() -> None:
    radar = _radar_with_sources()
    radar["global_search_policy"]["sources"] = [
        {
            "source_id": "spark_registry",
            "source_type": "company_registry",
            "provider_id": "spark",
            "connector_profile_id": "dadata_registry",
            "usage_obligation": "required_for_identity",
        },
        {
            "source_id": "openrouter_web",
            "source_type": "search_engine",
            "reference": "openrouter:web_search",
            "usage_obligation": "required_for_coverage",
        },
    ]

    plan = RadarSearchExpansionService(max_variants=6).plan_expansion(
        radar=radar,
        candidate_scope=["АО ПОЛИЭФ"],
        provider_metadata={},
        coverage_checks=[{"completeness_risk": "medium"}],
        unresolved_candidate_gaps=[],
    )

    assert plan.should_expand
    assert all("spark_registry" not in item.source_ids for item in plan.variants)
    assert any("openrouter_web" in item.source_ids for item in plan.variants)


def test_search_expansion_diversifies_first_variants_across_target_types() -> None:
    radar = _radar_with_sources()
    radar["task_context"] = {
        "benchmark_profile": "benchmark_smoke",
        "benchmark_target_hints": [
            {"canonical_name": "SIBUR Holding", "entity_type": "legal_entity"},
            {"canonical_name": "Gubkinsky GPP plant", "entity_type": "production_site"},
            {"canonical_name": "Vyngapurovsky GPP plant", "entity_type": "production_site"},
            {"canonical_name": "ZapSibNeftekhim JSC", "entity_type": "legal_entity"},
        ],
    }

    plan = RadarSearchExpansionService(max_variants=4).plan_expansion(
        radar=radar,
        candidate_scope=[],
        provider_metadata={},
        coverage_checks=[{"completeness_risk": "high"}],
        unresolved_candidate_gaps=[],
    )

    target_types = [item.target_type for item in plan.variants]
    target_counts = Counter(item.target_id for item in plan.variants)
    assert "production_site_or_branch_target" in target_types
    assert "holding_or_group_target" in target_types
    assert "known_subsidiary_or_legal_entity_target" in target_types
    assert max(target_counts.values()) <= 2
    assert any(item.budget_reserve_key == "production_site_coverage_probe" for item in plan.variants)


def test_search_expansion_records_not_selected_targets_when_variant_cap_is_hit() -> None:
    radar = _radar_with_sources()
    radar["task_context"] = {
        "benchmark_profile": "benchmark_smoke",
        "benchmark_target_hints": [
            {"canonical_name": "SIBUR Holding", "entity_type": "legal_entity"},
            {"canonical_name": "Gubkinsky GPP plant", "entity_type": "production_site"},
            {"canonical_name": "Vyngapurovsky GPP plant", "entity_type": "production_site"},
            {"canonical_name": "Tobolsk production site", "entity_type": "production_site"},
            {"canonical_name": "ZapSibNeftekhim JSC", "entity_type": "legal_entity"},
        ],
    }

    payload = RadarSearchExpansionService(max_variants=2).plan_expansion(
        radar=radar,
        candidate_scope=[],
        provider_metadata={},
        coverage_checks=[{"completeness_risk": "high"}],
        unresolved_candidate_gaps=[],
    ).to_payload()

    assert payload["targets_not_selected"]
    assert all(item["not_searched_reason"] == "not_selected" for item in payload["targets_not_selected"])
    assert payload["targets_by_type"]["production_site_or_branch_target"] >= 3


def test_expansion_scheduler_orders_guaranteed_lanes_before_optional_variants() -> None:
    variants = [
        _variant("legal-1", "known_subsidiary_or_legal_entity_target", "legal query 1"),
        _variant("site-1", "production_site_or_branch_target", "site query 1"),
        _variant("holding-1", "holding_or_group_target", "holding query"),
        _variant("legal-2", "known_subsidiary_or_legal_entity_target", "legal query 2"),
        _variant("site-2", "production_site_or_branch_target", "site query 2"),
        _variant("alias-1", "alias_or_language_variant_target", "alias query"),
    ]

    schedule = schedule_guaranteed_expansion_variants(
        variants=variants,
        targets=[_target(item) for item in variants],
        minimums={
            "holding_or_group_target": 1,
            "known_subsidiary_or_legal_entity_target": 2,
            "production_site_or_branch_target": 2,
        },
    )

    first_five = schedule.scheduled_variants[:5]
    assert [item.schedule_role for item in first_five] == ["guaranteed"] * 5
    assert {item.variant.target_id for item in first_five} == {"holding-1", "legal-1", "legal-2", "site-1", "site-2"}
    assert schedule.scheduled_variants[5].schedule_role == "optional"
    assert schedule.lane_allocation["production_site_or_branch_target"]["scheduled_minimum_satisfied"] is True


def test_expansion_scheduler_reports_unscheduled_targets() -> None:
    variants = [_variant("holding-1", "holding_or_group_target", "holding query")]
    targets = [
        _target(variants[0]),
        {
            "target_id": "site-1",
            "target_label": "Site 1",
            "target_type": "production_site_or_branch_target",
            "budget_reserve_key": "production_site_coverage_probe",
        },
    ]

    schedule = schedule_guaranteed_expansion_variants(
        variants=variants,
        targets=targets,
        minimums={"holding_or_group_target": 1, "production_site_or_branch_target": 1},
    )

    assert schedule.lane_allocation["production_site_or_branch_target"]["scheduled_minimum_satisfied"] is False
    assert schedule.unscheduled_targets[0]["target_id"] == "site-1"
    assert schedule.unscheduled_targets[0]["not_searched_reason"] == "selected_but_not_scheduled"


def test_selector_picks_lane_minimums_before_optional_variants() -> None:
    variants = [
        _variant("holding-1", "holding_or_group_target", "holding query"),
        *[
            _variant(f"legal-{index}", "known_subsidiary_or_legal_entity_target", f"legal query {index}")
            for index in range(1, 11)
        ],
        *[
            _variant(f"site-{index}", "production_site_or_branch_target", f"site query {index}")
            for index in range(1, 11)
        ],
        *[
            _variant(f"optional-{index}", "source_backed_universe_gap_target", f"optional query {index}")
            for index in range(1, 4)
        ],
    ]

    selection = select_guaranteed_variants(
        variants,
        max_variants=3,
        minimums={
            "holding_or_group_target": 1,
            "known_subsidiary_or_legal_entity_target": 2,
            "production_site_or_branch_target": 2,
        },
        targets=[_target(item) for item in variants],
    )

    selected_by_type = Counter(item.target_type for item in selection.variants)
    first_five = selection.variants[:5]
    assert selection.effective_max_variants == 5
    assert selected_by_type["holding_or_group_target"] == 1
    assert selected_by_type["known_subsidiary_or_legal_entity_target"] == 2
    assert selected_by_type["production_site_or_branch_target"] == 2
    assert all(item.target_type != "source_backed_universe_gap_target" for item in first_five)
    assert selection.selected_guaranteed_count == 5
    assert selection.selected_optional_count == 0
    assert selection.diagnostics == []


def test_selector_reports_no_executable_variant_for_generated_lane_target() -> None:
    site_target = {
        "target_id": "site-1",
        "target_label": "Site 1",
        "target_type": "production_site_or_branch_target",
    }

    selection = select_guaranteed_variants(
        [_variant("holding-1", "holding_or_group_target", "holding query")],
        max_variants=5,
        minimums={"production_site_or_branch_target": 1},
        targets=[site_target],
    )

    reasons = {item["reason"] for item in selection.diagnostics}
    assert "no_executable_variant_for_target" in reasons
    assert selection.selected_guaranteed_count == 0


def test_benchmark_expansion_plan_raises_cap_to_lane_minimums() -> None:
    radar = _radar_with_sources()
    radar["task_context"] = {
        "benchmark_profile": "benchmark_smoke",
        "benchmark_target_probe_minimums": {
            "holding_or_group_target": 1,
            "known_subsidiary_or_legal_entity_target": 2,
            "production_site_or_branch_target": 2,
        },
        "benchmark_target_hints": [
            {"canonical_name": "SIBUR Holding", "entity_type": "legal_entity"},
            {"canonical_name": "ZapSibNeftekhim LLC", "entity_type": "legal_entity"},
            {"canonical_name": "POLIOM LLC", "entity_type": "legal_entity"},
            {"canonical_name": "Gubkinsky GPP plant", "entity_type": "production_site"},
            {"canonical_name": "Tobolsk production site", "entity_type": "production_site"},
        ],
    }

    payload = RadarSearchExpansionService(max_variants=3).plan_expansion(
        radar=radar,
        candidate_scope=[],
        provider_metadata={},
        coverage_checks=[{"completeness_risk": "high"}],
        unresolved_candidate_gaps=[],
    ).to_payload()

    selected_by_type = {
        key: len(value)
        for key, value in payload["variants_by_target_type"].items()
    }
    assert payload["selection_summary"]["effective_max_variants"] == 5
    assert payload["selection_summary"]["selected_guaranteed_count"] == 5
    assert selected_by_type["holding_or_group_target"] >= 1
    assert selected_by_type["known_subsidiary_or_legal_entity_target"] >= 2
    assert selected_by_type["production_site_or_branch_target"] >= 2


def test_registry_lookup_terms_generate_russian_variants_for_english_aliases() -> None:
    generator = RegistryLookupTermGenerator()

    polief = generator.terms_for_lookup(query='JSC "POLIEF"', candidate_scope=['JSC "POLIEF"'])
    neftekhim = generator.terms_for_lookup(query="SIBUR-Neftekhim JSC", candidate_scope=["SIBUR-Neftekhim JSC"])
    khimprom = generator.terms_for_lookup(query="SIBUR-Khimprom JSC", candidate_scope=["SIBUR-Khimprom JSC"])

    assert {'JSC "POLIEF"', "POLIEF", "ПОЛИЭФ", "АО ПОЛИЭФ"} <= set(polief.values)
    assert {"SIBUR-Neftekhim", "СИБУР-Нефтехим", "АО СИБУР-Нефтехим"} <= set(neftekhim.values)
    assert {"SIBUR-Khimprom", "СИБУР-Химпром", "АО СИБУР-Химпром"} <= set(khimprom.values)


def test_registry_lookup_terms_generate_site_relation_terms_from_russian_factory_name() -> None:
    plan = RegistryLookupTermGenerator().terms_for_lookup(
        query="ГУБКИНСКИЙ ГАЗОПЕРЕРАБАТЫВАЮЩИЙ ЗАВОД",
        candidate_scope=["ГУБКИНСКИЙ ГАЗОПЕРЕРАБАТЫВАЮЩИЙ ЗАВОД"],
        source_texts=["СИБУРТЮМЕНЬГАЗ управляет Губкинским ГПЗ"],
        limit=10,
    )

    assert "ГУБКИНСКИЙ ГАЗОПЕРЕРАБАТЫВАЮЩИЙ ЗАВОД" in plan.values
    assert "ГУБКИНСКИЙ ГПЗ" in plan.values
    assert "ГУБКИНСКИЙ ГАЗОПЕРЕРАБАТЫВАЮЩИЙ ЗАВОД СИБУР" in plan.values
    assert "ГУБКИНСКИЙ ГАЗОПЕРЕРАБАТЫВАЮЩИЙ ЗАВОД СИБУРТЮМЕНЬГАЗ" in plan.values


def test_registry_lookup_terms_skip_broad_and_placeholder_input() -> None:
    generator = RegistryLookupTermGenerator()

    broad = generator.terms_for_lookup(query="Найди все юридические лица группы СИБУР")
    placeholder = generator.terms_for_lookup(query="Кандидаты из шага 1", candidate_scope=["Кандидаты из шага 1"])

    assert broad.values == []
    assert placeholder.values == []


def test_recorded_dadata_tries_english_then_russian_terms_until_match() -> None:
    provider = RecordedDaDataCompanyRegistryProvider(fixtures=[{
        "source_ref": "dadata_polief",
        "legal_name": 'АО "ПОЛИЭФ"',
        "inn": "0258005638",
        "ogrn": "1020201699495",
    }])
    request = CompanyLookupRequest(
        radar_id="test",
        task_id="identity-polief",
        stage="qualification_gate",
        subject_id="q1",
        query='JSC "POLIEF"',
        source_id="dadata_registry",
        lookup_terms=['JSC "POLIEF"', "ПОЛИЭФ", "АО ПОЛИЭФ"],
        candidate_scope=['JSC "POLIEF"'],
    )

    result = provider.lookup_companies(request)

    attempts = result.provider_metadata["registry_lookup_attempts"]
    assert [item["term"] for item in attempts] == ['JSC "POLIEF"', "ПОЛИЭФ"]
    assert [item["outcome"] for item in attempts] == ["no_match", "used"]
    assert result.observations[0].legal_name == 'АО "ПОЛИЭФ"'
    assert result.outcomes[-1].observation_count == 1


def test_source_registry_uses_generated_russian_dadata_terms_for_english_alias() -> None:
    provider = RecordedDaDataCompanyRegistryProvider(fixtures=[{
        "source_ref": "dadata_polief",
        "legal_name": 'АО "ПОЛИЭФ"',
        "inn": "0258005638",
    }])
    task = RadarExecutionTask(
        task_id="identity-polief",
        stage="qualification_gate",
        subject_type="qualification",
        subject_id="q1",
        query='JSC "POLIEF"',
        purpose="Confirm identity.",
        source_ids=["dadata_registry"],
        candidate_scope=['JSC "POLIEF"'],
    )

    result = RadarSourceRegistry(company_registry_providers={"dadata": provider}).lookup_for_task(
        radar=_radar_with_sources(),
        task=task,
    )

    assert {'JSC "POLIEF"', "POLIEF", "ПОЛИЭФ", "АО ПОЛИЭФ"} <= set(provider.requests[0].lookup_terms)
    assert any(item["term"] in {"ПОЛИЭФ", "АО ПОЛИЭФ"} for item in result.provider_metadata["registry_lookup_attempts"])
    assert result.candidate_observations[0]["legal_name"] == 'АО "ПОЛИЭФ"'


def test_identity_obligation_no_match_is_non_blocking_with_source_backed_web_evidence() -> None:
    task = RadarExecutionTask(
        task_id="identity-polief",
        stage="qualification_gate",
        subject_type="qualification",
        subject_id="q1",
        query='JSC "POLIEF"',
        purpose="Confirm identity.",
        source_ids=["dadata_registry"],
        candidate_scope=['JSC "POLIEF"'],
    )
    source = RadarSourceEvidence(
        evidence_ref="web_polief",
        title="ПОЛИЭФ - СИБУР",
        url="https://www.sibur.ru/polief",
        snippet="ПОЛИЭФ входит в производственный контур СИБУР.",
        source_type="web",
    )
    observations = [{"legal_name": 'JSC "POLIEF"', "evidence_refs": ["web_polief"]}]

    decisions = obligation_decisions_from_plan(
        global_policy=_identity_only_radar()["global_search_policy"],
        steps=[task],
        source_policy_decisions=[{"source_id": "dadata_registry", "decision": "selected"}],
        source_provider_outcomes=[{
            "source_id": "dadata_registry",
            "provider_id": "dadata",
            "outcome": "no_match",
            "query": 'JSC "POLIEF"',
            "observation_count": 0,
        }],
        sources=[source],
        observations=observations,
    )

    by_source = {item["source_id"]: item for item in decisions}
    assert by_source["dadata_registry"]["status"] == "cross_source_identity_supported"
    assert source_obligation_summary(decisions)["blocking_count"] == 0


def test_identity_obligation_no_match_without_evidence_remains_blocking() -> None:
    task = RadarExecutionTask(
        task_id="identity-polief",
        stage="qualification_gate",
        subject_type="qualification",
        subject_id="q1",
        query='JSC "POLIEF"',
        purpose="Confirm identity.",
        source_ids=["dadata_registry"],
        candidate_scope=['JSC "POLIEF"'],
    )

    decisions = obligation_decisions_from_plan(
        global_policy=_identity_only_radar()["global_search_policy"],
        steps=[task],
        source_policy_decisions=[{"source_id": "dadata_registry", "decision": "selected"}],
        source_provider_outcomes=[{
            "source_id": "dadata_registry",
            "provider_id": "dadata",
            "outcome": "no_match",
            "query": 'JSC "POLIEF"',
            "observation_count": 0,
        }],
        sources=[],
        observations=[],
    )

    by_source = {item["source_id"]: item for item in decisions}
    assert by_source["dadata_registry"]["status"] == "identity_not_confirmed_after_all_terms"
    assert source_obligation_summary(decisions)["blocking_count"] == 1


def test_staged_execution_runs_search_expansion_for_coverage_gap() -> None:
    provider = _ExpansionProvider()
    radar = _radar_with_sources()
    radar["qualification_criteria"] = [{"code": "q1", "label": "SIBUR relation", "requirement_level": "required"}]
    plan = RadarExecutionPlan(
        radar_id="test",
        tasks=[
            RadarExecutionTask(
                task_id="discover",
                stage="qualification_discovery",
                subject_type="qualification",
                subject_id="q1",
                query="Find SIBUR production assets.",
                purpose="Discover.",
                source_ids=["openrouter_web"],
            ),
            RadarExecutionTask(
                task_id="coverage",
                stage="coverage_check",
                subject_type="qualification",
                subject_id="q1",
                query="Check weak coverage.",
                purpose="Coverage.",
                source_ids=["openrouter_web", "sibur_site"],
            ),
        ],
    )

    _, events, execution_results = run_staged_radar_execution(
        radar=radar,
        execution_plan=plan,
        provider=provider,
        max_total_web_tasks_per_run=10,
    )

    expansion_queries = [item["query"] for item in execution_results["search_expansion_query_variants"]]
    assert any("Губкинский газоперерабатывающий завод СИБУР" in query for query in expansion_queries)
    assert any(call.queries[0].query_id.startswith("coverage:search-expansion") for call in provider.calls)
    assert any(event.event_type == "search_expansion_executed" for event in events)
    assert any(item["legal_name"] == "Губкинский ГПЗ" for item in execution_results["candidate_universe"])


def test_staged_execution_skips_expansion_when_reserve_is_exhausted() -> None:
    provider = _ExpansionProvider()
    radar = _radar_with_sources()
    radar["qualification_criteria"] = [{"code": "q1", "label": "SIBUR relation", "requirement_level": "required"}]
    plan = RadarExecutionPlan(
        radar_id="test",
        tasks=[
            RadarExecutionTask(
                task_id="coverage",
                stage="coverage_check",
                subject_type="qualification",
                subject_id="q1",
                query="Check weak coverage.",
                purpose="Coverage.",
                source_ids=["openrouter_web", "sibur_site"],
            ),
        ],
    )
    budget = RadarExternalCallBudget(
        RadarExternalCallBudgetSettings(
            budget_reserve_limits={
                "official_coverage_probe": 0,
                "open_web_coverage_probe": 0,
                "production_site_coverage_probe": 0,
            }
        )
    )

    with external_call_budget_context(budget):
        _, events, execution_results = run_staged_radar_execution(
            radar=radar,
            execution_plan=plan,
            provider=provider,
            max_total_web_tasks_per_run=10,
        )

    assert execution_results["expansion_target_queue"]
    assert execution_results["targets_not_searched"]
    assert execution_results["budget_reserve_exhaustion_events"]
    assert any(event.event_type == "search_expansion_skipped_budget_reserve" for event in events)


class _ExpansionProvider:
    runtime_name = "expansion-provider"

    def __init__(self) -> None:
        self.calls: list[Any] = []

    def run_search_plan(self, *, radar: dict[str, Any], search_plan: Any) -> WebSearchProviderResult:
        self.calls.append(search_plan)
        query = search_plan.queries[0]
        if query.query_id == "discover":
            return WebSearchProviderResult(
                sources=[RadarSourceEvidence(
                    evidence_ref="src_candidate_a",
                    title="Candidate A - SIBUR",
                    url="https://www.sibur.ru/example/a",
                    snippet="Candidate A is connected to SIBUR.",
                    source_type="web",
                )],
                candidate_observations=[{
                    "legal_name": "Candidate A",
                    "evidence_refs": ["src_candidate_a"],
                    "qualification": [{
                        "criterion_code": "q1",
                        "status": "confirmed",
                        "evidence_refs": ["src_candidate_a"],
                    }],
                }],
            )
        if query.query_id == "coverage":
            return WebSearchProviderResult(provider_metadata={
                "coverage_findings": [{"summary": "Coverage is weak.", "completeness_risk": "high"}],
                "candidate_universe_gaps": [{
                    "legal_name": "Губкинский газоперерабатывающий завод",
                    "reason": "Coverage gap from weak discovery.",
                    "source_refs": [],
                }],
            })
        if "Губкинский" in query.query:
            return WebSearchProviderResult(
                sources=[RadarSourceEvidence(
                    evidence_ref="src_gubkin",
                    title="СИБУР рассказал про Губкинский газоперерабатывающий завод",
                    url="https://www.sibur.ru/example/gubkinsky-gpp",
                    snippet="Губкинский ГПЗ связан с производственным контуром СИБУР.",
                    source_type="web",
                )],
                candidate_observations=[{
                    "legal_name": "Губкинский ГПЗ",
                    "entity_type": "production_site",
                    "not_candidate_reason": "not_standalone_legal_entity",
                    "evidence_refs": ["src_gubkin"],
                    "review_flags": ["requires_human_review", "not_standalone_legal_entity"],
                    "qualification": [{
                        "criterion_code": "q1",
                        "status": "weak",
                        "evidence_refs": ["src_gubkin"],
                    }],
                }],
            )
        return WebSearchProviderResult()


def _radar_with_sources() -> dict[str, Any]:
    return {
        "radar_id": "test",
        "name": "SIBUR benchmark",
        "description": "Find SIBUR production assets.",
        "intent_signals": [],
        "global_search_policy": {
            "allow_open_web": True,
            "sources": [
                {
                    "source_id": "dadata_registry",
                    "source_type": "company_registry",
                    "provider_id": "dadata",
                    "reference": "company_registry:dadata",
                    "usage_obligation": "required_for_identity",
                },
                {
                    "source_id": "sibur_site",
                    "source_type": "url",
                    "reference": "https://www.sibur.ru",
                    "usage_obligation": "preferred",
                },
                {
                    "source_id": "openrouter_web",
                    "source_type": "search_engine",
                    "reference": "openrouter:web_search",
                    "usage_obligation": "required_for_coverage",
                },
            ],
        },
    }


def _identity_only_radar() -> dict[str, Any]:
    return {
        "radar_id": "identity-only",
        "global_search_policy": {
            "sources": [{
                "source_id": "dadata_registry",
                "source_type": "company_registry",
                "provider_id": "dadata",
                "reference": "company_registry:dadata",
                "usage_obligation": "required_for_identity",
            }],
        },
    }


def _variant(target_id: str, target_type: str, query: str) -> RadarSearchExpansionVariant:
    return RadarSearchExpansionVariant(
        query=query,
        source_ids=["openrouter_web"],
        source_scope="configured",
        reason="official_domain_coverage",
        target_id=target_id,
        target_type=target_type,
        budget_reserve_key=(
            "production_site_coverage_probe"
            if target_type == "production_site_or_branch_target"
            else "official_coverage_probe"
        ),
    )


def _target(variant: RadarSearchExpansionVariant) -> dict[str, Any]:
    return {
        "target_id": variant.target_id,
        "target_label": variant.query,
        "target_type": variant.target_type,
        "budget_reserve_key": variant.budget_reserve_key,
    }
