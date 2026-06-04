from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from power_web_os.domain import AccessPlan, AccessRoute, Account, PowerWebRole


@dataclass(frozen=True, slots=True)
class PowerWebNode:
    node_id: str
    label: str
    node_type: str
    role: str
    state: str
    stance: str
    influence: float
    surfaced: bool
    route_member: bool
    x: float
    y: float
    relation: str | None = None


@dataclass(frozen=True, slots=True)
class PowerWebEdge:
    edge_id: str
    source: str
    target: str
    edge_type: str
    highlighted: bool
    label: str


@dataclass(frozen=True, slots=True)
class PowerWebSummary:
    visible_count: int
    missing_count: int
    total_count: int
    route_coverage: int
    primary_route_type: str | None
    primary_route_score: int | None


@dataclass(frozen=True, slots=True)
class PowerWebBoard:
    account_id: str
    account_name: str
    summary: PowerWebSummary
    nodes: tuple[PowerWebNode, ...]
    edges: tuple[PowerWebEdge, ...]
    route_path: tuple[str, ...]


class PowerWebBoardBuilder:
    """Builds a deterministic influence-map read model for the current demo perimeter."""

    def build(self, *, account: Account, access_plan: AccessPlan) -> PowerWebBoard:
        primary_route = access_plan.routes[0] if access_plan.routes else None
        account_node_id = f"account:{account.account_id}"
        base_nodes = [self._account_node(account, account_node_id)]
        role_nodes = [self._role_node(role, index, len(account.roles)) for index, role in enumerate(account.roles)]
        route_path = self._route_path(account, role_nodes, primary_route)
        missing_roles = tuple(dict.fromkeys((*account.missing_roles, *self._route_missing_roles(primary_route, route_path))))
        missing_nodes = [
            self._missing_node(role=role, index=index, total=max(1, len(missing_roles)), route_member=f"missing:{role}" in route_path)
            for index, role in enumerate(missing_roles)
        ]

        route_set = set(route_path)
        nodes = tuple(
            node if node.node_id not in route_set else self._mark_route_member(node)
            for node in (*base_nodes, *role_nodes, *missing_nodes)
        )
        edges = self._edges(account_node_id=account_node_id, nodes=nodes, route_path=route_path)
        summary = PowerWebSummary(
            visible_count=len(account.roles),
            missing_count=len(missing_roles),
            total_count=len(account.roles) + len(missing_roles),
            route_coverage=len([node_id for node_id in route_path if not node_id.startswith("account:")]),
            primary_route_type=primary_route.route_type if primary_route else None,
            primary_route_score=primary_route.score if primary_route else None,
        )
        return PowerWebBoard(
            account_id=account.account_id,
            account_name=account.name,
            summary=summary,
            nodes=nodes,
            edges=edges,
            route_path=route_path,
        )

    def _route_path(
        self,
        account: Account,
        role_nodes: list[PowerWebNode],
        route: AccessRoute | None,
    ) -> tuple[str, ...]:
        account_node_id = f"account:{account.account_id}"
        if route is None:
            return (account_node_id,)

        if route.route_type == "partner_intro":
            partner = next((node for node in role_nodes if node.relation == "partner"), None)
            return (partner.node_id, account_node_id) if partner else (account_node_id,)

        if route.route_type == "technical_benchmark":
            technical = next(
                (node for node in role_nodes if any(token in node.role.lower() for token in ("data", "it", "tech"))),
                None,
            )
            return (technical.node_id, account_node_id) if technical else (account_node_id,)

        if route.route_type == "procurement_discovery":
            procurement = next((node for node in role_nodes if "procurement" in node.role.lower()), None)
            return (procurement.node_id, account_node_id) if procurement else ("missing:procurement_role", account_node_id)

        if route.route_type == "dark_stakeholder_discovery" and account.missing_roles:
            return (f"missing:{account.missing_roles[0]}", account_node_id)

        return (account_node_id,)

    @staticmethod
    def _route_missing_roles(route: AccessRoute | None, route_path: tuple[str, ...]) -> tuple[str, ...]:
        if route and route.route_type == "procurement_discovery" and "missing:procurement_role" in route_path:
            return ("procurement_role",)
        return ()

    @staticmethod
    def _account_node(account: Account, node_id: str) -> PowerWebNode:
        return PowerWebNode(
            node_id=node_id,
            label=account.name,
            node_type="account",
            role="account",
            state="selected",
            stance="neutral",
            influence=account.icp_fit,
            surfaced=True,
            route_member=True,
            x=0.5,
            y=0.5,
        )

    def _role_node(self, role: PowerWebRole, index: int, total: int) -> PowerWebNode:
        x, y = self._position(index=index, total=max(1, total), radius=0.34)
        return PowerWebNode(
            node_id=f"role:{self._slug(role.person_name or role.role)}",
            label=role.person_name or role.role,
            node_type="partner" if role.relation == "partner" else "person",
            role=role.role,
            state=role.state,
            stance=self._stance(role),
            influence=role.influence,
            surfaced=True,
            route_member=False,
            x=x,
            y=y,
            relation=role.relation,
        )

    def _missing_node(self, *, role: str, index: int, total: int, route_member: bool) -> PowerWebNode:
        x, y = self._position(index=index, total=max(1, total), radius=0.42, offset=0.5)
        return PowerWebNode(
            node_id=f"missing:{role}",
            label=role,
            node_type="missing",
            role=role,
            state="missing",
            stance="unsurfaced",
            influence=0.0,
            surfaced=False,
            route_member=route_member,
            x=x,
            y=y,
        )

    @staticmethod
    def _edges(*, account_node_id: str, nodes: tuple[PowerWebNode, ...], route_path: tuple[str, ...]) -> tuple[PowerWebEdge, ...]:
        directed_route_pairs = set(zip(route_path, route_path[1:]))
        route_pairs = directed_route_pairs | {(target, source) for source, target in directed_route_pairs}
        edges = []
        for node in nodes:
            if node.node_id == account_node_id:
                continue
            edge_type = "missing_gap" if node.node_type == "missing" else "partner_to_account" if node.node_type == "partner" else "account_to_role"
            highlighted = (node.node_id, account_node_id) in route_pairs
            edges.append(
                PowerWebEdge(
                    edge_id=f"{node.node_id}->{account_node_id}",
                    source=node.node_id,
                    target=account_node_id,
                    edge_type=edge_type,
                    highlighted=highlighted,
                    label=edge_type,
                )
            )
        return tuple(edges)

    @staticmethod
    def _mark_route_member(node: PowerWebNode) -> PowerWebNode:
        return PowerWebNode(**{**node_to_payload(node), "route_member": True})

    @staticmethod
    def _stance(role: PowerWebRole) -> str:
        if role.relation == "partner":
            return "ally"
        if role.state == "blocker":
            return "blocker"
        if role.state == "hypothesis":
            return "neutral"
        return "ally"

    @staticmethod
    def _position(*, index: int, total: int, radius: float, offset: float = 0.0) -> tuple[float, float]:
        import math

        angle = offset + (math.tau * index / total)
        return (round(0.5 + math.cos(angle) * radius, 3), round(0.5 + math.sin(angle) * radius, 3))

    @staticmethod
    def _slug(value: str) -> str:
        return "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")


def node_to_payload(node: PowerWebNode) -> dict[str, Any]:
    return {
        "node_id": node.node_id,
        "label": node.label,
        "node_type": node.node_type,
        "role": node.role,
        "state": node.state,
        "stance": node.stance,
        "influence": node.influence,
        "surfaced": node.surfaced,
        "route_member": node.route_member,
        "x": node.x,
        "y": node.y,
        "relation": node.relation,
    }


def edge_to_payload(edge: PowerWebEdge) -> dict[str, Any]:
    return {
        "edge_id": edge.edge_id,
        "source": edge.source,
        "target": edge.target,
        "edge_type": edge.edge_type,
        "highlighted": edge.highlighted,
        "label": edge.label,
    }


def summary_to_payload(summary: PowerWebSummary) -> dict[str, Any]:
    return {
        "visible_count": summary.visible_count,
        "missing_count": summary.missing_count,
        "total_count": summary.total_count,
        "route_coverage": summary.route_coverage,
        "primary_route_type": summary.primary_route_type,
        "primary_route_score": summary.primary_route_score,
    }


def board_to_payload(board: PowerWebBoard) -> dict[str, Any]:
    return {
        "account_id": board.account_id,
        "account_name": board.account_name,
        "summary": summary_to_payload(board.summary),
        "nodes": [node_to_payload(node) for node in board.nodes],
        "edges": [edge_to_payload(edge) for edge in board.edges],
        "route_path": list(board.route_path),
    }
