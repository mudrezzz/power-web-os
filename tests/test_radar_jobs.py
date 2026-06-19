from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from power_web_os.application.persisted_live_radar import QueuedLiveRadarRunService
from power_web_os.application.radar_records import RadarRecord, RadarRunRecord, RadarRunStatus
from power_web_os.jobs import CeleryJobQueue, ConfiguredRadarRunScheduler
from power_web_os.jobs import radar_jobs
from power_web_os.persistence import (
    Base,
    SqlAlchemyRadarRepository,
    SqlAlchemyRadarRunEventRepository,
    SqlAlchemyRadarRunOutputRepository,
    SqlAlchemyRadarRunRepository,
    create_database_engine,
    create_session_factory,
    session_scope,
)


def sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


def test_celery_queue_adapter_enqueues_only_run_id() -> None:
    task = _RecordingTask()
    run = RadarRunRecord(run_id="run-1", radar_id="toir-quick-live", run_metadata={"secret": "not sent"})

    CeleryJobQueue(task=task).enqueue_radar_run(run)

    assert task.calls == [("run-1",)]


def test_execute_radar_run_once_completes_and_persists_output(tmp_path: Path) -> None:
    session_factory = _seed_database(tmp_path, run_id="run-success")

    completed = radar_jobs.execute_radar_run_once(
        run_id="run-success",
        live_executor=_FakeExecutor(_artifact()),
        session_factory=session_factory,
    )

    with session_scope(session_factory) as session:
        stored_run = SqlAlchemyRadarRunRepository(session).get("run-success")
        output = SqlAlchemyRadarRunOutputRepository(session).get("run-success")
        events = SqlAlchemyRadarRunEventRepository(session).list_for_run("run-success")

    assert completed.status is RadarRunStatus.COMPLETED
    assert stored_run is not None
    assert stored_run.status is RadarRunStatus.COMPLETED
    assert output is not None
    assert output.candidates_payload[0]["legal_name"] == "Candidate A"
    assert [event.event_type for event in events][0] == "run_started"
    assert [event.event_type for event in events][-1] == "run_completed"


def test_execute_radar_run_once_commits_running_state_before_provider_work(tmp_path: Path) -> None:
    session_factory = _seed_database(tmp_path, run_id="run-transaction-boundary")
    executor = _InspectingExecutor(session_factory=session_factory, artifact=_artifact())

    completed = radar_jobs.execute_radar_run_once(
        run_id="run-transaction-boundary",
        live_executor=executor,
        session_factory=session_factory,
    )

    assert completed.status is RadarRunStatus.COMPLETED
    assert executor.observed_status == RadarRunStatus.RUNNING


def test_execute_radar_run_once_failure_persists_failed_state(tmp_path: Path) -> None:
    session_factory = _seed_database(tmp_path, run_id="run-failed")

    failed = radar_jobs.execute_radar_run_once(
        run_id="run-failed",
        live_executor=_FailingExecutor(),
        session_factory=session_factory,
    )

    with session_scope(session_factory) as session:
        stored_run = SqlAlchemyRadarRunRepository(session).get("run-failed")
        output = SqlAlchemyRadarRunOutputRepository(session).get("run-failed")
        events = SqlAlchemyRadarRunEventRepository(session).list_for_run("run-failed")

    assert failed.status is RadarRunStatus.FAILED
    assert stored_run is not None
    assert stored_run.error_message == "provider unavailable"
    assert output is None
    assert [event.event_type for event in events] == ["run_started", "run_failed"]


def test_celery_eager_task_executes_without_redis(tmp_path: Path, monkeypatch) -> None:
    database_url = sqlite_url(tmp_path / "celery-eager.db")
    _seed_database(tmp_path, database_url=database_url, run_id="run-eager")
    monkeypatch.setenv("POWER_WEB_OS_DATABASE_URL", database_url)
    monkeypatch.setattr(radar_jobs, "default_live_executor", lambda **_: _FakeExecutor(_artifact()))
    radar_jobs.radar_celery_app.conf.task_always_eager = True
    radar_jobs.radar_celery_app.conf.task_eager_propagates = True

    result = radar_jobs.execute_radar_run_task.delay("run-eager").get()

    assert result == {"run_id": "run-eager", "radar_id": "toir-quick-live", "status": "completed"}


def test_configured_scheduler_enqueues_due_radar_runs_once(tmp_path: Path) -> None:
    session_factory = _seed_database(tmp_path)
    queue = _RecordingQueue()

    with session_scope(session_factory) as session:
        run_service = QueuedLiveRadarRunService(run_repository=SqlAlchemyRadarRunRepository(session))
        scheduler = ConfiguredRadarRunScheduler(
            radar_ids=("toir-quick-live",),
            run_service=run_service,
            job_queue=queue,
        )
        first = scheduler.schedule_due_runs(now=datetime(2026, 6, 17, tzinfo=UTC))
        second = scheduler.schedule_due_runs(now=datetime(2026, 6, 17, tzinfo=UTC))

    assert len(first) == 1
    assert second[0].run_id == first[0].run_id
    assert queue.enqueued_run_ids == [first[0].run_id]


def _seed_database(
    tmp_path: Path,
    *,
    database_url: str | None = None,
    run_id: str | None = None,
):
    engine = create_database_engine(database_url=database_url or sqlite_url(tmp_path / "jobs.db"))
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)
    with session_scope(session_factory) as session:
        radar = SqlAlchemyRadarRepository(session).upsert(
            RadarRecord(
                radar_id="toir-quick-live",
                name="TOIR Quick Live Radar",
                status="experimental_live",
                owner="Industrial ABM",
            )
        )
        if run_id is not None:
            SqlAlchemyRadarRunRepository(session).create(
                RadarRunRecord(
                    run_id=run_id,
                    radar_id=radar.radar_id,
                    correlation_id=f"corr-{run_id}",
                    run_metadata={
                        "execution_mode": "queued_live_radar",
                        "live": False,
                        "requester": "test",
                        "task_context": {},
                    },
                )
            )
    return session_factory


class _RecordingTask:
    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []

    def delay(self, *args: str) -> None:
        self.calls.append(tuple(args))


class _RecordingQueue:
    def __init__(self) -> None:
        self.enqueued_run_ids: list[str] = []

    def enqueue_radar_run(self, run: RadarRunRecord) -> None:
        self.enqueued_run_ids.append(run.run_id)


class _FakeExecutor:
    def __init__(self, artifact: dict[str, Any]) -> None:
        self._artifact = artifact

    def execute(self, *, live: bool, task_context: dict[str, object]) -> dict[str, object]:
        _ = live, task_context
        return self._artifact


class _FailingExecutor:
    def execute(self, *, live: bool, task_context: dict[str, object]) -> dict[str, object]:
        _ = live, task_context
        raise RuntimeError("provider unavailable")


class _InspectingExecutor:
    def __init__(self, *, session_factory, artifact: dict[str, Any]) -> None:
        self._session_factory = session_factory
        self._artifact = artifact
        self.observed_status: RadarRunStatus | None = None

    def execute(self, *, live: bool, task_context: dict[str, object]) -> dict[str, object]:
        _ = live
        with session_scope(self._session_factory) as session:
            run = SqlAlchemyRadarRunRepository(session).get(str(task_context["run_id"]))
        self.observed_status = run.status if run is not None else None
        return self._artifact


def _artifact() -> dict[str, Any]:
    return {
        "artifact_type": "icp_radar_live_run",
        "artifact_version": "0.6.3.4",
        "radar": {"radar_id": "toir-quick-live"},
        "run_metadata": {"runtime": "recorded"},
        "search_plan": {"radar_id": "toir-quick-live", "queries": []},
        "sources": [{"evidence_ref": "src_1", "title": "Source A", "url": "https://example.test"}],
        "candidates": [{"candidate_id": "candidate-a", "legal_name": "Candidate A"}],
        "contract_validation": [],
    }
