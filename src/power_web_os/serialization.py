from __future__ import annotations

from typing import Any

from power_web_os.board import PowerWebBoard, PowerWebBoardBuilder, board_to_payload
from power_web_os.domain import AccessPlan, AccessRoute, Account, Evidence, Playbook, PowerWebRole, Signal


def account_from_payload(payload: dict[str, Any]) -> Account:
    return Account(
        account_id=str(payload["account_id"]),
        name=str(payload["name"]),
        icp_fit=float(payload["icp_fit"]),
        signals=tuple(signal_from_payload(item) for item in payload.get("signals", [])),
        roles=tuple(role_from_payload(item) for item in payload.get("roles", [])),
        missing_roles=tuple(str(item) for item in payload.get("missing_roles", [])),
    )


def playbook_from_payload(payload: dict[str, Any]) -> Playbook:
    return Playbook(
        name=str(payload["name"]),
        allowed_routes=tuple(str(item) for item in payload["allowed_routes"]),
        blocked_channels=tuple(str(item) for item in payload.get("blocked_channels", [])),
        available_assets=tuple(str(item) for item in payload.get("available_assets", [])),
        required_review_for=tuple(str(item) for item in payload.get("required_review_for", [])),
    )


def signal_from_payload(payload: dict[str, Any]) -> Signal:
    return Signal(
        kind=str(payload["kind"]),
        summary=str(payload["summary"]),
        strength=float(payload["strength"]),
        evidence=tuple(evidence_from_payload(item) for item in payload.get("evidence", [])),
    )


def evidence_from_payload(payload: dict[str, Any]) -> Evidence:
    return Evidence(
        source=str(payload["source"]),
        url=str(payload["url"]) if payload.get("url") is not None else None,
        summary=str(payload["summary"]),
        confidence=float(payload.get("confidence", 0.5)),
    )


def role_from_payload(payload: dict[str, Any]) -> PowerWebRole:
    return PowerWebRole(
        role=str(payload["role"]),
        person_name=str(payload["person_name"]) if payload.get("person_name") is not None else None,
        state=str(payload["state"]),
        influence=float(payload["influence"]),
        relation=str(payload["relation"]) if payload.get("relation") is not None else None,
    )


def access_plan_from_payload(payload: dict[str, Any]) -> AccessPlan:
    return AccessPlan(
        account_id=str(payload["account_id"]),
        account_name=str(payload["account_name"]),
        routes=tuple(access_route_from_payload(item) for item in payload.get("routes", [])),
        unresolved_gaps=tuple(str(item) for item in payload.get("unresolved_gaps", [])),
    )


def access_route_from_payload(payload: dict[str, Any]) -> AccessRoute:
    return AccessRoute(
        route_type=str(payload["route_type"]),
        title=str(payload["title"]),
        score=int(payload["score"]),
        reason=str(payload["reason"]),
        risk=str(payload["risk"]),
        owner=str(payload["owner"]),
        evidence_refs=tuple(str(item) for item in payload.get("evidence_refs", [])),
        expected_state_change=(
            str(payload["expected_state_change"]) if payload.get("expected_state_change") is not None else None
        ),
        requires_human_review=bool(payload.get("requires_human_review", True)),
    )


def account_to_payload(account: Account) -> dict[str, Any]:
    return {
        "account_id": account.account_id,
        "name": account.name,
        "icp_fit": account.icp_fit,
        "signals": [signal_to_payload(item) for item in account.signals],
        "roles": [role_to_payload(item) for item in account.roles],
        "missing_roles": list(account.missing_roles),
    }


def playbook_to_payload(playbook: Playbook) -> dict[str, Any]:
    return {
        "name": playbook.name,
        "allowed_routes": list(playbook.allowed_routes),
        "blocked_channels": list(playbook.blocked_channels),
        "available_assets": list(playbook.available_assets),
        "required_review_for": list(playbook.required_review_for),
    }


def signal_to_payload(signal: Signal) -> dict[str, Any]:
    return {
        "kind": signal.kind,
        "summary": signal.summary,
        "strength": signal.strength,
        "evidence": [evidence_to_payload(item) for item in signal.evidence],
    }


def evidence_to_payload(evidence: Evidence) -> dict[str, Any]:
    return {
        "source": evidence.source,
        "url": evidence.url,
        "summary": evidence.summary,
        "confidence": evidence.confidence,
    }


def role_to_payload(role: PowerWebRole) -> dict[str, Any]:
    return {
        "role": role.role,
        "person_name": role.person_name,
        "state": role.state,
        "influence": role.influence,
        "relation": role.relation,
    }


def access_plan_to_payload(plan: AccessPlan) -> dict[str, Any]:
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


def build_access_plan_artifact(
    *,
    account: Account,
    playbook: Playbook,
    plan: AccessPlan,
    workflow_metadata: dict[str, Any],
    power_web_board: PowerWebBoard | None = None,
) -> dict[str, Any]:
    board = power_web_board or PowerWebBoardBuilder().build(account=account, access_plan=plan)
    return {
        "artifact_type": "access_plan",
        "artifact_version": "0.2",
        "account": account_to_payload(account),
        "playbook": playbook_to_payload(playbook),
        "access_plan": access_plan_to_payload(plan),
        "power_web_board": board_to_payload(board),
        "workflow_metadata": workflow_metadata,
    }
