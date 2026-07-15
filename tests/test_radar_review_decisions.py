from __future__ import annotations

import pytest

from power_web_os.application.radar.lifecycle.records import RadarReviewDecisionRecord
from power_web_os.application.radar.lifecycle.review import (
    RadarReviewDecisionCommand,
    RadarReviewDecisionService,
    RadarReviewValidationError,
)


def test_review_service_accepts_valid_qualification_and_signal_decisions() -> None:
    repository = _InMemoryReviewRepository()
    service = RadarReviewDecisionService(repository=repository)

    qualification = service.save(
        RadarReviewDecisionCommand(
            run_id="run-1",
            radar_id="toir-quick-live",
            candidate_id="candidate-a",
            subject_type="qualification",
            subject_id="rule-q1",
            status="corrected",
            reviewer="reviewer-a",
            comment="Evidence only partially supports this rule.",
            decision_payload={"corrected_assessment": "partially_matches"},
            score_impact={"original_assessment": "matches", "effective_assessment": "partially_matches"},
        )
    )
    signal = service.save(
        RadarReviewDecisionCommand(
            run_id="run-1",
            radar_id="toir-quick-live",
            candidate_id="candidate-a",
            subject_type="signal",
            subject_id="S1",
            status="corrected",
            reviewer="reviewer-a",
            comment="Signal exists but should not be max strength.",
            decision_payload={"adjusted_score": 1},
            score_impact={"original_score": 2, "effective_score": 1, "delta": -1},
        )
    )

    assert qualification.status == "corrected"
    assert signal.decision_payload["adjusted_score"] == 1
    assert service.list_for_run("run-1") == (qualification, signal)


@pytest.mark.parametrize(
    "command",
    [
        RadarReviewDecisionCommand(
            run_id="run-1",
            radar_id="radar-1",
            candidate_id="candidate-a",
            subject_type="qualification",
            subject_id="rule-q1",
            status="corrected",
            comment="",
            decision_payload={"corrected_assessment": "matches"},
        ),
        RadarReviewDecisionCommand(
            run_id="run-1",
            radar_id="radar-1",
            candidate_id="candidate-a",
            subject_type="qualification",
            subject_id="rule-q1",
            status="corrected",
            comment="Needs correction.",
            decision_payload={"corrected_assessment": "unsupported"},
        ),
        RadarReviewDecisionCommand(
            run_id="run-1",
            radar_id="radar-1",
            candidate_id="candidate-a",
            subject_type="signal",
            subject_id="S1",
            status="stale",
            comment="",
        ),
        RadarReviewDecisionCommand(
            run_id="run-1",
            radar_id="radar-1",
            candidate_id="candidate-a",
            subject_type="signal",
            subject_id="S1",
            status="corrected",
            comment="Needs correction.",
            decision_payload={"adjusted_score": 3},
        ),
    ],
)
def test_review_service_rejects_invalid_decisions(command: RadarReviewDecisionCommand) -> None:
    service = RadarReviewDecisionService(repository=_InMemoryReviewRepository())

    with pytest.raises(RadarReviewValidationError):
        service.save(command)


class _InMemoryReviewRepository:
    def __init__(self) -> None:
        self._records: dict[tuple[str, str, str, str], RadarReviewDecisionRecord] = {}

    def upsert(self, record: RadarReviewDecisionRecord) -> RadarReviewDecisionRecord:
        self._records[(record.run_id, record.candidate_id, record.subject_type, record.subject_id)] = record
        return record

    def get(
        self,
        *,
        run_id: str,
        candidate_id: str,
        subject_type: str,
        subject_id: str,
    ) -> RadarReviewDecisionRecord | None:
        return self._records.get((run_id, candidate_id, subject_type, subject_id))

    def list_for_run(self, run_id: str) -> tuple[RadarReviewDecisionRecord, ...]:
        return tuple(record for record in self._records.values() if record.run_id == run_id)

    def delete(self, *, run_id: str, candidate_id: str, subject_type: str, subject_id: str) -> bool:
        return self._records.pop((run_id, candidate_id, subject_type, subject_id), None) is not None
