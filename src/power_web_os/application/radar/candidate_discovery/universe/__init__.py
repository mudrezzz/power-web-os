"""Candidate-discovery universe source-of-truth package."""

from power_web_os.application.radar.candidate_discovery.universe.coverage import coverage_risk, coverage_warnings
from power_web_os.application.radar.candidate_discovery.universe.gaps import (
    dedupe_gap_payloads,
    gap_items,
    gap_observations,
    gap_payloads,
)
from power_web_os.application.radar.candidate_discovery.universe.identity import (
    candidate_name,
    candidate_name_set,
    candidate_source_refs,
    first_task_id,
    source_refs,
    stable_id,
)
from power_web_os.application.radar.candidate_discovery.universe.metadata import dict_list, merge_provider_metadata
from power_web_os.application.radar.candidate_discovery.universe.projection import candidate_universe_entries
from power_web_os.application.radar.candidate_discovery.universe.signal_scope import filter_signal_result

__all__ = [
    "candidate_name",
    "candidate_name_set",
    "candidate_source_refs",
    "candidate_universe_entries",
    "coverage_risk",
    "coverage_warnings",
    "dedupe_gap_payloads",
    "dict_list",
    "filter_signal_result",
    "first_task_id",
    "gap_items",
    "gap_observations",
    "gap_payloads",
    "merge_provider_metadata",
    "source_refs",
    "stable_id",
]
