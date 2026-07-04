"""Support helpers for staged live Radar execution orchestration."""

from __future__ import annotations

from typing import Any

from power_web_os.application.radar.candidate_discovery.contracts import (
    LiveRadarCandidate,
    LiveRadarPipelineEvent,
    RadarExecutionTask,
    RadarSourceEvidence,
    WebSearchProviderResult,
)
from power_web_os.application.live_radar_normalization import normalize_live_candidate
from power_web_os.application.live_radar_universe import candidate_name


class CandidateProjectionService:
    """Projects raw observations into candidate and candidate-universe records.

    Owns:
    - Normalized candidate projection, gate summaries, rejected candidate
      summaries, and signal-status enrichment for candidate universe rows.

    Does not own:
    - Entity-resolution merge, provider execution, source obligation policy, or
      checkpoint decisions.

    Architecture:
    docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md#candidateprojectionservice
    """

    def candidate_names_matching(self, observations: list[dict[str, Any]], lower_names: set[str]) -> list[str]:
        names: list[str] = []
        seen: set[str] = set()
        for item in observations:
            name = candidate_name(item)
            key = name.lower()
            if name and key in lower_names and key not in seen:
                seen.add(key)
                names.append(name)
        return names

    def normalized_candidates(
        self,
        *,
        radar: dict[str, Any],
        sources: list[RadarSourceEvidence],
        observations: list[dict[str, Any]],
        merge_observations: Any,
    ) -> list[LiveRadarCandidate]:
        return [normalize_live_candidate(item, radar=radar, sources=sources) for item in merge_observations(observations)]

    def candidate_rejected(
        self,
        candidate: LiveRadarCandidate,
        *,
        completed_qualification_ids: list[str] | None = None,
    ) -> bool:
        completed = set(completed_qualification_ids or [item.criterion_code for item in candidate.qualification])
        return any(
            item.criterion_code in completed
            and item.requirement_level == "required"
            and item.final_assessment == "does_not_match"
            for item in candidate.qualification
        )

    def gate_summary(self, candidates: list[LiveRadarCandidate], subject_id: str) -> dict[str, Any]:
        statuses = {"accepted": 0, "unknown": 0, "rejected": 0}
        for candidate in candidates:
            rule = next((item for item in candidate.qualification if item.criterion_code == subject_id), None)
            if rule is None or rule.final_assessment in {"unknown", "partially_matches"}:
                statuses["unknown"] += 1
            elif rule.final_assessment == "does_not_match":
                statuses["rejected"] += 1
            else:
                statuses["accepted"] += 1
        return {"subject_id": subject_id, **statuses}

    def rejected_candidate_summaries(self, candidates: list[LiveRadarCandidate]) -> list[dict[str, Any]]:
        return [
            {
                "candidate_id": candidate.candidate_id,
                "legal_name": candidate.legal_name,
                "failed_rules": [
                    item.criterion_code
                    for item in candidate.qualification
                    if item.requirement_level == "required" and item.final_assessment == "does_not_match"
                ],
            }
            for candidate in candidates
            if self.candidate_rejected(candidate)
        ]

    def candidate_universe_with_signal_statuses(
        self,
        candidate_universe: list[LiveRadarCandidate],
        signal_search_statuses: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        statuses_by_name: dict[str, list[dict[str, Any]]] = {}
        for item in signal_search_statuses:
            name = str(item.get("candidate_name", "")).lower()
            if name:
                statuses_by_name.setdefault(name, []).append(item)
        payloads = []
        for item in candidate_universe:
            payload = item.model_dump()
            payload["signal_searches"] = statuses_by_name.get(str(payload.get("legal_name", "")).lower(), [])
            payloads.append(payload)
        return payloads


class PipelineEventFactory:
    """Builds product-safe execution events and signal-status payloads.

    Owns:
    - Product-safe pipeline events, budget warning events, source-obligation
      events, and not-searched signal observation payloads.

    Does not own:
    - Event persistence, provider execution, candidate scoring, or phase order.

    Architecture:
    docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md#pipelineeventfactory
    """

    def __init__(self, projection: CandidateProjectionService | None = None) -> None:
        self._projection = projection or CandidateProjectionService()

    def task_event(
        self,
        task: RadarExecutionTask,
        result: WebSearchProviderResult,
        event_type: str,
        *,
        payload: dict[str, Any] | None = None,
    ) -> LiveRadarPipelineEvent:
        return LiveRadarPipelineEvent(
            event_type=event_type,
            phase="collection",
            actor="workflow",
            node_name=task.task_id,
            visibility="operator",
            summary=f"Executed {task.stage} task {task.task_id}.",
            payload=self._task_payload(task, result, payload),
            source_refs=[source.evidence_ref for source in result.sources if source.evidence_ref],
        )

    def candidate_filtered_events(
        self,
        task: RadarExecutionTask,
        candidates: list[LiveRadarCandidate],
    ) -> list[LiveRadarPipelineEvent]:
        return [
            self._candidate_filtered_event(task, candidates, item)
            for item in self._projection.rejected_candidate_summaries(candidates)
        ]

    def signal_planned_event(self, task: RadarExecutionTask) -> LiveRadarPipelineEvent:
        return LiveRadarPipelineEvent(
            event_type="signal_search_planned",
            phase="planning",
            actor="workflow",
            node_name=task.task_id,
            summary=f"Planned signal search {task.subject_id} for {', '.join(task.candidate_scope)}.",
            payload={"subject_id": task.subject_id, "candidate_scope": list(task.candidate_scope)},
            candidate_refs=list(task.candidate_scope),
        )

    def budget_warning_event(self, warnings: list[str]) -> LiveRadarPipelineEvent:
        return LiveRadarPipelineEvent(
            event_type="validation_warning",
            phase="validation",
            actor="workflow",
            node_name="execution-budget",
            visibility="operator",
            summary="Radar execution budget limited remaining signal searches.",
            payload={"warnings": list(warnings)},
        )

    def useful_result_warning_event(self, warnings: list[str]) -> LiveRadarPipelineEvent:
        return LiveRadarPipelineEvent(
            event_type="validation_warning",
            phase="collection",
            actor="application",
            node_name="useful_result_budget",
            visibility="operator",
            summary="Useful-result budget triggered bounded discovery retries.",
            payload={"warnings": warnings},
        )

    def source_obligation_events(self, decisions: list[dict[str, Any]]) -> list[LiveRadarPipelineEvent]:
        return [
            event
            for decision in decisions
            if (event := self._source_obligation_event(decision)) is not None
        ]

    def budget_decision(self, result: WebSearchProviderResult) -> dict[str, Any]:
        decision = result.provider_metadata.get("budget_decision")
        return dict(decision) if isinstance(decision, dict) and not decision.get("accepted", True) else {}

    def not_searched_signal_observation(
        self,
        candidate_name: str,
        task: RadarExecutionTask,
        decision: dict[str, Any],
    ) -> dict[str, Any]:
        reason = str(decision.get("state") or "not_searched_budget_limited")
        message = str(decision.get("message") or "Signal search was not executed because an execution budget was exhausted.")
        return {
            "legal_name": candidate_name,
            "signals": [self._not_searched_signal_payload(task, decision, reason, message)],
            "review_flags": [reason],
        }

    def signal_status_record(self, candidate_name: str, task: RadarExecutionTask, decision: dict[str, Any]) -> dict[str, Any]:
        return {
            "candidate_name": candidate_name,
            "signal_id": task.subject_id,
            "task_id": task.task_id,
            "search_status": str(decision.get("state") or "not_searched_budget_limited"),
            "not_searched_reason": str(decision.get("reason") or "budget_limited"),
            "budget_key": str(decision.get("key") or ""),
            "message": str(decision.get("message") or ""),
        }

    def _task_payload(
        self,
        task: RadarExecutionTask,
        result: WebSearchProviderResult,
        payload: dict[str, Any] | None,
    ) -> dict[str, Any]:
        return {
            "stage": task.stage,
            "subject_type": task.subject_type,
            "subject_id": task.subject_id,
            "candidate_scope": list(task.candidate_scope),
            "source_count": len(result.sources),
            "candidate_observation_count": len(result.candidate_observations),
            **(payload or {}),
        }

    def _candidate_filtered_event(
        self,
        task: RadarExecutionTask,
        candidates: list[LiveRadarCandidate],
        item: dict[str, Any],
    ) -> LiveRadarPipelineEvent:
        candidate = next(candidate for candidate in candidates if candidate.candidate_id == item["candidate_id"])
        return LiveRadarPipelineEvent(
            event_type="candidate_filtered",
            phase="collection",
            actor="workflow",
            node_name=task.task_id,
            visibility="operator",
            summary=f"Candidate {candidate.legal_name} did not pass qualification gate {task.subject_id}.",
            payload={"subject_id": task.subject_id, "failed_rules": item["failed_rules"]},
            candidate_refs=[candidate.candidate_id],
        )

    def _source_obligation_event(self, decision: dict[str, Any]) -> LiveRadarPipelineEvent | None:
        status = str(decision.get("status") or "")
        source_id = str(decision.get("source_id") or "")
        if status == "not_applicable" or not source_id:
            return None
        return LiveRadarPipelineEvent(
            event_type=_source_obligation_event_type(status),
            phase="collection",
            actor="application",
            node_name="source_obligation_policy",
            visibility="operator",
            summary=f"{source_id}: {decision.get('usage_obligation')} -> {status}",
            payload=decision,
        )

    def _not_searched_signal_payload(
        self,
        task: RadarExecutionTask,
        decision: dict[str, Any],
        reason: str,
        message: str,
    ) -> dict[str, Any]:
        return {
            "signal_code": task.subject_id,
            "status": "unclear",
            "score": 0,
            "confidence": "low",
            "summary": message,
            "search_status": reason,
            "not_searched_reason": str(decision.get("reason") or "budget_limited"),
            "review_flags": [reason],
            "score_evaluation": {
                "applied_score": 0,
                "rule_snapshot": task.rule_snapshot,
                "explanation": "The signal was not searched and must not be treated as a negative observation.",
            },
        }


def _source_obligation_event_type(status: str) -> str:
    if status == "satisfied":
        return "source_obligation_satisfied"
    if status.startswith("attempted_"):
        return "source_obligation_attempted"
    if status == "skipped_with_rationale":
        return "source_obligation_skipped"
    return "source_obligation_unsatisfied"
