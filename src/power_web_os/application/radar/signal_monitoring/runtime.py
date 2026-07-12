"""Durable application lifecycle for standalone signal-monitoring runs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable
from uuid import uuid4

from power_web_os.application.ports import (
    RadarDefinitionRepository,
    RadarRunEventRepository,
    RadarRunOutputRepository,
    RadarRunRepository,
    SignalMonitoringRunOutputRepository,
)
from power_web_os.application.radar.signal_monitoring.artifact import SignalMonitoringArtifactProjector
from power_web_os.application.radar.signal_monitoring.contracts import (
    SignalMonitoringBudget,
    SignalMonitoringCandidateScopeMode,
    SignalMonitoringInput,
)
from power_web_os.application.radar.signal_monitoring.executor import SignalMonitoringExecutor
from power_web_os.application.radar.signal_monitoring.input_assembler import (
    SignalMonitoringInputAssembler,
    SignalMonitoringInputError,
)
from power_web_os.application.radar_records import (
    RadarRunRecord,
    RadarRunStatus,
    SignalMonitoringRunOutputRecord,
)
from power_web_os.application.radar_run_journal import RadarRunEventCommand, RadarRunJournal


@dataclass(frozen=True, slots=True)
class SignalMonitoringRunCommand:
    radar_id: str
    source_candidate_run_id: str
    candidate_scope_mode: SignalMonitoringCandidateScopeMode = "accepted_and_review_needed"
    candidate_ids: tuple[str, ...] = ()
    signal_codes: tuple[str, ...] = ()
    lookback_days: int | None = None
    run_id: str | None = None
    idempotency_key: str | None = None
    correlation_id: str | None = None
    requester: str = "api"
    run_profile: str = "signal_monitoring_smoke"
    budget: SignalMonitoringBudget | None = None


@dataclass(frozen=True, slots=True)
class QueuedSignalMonitoringRunResult:
    run: RadarRunRecord
    should_enqueue: bool


class QueuedSignalMonitoringRunService:
    """Validate, snapshot, and queue a standalone signal-monitoring run."""

    def __init__(
        self,
        *,
        run_repository: RadarRunRepository,
        candidate_output_repository: RadarRunOutputRepository,
        signal_output_repository: SignalMonitoringRunOutputRepository,
        definition_repository: RadarDefinitionRepository,
        event_repository: RadarRunEventRepository | None = None,
        input_assembler: SignalMonitoringInputAssembler | None = None,
    ) -> None:
        self._run_repository = run_repository
        self._candidate_output_repository = candidate_output_repository
        self._signal_output_repository = signal_output_repository
        self._definition_repository = definition_repository
        self._journal = RadarRunJournal(repository=event_repository) if event_repository else None
        self._input_assembler = input_assembler or SignalMonitoringInputAssembler()

    def create(self, command: SignalMonitoringRunCommand) -> QueuedSignalMonitoringRunResult:
        if command.idempotency_key:
            existing = self._run_repository.find_by_idempotency_key(command.idempotency_key)
            if existing is not None:
                if existing.pipeline_id != "signal_monitoring":
                    raise SignalMonitoringInputError("Idempotency key belongs to another Radar pipeline.")
                return QueuedSignalMonitoringRunResult(existing, False)

        run_id = command.run_id or f"signal-run-{uuid4()}"
        monitoring_input = self._assemble(run_id=run_id, command=command)
        run = self._run_repository.create(RadarRunRecord(
            run_id=run_id,
            radar_id=command.radar_id,
            pipeline_id="signal_monitoring",
            source_run_id=command.source_candidate_run_id,
            idempotency_key=command.idempotency_key,
            correlation_id=command.correlation_id or f"corr-{run_id}",
            run_metadata={
                "pipeline_id": "signal_monitoring",
                "execution_mode": "queued_signal_monitoring",
                "source_candidate_run_id": command.source_candidate_run_id,
                "requester": command.requester,
                "run_profile": command.run_profile,
                "signal_monitoring_input": monitoring_input.model_dump(mode="json"),
            },
        ))
        self._append_event(run, "signal_run_queued", "Signal monitoring run queued.")
        return QueuedSignalMonitoringRunResult(run, True)

    def preflight(self, command: SignalMonitoringRunCommand) -> dict[str, Any]:
        try:
            monitoring_input = self._assemble(run_id=command.run_id or "signal-preflight", command=command)
        except SignalMonitoringInputError as exc:
            return {"ready_for_live_run": False, "issues": [str(exc)]}
        return {
            "ready_for_live_run": True,
            "issues": [],
            "candidate_count": len(monitoring_input.candidates),
            "signal_rule_count": len(monitoring_input.signal_rules),
            "lookback_days": monitoring_input.lookback_days,
            "budget": monitoring_input.budget.model_dump(mode="json"),
            "source_candidate_run_id": monitoring_input.source_candidate_run_id,
        }

    def _assemble(self, *, run_id: str, command: SignalMonitoringRunCommand) -> SignalMonitoringInput:
        source_run = self._run_repository.get(command.source_candidate_run_id)
        if source_run is None:
            raise SignalMonitoringInputError(f"Source candidate run not found: {command.source_candidate_run_id}")
        if source_run.pipeline_id != "candidate_discovery":
            raise SignalMonitoringInputError("Source run must be a candidate-discovery run.")
        if source_run.radar_id != command.radar_id:
            raise SignalMonitoringInputError("Source run belongs to another Radar.")
        source_output = self._candidate_output_repository.get(command.source_candidate_run_id)
        if source_output is None:
            raise SignalMonitoringInputError("Source candidate run has no persisted output.")
        definition = self._definition_repository.get_active(command.radar_id)
        if definition is None:
            raise SignalMonitoringInputError("Radar has no active definition.")
        return self._input_assembler.assemble(
            run_id=run_id,
            radar_id=command.radar_id,
            source_run=source_run,
            source_output=source_output,
            definition=definition,
            candidate_scope_mode=command.candidate_scope_mode,
            candidate_ids=command.candidate_ids,
            signal_codes=command.signal_codes,
            lookback_days=command.lookback_days,
            previous_outputs=self._signal_output_repository.list_for_radar(command.radar_id),
            budget=command.budget or (
                self._input_assembler.quality_budget()
                if command.run_profile == "signal_monitoring_quality"
                else None
            ),
        )

    def _append_event(self, run: RadarRunRecord, event_type: str, summary: str) -> None:
        if self._journal:
            self._journal.append(RadarRunEventCommand(
                run_id=run.run_id,
                event_type=event_type,
                phase="signal_monitoring_lifecycle",
                actor="application",
                node_name="queued_signal_monitoring_run_service",
                summary=summary,
                payload={"pipeline_id": run.pipeline_id, "source_run_id": run.source_run_id},
            ))


class PersistedSignalMonitoringRunExecutor:
    """Execute one queued signal run and persist its pipeline-specific artifact."""

    def __init__(
        self,
        *,
        run_repository: RadarRunRepository,
        output_repository: SignalMonitoringRunOutputRepository,
        executor: SignalMonitoringExecutor,
        artifact_projector: SignalMonitoringArtifactProjector | None = None,
        event_repository: RadarRunEventRepository | None = None,
        commit_after_start: Any | None = None,
    ) -> None:
        self._run_repository = run_repository
        self._output_repository = output_repository
        self._executor = executor
        self._artifact_projector = artifact_projector or SignalMonitoringArtifactProjector()
        self._journal = RadarRunJournal(repository=event_repository) if event_repository else None
        self._commit_after_start = commit_after_start

    def execute(self, run_id: str) -> RadarRunRecord:
        run = self._run_repository.get(run_id)
        if run is None:
            raise KeyError(f"Signal monitoring run not found: {run_id}")
        if run.pipeline_id != "signal_monitoring":
            raise ValueError("Candidate-discovery run cannot be executed by signal monitoring.")
        if run.status.is_terminal:
            return run
        raw_input = run.run_metadata.get("signal_monitoring_input")
        if not isinstance(raw_input, dict):
            return self._fail(run, "Signal monitoring input snapshot is missing.")
        monitoring_input = SignalMonitoringInput.model_validate(raw_input)
        running = self._run_repository.update_status(
            run.run_id,
            RadarRunStatus.RUNNING,
            run_metadata={**run.run_metadata, "execution_mode": "persisted_signal_monitoring"},
        )
        if self._commit_after_start:
            self._commit_after_start()
        self._append_event(running, "signal_run_started", "Signal monitoring run started.")
        try:
            outcome = self._executor.run(monitoring_input)
            provider_runtime = str(getattr(self._executor.provider, "runtime_name", ""))
            artifact = self._artifact_projector.project(
                monitoring_input=monitoring_input,
                outcome=outcome,
                provider_runtime=provider_runtime,
            )
            self._output_repository.upsert(SignalMonitoringRunOutputRecord(
                run_id=run.run_id,
                source_run_id=monitoring_input.source_candidate_run_id,
                artifact_version=str(artifact["artifact_version"]),
                input_snapshot_payload=dict(artifact["input_snapshot"]),
                plan_payload={"tasks": list(artifact["tasks"])},
                observations_payload=list(artifact["observations"]),
                artifact_payload=artifact,
            ))
            completed = self._run_repository.update_status(
                run.run_id,
                RadarRunStatus.COMPLETED,
                run_metadata={
                    **running.run_metadata,
                    "artifact_type": artifact["artifact_type"],
                    "artifact_version": artifact["artifact_version"],
                    "completion_state": artifact["completion_state"],
                    "candidate_count": artifact["summary"]["candidate_count"],
                    "observation_count": artifact["summary"]["observation_count"],
                    "provider_call_count": artifact["summary"]["provider_call_count"],
                },
            )
            self._append_event(completed, "signal_run_completed", "Signal monitoring run completed.")
            return completed
        except Exception as exc:
            return self._fail(run, str(exc), exception_type=type(exc).__name__)

    def _fail(self, run: RadarRunRecord, message: str, *, exception_type: str = "SignalMonitoringRuntimeError") -> RadarRunRecord:
        failed = self._run_repository.update_status(
            run.run_id,
            RadarRunStatus.FAILED,
            error_message=message,
            error_metadata={"exception_type": exception_type},
        )
        self._append_event(failed, "signal_run_failed", message)
        return failed

    def _append_event(self, run: RadarRunRecord, event_type: str, summary: str) -> None:
        if self._journal:
            self._journal.append(RadarRunEventCommand(
                run_id=run.run_id,
                event_type=event_type,
                phase="signal_monitoring_lifecycle",
                actor="worker",
                node_name="persisted_signal_monitoring_run_executor",
                summary=summary,
                payload={"pipeline_id": run.pipeline_id, "source_run_id": run.source_run_id},
            ))
