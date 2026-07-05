from __future__ import annotations

from pathlib import Path

from power_web_os.application.connector_profiles import (
    ConnectorProfile,
    ConnectorProfileRegistry,
    compile_connector_capability,
    default_connector_profile_registry,
    load_connector_profile,
    validate_connector_profile,
)
from power_web_os.application.radar.candidate_discovery.planning.discovery_planning import build_discovery_planning_input
from power_web_os.application.radar.candidate_discovery.contracts import RadarExecutionTask
from power_web_os.application.radar.shared.source_cards import RadarPlannerSourceUse
from power_web_os.application.radar_source_providers import RadarSourceRegistry


def test_default_connector_profiles_load_and_compile() -> None:
    registry = ConnectorProfileRegistry.from_directory(Path("config/connectors"))

    dadata = registry.capability("dadata_registry")
    openrouter = registry.capability("openrouter_web")
    sibur = registry.capability("sibur_site")

    assert dadata is not None
    assert dadata.source_type == "company_registry"
    assert dadata.supports_lookup
    assert dadata.supports_identity
    assert dadata.supports_enrichment
    assert dadata.requires_concrete_input
    assert not dadata.supports_broad_discovery
    assert not dadata.supports_coverage
    assert not dadata.supports_signal_evidence
    assert "free_text_query" not in dadata.required_input_kinds
    assert "DADATA_API_KEY" in dadata.credential_env_vars
    assert dadata.capability_class == "lookup_only_identity_enrichment"
    assert "concrete_company" in dadata.accepted_input_shapes
    assert "broad_query" in dadata.bad_input_shapes
    assert "alias_no_match_non_blocking" in dadata.non_blocking_outcomes
    assert {"ru", "en"} <= set(dadata.language_hints)
    assert openrouter is not None
    assert openrouter.source_type == "search_engine"
    assert openrouter.supports_broad_discovery
    assert openrouter.supports_coverage
    assert openrouter.supports_signal_evidence
    assert openrouter.capability_class == "broad_web_retrieval"
    assert "broad_query" in openrouter.accepted_input_shapes
    assert sibur is not None
    assert sibur.source_type == "url"
    assert sibur.supports_coverage
    assert not sibur.supports_lookup
    assert sibur.capability_class == "official_or_domain_coverage"


def test_default_connector_registry_loads_from_docker_like_cwd(tmp_path: Path, monkeypatch) -> None:
    config_dir = tmp_path / "config" / "connectors"
    config_dir.mkdir(parents=True)
    for profile_path in Path("config/connectors").glob("*.json"):
        (config_dir / profile_path.name).write_text(profile_path.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    registry = default_connector_profile_registry()

    assert registry.capability("dadata_registry") is not None
    assert registry.capability("openrouter_web") is not None
    assert registry.capability("sibur_site") is not None


def test_connector_profile_with_internal_stage_name_is_rejected() -> None:
    profile = ConnectorProfile(
        id="bad_profile",
        display_name="Bad profile",
        description="This profile says qualification_gate and should be rejected.",
        source_type="search_engine",
        runtime_provider_id="bad",
        good_inputs=("free text",),
        bad_inputs=("none",),
        expected_facts=("url",),
        limitations=("none",),
    )

    issues = validate_connector_profile(profile)

    assert {issue.code for issue in issues} == {"connector_profile_uses_internal_stage_names"}


def test_profile_loader_reports_missing_required_fields(tmp_path: Path) -> None:
    profile_path = tmp_path / "minimal.json"
    profile_path.write_text('{"id": "minimal", "display_name": "Minimal"}', encoding="utf-8")

    profile, issues = load_connector_profile(profile_path)

    assert profile is not None
    assert "connector_profile_missing_fields" in {issue.code for issue in issues}


def test_human_profile_compiles_to_lookup_only_capability() -> None:
    profile = ConnectorProfile(
        id="generic_registry",
        display_name="Generic registry",
        description="Company registry lookup for legal entity identity and enrichment.",
        source_type="company_registry",
        runtime_provider_id="generic",
        good_inputs=("Concrete legal name", "INN", "OGRN"),
        bad_inputs=("Broad natural-language holding contour discovery",),
        expected_facts=("Legal entity name", "INN", "OGRN", "Address", "Status"),
        limitations=("Lookup-only source; not a broad enumeration engine",),
    )

    capability = compile_connector_capability(profile)

    assert capability.supports_lookup
    assert capability.supports_identity
    assert capability.requires_concrete_input
    assert not capability.supports_broad_discovery
    assert not capability.supports_coverage
    assert not capability.supports_signal_evidence
    assert "free_text_query" not in capability.required_input_kinds
    assert "legal_identity" in capability.returned_fact_kinds


def test_spark_like_registry_profile_compiles_without_provider_specific_branch() -> None:
    profile = ConnectorProfile(
        id="spark_registry",
        display_name="SPARK registry",
        description="Structured company registry lookup for legal identity, registry status, and enrichment facts.",
        source_type="company_registry",
        runtime_provider_id="spark",
        good_inputs=("Concrete company name", "INN", "OGRN", "Russian legal-name alias"),
        bad_inputs=("Broad holding contour enumeration", "Signal evidence query"),
        expected_facts=("Legal entity name", "INN", "OGRN", "Registry status", "Industry"),
        limitations=("Lookup-only source; requires concrete input",),
    )

    capability = compile_connector_capability(profile)

    assert capability.capability_class == "lookup_only_identity_enrichment"
    assert capability.requires_concrete_input
    assert not capability.supports_broad_discovery
    assert "broad_query" in capability.bad_input_shapes
    assert "alias_no_match_non_blocking" in capability.non_blocking_outcomes


def test_planner_source_cards_are_compiled_without_credentials() -> None:
    planning_input = build_discovery_planning_input(
        radar={
            "radar_id": "source-card-radar",
            "qualification_criteria": [{"code": "Q1", "label": "Find companies"}],
            "global_search_policy": {
                "sources": [
                    {"source_id": "dadata_registry", "connector_profile_id": "dadata_registry", "usage_obligation": "required_for_identity"},
                    {"source_id": "openrouter_web", "connector_profile_id": "openrouter_web", "usage_obligation": "required_for_coverage"},
                    {"source_id": "sibur_site", "connector_profile_id": "sibur_site", "usage_obligation": "preferred"},
                ]
            },
        },
        task_context={},
        live=False,
        provider_metadata={},
    )

    cards = {card.source_id: card for card in planning_input.source_cards}
    serialized = str([card.model_dump() for card in planning_input.source_cards])

    assert cards["dadata_registry"].requires_concrete_input
    assert not cards["dadata_registry"].supports_broad_discovery
    assert not cards["dadata_registry"].supports_coverage
    assert not cards["dadata_registry"].supports_signal_evidence
    assert "free_text_query" not in cards["dadata_registry"].required_input_kinds
    assert cards["openrouter_web"].supports_broad_discovery
    assert cards["openrouter_web"].supports_signal_evidence
    assert cards["sibur_site"].source_type == "url"
    assert "DADATA_API_KEY" not in serialized
    assert "DADATA_SECRET_KEY" not in serialized
    assert "OPENROUTER_API_KEY" not in serialized


def test_planner_source_use_accepts_official_domain_query_shape() -> None:
    source_use = RadarPlannerSourceUse(
        source_id="sibur_site",
        connector_profile_id="sibur_site",
        intended_use="official_evidence",
        input_shape="official_domain_query",
        expected_fact_kinds=["web_source"],
        rationale="Search the configured official domain for source-backed coverage.",
    )

    assert source_use.input_shape == "official_domain_query"


def test_lookup_only_profile_blocks_broad_registry_lookup_without_provider_call() -> None:
    registry = ConnectorProfileRegistry.from_profiles([
        ConnectorProfile(
            id="generic_registry",
            display_name="Generic registry",
            description="Company registry lookup for legal entity identity.",
            source_type="company_registry",
            runtime_provider_id="generic",
            good_inputs=("Concrete legal name", "INN", "OGRN"),
            bad_inputs=("Broad natural-language holding contour discovery",),
            expected_facts=("Legal entity name", "INN", "OGRN"),
            limitations=("Lookup-only source; not a broad enumeration engine",),
        )
    ])
    provider = _CountingCompanyRegistryProvider()
    radar = {
        "radar_id": "generic-radar",
        "global_search_policy": {
            "sources": [{
                "source_id": "generic_registry",
                "connector_profile_id": "generic_registry",
                "source_type": "company_registry",
                "provider_id": "generic",
                "reference": "company_registry:generic",
            }]
        },
    }
    task = RadarExecutionTask(
        task_id="discover",
        stage="qualification_discovery",
        subject_type="qualification",
        subject_id="Q1",
        rule_snapshot="Find all companies in the target holding.",
        query="Find all legal entities in the holding contour",
        purpose="Discover candidate universe.",
        source_ids=["generic_registry"],
    )

    result = RadarSourceRegistry(
        company_registry_providers={"generic": provider},
        connector_profile_registry=registry,
    ).lookup_for_task(radar=radar, task=task)

    assert provider.calls == 0
    outcome = result.provider_metadata["source_provider_outcomes"][0]
    assert outcome["outcome"] == "registry_lookup_insufficient"
    assert outcome["connector_profile_id"] == "generic_registry"


class _CountingCompanyRegistryProvider:
    provider_id = "generic"
    provider_type = "company_registry"

    def __init__(self) -> None:
        self.calls = 0

    def lookup_companies(self, request):  # noqa: ANN001
        self.calls += 1
        raise AssertionError("Broad lookup-only registry requests must be blocked before provider call.")
