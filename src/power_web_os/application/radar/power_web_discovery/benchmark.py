"""Versioned guided/blind benchmark contracts for Power Web discovery."""

from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .contracts import EmploymentState, IdentityHypothesisState, RoleDemand


class BenchmarkModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PowerWebBenchmarkPlanningContext(BenchmarkModel):
    account_id: str
    account_name: str
    product_context: str
    role_policy: tuple[RoleDemand, ...] = Field(min_length=8)
    allowed_source_lanes: tuple[str, ...] = Field(min_length=1)


class PowerWebGuidedHint(BenchmarkModel):
    hint_id: str
    hint_type: Literal["role", "source_lane", "query_theme"]
    value: str
    reason: str


class ProfileControl(BenchmarkModel):
    control_id: str
    profile_ref: str
    anonymous: bool
    expected_display_name: str | None = None
    expected_employer: str
    expected_title: str
    source_lane: str
    expected_public_facts: tuple[str, ...] = Field(min_length=1)
    provenance_urls: tuple[str, ...] = Field(min_length=1)
    expected_role_demand_ids: tuple[str, ...] = ()
    as_of: date
    expected_state: Literal["retained_profile", "rejected_profile"]

    @model_validator(mode="after")
    def preserve_expected_anonymity(self) -> "ProfileControl":
        if self.anonymous and self.expected_display_name:
            raise ValueError("anonymous benchmark profile must not contain an expected display name")
        if not self.anonymous and not self.expected_display_name:
            raise ValueError("named benchmark profile requires an expected display name")
        return self


class IdentityPairControl(BenchmarkModel):
    control_id: str
    left_profile_ref: str
    right_profile_ref: str
    expected_state: IdentityHypothesisState
    provenance_urls: tuple[str, ...] = Field(min_length=1)
    as_of: date


class EmploymentControl(BenchmarkModel):
    control_id: str
    subject_ref: str
    employer: str
    title: str
    expected_state: EmploymentState
    provenance_urls: tuple[str, ...] = Field(min_length=1)
    as_of: date


class RelationshipControl(BenchmarkModel):
    control_id: str
    source_ref: str
    target_ref: str
    relationship_type: str
    expected_state: Literal["confirmed", "review_needed", "rejected"]
    provenance_urls: tuple[str, ...] = Field(min_length=1)
    as_of: date


class PowerWebBlindControls(BenchmarkModel):
    profiles: tuple[ProfileControl, ...] = Field(min_length=10)
    identity_pairs: tuple[IdentityPairControl, ...] = Field(min_length=8)
    employment: tuple[EmploymentControl, ...] = Field(min_length=3)
    relationships: tuple[RelationshipControl, ...] = Field(min_length=3)

    @model_validator(mode="after")
    def validate_control_coverage(self) -> "PowerWebBlindControls":
        profile_refs = [item.profile_ref for item in self.profiles]
        if len(profile_refs) != len(set(profile_refs)):
            raise ValueError("benchmark profile refs must be unique")
        known_profiles = set(profile_refs)
        referenced_profiles = {
            ref
            for item in self.identity_pairs
            for ref in (item.left_profile_ref, item.right_profile_ref)
        } | {item.subject_ref for item in self.employment} | {
            item.source_ref for item in self.relationships
        }
        missing_profiles = referenced_profiles - known_profiles
        if missing_profiles:
            raise ValueError(f"benchmark controls reference unknown profiles: {sorted(missing_profiles)}")
        same_states = {"possible", "probable", "confirmed_same"}
        same_count = sum(item.expected_state in same_states for item in self.identity_pairs)
        different_count = sum(item.expected_state in {"confirmed_different", "rejected"} for item in self.identity_pairs)
        if same_count < 4 or different_count < 4:
            raise ValueError("benchmark requires at least four same-person and four different-person controls")
        employment_states = {item.expected_state for item in self.employment}
        if employment_states != {"current", "former", "unknown"}:
            raise ValueError("benchmark requires current, former and unknown employment controls")
        if not any(item.anonymous for item in self.profiles):
            raise ValueError("benchmark requires at least one anonymous HH-style profile")
        return self


class PowerWebQualityThresholds(BenchmarkModel):
    blind_control_leakage: int = 0
    false_confirmed_person_merges: int = 0
    confirmed_identity_precision: float = 1.0
    same_person_hypothesis_retention: float = 1.0
    same_person_probable_or_confirmed_recall: float = 0.8
    required_role_coverage: float = 0.8
    employment_accuracy: float = 0.9
    confirmed_relationships_without_provenance: int = 0
    visible_graph_items_without_explanation: int = 0
    unexplained_benchmark_misses: int = 0


class PowerWebBenchmark(BenchmarkModel):
    schema_version: Literal["power_web_benchmark.v1"] = "power_web_benchmark.v1"
    benchmark_id: str
    benchmark_version: str
    as_of: date
    status: Literal["draft", "user_accepted", "superseded"]
    planning_context: PowerWebBenchmarkPlanningContext
    guided_hints: tuple[PowerWebGuidedHint, ...] = ()
    blind_controls: PowerWebBlindControls
    thresholds: PowerWebQualityThresholds = Field(default_factory=PowerWebQualityThresholds)

    @model_validator(mode="after")
    def validate_role_references(self) -> "PowerWebBenchmark":
        role_ids = {item.demand_id for item in self.planning_context.role_policy}
        referenced_roles = {
            role_id
            for profile in self.blind_controls.profiles
            for role_id in profile.expected_role_demand_ids
        } | {item.target_ref for item in self.blind_controls.relationships}
        missing_roles = referenced_roles - role_ids
        if missing_roles:
            raise ValueError(f"benchmark controls reference unknown role demands: {sorted(missing_roles)}")
        return self

    def planning_payload(self, *, guided: bool) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "benchmark_id": self.benchmark_id,
            "benchmark_version": self.benchmark_version,
            "as_of": self.as_of.isoformat(),
            "planning_context": self.planning_context.model_dump(mode="json"),
            "benchmark_mode": "guided" if guided else "blind",
        }
        if guided:
            payload["guided_hints"] = [item.model_dump(mode="json") for item in self.guided_hints]
        return payload

    def assert_no_blind_leakage(self, payload: dict[str, object]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        controls = self.blind_controls
        forbidden = (
            {item.control_id for item in controls.profiles}
            | {item.profile_ref for item in controls.profiles}
            | {item.expected_display_name for item in controls.profiles if item.expected_display_name}
            | {url for item in controls.profiles for url in item.provenance_urls}
            | {item.control_id for item in controls.identity_pairs}
            | {item.left_profile_ref for item in controls.identity_pairs}
            | {item.right_profile_ref for item in controls.identity_pairs}
            | {url for item in controls.identity_pairs for url in item.provenance_urls}
            | {item.control_id for item in controls.employment}
            | {item.subject_ref for item in controls.employment}
            | {url for item in controls.employment for url in item.provenance_urls}
            | {item.control_id for item in controls.relationships}
            | {item.source_ref for item in controls.relationships}
            | {url for item in controls.relationships for url in item.provenance_urls}
        )
        if "blind_controls" in payload or '"expected_state"' in encoded:
            raise ValueError("blind benchmark structure leaked into planning payload")
        leaked = sorted(value for value in forbidden if value and value in encoded)
        if leaked:
            raise ValueError(f"blind benchmark controls leaked into planning payload: {leaked}")


class PowerWebBenchmarkFreeze(BenchmarkModel):
    schema_version: Literal["power_web_benchmark_freeze.v1"] = "power_web_benchmark_freeze.v1"
    benchmark_path: str
    benchmark_sha256: str
    benchmark_id: str
    benchmark_version: str
    accepted_by_user: bool
    accepted_at: str


def benchmark_sha256(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_benchmark_freeze(*, benchmark_path: Path, freeze_path: Path) -> PowerWebBenchmarkFreeze:
    benchmark = PowerWebBenchmark.model_validate_json(benchmark_path.read_text(encoding="utf-8"))
    freeze = PowerWebBenchmarkFreeze.model_validate_json(freeze_path.read_text(encoding="utf-8"))
    if not freeze.accepted_by_user:
        raise ValueError("benchmark freeze is not user accepted")
    if freeze.benchmark_id != benchmark.benchmark_id or freeze.benchmark_version != benchmark.benchmark_version:
        raise ValueError("benchmark identity does not match freeze record")
    if freeze.benchmark_sha256 != benchmark_sha256(benchmark_path):
        raise ValueError("benchmark changed after freeze")
    return freeze
