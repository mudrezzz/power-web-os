"""Provider-neutral contracts for the future Power Web discovery pipeline."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


IdentityHypothesisState = Literal[
    "possible",
    "probable",
    "confirmed_same",
    "confirmed_different",
    "rejected",
]
EmploymentState = Literal["current", "former", "unknown"]
ReviewState = Literal["confirmed", "review_needed", "rejected"]
GapKind = Literal["role", "source", "profile", "identity", "employment", "relationship"]


class PowerWebContract(BaseModel):
    """Strict base model that prevents unreviewed provider fields from leaking in."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class RoleDemand(PowerWebContract):
    demand_id: str = Field(min_length=1)
    role: str = Field(min_length=1)
    required: bool = True
    scope: str = Field(min_length=1)
    aliases: tuple[str, ...] = ()
    expected_evidence: tuple[str, ...] = ()
    reason: str = Field(min_length=1)


class SourceEvidence(PowerWebContract):
    evidence_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    url: str = Field(pattern=r"^https?://")
    title: str = Field(min_length=1)
    excerpt: str = Field(min_length=1, max_length=1200)
    retrieved_at: datetime
    published_at: date | None = None
    capability: str = Field(min_length=1)
    claim_refs: tuple[str, ...] = ()
    image_fingerprints: tuple[str, ...] = ()
    access_limited: bool = False


class PersonProfile(PowerWebContract):
    """One source-native profile; absence of a public name is preserved."""

    profile_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    display_name: str | None = None
    anonymous: bool = False
    aliases: tuple[str, ...] = ()
    role_titles: tuple[str, ...] = ()
    employers: tuple[str, ...] = ()
    locations: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    image_fingerprints: tuple[str, ...] = ()

    @model_validator(mode="after")
    def preserve_anonymity(self) -> "PersonProfile":
        if self.anonymous and self.display_name:
            raise ValueError("anonymous profile must not invent a display name")
        if not self.anonymous and not self.display_name:
            raise ValueError("named profile requires display_name")
        return self


class IdentityHypothesis(PowerWebContract):
    hypothesis_id: str = Field(min_length=1)
    left_profile_id: str = Field(min_length=1)
    right_profile_id: str = Field(min_length=1)
    state: IdentityHypothesisState
    compatible_features: tuple[str, ...] = ()
    hard_contradictions: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    reason: str = Field(min_length=1)
    reversible: bool = True

    @model_validator(mode="after")
    def enforce_confirmation_evidence(self) -> "IdentityHypothesis":
        if self.left_profile_id == self.right_profile_id:
            raise ValueError("identity hypothesis requires two distinct profiles")
        if self.state == "confirmed_same":
            dimensions = set(self.compatible_features)
            independent = {feature for feature in dimensions if feature != "image_fingerprint"}
            if len(dimensions) < 2 or not independent:
                raise ValueError("confirmed_same requires at least two compatible dimensions")
            if self.hard_contradictions:
                raise ValueError("hard contradiction blocks confirmed_same")
        return self


class PersonIdentity(PowerWebContract):
    """A confirmed, reversible identity over retained source profiles."""

    identity_id: str = Field(min_length=1)
    profile_ids: tuple[str, ...] = Field(min_length=2)
    confirmation_hypothesis_ids: tuple[str, ...] = Field(min_length=1)
    display_name: str | None = None
    reversible: bool = True

    @model_validator(mode="after")
    def require_distinct_profiles(self) -> "PersonIdentity":
        if len(set(self.profile_ids)) < 2:
            raise ValueError("confirmed identity requires at least two distinct profiles")
        return self


class EmploymentClaim(PowerWebContract):
    claim_id: str = Field(min_length=1)
    subject_ref: str = Field(min_length=1)
    employer: str = Field(min_length=1)
    unit: str | None = None
    title: str = Field(min_length=1)
    started_on: date | None = None
    ended_on: date | None = None
    state: EmploymentState
    evidence_refs: tuple[str, ...] = Field(min_length=1)


class RelationshipClaim(PowerWebContract):
    claim_id: str = Field(min_length=1)
    relationship_type: str = Field(min_length=1)
    source_ref: str = Field(min_length=1)
    target_ref: str = Field(min_length=1)
    valid_from: date | None = None
    valid_to: date | None = None
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    state: ReviewState


class InfluenceHypothesis(PowerWebContract):
    hypothesis_id: str = Field(min_length=1)
    subject_ref: str = Field(min_length=1)
    role_demand_id: str = Field(min_length=1)
    influence_type: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    state: ReviewState
    reason: str = Field(min_length=1)


class PowerWebGap(PowerWebContract):
    gap_id: str = Field(min_length=1)
    kind: GapKind
    subject_ref: str = Field(min_length=1)
    path_reason: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = ()


class PowerWebGraphNode(PowerWebContract):
    node_id: str = Field(min_length=1)
    node_type: Literal["account", "profile", "person", "role", "organization", "gap"]
    label: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = ()
    gap_reason: str | None = None

    @model_validator(mode="after")
    def require_explanation(self) -> "PowerWebGraphNode":
        if not self.evidence_refs and not self.gap_reason:
            raise ValueError("visible graph node requires evidence or a gap reason")
        return self


class PowerWebGraphEdge(PowerWebContract):
    edge_id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    target: str = Field(min_length=1)
    edge_type: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = ()
    hypothesis_reason: str | None = None

    @model_validator(mode="after")
    def require_explanation(self) -> "PowerWebGraphEdge":
        if not self.evidence_refs and not self.hypothesis_reason:
            raise ValueError("visible graph edge requires evidence or a hypothesis reason")
        return self


class PowerWebArtifact(PowerWebContract):
    schema_version: Literal["power_web_discovery.v1"] = "power_web_discovery.v1"
    run_id: str = Field(min_length=1)
    pipeline_id: Literal["power_web_discovery"] = "power_web_discovery"
    account_id: str = Field(min_length=1)
    source_candidate_run_id: str = Field(min_length=1)
    source_signal_run_id: str | None = None
    as_of: datetime
    role_demands: tuple[RoleDemand, ...] = ()
    evidence: tuple[SourceEvidence, ...] = ()
    profiles: tuple[PersonProfile, ...] = ()
    identity_hypotheses: tuple[IdentityHypothesis, ...] = ()
    identities: tuple[PersonIdentity, ...] = ()
    employment_claims: tuple[EmploymentClaim, ...] = ()
    relationship_claims: tuple[RelationshipClaim, ...] = ()
    influence_hypotheses: tuple[InfluenceHypothesis, ...] = ()
    graph_nodes: tuple[PowerWebGraphNode, ...] = ()
    graph_edges: tuple[PowerWebGraphEdge, ...] = ()
    gaps: tuple[PowerWebGap, ...] = ()
    diagnostics: tuple[str, ...] = ()
    raw_html_retained: Literal[False] = False
    raw_images_retained: Literal[False] = False
    private_contacts_retained: Literal[False] = False
    automated_outreach_allowed: Literal[False] = False

    @model_validator(mode="after")
    def validate_references(self) -> "PowerWebArtifact":
        evidence_ids = {item.evidence_id for item in self.evidence}
        referenced = {
            ref
            for collection in (
                self.profiles,
                self.identity_hypotheses,
                self.employment_claims,
                self.relationship_claims,
                self.influence_hypotheses,
                self.graph_nodes,
                self.graph_edges,
            )
            for item in collection
            for ref in item.evidence_refs
        }
        missing = referenced - evidence_ids
        if missing:
            raise ValueError(f"unresolved evidence refs: {sorted(missing)}")
        return self
