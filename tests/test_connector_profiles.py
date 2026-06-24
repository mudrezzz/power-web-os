from __future__ import annotations

from pathlib import Path

from power_web_os.application.connector_profiles import (
    ConnectorProfile,
    ConnectorProfileRegistry,
    compile_connector_capability,
    load_connector_profile,
    validate_connector_profile,
)
from power_web_os.application.live_radar_contracts import RadarExecutionTask
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
    assert "DADATA_API_KEY" in dadata.credential_env_vars
    assert openrouter is not None
    assert openrouter.source_type == "search_engine"
    assert openrouter.supports_broad_discovery
    assert openrouter.supports_coverage
    assert openrouter.supports_signal_evidence
    assert sibur is not None
    assert sibur.source_type == "url"
    assert sibur.supports_coverage
    assert not sibur.supports_lookup


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
    assert "legal_identity" in capability.returned_fact_kinds


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
