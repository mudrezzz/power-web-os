from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from power_web_os.domain import AccessPlan, Account, Playbook
from power_web_os.planner import DeterministicAccessPlanner

KNOWN_ROUTE_TYPES = (
    "partner_intro",
    "technical_benchmark",
    "procurement_discovery",
    "dark_stakeholder_discovery",
)


@dataclass(frozen=True, slots=True)
class RoutePolicyDecision:
    route_type: str
    status: str
    reason: str
    route_score: int | None
    requires_human_review: bool


@dataclass(frozen=True, slots=True)
class PlaybookVariantAnalysis:
    variant_id: str
    label: str
    description: str
    playbook: Playbook
    route_preview: AccessPlan
    route_decisions: tuple[RoutePolicyDecision, ...]


@dataclass(frozen=True, slots=True)
class PlaybookAnalysis:
    contract_version: str
    current: PlaybookVariantAnalysis
    variants: tuple[PlaybookVariantAnalysis, ...]


class PlaybookAnalysisBuilder:
    """Explains how deterministic playbook rules shape generated access routes."""

    def __init__(self, planner: DeterministicAccessPlanner | None = None) -> None:
        self._planner = planner or DeterministicAccessPlanner()

    def build(self, *, account: Account, playbook: Playbook, access_plan: AccessPlan) -> PlaybookAnalysis:
        current = self._variant(
            variant_id="current",
            label="Current playbook",
            description="Rules used for the generated Access Plan.",
            account=account,
            playbook=playbook,
            route_preview=access_plan,
        )
        no_partner_playbook = self._without_partner_motion(playbook)
        no_partner_plan = self._planner.build_plan(account, no_partner_playbook)
        no_partner = self._variant(
            variant_id="no_partner_motion",
            label="No partner motion",
            description="What-if variant with partner intro and partner-case assets disabled.",
            account=account,
            playbook=no_partner_playbook,
            route_preview=no_partner_plan,
        )
        return PlaybookAnalysis(contract_version="0.6", current=current, variants=(no_partner,))

    def _variant(
        self,
        *,
        variant_id: str,
        label: str,
        description: str,
        account: Account,
        playbook: Playbook,
        route_preview: AccessPlan,
    ) -> PlaybookVariantAnalysis:
        return PlaybookVariantAnalysis(
            variant_id=variant_id,
            label=label,
            description=description,
            playbook=playbook,
            route_preview=route_preview,
            route_decisions=tuple(
                self._decision(
                    account=account,
                    playbook=playbook,
                    route_preview=route_preview,
                    route_type=route_type,
                    variant_id=variant_id,
                )
                for route_type in KNOWN_ROUTE_TYPES
            ),
        )

    def _decision(
        self,
        *,
        account: Account,
        playbook: Playbook,
        route_preview: AccessPlan,
        route_type: str,
        variant_id: str,
    ) -> RoutePolicyDecision:
        route = next((item for item in route_preview.routes if item.route_type == route_type), None)
        requires_review = route_type in playbook.required_review_for or "all" in playbook.required_review_for
        if route is not None:
            return RoutePolicyDecision(
                route_type=route_type,
                status="recommended",
                reason="Allowed by playbook and supported by account evidence.",
                route_score=route.score,
                requires_human_review=route.requires_human_review,
            )

        if route_type not in playbook.allowed_routes:
            return RoutePolicyDecision(
                route_type=route_type,
                status="blocked",
                reason=(
                    "Partner motion disabled in this what-if playbook."
                    if variant_id == "no_partner_motion" and route_type == "partner_intro"
                    else "Route is not allowed by this playbook."
                ),
                route_score=None,
                requires_human_review=requires_review,
            )

        return RoutePolicyDecision(
            route_type=route_type,
            status="allowed_not_available",
            reason=self._unavailable_reason(account=account, route_type=route_type),
            route_score=None,
            requires_human_review=requires_review,
        )

    @staticmethod
    def _without_partner_motion(playbook: Playbook) -> Playbook:
        return Playbook(
            name=f"{playbook.name} / no partner motion",
            allowed_routes=tuple(route for route in playbook.allowed_routes if route != "partner_intro"),
            blocked_channels=playbook.blocked_channels,
            available_assets=tuple(asset for asset in playbook.available_assets if "partner_case" not in asset),
            required_review_for=playbook.required_review_for,
        )

    @staticmethod
    def _unavailable_reason(*, account: Account, route_type: str) -> str:
        if route_type == "partner_intro":
            return "No surfaced partner role is connected to this account."
        if route_type == "technical_benchmark":
            return "Needs both a technical stakeholder and a hiring signal."
        if route_type == "procurement_discovery":
            return "Needs a procurement signal before this route can be ranked."
        if route_type == "dark_stakeholder_discovery":
            if account.missing_roles:
                return "Missing roles exist, but stronger allowed routes outrank this discovery move."
            return "No missing roles are present in the current account artifact."
        return "Route conditions are not met."


def route_policy_decision_to_payload(decision: RoutePolicyDecision) -> dict[str, Any]:
    return {
        "route_type": decision.route_type,
        "status": decision.status,
        "reason": decision.reason,
        "route_score": decision.route_score,
        "requires_human_review": decision.requires_human_review,
    }


def playbook_variant_to_payload(variant: PlaybookVariantAnalysis) -> dict[str, Any]:
    return {
        "variant_id": variant.variant_id,
        "label": variant.label,
        "description": variant.description,
        "playbook": _playbook_to_payload(variant.playbook),
        "route_preview": _access_plan_to_payload(variant.route_preview),
        "route_decisions": [route_policy_decision_to_payload(item) for item in variant.route_decisions],
        "review_policy": {
            "required_review_for": list(variant.playbook.required_review_for),
            "mode": "review_first" if "all" in variant.playbook.required_review_for else "selective_review",
        },
        "assets": list(variant.playbook.available_assets),
        "blocked_channels": list(variant.playbook.blocked_channels),
    }


def playbook_analysis_to_payload(analysis: PlaybookAnalysis) -> dict[str, Any]:
    return {
        "contract_version": analysis.contract_version,
        "current": playbook_variant_to_payload(analysis.current),
        "variants": [playbook_variant_to_payload(item) for item in analysis.variants],
    }


def _playbook_to_payload(playbook: Playbook) -> dict[str, Any]:
    return {
        "name": playbook.name,
        "allowed_routes": list(playbook.allowed_routes),
        "blocked_channels": list(playbook.blocked_channels),
        "available_assets": list(playbook.available_assets),
        "required_review_for": list(playbook.required_review_for),
    }


def _access_plan_to_payload(plan: AccessPlan) -> dict[str, Any]:
    return {
        "account_id": plan.account_id,
        "account_name": plan.account_name,
        "unresolved_gaps": list(plan.unresolved_gaps),
        "routes": [
            {
                "route_type": route.route_type,
                "title": route.title,
                "score": route.score,
                "reason": route.reason,
                "risk": route.risk,
                "owner": route.owner,
                "evidence_refs": list(route.evidence_refs),
                "expected_state_change": route.expected_state_change,
                "requires_human_review": route.requires_human_review,
            }
            for route in plan.routes
        ],
    }
