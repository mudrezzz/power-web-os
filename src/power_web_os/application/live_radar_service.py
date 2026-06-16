"""Application service for one live Radar execution pass.

The service owns provider-neutral orchestration: build a plan, call a provider
port, normalize observations, validate contracts, and shape the live run artifact.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from power_web_os.application.live_radar_contracts import (
    LiveICPRadarRunState,
    LiveRadarRunArtifact,
    WebSearchProvider,
)
from power_web_os.application.live_radar_definition import build_live_mini_radar_definition, build_live_mini_radar_search_plan
from power_web_os.application.live_radar_normalization import (
    _dedupe_sources,
    _rank_candidates,
    normalize_live_candidate,
    validate_live_radar_qualification_contract,
)


class LiveRadarRunService:
    def __init__(self, provider: WebSearchProvider) -> None:
        self._provider = provider

    def run(self, *, state: LiveICPRadarRunState, node_name: str, runtime_mode: str, framework_available: bool) -> LiveICPRadarRunState:
        radar = state.radar or build_live_mini_radar_definition()
        plan = build_live_mini_radar_search_plan(radar)
        provider_result = self._provider.run_search_plan(radar=radar, search_plan=plan)
        sources = _dedupe_sources(provider_result.sources)
        candidates = _rank_candidates([
            normalize_live_candidate(item, radar=radar, sources=sources)
            for item in provider_result.candidate_observations
        ])
        state_for_metadata = state.model_copy(update={
            "search_plan": plan.model_dump(),
            "sources": [item.model_dump() for item in sources],
            "candidates": [item.model_dump() for item in candidates],
        })
        metadata = self._runtime_metadata(
            state=state_for_metadata,
            node_name=node_name,
            provider_metadata=provider_result.provider_metadata,
            runtime_mode=runtime_mode,
            framework_available=framework_available,
        )
        artifact = LiveRadarRunArtifact(
            radar=radar,
            run_metadata=metadata,
            search_plan=plan.model_dump(),
            sources=[item.model_dump() for item in sources],
            candidates=[item.model_dump() for item in candidates],
            contract_validation=[
                issue.model_dump()
                for issue in validate_live_radar_qualification_contract(
                    candidates=candidates,
                    sources=sources,
                    radar=radar,
                )
            ],
        )
        return state.model_copy(update={
            "radar": radar,
            "search_plan": plan.model_dump(),
            "sources": [item.model_dump() for item in sources],
            "candidates": [item.model_dump() for item in candidates],
            "workflow_metadata": metadata,
            "artifact": artifact.model_dump(),
            "error_message": None,
        })

    def _runtime_metadata(
        self,
        *,
        state: LiveICPRadarRunState,
        node_name: str,
        provider_metadata: dict[str, Any],
        runtime_mode: str,
        framework_available: bool,
    ) -> dict[str, Any]:
        return {
            "workflow_name": "LiveICPRadarRunWorkflow",
            "runtime": getattr(self._provider, "runtime_name", "recorded") if state.live else "recorded",
            "framework_available": framework_available,
            "runtime_mode": runtime_mode,
            "node_name": node_name,
            "task_id": state.task_context.get("task_id"),
            "correlation_id": state.task_context.get("correlation_id"),
            "model": provider_metadata.get("model"),
            "web_mode": provider_metadata.get("web_mode"),
            "query_count": len(state.search_plan["queries"]) if state.search_plan else 0,
            "source_count": len(state.sources),
            "candidate_count": len(state.candidates),
            "run_at": _now_iso(),
        }


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()
