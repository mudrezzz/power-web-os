"""Provider-neutral ports for Power Web handoff preparation."""

from __future__ import annotations

from typing import Protocol

from power_web_os.application.radar.power_web_discovery.contracts import (
    CandidateHandoffSource,
    PowerWebHandoffSnapshot,
    PowerWebSignalContextSnapshot,
    ProductHandoffSource,
    RadarPowerWebPolicyVersion,
)


class RadarPowerWebPolicyRepository(Protocol):
    def get_active(self, radar_id: str) -> RadarPowerWebPolicyVersion | None: ...
    def list_versions(self, radar_id: str) -> tuple[RadarPowerWebPolicyVersion, ...]: ...
    def save(self, policy: RadarPowerWebPolicyVersion) -> RadarPowerWebPolicyVersion: ...


class PowerWebHandoffRepository(Protocol):
    def get(self, handoff_id: str) -> PowerWebHandoffSnapshot | None: ...
    def find_by_idempotency_key(self, idempotency_key: str) -> PowerWebHandoffSnapshot | None: ...
    def create(self, handoff: PowerWebHandoffSnapshot) -> PowerWebHandoffSnapshot: ...
    def list_for_candidate(
        self, *, radar_id: str, source_candidate_run_id: str, candidate_id: str
    ) -> tuple[PowerWebHandoffSnapshot, ...]: ...


class PowerWebCandidateReader(Protocol):
    def get_candidate(
        self, *, radar_id: str, source_candidate_run_id: str, candidate_id: str
    ) -> CandidateHandoffSource | None: ...


class PowerWebProductReader(Protocol):
    def get_active_product(self, product_id: str) -> ProductHandoffSource | None: ...


class PowerWebSignalReader(Protocol):
    def list_candidate_contexts(
        self, *, radar_id: str, source_candidate_run_id: str, candidate_id: str
    ) -> tuple[PowerWebSignalContextSnapshot, ...]: ...
