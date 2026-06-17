"""Application service for structured Radar run audit events.

The journal stores product-facing reasoning artifacts such as plans,
observations, score explanations, and validation summaries. It deliberately
rejects raw hidden chain-of-thought fields.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from power_web_os.application.ports import RadarRunEventRepository
from power_web_os.application.radar_records import RadarRunEventRecord

FORBIDDEN_RAW_REASONING_KEYS = {"chain_of_thought", "hidden_reasoning", "internal_thoughts"}
VALID_VISIBILITIES = {"user", "operator", "debug"}


@dataclass(frozen=True, slots=True)
class RadarRunEventCommand:
    run_id: str
    event_type: str
    phase: str
    actor: str
    summary: str
    node_name: str = ""
    visibility: str = "user"
    payload: dict[str, Any] = field(default_factory=dict)
    source_refs: list[str] = field(default_factory=list)
    candidate_refs: list[str] = field(default_factory=list)


class RadarRunJournal:
    """Append structured audit events without owning storage details."""

    def __init__(self, *, repository: RadarRunEventRepository) -> None:
        self._repository = repository

    def append(self, command: RadarRunEventCommand) -> RadarRunEventRecord:
        _validate_visibility(command.visibility)
        _reject_raw_reasoning(command.payload)
        sequence = self._repository.next_sequence(command.run_id)
        return self._repository.append(
            RadarRunEventRecord(
                event_id=f"{command.run_id}:{sequence:06d}:{command.event_type}",
                run_id=command.run_id,
                sequence=sequence,
                event_type=command.event_type,
                phase=command.phase,
                actor=command.actor,
                node_name=command.node_name,
                visibility=command.visibility,
                summary=command.summary,
                payload=dict(command.payload),
                source_refs=list(command.source_refs),
                candidate_refs=list(command.candidate_refs),
            )
        )

    def list_for_run(self, run_id: str) -> tuple[RadarRunEventRecord, ...]:
        return self._repository.list_for_run(run_id)

    def append_artifact_events(self, *, run_id: str, artifact: dict[str, object]) -> tuple[RadarRunEventRecord, ...]:
        events: list[RadarRunEventRecord] = []
        for command in artifact_event_commands(run_id=run_id, artifact=artifact):
            events.append(self.append(command))
        return tuple(events)


def artifact_event_commands(*, run_id: str, artifact: dict[str, object]) -> tuple[RadarRunEventCommand, ...]:
    commands: list[RadarRunEventCommand] = []
    queries = _list(_dict(artifact.get("search_plan")).get("queries"))
    sources = _list(artifact.get("sources"))
    candidates = _list(artifact.get("candidates"))
    validation = _list(artifact.get("contract_validation"))

    commands.append(
        RadarRunEventCommand(
            run_id=run_id,
            event_type="plan_created",
            phase="planning",
            actor="workflow",
            node_name="live_radar_executor",
            summary=f"Live Radar plan prepared with {len(queries)} search queries.",
            payload={"query_count": len(queries)},
        )
    )
    for query in queries:
        commands.append(
            RadarRunEventCommand(
                run_id=run_id,
                event_type="search_query_planned",
                phase="planning",
                actor="workflow",
                node_name=str(query.get("query_id", "")),
                summary=str(query.get("query", "")),
                payload={
                    "purpose": str(query.get("purpose", "")),
                    "expected_evidence": [str(item) for item in query.get("expected_evidence", []) if isinstance(item, str)],
                },
            )
        )
    for source in sources:
        source_ref = str(source.get("evidence_ref", ""))
        commands.append(
            RadarRunEventCommand(
                run_id=run_id,
                event_type="source_collected",
                phase="collection",
                actor="provider",
                node_name=str(source.get("query_id", "")),
                summary=str(source.get("title") or source.get("snippet") or source_ref),
                payload={"url": str(source.get("url", "")), "source_type": str(source.get("source_type", "web"))},
                source_refs=[source_ref] if source_ref else [],
            )
        )
    for candidate in candidates:
        candidate_id = str(candidate.get("candidate_id", ""))
        source_refs = [str(item) for item in candidate.get("evidence_refs", []) if isinstance(item, str)]
        commands.append(
            RadarRunEventCommand(
                run_id=run_id,
                event_type="candidate_extracted",
                phase="extraction",
                actor="workflow",
                node_name=candidate_id,
                summary=str(candidate.get("legal_name") or candidate_id),
                payload={"review_flags": [str(item) for item in candidate.get("review_flags", []) if isinstance(item, str)]},
                source_refs=source_refs,
                candidate_refs=[candidate_id] if candidate_id else [],
            )
        )
        commands.extend(_candidate_evaluation_events(run_id=run_id, candidate=candidate, candidate_id=candidate_id))
    for issue in validation:
        commands.append(
            RadarRunEventCommand(
                run_id=run_id,
                event_type="validation_warning",
                phase="validation",
                actor="validator",
                visibility="operator",
                summary=str(issue.get("message", "")),
                payload={"severity": str(issue.get("severity", "warning")), "path": str(issue.get("path", ""))},
            )
        )
    commands.append(
        RadarRunEventCommand(
            run_id=run_id,
            event_type="self_check_completed",
            phase="validation",
            actor="validator",
            summary=f"Artifact self-check completed with {len(validation)} validation issues.",
            payload={"validation_issue_count": len(validation), "candidate_count": len(candidates), "source_count": len(sources)},
        )
    )
    return tuple(commands)


def _candidate_evaluation_events(
    *,
    run_id: str,
    candidate: dict[str, Any],
    candidate_id: str,
) -> list[RadarRunEventCommand]:
    commands: list[RadarRunEventCommand] = []
    for item in _list(candidate.get("qualification")) + _list(candidate.get("signals")):
        subject_id = str(item.get("rule_id") or item.get("criterion_code") or item.get("signal_code") or "")
        source_refs = [str(ref) for ref in item.get("evidence_refs", []) if isinstance(ref, str)]
        commands.append(
            RadarRunEventCommand(
                run_id=run_id,
                event_type="signal_evaluated",
                phase="evaluation",
                actor="workflow",
                node_name=subject_id,
                summary=str(item.get("summary") or item.get("rationale") or subject_id),
                payload={
                    "status": str(item.get("status", "")),
                    "confidence": str(item.get("confidence", "")),
                    "score": item.get("score"),
                    "final_assessment": item.get("final_assessment"),
                },
                source_refs=source_refs,
                candidate_refs=[candidate_id] if candidate_id else [],
            )
        )
    score = _dict(candidate.get("score"))
    if score:
        commands.append(
            RadarRunEventCommand(
                run_id=run_id,
                event_type="score_explained",
                phase="evaluation",
                actor="workflow",
                node_name=candidate_id,
                summary=f"Candidate scored as {score.get('tier', 'unranked')}.",
                payload=score,
                candidate_refs=[candidate_id] if candidate_id else [],
            )
        )
    return commands


def _reject_raw_reasoning(value: object) -> None:
    if isinstance(value, dict):
        forbidden = FORBIDDEN_RAW_REASONING_KEYS & {str(key) for key in value}
        if forbidden:
            raise ValueError(f"Raw hidden reasoning fields are not allowed in Radar run journal: {sorted(forbidden)}")
        for nested in value.values():
            _reject_raw_reasoning(nested)
    elif isinstance(value, list):
        for item in value:
            _reject_raw_reasoning(item)


def _validate_visibility(value: str) -> None:
    if value not in VALID_VISIBILITIES:
        raise ValueError(f"Unsupported Radar run journal visibility: {value}")


def _list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _dict(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}
