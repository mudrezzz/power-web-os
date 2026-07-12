from __future__ import annotations

from typing import Any

from power_web_os.application.radar.shared.source_cards import RadarPlannerSourceCard
from power_web_os.application.radar.signal_monitoring.contracts import (
    SignalAttemptRole,
    SignalMonitoringCandidate,
    SignalMonitoringProviderResult,
    SignalMonitoringInput,
    SignalMonitoringSignalRule,
    SignalMonitoringSourceHint,
    SignalMonitoringSourcePolicy,
    SignalSearchTask,
    SignalSourceRef,
)
from power_web_os.application.radar.signal_monitoring.executor import SignalMonitoringExecutor
from power_web_os.application.radar.signal_monitoring.source_strategy import SignalMonitoringSourceStrategy


class ScriptedSignalProvider:
    runtime_name = "scripted-signal-provider"

    def __init__(self, payloads: list[Any]) -> None:
        self.payloads = list(payloads)
        self.calls: list[tuple[str, SignalAttemptRole]] = []

    def run_signal_task(
        self,
        *,
        task: SignalSearchTask,
        attempt_role: SignalAttemptRole,
    ) -> SignalMonitoringProviderResult:
        self.calls.append((task.task_id, attempt_role))
        payload = self.payloads.pop(0) if self.payloads else searched_negative_payload()
        return SignalMonitoringProviderResult(payload=payload)


def card(
    source_id: str,
    *,
    profile_id: str | None = None,
    source_type: str = "web",
    signal: bool = True,
    broad: bool = False,
) -> RadarPlannerSourceCard:
    return RadarPlannerSourceCard(
        source_id=source_id,
        source_label=source_id,
        connector_profile_id=profile_id or source_id,
        source_type=source_type,
        supports_signal_evidence=signal,
        supports_broad_discovery=broad,
    )


def monitoring_input(**overrides: Any) -> SignalMonitoringInput:
    payload: dict[str, Any] = {
        "run_id": "signal-run-source-strategy",
        "radar_id": "signal-radar",
        "candidates": [
            SignalMonitoringCandidate(
                candidate_id="candidate-a",
                display_name="Candidate A",
                source_refs=["known-src-a"],
            )
        ],
        "signal_rules": [SignalMonitoringSignalRule(signal_code="toir_tender", label="TOIR tender")],
        "source_cards": [card("openrouter_web", source_type="open_web", signal=True, broad=True)],
    }
    payload.update(overrides)
    return SignalMonitoringInput(**payload)


def observed_payload(*, summary: str = "New TOIR tender", observed_at: str = "2026-06-30") -> dict[str, Any]:
    return {
        "sources": [
            {
                "source_ref": "src-signal",
                "title": "Tender",
                "url": "https://example.test/signal",
                "snippet": "Candidate A posted a TOIR tender.",
                "published_at": observed_at,
            }
        ],
        "observations": [
            {
                "candidate_id": "candidate-a",
                "signal_code": "toir_tender",
                "status": "observed",
                "summary": summary,
                "score": 2,
                "evidence_refs": ["src-signal"],
                "event_at": observed_at,
            }
        ],
    }


def searched_negative_payload() -> dict[str, Any]:
    return {
        "sources": [{"source_ref": "src-empty", "title": "Search result", "url": "https://example.test/empty"}],
        "observations": [
            {
                "candidate_id": "candidate-a",
                "signal_code": "toir_tender",
                "status": "not_observed",
                "summary": "Searched the allowed sources and found no fresh signal.",
            }
        ],
    }


def test_strategy_prefers_known_sources_before_official_and_open_web() -> None:
    strategy = SignalMonitoringSourceStrategy()
    result = strategy.select_sources(
        monitoring_input(
            known_sources=[
                SignalSourceRef(
                    source_ref="known-src-a",
                    title="Candidate page",
                    url="https://candidate.test/news",
                    source_id="candidate_site",
                    lifecycle_state="used",
                )
            ],
            source_cards=[
                card("candidate_site", source_type="web", signal=True),
                card("official_site", source_type="url", signal=True),
                card("openrouter_web", source_type="open_web", signal=True, broad=True),
            ],
            source_policy=SignalMonitoringSourcePolicy(official_source_ids=["official_site"]),
        )
    )

    selected = [decision.lane for decision in result.decisions if decision.status == "selected"]
    assert selected[:3] == ["known_source", "official_company", "open_web"]


def test_strategy_orders_signal_specific_before_generic_open_web() -> None:
    result = SignalMonitoringSourceStrategy().select_sources(
        monitoring_input(
            source_cards=[
                card("signal_portal", source_type="web", signal=True),
                card("openrouter_web", source_type="open_web", signal=True, broad=True),
            ],
            source_policy=SignalMonitoringSourcePolicy(
                signal_source_hints=[SignalMonitoringSourceHint(source_id="signal_portal", label="Tender portal")]
            ),
        )
    )

    selected = [decision.lane for decision in result.decisions if decision.status == "selected"]
    assert selected[:2] == ["signal_specific", "open_web"]


def test_broad_web_source_in_criterion_policy_remains_separate_open_web_lane() -> None:
    result = SignalMonitoringSourceStrategy().select_sources(
        monitoring_input(
            source_cards=[card("openrouter_web", source_type="search_engine", signal=True, broad=True)],
            source_policy=SignalMonitoringSourcePolicy(
                preferred_source_ids=["openrouter_web"],
                allowed_source_ids=["openrouter_web"],
            ),
        )
    )

    selected = [decision for decision in result.decisions if decision.status == "selected"]
    assert [decision.lane for decision in selected] == ["open_web"]


def test_open_web_is_not_selected_when_policy_disallows_it() -> None:
    result = SignalMonitoringSourceStrategy().select_sources(
        monitoring_input(source_policy=SignalMonitoringSourcePolicy(allow_open_web=False))
    )

    assert result.selected_decision_ids == []
    assert any(decision.reason == "Open web signal search is disabled by signal source policy." for decision in result.decisions)


def test_required_source_without_signal_capability_is_blocking() -> None:
    result = SignalMonitoringSourceStrategy().select_sources(
        monitoring_input(
            source_cards=[card("registry_identity", profile_id="registry_profile", signal=False)],
            source_policy=SignalMonitoringSourcePolicy(required_source_ids=["registry_identity"], allow_open_web=False),
        )
    )

    assert any(
        decision.reason == "required_signal_source_not_signal_capable" and decision.diagnostic_severity == "blocking"
        for decision in result.decisions
    )
    assert any(diagnostic.code == "required_signal_source_not_signal_capable" for diagnostic in result.diagnostics)


def test_identity_only_connector_is_skipped_by_capability_not_provider_name() -> None:
    result = SignalMonitoringSourceStrategy().select_sources(
        monitoring_input(
            source_cards=[card("company_registry", profile_id="anything_identity_only", signal=False)],
            source_policy=SignalMonitoringSourcePolicy(preferred_source_ids=["company_registry"], allow_open_web=False),
        )
    )

    serialized = result.model_dump_json()
    assert "source_not_signal_capable" in serialized or "no_executable_signal_source_lane" in serialized
    assert "dadata" not in serialized.lower()


def test_signal_capable_registry_like_connector_is_allowed_by_capability() -> None:
    result = SignalMonitoringSourceStrategy().select_sources(
        monitoring_input(
            source_cards=[card("spark_like_registry", profile_id="spark_like", source_type="registry", signal=True, broad=True)],
            source_policy=SignalMonitoringSourcePolicy(allowed_source_ids=["spark_like_registry"]),
        )
    )

    assert result.selected_decision_ids
    assert any(decision.source_id == "spark_like_registry" for decision in result.decisions if decision.status == "selected")


def test_executor_executes_known_and_official_lanes_without_losing_source_decisions() -> None:
    provider = ScriptedSignalProvider([searched_negative_payload(), observed_payload()])
    monitoring = monitoring_input(
        known_sources=[
            SignalSourceRef(
                source_ref="known-src-a",
                title="Known page",
                url="https://candidate.test/known",
                source_id="candidate_site",
            )
        ],
        configured_sources=[SignalSourceRef(
            source_ref="configured:official_site",
            title="Official site",
            url="https://official.test",
            source_id="official_site",
        )],
        source_cards=[
            card("candidate_site", signal=True),
            card("official_site", signal=True),
        ],
        source_policy=SignalMonitoringSourcePolicy(official_source_ids=["official_site"], allow_open_web=False),
    )

    outcome = SignalMonitoringExecutor(provider).run(monitoring)

    assert {task.source_lane for task in outcome.tasks} == {"known_source", "official_company"}
    assert len(provider.calls) == 2
    assert {item.status for item in outcome.source_lane_ledger} == {"executed"}
    assert len(outcome.search_execution_receipts) == 2
    assert any(
        decision.lane == "official_company" and decision.status == "selected"
        for decision in outcome.source_strategy_decisions
    )


def test_all_lanes_limited_produces_not_searched_policy_limited_not_not_observed() -> None:
    provider = ScriptedSignalProvider([observed_payload()])
    monitoring = monitoring_input(
        source_cards=[card("identity_only", signal=False)],
        source_policy=SignalMonitoringSourcePolicy(allowed_source_ids=["identity_only"], allow_open_web=False),
    )

    outcome = SignalMonitoringExecutor(provider).run(monitoring)

    assert outcome.tasks
    assert outcome.observations[0].observation_status == "unclear"
    assert outcome.observations[0].search_status == "not_searched_policy_limited"
    assert provider.calls == []
