from __future__ import annotations

from typing import Any

from power_web_os.application.radar.shared.source_cards import RadarPlannerSourceCard
from power_web_os.application.radar.signal_monitoring.contracts import (
    SignalAttemptRole,
    SignalMonitoringBudget,
    SignalMonitoringCandidate,
    SignalMonitoringInput,
    SignalMonitoringProviderResult,
    SignalMonitoringSignalRule,
    SignalMonitoringSourcePolicy,
    SignalMonitoringWatermark,
    SignalSearchTask,
    SignalSourceBindingDecision,
    SignalSourceRef,
)
from power_web_os.application.radar.signal_monitoring.evidence import SignalEvidenceValidationService
from power_web_os.application.radar.signal_monitoring.executor import SignalMonitoringExecutor
from power_web_os.application.radar.signal_monitoring.payloads import parse_payload, ParsedSignalPayload
from power_web_os.application.radar.signal_monitoring.windows import SignalMonitoringWindowPolicy


class _LaneProvider:
    runtime_name = "recorded-lane-provider"
    model_id = "recorded-model"

    def __init__(self, *, fail_lane: str = "", positive_lane: str = "") -> None:
        self.fail_lane = fail_lane
        self.positive_lane = positive_lane
        self.tasks: list[SignalSearchTask] = []

    def run_signal_task(
        self,
        *,
        task: SignalSearchTask,
        attempt_role: SignalAttemptRole,
    ) -> SignalMonitoringProviderResult:
        _ = attempt_role
        self.tasks.append(task)
        if task.source_lane == self.fail_lane:
            raise TimeoutError("recorded lane timeout")
        if task.source_lane == self.positive_lane:
            source_ref = f"source-{task.source_lane}"
            return SignalMonitoringProviderResult(payload={
                "sources": [{
                    "source_ref": source_ref,
                    "title": "Official modernization notice",
                    "url": "https://official.test/news/modernization",
                    "snippet": "Candidate A commissioned new equipment.",
                    "published_at": "2026-07-01",
                }],
                "observations": [{
                    "candidate_id": task.candidate_id,
                    "signal_code": task.signal_code,
                    "status": "observed",
                    "summary": "Candidate A commissioned new equipment.",
                    "score": 2,
                    "evidence_refs": [source_ref],
                    "event_at": "2026-07-01",
                    "confidence": "strong",
                }],
            })
        return SignalMonitoringProviderResult(payload={"sources": [], "observations": []})


class _FailOnceProvider:
    runtime_name = "fail-once-provider"
    model_id = "recorded-model"

    def __init__(self) -> None:
        self.calls = 0

    def run_signal_task(
        self,
        *,
        task: SignalSearchTask,
        attempt_role: SignalAttemptRole,
    ) -> SignalMonitoringProviderResult:
        self.calls += 1
        if self.calls == 1:
            raise TimeoutError("deterministic transport fault")
        return SignalMonitoringProviderResult(payload={
            "sources": [{
                "source_ref": "retry-source",
                "title": "Candidate A retry source",
                "url": "https://official.test/news/retry",
                "published_at": "2026-07-01",
            }],
            "observations": [{
                "candidate_id": task.candidate_id,
                "signal_code": task.signal_code,
                "status": "observed",
                "summary": "Candidate A modernization after retry.",
                "score": 2,
                "evidence_refs": ["retry-source"],
                "event_at": "2026-07-01",
            }],
        })


def test_multilane_plan_executes_known_official_and_open_web_with_receipts() -> None:
    provider = _LaneProvider()
    outcome = SignalMonitoringExecutor(provider).run(_monitoring_input())

    assert {task.source_lane for task in outcome.search_plan.tasks} == {
        "known_source", "official_company", "open_web"
    }
    assert len(outcome.source_lane_ledger) == 3
    assert {item.status for item in outcome.source_lane_ledger} == {"executed"}
    assert len(outcome.search_execution_receipts) == 3
    assert all(item.query and item.window_start and item.window_end for item in outcome.search_execution_receipts)
    known = next(task for task in outcome.tasks if task.source_lane == "known_source")
    assert known.source_contracts[0].url == "https://candidate.test/news"
    assert known.source_contracts[0].title == "Candidate news"
    assert known.source_contracts[0].source_id == "candidate_site"
    official = next(task for task in outcome.tasks if task.source_lane == "official_company")
    assert official.domain_restrictions == ["official.test"]
    assert outcome.observations[0].observation_status == "not_observed"
    lifecycle_states = {item.state for item in outcome.source_lifecycle}
    assert {"planned", "requested", "no_results"}.issubset(lifecycle_states)
    assert outcome.budget_counters["signal_source_verifications"] == 0


def test_query_revision_never_bypasses_disabled_open_web_policy() -> None:
    monitoring = _monitoring_input(source_policy=SignalMonitoringSourcePolicy(
        allowed_source_ids=["candidate_site", "official_site"],
        official_source_ids=["official_site"],
        allow_open_web=False,
    ))

    outcome = SignalMonitoringExecutor(_LaneProvider()).run(monitoring)

    assert {task.source_lane for task in outcome.tasks} == {"known_source", "official_company"}
    assert not any(task.revision_index for task in outcome.tasks)


def test_criterion_specific_sources_are_scheduled_only_for_matching_rule() -> None:
    monitoring = _monitoring_input(
        known_sources=[],
        configured_sources=[
            SignalSourceRef(source_ref="configured:criterion-a", source_id="criterion-a", url="https://a.test"),
            SignalSourceRef(source_ref="configured:criterion-b", source_id="criterion-b", url="https://b.test"),
        ],
        source_cards=[_card("criterion-a"), _card("criterion-b")],
        source_policy=SignalMonitoringSourcePolicy(
            allowed_source_ids=["criterion-a", "criterion-b"],
            preferred_source_ids=["criterion-a", "criterion-b"],
            allow_open_web=False,
        ),
        signal_rules=[SignalMonitoringSignalRule(
            signal_code="S1",
            label="Modernization",
            source_ids=["criterion-a"],
        )],
    )

    outcome = SignalMonitoringExecutor(_LaneProvider()).run(monitoring)

    assert [task.source_ids for task in outcome.tasks] == [["criterion-a"]]


def test_incomplete_required_lane_cannot_become_not_observed() -> None:
    outcome = SignalMonitoringExecutor(_LaneProvider(fail_lane="official_company")).run(_monitoring_input())

    assert outcome.observations[0].observation_status == "unclear"
    assert outcome.observations[0].search_status == "review_needed"
    checkpoint = outcome.checkpoint_decisions[0]
    assert checkpoint.action == "review_needed_coverage_incomplete"
    assert checkpoint.completed_required_task_count < checkpoint.required_task_count
    failed = next(item for item in outcome.search_execution_receipts if item.source_lane == "official_company")
    assert failed.outcome == "provider_error"


def test_valid_positive_requires_entity_criterion_date_source_and_official_domain() -> None:
    task = _task()
    parsed = parse_payload({
        "sources": [{
            "source_ref": "official-event",
            "title": "Modernization",
            "url": "https://official.test/news/1",
            "snippet": "Candidate A modernization project.",
            "published_at": "2026-07-01",
        }],
        "observations": [{
            "candidate_id": task.candidate_id,
            "signal_code": task.signal_code,
            "status": "observed",
            "summary": "New equipment commissioned.",
            "score": 2,
            "evidence_refs": ["official-event"],
            "event_at": "2026-07-01",
        }],
    })
    assert isinstance(parsed, ParsedSignalPayload)

    observation, record = SignalEvidenceValidationService().validate(
        task=task,
        parsed=parsed,
        previous_fingerprints=set(),
    )

    assert record.accepted is True
    assert observation.observation_status == "observed"
    assert observation.score >= 1


def test_provider_object_evidence_refs_are_resolved_as_sources() -> None:
    task = _task()
    parsed = parse_payload({
        "sources": [],
        "observations": [{
            "candidate_id": task.candidate_id,
            "signal_code": task.signal_code,
            "status": "observed",
            "summary": "Candidate A completed modernization.",
            "score": 2,
            "evidence_refs": [{
                "source_ref": "configured:official_site",
                "url": "https://official.test/news/object-ref",
                "title": "Candidate A modernization",
                "published_at": "2026-07-01",
            }],
            "event_at": "2026-07-01",
        }],
    })
    assert isinstance(parsed, ParsedSignalPayload)

    observation, record = SignalEvidenceValidationService().validate(
        task=task,
        parsed=parsed,
        previous_fingerprints=set(),
    )

    assert record.accepted is True
    assert observation.observation_status == "observed"
    assert observation.source_refs[0].startswith("configured:official_site::")
    assert observation.sources[0].url == "https://official.test/news/object-ref"


def test_confirmed_observation_does_not_keep_out_of_window_evidence_as_confirming_source() -> None:
    task = _task()
    parsed = parse_payload({
        "sources": [
            {
                "source_ref": "fresh",
                "title": "Candidate A modernization",
                "url": "https://official.test/news/fresh",
                "published_at": "2026-07-01",
            },
            {
                "source_ref": "old",
                "title": "Candidate A old modernization",
                "url": "https://official.test/news/old",
                "published_at": "2024-01-01",
            },
        ],
        "observations": [{
            "candidate_id": task.candidate_id,
            "signal_code": task.signal_code,
            "status": "observed",
            "summary": "Candidate A modernization.",
            "score": 2,
            "evidence_refs": ["fresh", "old"],
        }],
    })
    assert isinstance(parsed, ParsedSignalPayload)

    observation, record = SignalEvidenceValidationService().validate(
        task=task,
        parsed=parsed,
        previous_fingerprints=set(),
    )

    assert record.accepted is True
    assert observation.observation_status == "observed"
    assert observation.source_refs == ["fresh"]
    assert {item.source_ref for item in observation.evidence} == {"fresh", "old"}
    assert {
        item.source_ref
        for item in observation.evidence
        if item.temporal_status == "confirmed_in_window"
    } == {"fresh"}
    assert {
        item.source_ref
        for item in observation.evidence
        if item.temporal_status == "rejected_out_of_window"
    } == {"old"}


def test_transliterated_official_source_can_validate_cyrillic_candidate() -> None:
    task = _task().model_copy(update={
        "candidate_id": "ао-воронежсинтезкаучук",
        "candidate_name": "АО «Воронежсинтезкаучук»",
        "candidate_aliases": ["Воронежсинтезкаучук"],
        "domain_restrictions": ["sibur.ru"],
        "query": "site:sibur.ru АО «Воронежсинтезкаучук» ремонт",
    })
    parsed = parse_payload({
        "sources": [{
            "source_ref": "vsk-turnaround",
            "title": "Turnaround repair",
            "url": "https://www.sibur.ru/voronejkauchuk/press-center/turnaround-2026",
            "snippet": "Остановочный ремонт завершен.",
            "published_at": "2026-06-15",
        }],
        "observations": [{
            "candidate_id": task.candidate_id,
            "signal_code": task.signal_code,
            "status": "observed",
            "summary": "Остановочный ремонт завершен.",
            "score": 2,
            "evidence_refs": ["vsk-turnaround"],
            "event_at": "2026-06-15",
        }],
    })
    assert isinstance(parsed, ParsedSignalPayload)

    observation, record = SignalEvidenceValidationService().validate(
        task=task,
        parsed=parsed,
        previous_fingerprints=set(),
    )

    assert record.accepted is True
    assert observation.observation_status == "observed"


def test_retrieved_at_does_not_confirm_freshness_without_event_or_publication_date() -> None:
    task = _task()
    parsed = parse_payload({
        "sources": [{
            "source_ref": "retrieved-only",
            "title": "Candidate A modernization page",
            "url": "https://official.test/news/retrieved-only",
            "observed_at": "2026-07-01T12:00:00Z",
            "retrieved_at": "2026-07-01T12:00:00Z",
        }],
        "observations": [{
            "candidate_id": task.candidate_id,
            "signal_code": task.signal_code,
            "status": "observed",
            "summary": "Candidate A modernization.",
            "score": 2,
            "evidence_refs": ["retrieved-only"],
        }],
    })
    assert isinstance(parsed, ParsedSignalPayload)

    observation, record = SignalEvidenceValidationService().validate(
        task=task,
        parsed=parsed,
        previous_fingerprints=set(),
    )

    assert record.accepted is False
    assert record.reason == "review_needed_date_unknown"
    assert observation.search_status == "review_needed_date_unknown"
    assert observation.observation_status == "unclear"


def test_conflicting_dates_are_retained_for_human_review() -> None:
    task = _task()
    parsed = parse_payload({
        "sources": [{
            "source_ref": "conflict",
            "title": "Candidate A modernization page",
            "url": "https://official.test/news/conflict",
            "published_at": "2026-07-01",
            "date_conflict": True,
        }],
        "observations": [{
            "candidate_id": task.candidate_id,
            "signal_code": task.signal_code,
            "status": "observed",
            "summary": "Candidate A modernization.",
            "score": 2,
            "evidence_refs": ["conflict"],
            "event_at": "2026-07-01",
        }],
    })
    assert isinstance(parsed, ParsedSignalPayload)

    observation, record = SignalEvidenceValidationService().validate(
        task=task,
        parsed=parsed,
        previous_fingerprints=set(),
    )

    assert record.accepted is False
    assert record.reason == "review_needed_date_conflict"
    assert observation.search_status == "review_needed_date_conflict"


def test_evidence_for_another_company_is_rejected_as_negative_control() -> None:
    task = _task().model_copy(update={
        "candidate_id": "sibur-khimprom",
        "candidate_name": "Sibur-Khimprom",
    })
    parsed = parse_payload({
        "sources": [{
            "source_ref": "polief-expansion",
            "title": "POLIEF expanded PET capacity",
            "url": "https://www.sibur.ru/polief/products/",
            "snippet": "POLIEF completed a capacity expansion in Blagoveshchensk.",
        }],
        "observations": [{
            "candidate_id": "sibur-khimprom",
            "signal_code": task.signal_code,
            "status": "observed",
            "summary": "POLIEF expanded production.",
            "evidence_refs": ["polief-expansion"],
            "observed_at": "2026-07-01",
        }],
    })
    assert isinstance(parsed, ParsedSignalPayload)

    observation, record = SignalEvidenceValidationService().validate(
        task=task,
        parsed=parsed,
        previous_fingerprints=set(),
    )

    assert record.accepted is False
    assert record.reason == "observed_evidence_candidate_mismatch"
    assert observation.observation_status == "unclear"


def test_identity_only_source_cannot_confirm_fresh_signal() -> None:
    task = _task()
    parsed = parse_payload({
        "sources": [{
            "source_ref": "identity-page",
            "title": "Candidate A about page",
            "url": "https://official.test/about",
            "snippet": "Candidate A company profile.",
            "published_at": "2026-07-01",
        }],
        "observations": [{
            "candidate_id": task.candidate_id,
            "signal_code": task.signal_code,
            "status": "observed",
            "summary": "Candidate A profile page.",
            "score": 2,
            "evidence_refs": ["identity-page"],
            "event_at": "2026-07-01",
        }],
    })
    assert isinstance(parsed, ParsedSignalPayload)

    observation, record = SignalEvidenceValidationService().validate(
        task=task,
        parsed=parsed,
        previous_fingerprints=set(),
    )

    assert record.accepted is False
    assert record.reason == "source_capability_not_fresh_signal_capable"
    assert observation.search_status == "review_needed"


def test_known_source_lane_rejects_evidence_from_another_requested_url() -> None:
    task = _task().model_copy(update={
        "candidate_id": "sibur-khimprom",
        "candidate_name": "Sibur-Khimprom",
        "source_lane": "known_source",
        "source_contracts": [SignalSourceRef(
            source_ref="polief-products",
            url="https://www.sibur.ru/polief/products/",
        )],
    })
    parsed = parse_payload({
        "sources": [{
            "source_ref": "khimprom-news",
            "title": "Sibur-Khimprom modernization",
            "url": "https://www.sibur.ru/SiburKhimprom/press-center/news/",
        }],
        "observations": [{
            "candidate_id": task.candidate_id,
            "signal_code": task.signal_code,
            "status": "observed",
            "summary": "Sibur-Khimprom modernization.",
            "evidence_refs": ["khimprom-news"],
            "observed_at": "2026-07-01",
        }],
    })
    assert isinstance(parsed, ParsedSignalPayload)

    observation, record = SignalEvidenceValidationService().validate(
        task=task,
        parsed=parsed,
        previous_fingerprints=set(),
    )

    assert record.accepted is False
    assert record.reason == "known_source_evidence_url_mismatch"
    assert observation.search_status == "review_needed"


def test_evidence_outside_window_is_review_needed_not_observed() -> None:
    task = _task()
    parsed = parse_payload({
        "sources": [{
            "source_ref": "old",
            "title": "Candidate A old modernization",
            "url": "https://official.test/old",
            "published_at": "2024-01-01",
        }],
        "observations": [{
            "candidate_id": task.candidate_id,
            "signal_code": task.signal_code,
            "status": "observed",
            "summary": "Old modernization.",
            "score": 2,
            "evidence_refs": ["old"],
            "event_at": "2024-01-01",
        }],
    })
    assert isinstance(parsed, ParsedSignalPayload)

    observation, record = SignalEvidenceValidationService().validate(
        task=task,
        parsed=parsed,
        previous_fingerprints=set(),
    )

    assert record.accepted is False
    assert record.reason == "rejected_out_of_window"
    assert observation.search_status == "rejected_out_of_window"


def test_old_publication_does_not_confirm_freshness_from_unsupported_event_date() -> None:
    task = _task()
    parsed = parse_payload({
        "sources": [{
            "source_ref": "old-repair",
            "title": "Candidate A old turnaround repair",
            "url": "https://official.test/news/old-repair",
            "published_at": "2010-07-22",
            "snippet": "Candidate A completed a historical planned turnaround repair.",
        }],
        "observations": [{
            "candidate_id": task.candidate_id,
            "signal_code": task.signal_code,
            "status": "observed",
            "summary": "Candidate A has a fresh commissioning event.",
            "score": 2,
            "evidence_refs": ["old-repair"],
            "event_at": "2026-01-01",
            "event_end_at": "2026-03-31",
            "date_evidence": "2026-01-01",
        }],
    })
    assert isinstance(parsed, ParsedSignalPayload)

    observation, record = SignalEvidenceValidationService().validate(
        task=task,
        parsed=parsed,
        previous_fingerprints=set(),
    )

    assert record.accepted is False
    assert record.reason == "rejected_out_of_window"
    assert observation.search_status == "rejected_out_of_window"


def test_old_publication_can_confirm_future_plan_when_source_text_supports_event_date() -> None:
    task = _task()
    parsed = parse_payload({
        "sources": [{
            "source_ref": "future-plan",
            "title": "Candidate A future commissioning plan",
            "url": "https://official.test/news/future-plan",
            "published_at": "2025-02-27",
            "snippet": "Candidate A plans commissioning works in the first quarter of 2026.",
        }],
        "observations": [{
            "candidate_id": task.candidate_id,
            "signal_code": task.signal_code,
            "status": "observed",
            "summary": "Candidate A plans commissioning works.",
            "score": 2,
            "evidence_refs": ["future-plan"],
            "event_at": "2026-01-01",
            "event_end_at": "2026-03-31",
            "date_evidence": "first quarter of 2026",
        }],
    })
    assert isinstance(parsed, ParsedSignalPayload)

    observation, record = SignalEvidenceValidationService().validate(
        task=task,
        parsed=parsed,
        previous_fingerprints=set(),
    )

    assert record.accepted is True
    assert observation.observation_status == "observed"


def test_cross_entity_known_source_is_not_scheduled_as_known_source() -> None:
    monitoring = _monitoring_input(
        known_sources=[SignalSourceRef(
            source_ref="known-cross",
            source_id="candidate_site",
            title="Other entity news",
            url="https://candidate.test/other/news",
            snippet="Other entity modernization.",
        )],
        candidates=[SignalMonitoringCandidate(
            candidate_id="candidate-a",
            display_name="Candidate A",
            source_refs=["known-cross"],
            product_acceptance_status="product_candidate",
        )],
        source_binding_decisions=[SignalSourceBindingDecision(
            candidate_id="candidate-a",
            source_ref="known-cross",
            status="cross_entity",
            capability="official_press",
            reason="source_candidate_id_mismatch",
            scheduled_as_known_source=False,
        )],
    )

    outcome = SignalMonitoringExecutor(_LaneProvider()).run(monitoring)

    assert not any(task.source_lane == "known_source" for task in outcome.tasks)
    assert any(
        decision.source_ref == "known-cross"
        and decision.status == "rejected"
        and decision.reason == "source_candidate_id_mismatch"
        for decision in outcome.source_strategy_decisions
    )


def test_structured_registry_file_is_not_scheduled_as_known_signal_source() -> None:
    monitoring = _monitoring_input(
        known_sources=[SignalSourceRef(
            source_ref="registry-xlsx",
            source_id="candidate_site",
            title="Candidate registry export",
            url="https://official.test/export/companies.xlsx",
            snippet="Candidate A appears in the registry export.",
        )],
        candidates=[SignalMonitoringCandidate(
            candidate_id="candidate-a",
            display_name="Candidate A",
            source_refs=["registry-xlsx"],
            product_acceptance_status="product_candidate",
        )],
        source_binding_decisions=[SignalSourceBindingDecision(
            candidate_id="candidate-a",
            source_ref="registry-xlsx",
            status="matched_candidate",
            capability="identity_only",
            reason="structured_registry_or_disclosure_file",
            scheduled_as_known_source=False,
        )],
    )

    outcome = SignalMonitoringExecutor(_LaneProvider()).run(monitoring)

    assert not any(task.source_lane == "known_source" for task in outcome.tasks)
    assert any(
        decision.source_ref == "registry-xlsx"
        and decision.status == "rejected"
        and decision.reason == "structured_registry_or_disclosure_file"
        for decision in outcome.source_strategy_decisions
    )


def test_candidate_alias_is_used_only_for_bounded_revision() -> None:
    monitoring = _monitoring_input(
        candidates=[SignalMonitoringCandidate(
            candidate_id="candidate-a",
            display_name="Candidate A",
            legal_name="Candidate A LLC",
            aliases=["Candidate Alpha"],
            source_refs=["known-a"],
            product_acceptance_status="product_candidate",
        )],
        signal_rules=[SignalMonitoringSignalRule(
            signal_code="S1",
            label="Modernization",
            expected_evidence=["new equipment"],
        )],
    )

    outcome = SignalMonitoringExecutor(_LaneProvider()).run(monitoring)

    assert all(task.alternate_query for task in outcome.search_plan.tasks)
    assert any("Candidate A LLC" in task.alternate_query for task in outcome.search_plan.tasks)
    assert all(task.revision_index <= 1 for task in outcome.tasks)


def test_russian_candidate_query_uses_localized_signal_terms() -> None:
    monitoring = _monitoring_input(
        candidates=[SignalMonitoringCandidate(
            candidate_id="russian-candidate",
            display_name="АО «Русский завод»",
            legal_name="АО «Русский завод»",
            source_refs=[],
            product_acceptance_status="product_candidate",
        )],
        known_sources=[],
        configured_sources=[],
        source_cards=[_card("openrouter_web", source_type="open_web", broad=True)],
        source_policy=SignalMonitoringSourcePolicy(allowed_source_ids=["openrouter_web"]),
        signal_rules=[
            SignalMonitoringSignalRule(signal_code="S1", label="TOIR / reliability activity"),
            SignalMonitoringSignalRule(signal_code="S2", label="Modernization / capacity investment"),
        ],
    )

    outcome = SignalMonitoringExecutor(_LaneProvider()).run(monitoring)

    queries = {task.signal_code: task.query for task in outcome.search_plan.tasks}
    assert "остановочный ремонт" in queries["S1"]
    assert "модернизация" in queries["S2"]


def test_candidate_path_query_terms_ignore_structured_file_paths() -> None:
    monitoring = _monitoring_input(
        candidates=[SignalMonitoringCandidate(
            candidate_id="russian-candidate",
            display_name="АО «Русский завод»",
            legal_name="АО «Русский завод»",
            source_refs=["registry-xlsx", "official-section"],
            product_acceptance_status="product_candidate",
        )],
        known_sources=[
            SignalSourceRef(
                source_ref="registry-xlsx",
                url="https://official.test/upload/iblock/e70/export.xlsx",
            ),
            SignalSourceRef(
                source_ref="official-section",
                url="https://official.test/voronejkauchuk/press-center/news/",
            ),
        ],
        configured_sources=[],
        source_cards=[_card("openrouter_web", source_type="open_web", broad=True)],
        source_policy=SignalMonitoringSourcePolicy(allowed_source_ids=["openrouter_web"]),
    )

    outcome = SignalMonitoringExecutor(_LaneProvider()).run(monitoring)

    query = next(task.query for task in outcome.search_plan.tasks if task.source_lane == "open_web")
    assert "voronejkauchuk" in query
    assert "iblock" not in query


def test_incremental_signal_monitoring_dedupes_unknown_review_evidence() -> None:
    task = _task()
    parsed = parse_payload({
        "sources": [{
            "source_ref": "unknown-review",
            "title": "Candidate A modernization page",
            "url": "https://official.test/news/unknown-review",
        }],
        "observations": [{
            "candidate_id": task.candidate_id,
            "signal_code": task.signal_code,
            "status": "observed",
            "summary": "Candidate A modernization.",
            "score": 2,
            "evidence_refs": ["unknown-review"],
        }],
    })
    assert isinstance(parsed, ParsedSignalPayload)

    observation, record = SignalEvidenceValidationService().validate(
        task=task,
        parsed=parsed,
        previous_fingerprints=set(),
        previous_source_keys={"candidate-a|S1|https://official.test/news/unknown-review"},
    )

    assert record.accepted is False
    assert observation.search_status == "duplicate_existing_review"


def test_temporal_and_binding_decisions_have_product_safe_reasons() -> None:
    monitoring = _monitoring_input()

    outcome = SignalMonitoringExecutor(_LaneProvider(fail_lane="official_company")).run(monitoring)

    assert all(item.reason for item in outcome.source_lane_ledger)
    assert all(item.reason for item in outcome.evidence_validation_records)
    assert all(item.reason for item in outcome.source_binding_decisions)


def test_provider_transport_error_gets_bounded_primary_retry() -> None:
    provider = _FailOnceProvider()
    monitoring = _monitoring_input(
        known_sources=[],
        configured_sources=[],
        source_cards=[_card("openrouter_web", source_type="open_web", broad=True)],
        source_policy=SignalMonitoringSourcePolicy(allowed_source_ids=["openrouter_web"]),
        budget=SignalMonitoringBudget(
            max_signal_tasks=2,
            max_signal_provider_calls=3,
            max_retries_per_task=1,
            max_signal_extraction_retries=1,
        ),
    )

    outcome = SignalMonitoringExecutor(provider).run(monitoring)

    assert provider.calls == 2
    assert [item.attempt_role for item in outcome.provider_attempts] == ["primary", "primary_retry"]
    assert outcome.task_observations[0].observation_status == "observed"


def test_window_policy_uses_365_default_then_incremental_lane_watermark() -> None:
    monitoring = _monitoring_input(
        known_sources=[],
        configured_sources=[],
        source_cards=[_card("openrouter_web", source_type="open_web", broad=True)],
        source_policy=SignalMonitoringSourcePolicy(allowed_source_ids=["openrouter_web"]),
        lookback_days=365,
        lookback_basis="default_365",
        as_of="2026-07-10T12:00:00Z",
    )
    rule = monitoring.signal_rules[0]
    policy = SignalMonitoringWindowPolicy()

    initial = policy.resolve(
        monitoring_input=monitoring,
        candidate_id="candidate-a",
        rule=rule,
        source_lane="open_web",
    )
    assert initial.basis == "default_365"
    assert initial.lookback_days == 365
    assert initial.window_start == "2025-07-10T12:00:00Z"

    incremental_input = monitoring.model_copy(update={
        "previous_watermarks": [SignalMonitoringWatermark(
            candidate_id="candidate-a",
            signal_code="S1",
            source_lane="open_web",
            searched_through_at="2026-07-08T12:00:00Z",
        )]
    })
    incremental = policy.resolve(
        monitoring_input=incremental_input,
        candidate_id="candidate-a",
        rule=rule,
        source_lane="open_web",
    )
    assert incremental.basis == "incremental"
    assert incremental.window_start == "2026-07-06T12:00:00Z"
    assert incremental.previous_watermark == "2026-07-08T12:00:00Z"


def test_explicit_window_override_has_priority_over_criterion_policy() -> None:
    monitoring = _monitoring_input(
        lookback_days=365,
        lookback_basis="explicit_override",
        previous_watermarks=[SignalMonitoringWatermark(
            candidate_id="candidate-a",
            signal_code="S1",
            source_lane="open_web",
            searched_through_at="2026-07-08T12:00:00Z",
        )],
        signal_rules=[SignalMonitoringSignalRule(
            signal_code="S1",
            label="Modernization",
            initial_lookback_days=30,
        )],
    )

    window = SignalMonitoringWindowPolicy().resolve(
        monitoring_input=monitoring,
        candidate_id="candidate-a",
        rule=monitoring.signal_rules[0],
        source_lane="open_web",
    )

    assert window.basis == "explicit_override"
    assert window.lookback_days == 365
    assert window.previous_watermark == ""


def test_failed_lane_does_not_advance_its_watermark() -> None:
    monitoring = _monitoring_input(previous_watermarks=[SignalMonitoringWatermark(
        candidate_id="candidate-a",
        signal_code="S1",
        source_lane="official_company",
        searched_through_at="2026-06-01T00:00:00Z",
    )])
    outcome = SignalMonitoringExecutor(_LaneProvider(fail_lane="official_company")).run(monitoring)

    official = next(item for item in outcome.watermarks_after if item.source_lane == "official_company")
    assert official.searched_through_at == "2026-06-01T00:00:00Z"
    assert any(item.source_lane == "open_web" and item.searched_through_at == monitoring.as_of for item in outcome.watermarks_after)


def _monitoring_input(**overrides: Any) -> SignalMonitoringInput:
    payload: dict[str, Any] = {
        "run_id": "signal-run-quality",
        "radar_id": "signal-radar",
        "source_candidate_run_id": "candidate-run",
        "candidates": [SignalMonitoringCandidate(
            candidate_id="candidate-a",
            display_name="Candidate A",
            source_refs=["known-a"],
            product_acceptance_status="product_candidate",
        )],
        "signal_rules": [SignalMonitoringSignalRule(signal_code="S1", label="Modernization")],
        "known_sources": [SignalSourceRef(
            source_ref="known-a",
            source_id="candidate_site",
            title="Candidate news",
            url="https://candidate.test/news",
            snippet="Candidate A official news archive.",
        )],
        "configured_sources": [SignalSourceRef(
            source_ref="configured:official_site",
            source_id="official_site",
            title="Official site",
            url="https://official.test",
        )],
        "source_cards": [
            _card("candidate_site"),
            _card("official_site", source_type="url"),
            _card("openrouter_web", source_type="open_web", broad=True),
        ],
        "source_policy": SignalMonitoringSourcePolicy(
            allowed_source_ids=["candidate_site", "official_site", "openrouter_web"],
            official_source_ids=["official_site"],
        ),
        "budget": SignalMonitoringBudget(max_signal_tasks=16, max_signal_provider_calls=24),
        "lookback_days": 365,
        "lookback_basis": "explicit_override",
        "as_of": "2026-07-10T12:00:00Z",
    }
    payload.update(overrides)
    return SignalMonitoringInput(**payload)


def _card(source_id: str, *, source_type: str = "web", broad: bool = False) -> RadarPlannerSourceCard:
    return RadarPlannerSourceCard(
        source_id=source_id,
        source_label=source_id,
        connector_profile_id=source_id,
        source_type=source_type,
        supports_signal_evidence=True,
        supports_broad_discovery=broad,
    )


def _task() -> SignalSearchTask:
    return SignalSearchTask(
        task_id="signal-candidate-a-S1-official",
        candidate_id="candidate-a",
        candidate_name="Candidate A",
        signal_code="S1",
        signal_label="Modernization",
        query="site:official.test Candidate A modernization",
        lookback_days=365,
        source_lane="official_company",
        domain_restrictions=["official.test"],
        window_start="2025-07-10T12:00:00Z",
        window_end="2026-07-10T12:00:00Z",
    )
