from __future__ import annotations

import pytest

from power_web_os.application.radar.lifecycle.records import RadarRunRecord
from power_web_os.jobs.radar_jobs import SignalMonitoringCeleryJobQueue, radar_celery_app


class _Task:
    def __init__(self) -> None:
        self.run_ids: list[str] = []

    def delay(self, run_id: str) -> None:
        self.run_ids.append(run_id)


def test_signal_monitoring_queue_carries_only_run_id_and_rejects_candidate_run() -> None:
    task = _Task()
    queue = SignalMonitoringCeleryJobQueue(task=task)
    queue.enqueue_signal_monitoring_run(RadarRunRecord(
        run_id="signal-run-job",
        radar_id="radar",
        pipeline_id="signal_monitoring",
        source_run_id="candidate-run",
    ))
    assert task.run_ids == ["signal-run-job"]

    with pytest.raises(ValueError, match="only signal-monitoring"):
        queue.enqueue_signal_monitoring_run(RadarRunRecord(run_id="candidate-run", radar_id="radar"))


def test_candidate_and_signal_jobs_use_separate_celery_queues() -> None:
    routes = radar_celery_app.conf.task_routes
    assert routes["power_web_os.execute_radar_run"]["queue"] == "candidate_discovery"
    assert routes["power_web_os.execute_signal_monitoring_run"]["queue"] == "signal_monitoring"
