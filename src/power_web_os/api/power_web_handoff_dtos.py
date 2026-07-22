"""Transport contracts for Radar Power Web policy and immutable handoffs."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PowerWebApiDto(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RadarPowerWebPolicyUpdateRequest(PowerWebApiDto):
    expected_policy_version_id: str | None = None
    product_ids: list[str] = Field(default_factory=list)
    requester: str = Field(min_length=1)


class ReviewNeededAcknowledgementRequest(PowerWebApiDto):
    acknowledged: bool
    reviewer: str = Field(min_length=1)
    comment: str | None = None


class PowerWebHandoffCreateRequest(PowerWebApiDto):
    source_candidate_run_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    product_ids: list[str] | None = None
    include_latest_signal_context: bool = True
    review_needed_acknowledgement: ReviewNeededAcknowledgementRequest | None = None
    idempotency_key: str = Field(min_length=1)
    requester: str = Field(min_length=1)
