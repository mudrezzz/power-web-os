from __future__ import annotations

from types import SimpleNamespace

import pytest

import power_web_os.application.radar.candidate_discovery.service as service_module
from power_web_os.application.radar.candidate_discovery.contracts import (
    LiveICPRadarRunState,
    LiveRadarPipelineEvent,
    WebSearchProviderResult,
)
from power_web_os.application.radar.candidate_discovery.diagnostics.live_run_artifact import (
    LiveRadarRunArtifactProjector,
)
from power_web_os.application.radar.candidate_discovery.execution.options import CandidateDiscoveryExecutionOptions
from power_web_os.application.radar.candidate_discovery.execution.orchestrator import run_staged_radar_execution
from power_web_os.application.radar.candidate_discovery.planning.discovery_planning import (
    DeterministicRadarDiscoveryPlanner,
)
from power_web_os.application.radar.candidate_discovery.service import LiveRadarRunService
from power_web_os.application.radar.candidate_discovery.service_budget import ExternalBudgetMetadataMerger
from power_web_os.application.radar.candidate_discovery.service_context import LiveRadarTaskContextReader
from power_web_os.application.radar.candidate_discovery.service_events import LiveRadarEventStateProjector
from power_web_os.application.radar.candidate_discovery.service_factory import (
    LiveRadarRunComposition,
    LiveRadarRunServiceFactory,
)
from power_web_os.application.radar_source_providers import RadarSourceRegistry, SourceRegistryWebSearchProvider
from power_web_os.integrations.live_radar_openrouter import RecordedWebSearchProvider


def test_candidate_discovery_execution_options_parse_task_context() -> None:
    options = CandidateDiscoveryExecutionOptions.from_task_context(
        {
            "max_web_tasks_per_subject": "3",
            "max_discovery_tasks_per_rule": True,
            "max_gate_tasks_per_candidate_rule": -1,
            "run_profile": " smoke ",
            "budget_reserve_limits": {"planner": "2", "bad": True, 3: 4, "negative": -1},
            "semantic_task_reserve_limits": {"signal": 5},
        },
        {
            "source_policy_decisions": [{"source": "registry"}, "skip"],
        },
    )

    assert options.max_web_tasks_per_subject == 3
    assert options.max_discovery_tasks_per_rule is None
    assert options.max_gate_tasks_per_candidate_rule is None
    assert options.run_profile == "smoke"
    assert options.budget_reserve_limits == {"planner": 2}
    assert options.semantic_task_reserve_limits == {"signal": 5}
    assert options.source_policy_decisions == [{"source": "registry"}]


def test_live_radar_task_context_reader_returns_staged_execution_options() -> None:
    options = LiveRadarTaskContextReader({
        "max_web_tasks_per_subject": "3",
        "max_discovery_tasks_per_rule": True,
        "max_gate_tasks_per_candidate_rule": -1,
        "run_profile": " smoke ",
        "budget_reserve_limits": {"planner": "2", "bad": True, 3: 4, "negative": -1},
        "semantic_task_reserve_limits": {"signal": 5},
    }).staged_execution_options({
        "source_policy_decisions": [{"source": "registry"}, "skip"],
    })

    assert isinstance(options, CandidateDiscoveryExecutionOptions)
    assert options.max_web_tasks_per_subject == 3
    assert options.max_discovery_tasks_per_rule is None
    assert options.max_gate_tasks_per_candidate_rule is None
    assert options.run_profile == "smoke"
    assert options.budget_reserve_limits == {"planner": 2}
    assert options.semantic_task_reserve_limits == {"signal": 5}
    assert options.source_policy_decisions == [{"source": "registry"}]


def test_candidate_discovery_execution_options_project_budget_contracts() -> None:
    options = CandidateDiscoveryExecutionOptions.from_legacy_kwargs(
        max_web_tasks_per_subject=1,
        max_total_web_tasks_per_run=10,
        max_discovery_tasks_per_rule=2,
        semantic_task_reserve_limits={"coverage": 3},
        run_profile="smoke",
        max_openrouter_calls_per_run=4,
        budget_reserve_limits={"primary_discovery": 2},
        min_useful_sources_per_discovery_task=1,
        min_candidates_per_discovery_task=2,
        max_discovery_retries_per_task=3,
        max_checkpoint_revisions_per_run=4,
        max_checkpoint_retries_per_stage=5,
    )

    task_settings = options.to_task_budget_settings()
    external_settings = options.to_external_budget_settings()
    useful_budget = options.to_useful_budget()

    assert task_settings.compatibility_max_web_tasks_per_subject == 1
    assert task_settings.max_total_tasks_per_run == 10
    assert task_settings.max_discovery_tasks_per_rule == 2
    assert task_settings.semantic_task_reserve_limits == {"coverage": 3}
    assert external_settings.run_profile == "smoke"
    assert external_settings.max_openrouter_calls_per_run == 4
    assert external_settings.budget_reserve_limits["primary_discovery"] == 2
    assert useful_budget.min_sources == 1
    assert useful_budget.min_candidates == 2
    assert useful_budget.max_retries == 3
    assert options.checkpoint_policy_kwargs() == {
        "max_revisions_per_run": 4,
        "max_retries_per_stage": 5,
    }


def test_staged_execution_rejects_mixed_options_and_legacy_kwargs() -> None:
    with pytest.raises(ValueError, match="options"):
        run_staged_radar_execution(
            radar={},
            execution_plan=None,  # type: ignore[arg-type]
            provider=None,  # type: ignore[arg-type]
            options=CandidateDiscoveryExecutionOptions(),
            max_total_web_tasks_per_run=1,
        )


def test_live_radar_run_service_factory_builds_default_composition() -> None:
    provider = RecordedWebSearchProvider({"sources": [], "candidate_observations": []})
    source_registry = RadarSourceRegistry()

    composition = LiveRadarRunServiceFactory().build_composition(
        provider,
        source_registry=source_registry,
    )

    assert isinstance(composition, LiveRadarRunComposition)
    assert isinstance(composition.provider, SourceRegistryWebSearchProvider)
    assert isinstance(composition.discovery_planner, DeterministicRadarDiscoveryPlanner)
    assert composition.connector_profile_registry is source_registry.connector_profile_registry
    assert isinstance(composition.artifact_projector, LiveRadarRunArtifactProjector)
    assert isinstance(composition.budget_metadata_merger, ExternalBudgetMetadataMerger)
    assert isinstance(composition.event_state_projector, LiveRadarEventStateProjector)
    assert composition.task_context_reader_factory is LiveRadarTaskContextReader


def test_live_radar_run_service_factory_preserves_injected_collaborators() -> None:
    provider = RecordedWebSearchProvider({"sources": [], "candidate_observations": []})
    planner = DeterministicRadarDiscoveryPlanner()
    artifact_projector = LiveRadarRunArtifactProjector(provider)
    budget_merger = ExternalBudgetMetadataMerger()
    event_projector = LiveRadarEventStateProjector()

    def reader_factory(task_context: dict[str, object]) -> LiveRadarTaskContextReader:
        return LiveRadarTaskContextReader(task_context)

    composition = LiveRadarRunServiceFactory().build_composition(
        provider,
        discovery_planner=planner,
        artifact_projector=artifact_projector,
        budget_metadata_merger=budget_merger,
        event_state_projector=event_projector,
        task_context_reader_factory=reader_factory,
    )

    assert composition.provider is provider
    assert composition.discovery_planner is planner
    assert composition.artifact_projector is artifact_projector
    assert composition.budget_metadata_merger is budget_merger
    assert composition.event_state_projector is event_projector
    assert composition.task_context_reader_factory is reader_factory


def test_live_radar_run_service_factory_create_and_legacy_constructor_remain_compatible() -> None:
    provider = RecordedWebSearchProvider({"sources": [], "candidate_observations": []})

    service_from_factory = LiveRadarRunServiceFactory().create(provider)
    service_from_legacy_constructor = LiveRadarRunService(provider)

    assert isinstance(service_from_factory, LiveRadarRunService)
    assert isinstance(service_from_legacy_constructor, LiveRadarRunService)


def test_live_radar_run_service_uses_injected_task_context_reader_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = RecordedWebSearchProvider({"sources": [], "candidate_observations": []})
    captured: dict[str, object] = {}

    class RecordingReader:
        def __init__(self, task_context: dict[str, object]) -> None:
            captured["task_context"] = task_context

        def staged_execution_options(self, discovery_plan: dict[str, object]) -> CandidateDiscoveryExecutionOptions:
            captured["discovery_plan"] = discovery_plan
            return CandidateDiscoveryExecutionOptions(max_total_web_tasks_per_run=1)

    def fake_run_staged_radar_execution(**kwargs: object) -> tuple[WebSearchProviderResult, list[object], dict[str, int]]:
        captured["options"] = kwargs["options"]
        return WebSearchProviderResult(), [], {"executed_task_count": 0}

    monkeypatch.setattr(service_module, "run_staged_radar_execution", fake_run_staged_radar_execution)
    service = LiveRadarRunServiceFactory().create(
        provider,
        task_context_reader_factory=RecordingReader,
    )
    state = LiveICPRadarRunState(
        task_context={"max_total_web_tasks_per_run": 9},
        discovery_plan={"source_policy_decisions": []},
        live=False,
    )

    service.run_web_search(state)

    assert captured["task_context"] == {"max_total_web_tasks_per_run": 9}
    assert captured["discovery_plan"] == {"source_policy_decisions": []}
    assert isinstance(captured["options"], CandidateDiscoveryExecutionOptions)
    assert captured["options"].max_total_web_tasks_per_run == 1


def test_external_budget_metadata_merger_preserves_all_budget_surfaces() -> None:
    merged = ExternalBudgetMetadataMerger().merge(
        {
            "external_call_budget_counters": {"openrouter_server_tool_web_search:run": 1, "planner": "2"},
            "external_call_budget_counters_by_role": {"planner": 1},
            "budget_reserve_counters": {"semantic": "4"},
            "external_call_budget_exhaustion_events": [{"event": "base"}],
            "provider_retry_records": [{"retry": "base"}],
            "post_call_budget_overruns": [{"overrun": "base"}],
            "budget_reserve_exhaustion_events": [{"reserve": "base"}],
            "openrouter_server_tool_usage": {"web_search_requests": 1},
            "external_call_budget_settings": {"max": 5},
            "run_profile": "smoke",
        },
        {
            "external_call_budget_counters": {"openrouter_server_tool_web_search:run": 3},
            "external_call_budget_counters_by_role": {"execution": 2},
            "budget_reserve_counters": {"semantic": 1},
            "external_call_budget_exhaustion_events": [{"event": "current"}],
            "provider_retry_records": [{"retry": "current"}],
            "post_call_budget_overruns": [{"overrun": "current"}],
            "budget_reserve_exhaustion_events": [{"reserve": "current"}],
            "openrouter_server_tool_usage": {"web_search_requests": 0},
        },
    )

    assert merged["external_call_budget_counters"] == {
        "openrouter_server_tool_web_search:run": 4,
        "planner": 2,
    }
    assert merged["external_call_budget_counters_by_role"] == {"planner": 1, "execution": 2}
    assert merged["budget_reserve_counters"] == {"semantic": 5}
    assert merged["external_call_budget_exhaustion_events"] == [{"event": "base"}, {"event": "current"}]
    assert merged["provider_retry_records"] == [{"retry": "base"}, {"retry": "current"}]
    assert merged["post_call_budget_overruns"] == [{"overrun": "base"}, {"overrun": "current"}]
    assert merged["budget_reserve_exhaustion_events"] == [{"reserve": "base"}, {"reserve": "current"}]
    assert merged["openrouter_server_tool_usage"]["web_search_requests"] == 4
    assert merged["external_call_budget_settings"] == {"max": 5}
    assert merged["run_profile"] == "smoke"


def test_live_radar_event_state_projector_appends_event_payloads() -> None:
    state = SimpleNamespace(pipeline_events=[{"event_type": "existing"}])
    event = LiveRadarPipelineEvent(
        event_type="source_collected",
        phase="collection",
        actor="provider",
        node_name="run_web_search",
        visibility="operator",
        summary="Collected sources.",
    )

    projected = LiveRadarEventStateProjector().append(state, [event])

    assert projected[0] == {"event_type": "existing"}
    assert projected[1]["event_type"] == "source_collected"
    assert projected[1]["phase"] == "collection"
