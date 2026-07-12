from __future__ import annotations

from power_web_os.application.radar.signal_monitoring.contracts import (
    SignalMonitoringCandidate,
    SignalSourceRef,
)
from power_web_os.application.radar.signal_monitoring.source_binding import (
    SignalSourceBindingService,
    apply_capability,
)


def test_sources_receive_generic_capability_and_basis() -> None:
    source = apply_capability(SignalSourceRef(
        source_ref="press-a",
        title="Candidate A press release",
        url="https://candidate.test/press/news/modernization",
    ))

    assert source.capability == "official_press"
    assert source.capability_basis


def test_cross_entity_source_is_retained_but_not_scheduled() -> None:
    decision = SignalSourceBindingService().bind(
        candidate=SignalMonitoringCandidate(
            candidate_id="candidate-a",
            display_name="Candidate A",
            aliases=["Candidate A"],
        ),
        source=SignalSourceRef(
            source_ref="source-b",
            title="Candidate B press release",
            url="https://candidate.test/candidate-b/press/news",
            candidate_id="candidate-b",
        ),
    )

    assert decision.status == "cross_entity"
    assert decision.scheduled_as_known_source is False
    assert decision.reason == "source_candidate_id_mismatch"


def test_identity_only_source_cannot_confirm_fresh_signal() -> None:
    decision = SignalSourceBindingService().bind(
        candidate=SignalMonitoringCandidate(
            candidate_id="candidate-a",
            display_name="Candidate A",
            aliases=["Candidate A"],
        ),
        source=SignalSourceRef(
            source_ref="about-a",
            title="Candidate A profile",
            url="https://candidate.test/about",
            snippet="Candidate A company profile.",
        ),
    )

    assert decision.status == "matched_candidate"
    assert decision.capability == "identity_only"
    assert decision.scheduled_as_known_source is False


def test_cyrillic_candidate_matches_transliterated_source_url_without_hardcode() -> None:
    decision = SignalSourceBindingService().bind(
        candidate=SignalMonitoringCandidate(
            candidate_id="ао-воронежсинтезкаучук",
            display_name="АО «Воронежсинтезкаучук»",
            aliases=["Воронежсинтезкаучук"],
        ),
        source=SignalSourceRef(
            source_ref="press-vsk",
            title="Turnaround repair press release",
            url="https://www.sibur.ru/voronejkauchuk/press-center/turnaround",
            snippet="News page for the plant.",
        ),
    )

    assert decision.status == "matched_candidate"
    assert decision.scheduled_as_known_source is True
