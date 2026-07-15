"""Cumulative product read model for persisted Signal Monitoring runs."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Iterable

from power_web_os.application.ports import (
    RadarRunOutputRepository,
    RadarRunRepository,
    SignalMonitoringRunOutputRepository,
)
from power_web_os.application.radar.lifecycle.records import RadarRunRecord, SignalMonitoringRunOutputRecord


class SignalMonitoringCandidateSurfaceProjector:
    """Build an evidence-complete current and cumulative monitoring surface.

    Owns:
    - Product outcome language, evidence/source resolution, and cumulative pair state.

    Does not own:
    - Signal search, temporal validation, persistence, candidate identity, or scoring.

    Architecture:
    docs/radar/pipelines/RADAR_PIPELINE_SPLIT_UI_CONTRACT.md
    """

    ARTIFACT_VERSION = "signal_monitoring_candidate_surface.v1"

    def project(
        self,
        *,
        selected_run: RadarRunRecord,
        source_candidates: Iterable[dict[str, Any]],
        history: Iterable[tuple[RadarRunRecord, SignalMonitoringRunOutputRecord]],
    ) -> dict[str, Any]:
        ordered = sorted(history, key=lambda item: self._run_time(item[0]))
        snapshots = [(run, self._snapshot(output)) for run, output in ordered]
        selected_snapshot = next(snapshot for run, snapshot in snapshots if run.run_id == selected_run.run_id)
        signal_rules = self._signal_rules(selected_snapshot)
        monitored = self._monitored_candidates(selected_snapshot)
        current_pairs = selected_snapshot["pairs"]
        history_by_pair: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for run, snapshot in snapshots:
            for pair_key, pair in snapshot["pairs"].items():
                history_by_pair[pair_key].append({**pair, "run_id": run.run_id})

        candidates: list[dict[str, Any]] = []
        unresolved_refs: set[str] = set()
        current_confirmed = 0
        current_review = 0
        current_negative = 0
        cumulative_confirmed = 0
        cumulative_review = 0
        pair_count = 0
        source_by_id: dict[str, dict[str, Any]] = {}
        for item in source_candidates:
            candidate_id = str(item.get("candidate_id") or item.get("account_id") or "")
            if candidate_id:
                source_by_id[candidate_id] = {**source_by_id.get(candidate_id, {}), **item}
        for candidate_id in monitored:
            source_by_id[candidate_id] = {**source_by_id.get(candidate_id, {}), **monitored[candidate_id]}

        for candidate in source_by_id.values():
            candidate_id = str(candidate.get("candidate_id") or candidate.get("account_id") or "")
            if not candidate_id:
                continue
            is_monitored = candidate_id in monitored
            outcomes: list[dict[str, Any]] = []
            if is_monitored:
                for rule in signal_rules:
                    signal_code = rule["signal_code"]
                    pair_count += 1
                    current = current_pairs.get((candidate_id, signal_code)) or self._missing_pair(candidate_id, rule)
                    pair_history = history_by_pair.get((candidate_id, signal_code), [])
                    cumulative = self._cumulative(pair_history)
                    if current["technical_observation_status"] == "observed":
                        current_confirmed += 1
                    elif current["technical_observation_status"] == "unclear":
                        current_review += 1
                    elif current["technical_observation_status"] == "not_observed":
                        current_negative += 1
                    if cumulative["presentation_status"] == "found_fresh":
                        cumulative_confirmed += 1
                    elif cumulative["presentation_status"] in {
                        "found_relevant_date_unknown",
                        "found_historical_not_counted",
                        "coverage_incomplete",
                    }:
                        cumulative_review += 1
                    unresolved_refs.update(
                        item["source_ref"]
                        for item in [*current["evidence"], *current["searched_sources"]]
                        if not item["resolved"]
                    )
                    outcomes.append({
                        "signal_code": signal_code,
                        "signal_label": rule["signal_label"],
                        "current": current,
                        "cumulative": cumulative,
                        "new_in_selected_run": (
                            current["presentation_status"] == "found_fresh"
                            and not any(item["presentation_status"] == "found_fresh" for item in pair_history[:-1])
                        ),
                    })
            candidates.append({
                "candidate_id": candidate_id,
                "candidate_name": str(
                    candidate.get("legal_name")
                    or candidate.get("display_name")
                    or candidate.get("name")
                    or candidate_id
                ),
                "monitored": is_monitored,
                "monitoring_status": self._candidate_status(outcomes) if is_monitored else "not_monitored",
                "outcomes": outcomes,
            })

        monitored_count = len(monitored)
        return {
            "artifact_type": "signal_monitoring_candidate_surface",
            "artifact_version": self.ARTIFACT_VERSION,
            "pipeline_id": "signal_monitoring",
            "radar_id": selected_run.radar_id,
            "selected_run_id": selected_run.run_id,
            "source_candidate_run_id": selected_run.source_run_id,
            "history_run_ids": [run.run_id for run, _ in snapshots],
            "summary": {
                "candidate_count": len(candidates),
                "monitored_candidate_count": monitored_count,
                "not_monitored_candidate_count": max(0, len(candidates) - monitored_count),
                "criterion_count": len(signal_rules),
                "pair_count": pair_count,
                "current_confirmed_count": current_confirmed,
                "current_review_count": current_review,
                "current_searched_negative_count": current_negative,
                "new_confirmed_count": sum(
                    outcome["new_in_selected_run"]
                    for candidate in candidates
                    for outcome in candidate["outcomes"]
                ),
                "cumulative_confirmed_count": cumulative_confirmed,
                "cumulative_review_count": cumulative_review,
                "unresolved_source_ref_count": len(unresolved_refs),
            },
            "unresolved_source_refs": sorted(unresolved_refs),
            "candidates": candidates,
        }

    def _snapshot(self, output: SignalMonitoringRunOutputRecord) -> dict[str, Any]:
        artifact = output.artifact_payload
        source_index = self._source_index(artifact)
        task_rows = self._dict_list(artifact.get("task_observations"))
        tasks_by_pair: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for row in task_rows:
            tasks_by_pair[self._pair_key(row)].append(row)
        ledger_by_pair: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for row in self._dict_list(artifact.get("source_lane_ledger")):
            ledger_by_pair[self._pair_key(row)].append(row)

        pairs: dict[tuple[str, str], dict[str, Any]] = {}
        for observation in self._dict_list(artifact.get("observations")):
            key = self._pair_key(observation)
            tasks = tasks_by_pair.get(key, [])
            evidence = self._evidence(tasks, source_index)
            searched = self._searched_sources(observation, tasks, source_index, evidence)
            pairs[key] = {
                "candidate_id": key[0],
                "signal_code": key[1],
                "technical_observation_status": str(observation.get("observation_status") or ""),
                "technical_search_status": str(observation.get("search_status") or ""),
                "summary": str(observation.get("summary") or ""),
                "score": self._number(observation.get("score")),
                "presentation_status": self._presentation_status(observation, evidence, ledger_by_pair.get(key, [])),
                "coverage_complete": self._coverage_complete(observation, ledger_by_pair.get(key, [])),
                "evidence": evidence,
                "searched_sources": searched,
            }
        return {
            "artifact": artifact,
            "pairs": pairs,
        }

    def _source_index(self, artifact: dict[str, Any]) -> dict[str, dict[str, Any]]:
        index: dict[str, dict[str, Any]] = {}
        collections = [artifact.get("sources"), artifact.get("known_sources")]
        for task in self._dict_list(artifact.get("task_observations")):
            collections.append(task.get("sources"))
        for collection in collections:
            for source in self._dict_list(collection):
                source_ref = str(source.get("source_ref") or "")
                if source_ref:
                    index[source_ref] = {**index.get(source_ref, {}), **source}
        return index

    def _evidence(
        self,
        tasks: list[dict[str, Any]],
        source_index: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        result: dict[tuple[str, str, str], dict[str, Any]] = {}
        for task in tasks:
            for evidence in self._dict_list(task.get("evidence")):
                source_ref = str(evidence.get("source_ref") or "")
                if not source_ref:
                    continue
                temporal = str(evidence.get("temporal_status") or "not_applicable")
                key = (source_ref, temporal, str(evidence.get("fact") or ""))
                result[key] = self._resolved_source(source_ref, source_index, evidence=evidence)
        return list(result.values())

    def _searched_sources(
        self,
        observation: dict[str, Any],
        tasks: list[dict[str, Any]],
        source_index: dict[str, dict[str, Any]],
        evidence: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        evidence_refs = {item["source_ref"] for item in evidence}
        refs: set[str] = set(self._string_list(observation.get("source_refs")))
        for task in tasks:
            refs.update(self._string_list(task.get("source_refs")))
            refs.update(str(item.get("source_ref") or "") for item in self._dict_list(task.get("sources")))
        return [self._resolved_source(ref, source_index) for ref in sorted(refs - evidence_refs) if ref]

    def _resolved_source(
        self,
        source_ref: str,
        source_index: dict[str, dict[str, Any]],
        *,
        evidence: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        source = source_index.get(source_ref, {})
        evidence = evidence or {}
        resolved = bool(source.get("url") or source.get("title"))
        return {
            "source_ref": source_ref,
            "resolved": resolved,
            "resolution_reason": "resolved_from_artifact" if resolved else "source_ref_not_resolved",
            "title": str(source.get("title") or ""),
            "url": str(source.get("url") or ""),
            "snippet": str(source.get("snippet") or ""),
            "source_lane": str(source.get("source_lane") or ""),
            "fact": str(evidence.get("fact") or ""),
            "excerpt": str(evidence.get("excerpt") or ""),
            "event_at": str(evidence.get("event_at") or ""),
            "published_at": str(evidence.get("published_at") or source.get("published_at") or ""),
            "temporal_status": str(evidence.get("temporal_status") or "not_applicable"),
            "date_basis": str(evidence.get("date_basis") or source.get("date_basis") or "none"),
            "date_confidence": str(evidence.get("date_confidence") or source.get("date_confidence") or "weak"),
        }

    def _cumulative(self, history: list[dict[str, Any]]) -> dict[str, Any]:
        if not history:
            return {
                "presentation_status": "not_monitored",
                "origin_run_id": "",
                "latest_run_id": "",
                "evidence": [],
                "history": [],
            }
        preferred = self._preferred_history_item(history)
        evidence = self._merge_evidence(history)
        return {
            "presentation_status": preferred["presentation_status"],
            "origin_run_id": preferred["run_id"],
            "latest_run_id": history[-1]["run_id"],
            "evidence": evidence,
            "history": [{
                "run_id": item["run_id"],
                "presentation_status": item["presentation_status"],
                "technical_observation_status": item["technical_observation_status"],
                "technical_search_status": item["technical_search_status"],
            } for item in history],
        }

    @staticmethod
    def _preferred_history_item(history: list[dict[str, Any]]) -> dict[str, Any]:
        priority = {
            "found_fresh": 5,
            "found_relevant_date_unknown": 4,
            "found_historical_not_counted": 3,
            "coverage_incomplete": 2,
            "not_found_after_complete_coverage": 1,
            "not_monitored": 0,
        }
        return max(history, key=lambda item: (priority.get(item["presentation_status"], 0), history.index(item)))

    @staticmethod
    def _merge_evidence(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
        merged: dict[tuple[str, str, str], dict[str, Any]] = {}
        for item in history:
            for evidence in item["evidence"]:
                key = (evidence["source_ref"], evidence["temporal_status"], evidence["fact"])
                merged[key] = {**evidence, "origin_run_id": item["run_id"]}
        return list(merged.values())

    @staticmethod
    def _presentation_status(
        observation: dict[str, Any],
        evidence: list[dict[str, Any]],
        ledger: list[dict[str, Any]],
    ) -> str:
        temporal = {item["temporal_status"] for item in evidence}
        if "confirmed_in_window" in temporal and observation.get("observation_status") == "observed":
            return "found_fresh"
        if temporal & {"review_needed_date_unknown", "review_needed_date_conflict"}:
            return "found_relevant_date_unknown"
        if "rejected_out_of_window" in temporal:
            return "found_historical_not_counted"
        if observation.get("observation_status") == "not_observed" and SignalMonitoringCandidateSurfaceProjector._coverage_complete(observation, ledger):
            return "not_found_after_complete_coverage"
        return "coverage_incomplete"

    @staticmethod
    def _coverage_complete(observation: dict[str, Any], ledger: list[dict[str, Any]]) -> bool:
        required = [item for item in ledger if item.get("required")]
        return bool(required) and all(item.get("status") == "executed" for item in required) or (
            observation.get("observation_status") == "not_observed"
            and observation.get("search_status") == "searched"
        )

    @staticmethod
    def _candidate_status(outcomes: list[dict[str, Any]]) -> str:
        statuses = {item["cumulative"]["presentation_status"] for item in outcomes}
        if "found_fresh" in statuses:
            return "found_fresh"
        if statuses & {"found_relevant_date_unknown", "found_historical_not_counted", "coverage_incomplete"}:
            return "review_needed"
        return "not_found_after_complete_coverage"

    @staticmethod
    def _signal_rules(snapshot: dict[str, Any]) -> list[dict[str, str]]:
        result: list[dict[str, str]] = []
        for item in SignalMonitoringCandidateSurfaceProjector._dict_list(snapshot["artifact"].get("signal_rules")):
            code = str(item.get("signal_code") or item.get("code") or "")
            if code:
                result.append({"signal_code": code, "signal_label": str(item.get("label") or item.get("name") or code)})
        return result

    @staticmethod
    def _monitored_candidates(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for item in SignalMonitoringCandidateSurfaceProjector._dict_list(snapshot["artifact"].get("candidates")):
            candidate_id = str(item.get("candidate_id") or "")
            if candidate_id:
                result[candidate_id] = item
        return result

    @staticmethod
    def _missing_pair(candidate_id: str, rule: dict[str, str]) -> dict[str, Any]:
        return {
            "candidate_id": candidate_id,
            "signal_code": rule["signal_code"],
            "technical_observation_status": "",
            "technical_search_status": "",
            "summary": "",
            "score": 0,
            "presentation_status": "coverage_incomplete",
            "coverage_complete": False,
            "evidence": [],
            "searched_sources": [],
        }

    @staticmethod
    def _pair_key(value: dict[str, Any]) -> tuple[str, str]:
        return str(value.get("candidate_id") or ""), str(value.get("signal_code") or "")

    @staticmethod
    def _dict_list(value: object) -> list[dict[str, Any]]:
        return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []

    @staticmethod
    def _string_list(value: object) -> list[str]:
        return [str(item) for item in value if isinstance(item, str)] if isinstance(value, list) else []

    @staticmethod
    def _number(value: object) -> int | float:
        return value if isinstance(value, (int, float)) and not isinstance(value, bool) else 0

    @staticmethod
    def _run_time(run: RadarRunRecord) -> datetime:
        return run.completed_at or run.started_at or run.queued_at or datetime.min


class SignalMonitoringCandidateSurfaceService:
    """Load one selected run lineage and delegate cumulative projection.

    Owns:
    - Run/output eligibility and source candidate lookup for the read model.

    Does not own:
    - Persistence implementation, monitoring execution, or presentation rendering.

    Architecture:
    docs/radar/pipelines/RADAR_PIPELINE_SPLIT_UI_CONTRACT.md
    """

    def __init__(
        self,
        *,
        run_repository: RadarRunRepository,
        candidate_output_repository: RadarRunOutputRepository,
        signal_output_repository: SignalMonitoringRunOutputRepository,
        projector: SignalMonitoringCandidateSurfaceProjector | None = None,
    ) -> None:
        self._runs = run_repository
        self._candidate_outputs = candidate_output_repository
        self._signal_outputs = signal_output_repository
        self._projector = projector or SignalMonitoringCandidateSurfaceProjector()

    def build(self, run_id: str) -> dict[str, Any]:
        selected = self._runs.get(run_id)
        if selected is None or selected.pipeline_id != "signal_monitoring":
            raise KeyError(f"Signal monitoring run not found: {run_id}")
        if selected.status.value != "completed":
            raise ValueError(f"Signal monitoring run is not completed: {run_id}")
        selected_output = self._signal_outputs.get(run_id)
        if selected_output is None:
            raise ValueError(f"Signal monitoring run has no persisted output: {run_id}")
        source_run_id = selected.source_run_id or selected_output.source_run_id
        candidate_output = self._candidate_outputs.get(source_run_id)
        if candidate_output is None:
            raise ValueError(f"Source candidate run has no persisted output: {source_run_id}")

        selected_time = self._projector._run_time(selected)
        history: list[tuple[RadarRunRecord, SignalMonitoringRunOutputRecord]] = []
        for run in self._runs.list_for_radar(selected.radar_id, pipeline_id="signal_monitoring"):
            if run.status.value != "completed" or run.source_run_id != source_run_id:
                continue
            if self._projector._run_time(run) > selected_time:
                continue
            output = self._signal_outputs.get(run.run_id)
            if output is not None:
                history.append((run, output))
        if not any(run.run_id == run_id for run, _ in history):
            history.append((selected, selected_output))
        return self._projector.project(
            selected_run=selected,
            source_candidates=candidate_output.candidates_payload,
            history=history,
        )
