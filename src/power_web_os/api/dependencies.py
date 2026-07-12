"""API dependency wiring for Radar repositories and queue adapters."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Callable

from fastapi import Request

from power_web_os.application.ports import JobQueue, SignalMonitoringJobQueue
from power_web_os.jobs import CeleryJobQueue, SignalMonitoringCeleryJobQueue
from power_web_os.persistence import (
    SqlAlchemyRadarDefinitionRepository,
    SqlAlchemyRadarRepository,
    SqlAlchemyRadarReviewDecisionRepository,
    SqlAlchemyRadarRunEventRepository,
    SqlAlchemyRadarRunOutputRepository,
    SqlAlchemyRadarRunRepository,
    SqlAlchemyRadarRunTechnicalTraceRepository,
    SqlAlchemySignalMonitoringRunOutputRepository,
    session_scope,
)


@dataclass(frozen=True, slots=True)
class RadarApiContext:
    radar_repository: SqlAlchemyRadarRepository
    definition_repository: SqlAlchemyRadarDefinitionRepository
    run_repository: SqlAlchemyRadarRunRepository
    output_repository: SqlAlchemyRadarRunOutputRepository
    review_repository: SqlAlchemyRadarReviewDecisionRepository
    event_repository: SqlAlchemyRadarRunEventRepository
    technical_trace_repository: SqlAlchemyRadarRunTechnicalTraceRepository
    job_queue: JobQueue
    signal_monitoring_output_repository: SqlAlchemySignalMonitoringRunOutputRepository
    signal_monitoring_job_queue: SignalMonitoringJobQueue
    commit_before_enqueue: Callable[[], None]
    radar_max_web_tasks_per_subject: int
    radar_max_discovery_tasks_per_rule: int | None
    radar_max_gate_tasks_per_candidate_rule: int | None
    radar_max_signal_tasks_per_candidate_signal: int | None
    radar_max_total_web_tasks_per_run: int | None
    radar_source_verification_mode: str
    radar_min_useful_sources_per_discovery_task: int
    radar_min_candidates_per_discovery_task: int
    radar_max_discovery_retries_per_task: int
    radar_max_checkpoint_revisions_per_run: int
    radar_max_checkpoint_retries_per_stage: int
    radar_run_profile: str
    radar_max_openrouter_calls_per_run: int | None
    radar_max_openrouter_planner_calls_per_run: int | None
    radar_max_openrouter_web_task_calls_per_run: int | None
    radar_max_openrouter_server_tool_web_searches_per_run: int | None
    radar_max_dadata_lookups_per_run: int | None
    radar_max_source_verification_requests_per_run: int | None
    radar_max_provider_retries_per_task: int | None
    radar_openrouter_web_max_results_per_call: int | None
    radar_openrouter_web_max_total_results_per_call: int | None
    radar_smoke_max_candidates: int | None
    radar_smoke_max_signals: int | None
    runtime_config_report: dict[str, object]


def default_job_queue() -> JobQueue:
    return CeleryJobQueue()


def default_signal_monitoring_job_queue() -> SignalMonitoringJobQueue:
    return SignalMonitoringCeleryJobQueue()


def get_radar_api_context(request: Request) -> Iterator[RadarApiContext]:
    session_factory = request.app.state.session_factory
    job_queue_factory = request.app.state.job_queue_factory
    signal_monitoring_job_queue_factory = request.app.state.signal_monitoring_job_queue_factory
    radar_max_web_tasks_per_subject = int(getattr(request.app.state, "radar_max_web_tasks_per_subject", 20))
    radar_max_discovery_tasks_per_rule = _optional_int(getattr(request.app.state, "radar_max_discovery_tasks_per_rule", None))
    radar_max_gate_tasks_per_candidate_rule = _optional_int(
        getattr(request.app.state, "radar_max_gate_tasks_per_candidate_rule", None)
    )
    radar_max_signal_tasks_per_candidate_signal = _optional_int(
        getattr(request.app.state, "radar_max_signal_tasks_per_candidate_signal", None)
    )
    radar_max_total_web_tasks_per_run = _optional_int(getattr(request.app.state, "radar_max_total_web_tasks_per_run", None))
    radar_source_verification_mode = str(getattr(request.app.state, "radar_source_verification_mode", "soft"))
    radar_min_useful_sources_per_discovery_task = int(
        getattr(request.app.state, "radar_min_useful_sources_per_discovery_task", 3)
    )
    radar_min_candidates_per_discovery_task = int(getattr(request.app.state, "radar_min_candidates_per_discovery_task", 5))
    radar_max_discovery_retries_per_task = int(getattr(request.app.state, "radar_max_discovery_retries_per_task", 2))
    radar_max_checkpoint_revisions_per_run = int(getattr(request.app.state, "radar_max_checkpoint_revisions_per_run", 2))
    radar_max_checkpoint_retries_per_stage = int(getattr(request.app.state, "radar_max_checkpoint_retries_per_stage", 1))
    radar_run_profile = str(getattr(request.app.state, "radar_run_profile", "live"))
    radar_max_openrouter_calls_per_run = _optional_non_negative_int(
        getattr(request.app.state, "radar_max_openrouter_calls_per_run", None)
    )
    radar_max_openrouter_planner_calls_per_run = _optional_non_negative_int(
        getattr(request.app.state, "radar_max_openrouter_planner_calls_per_run", None)
    )
    radar_max_openrouter_web_task_calls_per_run = _optional_non_negative_int(
        getattr(request.app.state, "radar_max_openrouter_web_task_calls_per_run", None)
    )
    radar_max_openrouter_server_tool_web_searches_per_run = _optional_non_negative_int(
        getattr(request.app.state, "radar_max_openrouter_server_tool_web_searches_per_run", None)
    )
    radar_max_dadata_lookups_per_run = _optional_non_negative_int(
        getattr(request.app.state, "radar_max_dadata_lookups_per_run", None)
    )
    radar_max_source_verification_requests_per_run = _optional_non_negative_int(
        getattr(request.app.state, "radar_max_source_verification_requests_per_run", None)
    )
    radar_max_provider_retries_per_task = _optional_non_negative_int(
        getattr(request.app.state, "radar_max_provider_retries_per_task", None)
    )
    radar_openrouter_web_max_results_per_call = _optional_non_negative_int(
        getattr(request.app.state, "radar_openrouter_web_max_results_per_call", None)
    )
    radar_openrouter_web_max_total_results_per_call = _optional_non_negative_int(
        getattr(request.app.state, "radar_openrouter_web_max_total_results_per_call", None)
    )
    radar_smoke_max_candidates = _optional_non_negative_int(getattr(request.app.state, "radar_smoke_max_candidates", None))
    radar_smoke_max_signals = _optional_non_negative_int(getattr(request.app.state, "radar_smoke_max_signals", None))
    runtime_config_report = dict(getattr(request.app.state, "runtime_config_report", {}))
    with session_scope(session_factory) as session:
        yield RadarApiContext(
            radar_repository=SqlAlchemyRadarRepository(session),
            definition_repository=SqlAlchemyRadarDefinitionRepository(session),
            run_repository=SqlAlchemyRadarRunRepository(session),
            output_repository=SqlAlchemyRadarRunOutputRepository(session),
            review_repository=SqlAlchemyRadarReviewDecisionRepository(session),
            event_repository=SqlAlchemyRadarRunEventRepository(session),
            technical_trace_repository=SqlAlchemyRadarRunTechnicalTraceRepository(session),
            job_queue=job_queue_factory(),
            signal_monitoring_output_repository=SqlAlchemySignalMonitoringRunOutputRepository(session),
            signal_monitoring_job_queue=signal_monitoring_job_queue_factory(),
            commit_before_enqueue=session.commit,
            radar_max_web_tasks_per_subject=radar_max_web_tasks_per_subject,
            radar_max_discovery_tasks_per_rule=radar_max_discovery_tasks_per_rule,
            radar_max_gate_tasks_per_candidate_rule=radar_max_gate_tasks_per_candidate_rule,
            radar_max_signal_tasks_per_candidate_signal=radar_max_signal_tasks_per_candidate_signal,
            radar_max_total_web_tasks_per_run=radar_max_total_web_tasks_per_run,
            radar_source_verification_mode=radar_source_verification_mode,
            radar_min_useful_sources_per_discovery_task=radar_min_useful_sources_per_discovery_task,
            radar_min_candidates_per_discovery_task=radar_min_candidates_per_discovery_task,
            radar_max_discovery_retries_per_task=radar_max_discovery_retries_per_task,
            radar_max_checkpoint_revisions_per_run=radar_max_checkpoint_revisions_per_run,
            radar_max_checkpoint_retries_per_stage=radar_max_checkpoint_retries_per_stage,
            radar_run_profile=radar_run_profile,
            radar_max_openrouter_calls_per_run=radar_max_openrouter_calls_per_run,
            radar_max_openrouter_planner_calls_per_run=radar_max_openrouter_planner_calls_per_run,
            radar_max_openrouter_web_task_calls_per_run=radar_max_openrouter_web_task_calls_per_run,
            radar_max_openrouter_server_tool_web_searches_per_run=radar_max_openrouter_server_tool_web_searches_per_run,
            radar_max_dadata_lookups_per_run=radar_max_dadata_lookups_per_run,
            radar_max_source_verification_requests_per_run=radar_max_source_verification_requests_per_run,
            radar_max_provider_retries_per_task=radar_max_provider_retries_per_task,
            radar_openrouter_web_max_results_per_call=radar_openrouter_web_max_results_per_call,
            radar_openrouter_web_max_total_results_per_call=radar_openrouter_web_max_total_results_per_call,
            radar_smoke_max_candidates=radar_smoke_max_candidates,
            radar_smoke_max_signals=radar_smoke_max_signals,
            runtime_config_report=runtime_config_report,
        )


def _optional_int(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _optional_non_negative_int(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None
