from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Evidence:
    source: str
    url: str | None
    summary: str
    confidence: float = 0.5


@dataclass(frozen=True, slots=True)
class Signal:
    kind: str
    summary: str
    strength: float
    evidence: tuple[Evidence, ...] = ()


@dataclass(frozen=True, slots=True)
class PowerWebRole:
    role: str
    person_name: str | None
    state: str
    influence: float
    relation: str | None = None


@dataclass(frozen=True, slots=True)
class Account:
    account_id: str
    name: str
    icp_fit: float
    signals: tuple[Signal, ...] = ()
    roles: tuple[PowerWebRole, ...] = ()
    missing_roles: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Playbook:
    name: str
    allowed_routes: tuple[str, ...]
    blocked_channels: tuple[str, ...] = ()
    available_assets: tuple[str, ...] = ()
    required_review_for: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AccessRoute:
    route_type: str
    title: str
    score: int
    reason: str
    risk: str
    owner: str
    evidence_refs: tuple[str, ...] = ()
    expected_state_change: str | None = None
    requires_human_review: bool = True


@dataclass(frozen=True, slots=True)
class AccessPlan:
    account_id: str
    account_name: str
    routes: tuple[AccessRoute, ...] = field(default_factory=tuple)
    unresolved_gaps: tuple[str, ...] = field(default_factory=tuple)

