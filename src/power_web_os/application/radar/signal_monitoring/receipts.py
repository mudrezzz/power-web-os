"""Product-safe search receipts and source lifecycle records."""

from __future__ import annotations

from datetime import UTC, datetime

from power_web_os.application.radar.signal_monitoring.contracts import (
    SignalSearchExecutionReceipt,
    SignalSearchTask,
    SignalSourceLifecycleRecord,
    SignalSourceRef,
)


class SignalSearchReceiptFactory:
    """Create safe receipts without retaining raw provider responses."""

    def create(
        self,
        *,
        task: SignalSearchTask,
        sources: list[SignalSourceRef],
        engine: str,
        outcome: str,
        started_at: str,
        completed_at: str | None = None,
    ) -> SignalSearchExecutionReceipt:
        return SignalSearchExecutionReceipt(
            task_id=task.task_id,
            candidate_id=task.candidate_id,
            signal_code=task.signal_code,
            source_lane=task.source_lane,
            query=task.query,
            requested_urls=[item.url for item in task.source_contracts if item.url],
            requested_domains=list(task.domain_restrictions),
            engine=engine,
            window_start=task.window_start,
            window_end=task.window_end,
            started_at=started_at,
            completed_at=completed_at or _now(),
            result_count=len(sources),
            source_refs=[item.source_ref for item in sources],
            outcome=outcome,  # type: ignore[arg-type]
        )

    @staticmethod
    def planned(task: SignalSearchTask) -> SignalSourceLifecycleRecord:
        return SignalSourceLifecycleRecord(
            task_id=task.task_id,
            source_lane=task.source_lane,
            state="planned",
            reason="accepted_search_plan",
        )

    @staticmethod
    def requested(task: SignalSearchTask) -> SignalSourceLifecycleRecord:
        return SignalSourceLifecycleRecord(
            task_id=task.task_id,
            source_lane=task.source_lane,
            state="requested",
            reason="provider_request_started",
        )

    @staticmethod
    def lifecycle(receipt: SignalSearchExecutionReceipt) -> list[SignalSourceLifecycleRecord]:
        if not receipt.source_refs:
            state = "no_results" if receipt.outcome == "no_results" else "failed"
            return [SignalSourceLifecycleRecord(
                task_id=receipt.task_id,
                source_lane=receipt.source_lane,
                state=state,
                reason=receipt.outcome,
            )]
        return [
            SignalSourceLifecycleRecord(
                task_id=receipt.task_id,
                source_ref=source_ref,
                source_lane=receipt.source_lane,
                state="retrieved",
                reason="normalized_provider_source",
            )
            for source_ref in receipt.source_refs
        ]

    @staticmethod
    def accepted_evidence(task: SignalSearchTask, source_refs: list[str]) -> list[SignalSourceLifecycleRecord]:
        return [
            SignalSourceLifecycleRecord(
                task_id=task.task_id,
                source_ref=source_ref,
                source_lane=task.source_lane,
                state=state,
                reason="accepted_signal_evidence",
            )
            for source_ref in source_refs
            for state in ("verified", "linked", "used")
        ]


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
