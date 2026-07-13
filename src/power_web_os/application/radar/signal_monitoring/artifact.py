"""Product-safe artifact projection for persisted signal-monitoring runs."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
import json
from typing import Any

from power_web_os.application.radar.signal_monitoring.contracts import SignalMonitoringInput, SignalMonitoringOutcome


class SignalMonitoringArtifactProjector:
    """Project one signal outcome into a durable product-safe report.

    Owns:
    - Stable artifact shape, summary counters, lineage, and redaction checks.

    Does not own:
    - Task execution, provider calls, budgets, or persistence transactions.

    Architecture:
    docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md
    """

    ARTIFACT_VERSION = "signal_monitoring.v2"

    def project(
        self,
        *,
        monitoring_input: SignalMonitoringInput,
        outcome: SignalMonitoringOutcome,
        provider_runtime: str,
    ) -> dict[str, Any]:
        observations = [item.model_dump(mode="json") for item in outcome.observations]
        search_counts = Counter(item["search_status"] for item in observations)
        observation_counts = Counter(item["observation_status"] for item in observations)
        artifact = {
            "artifact_type": "radar_signal_monitoring_report",
            "artifact_version": self.ARTIFACT_VERSION,
            "pipeline_id": "signal_monitoring",
            "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "run_id": outcome.run_id,
            "signal_run_id": outcome.run_id,
            "radar_id": outcome.radar_id,
            "source_candidate_run_id": outcome.source_candidate_run_id,
            "completion_state": outcome.completion_state,
            "candidate_scope_mode": outcome.candidate_scope_mode,
            "model_profile_id": outcome.model_profile_id,
            "model_profile_summary": dict(outcome.model_profile_summary),
            "provider_runtime": provider_runtime,
            "lookback_days": monitoring_input.lookback_days,
            "input_snapshot": monitoring_input.model_dump(mode="json", exclude={"model_profile"}),
            "summary": {
                "candidate_count": len(monitoring_input.candidates),
                "accepted_candidate_count": sum(
                    item.product_acceptance_status == "product_candidate" for item in monitoring_input.candidates
                ),
                "review_needed_candidate_count": sum(
                    item.product_acceptance_status != "product_candidate" for item in monitoring_input.candidates
                ),
                "signal_rule_count": len(monitoring_input.signal_rules),
                "task_count": len(outcome.tasks),
                "observation_count": len(observations),
                "provider_call_count": outcome.budget_counters.get("signal_provider_calls", 0),
                "retry_count": outcome.budget_counters.get("signal_extraction_retries", 0),
                "observations_by_search_status": dict(sorted(search_counts.items())),
                "observations_by_observation_status": dict(sorted(observation_counts.items())),
            },
            "candidates": [item.model_dump(mode="json") for item in monitoring_input.candidates],
            "signal_rules": [item.model_dump(mode="json") for item in monitoring_input.signal_rules],
            "known_sources": [item.model_dump(mode="json") for item in monitoring_input.known_sources],
            "source_binding_decisions": [item.model_dump(mode="json") for item in outcome.source_binding_decisions],
            "tasks": [item.model_dump(mode="json") for item in outcome.tasks],
            "search_plan": outcome.search_plan.model_dump(mode="json") if outcome.search_plan else {},
            "plan_acceptance": outcome.plan_acceptance.model_dump(mode="json") if outcome.plan_acceptance else {},
            "task_observations": [item.model_dump(mode="json") for item in outcome.task_observations],
            "observations": observations,
            "sources": [item.model_dump(mode="json") for item in outcome.sources],
            "source_strategy_decisions": [item.model_dump(mode="json") for item in outcome.source_strategy_decisions],
            "source_strategy_diagnostics": [item.model_dump(mode="json") for item in outcome.source_strategy_diagnostics],
            "provider_attempts": [item.model_dump(mode="json") for item in outcome.provider_attempts],
            "source_lane_ledger": [item.model_dump(mode="json") for item in outcome.source_lane_ledger],
            "search_execution_receipts": [item.model_dump(mode="json") for item in outcome.search_execution_receipts],
            "source_lifecycle": [item.model_dump(mode="json") for item in outcome.source_lifecycle],
            "window_policy": {
                "initial_lookback_days": monitoring_input.lookback_days,
                "lookback_basis": monitoring_input.lookback_basis,
                "as_of": monitoring_input.as_of,
                "incremental_overlap_days": monitoring_input.incremental_overlap_days,
                "criteria": {
                    rule.signal_code: {
                        "enabled": rule.enabled,
                        "initial_lookback_days": rule.initial_lookback_days,
                        "incremental_overlap_days": rule.incremental_overlap_days,
                        "cadence": rule.cadence,
                        "source_lanes": list(rule.source_lanes),
                        "basis": dict(rule.policy_basis),
                    }
                    for rule in monitoring_input.signal_rules
                },
            },
            "watermarks_before": [item.model_dump(mode="json") for item in outcome.watermarks_before],
            "watermarks_after": [item.model_dump(mode="json") for item in outcome.watermarks_after],
            "evidence_validation_summary": {
                "accepted": sum(item.accepted for item in outcome.evidence_validation_records),
                "rejected": sum(not item.accepted for item in outcome.evidence_validation_records),
                "records": [item.model_dump(mode="json") for item in outcome.evidence_validation_records],
            },
            "checkpoint_decisions": [item.model_dump(mode="json") for item in outcome.checkpoint_decisions],
            "budget_settings": dict(outcome.budget_settings),
            "budget_counters": dict(outcome.budget_counters),
            "budget_exhaustion_events": [dict(item) for item in outcome.budget_exhaustion_events],
            "budgets": {
                "settings": dict(outcome.budget_settings),
                "counters": dict(outcome.budget_counters),
                "exhaustion_events": [dict(item) for item in outcome.budget_exhaustion_events],
            },
            "diagnostics": [item.model_dump(mode="json") for item in outcome.diagnostics],
        }
        self._assert_product_safe(artifact)
        return artifact

    @staticmethod
    def _assert_product_safe(artifact: dict[str, Any]) -> None:
        serialized = json.dumps(artifact, ensure_ascii=False)
        forbidden = (
            "OPENROUTER_API_KEY",
            "Authorization",
            "Bearer ",
            "sk-or-",
            "chain_of_thought",
            "hidden_reasoning",
            "internal_thoughts",
        )
        if any(token in serialized for token in forbidden):
            raise RuntimeError("Refusing to persist unsafe signal-monitoring artifact")
