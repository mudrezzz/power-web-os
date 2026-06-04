import json
from pathlib import Path

from power_web_os.board import PowerWebBoardBuilder
from power_web_os.demo import generate_access_plan_artifact, generate_account_radar_artifact
from power_web_os.domain import AccessPlan, AccessRoute, Account, PowerWebRole, Signal


def test_power_web_board_builds_surfaced_missing_and_route_nodes() -> None:
    account = Account(
        account_id="acct-sample",
        name="Sample Account",
        icp_fit=0.8,
        roles=(
            PowerWebRole("Head of Data", "Ada Lane", "identified", 0.8),
            PowerWebRole("Integrator", "Partner One", "hypothesis", 0.7, relation="partner"),
        ),
        missing_roles=("economic_buyer",),
    )
    route = AccessRoute(
        route_type="partner_intro",
        title="Request partner intro",
        score=82,
        reason="Partner One is connected.",
        risk="Partner risk.",
        owner="Partner Manager",
    )
    plan = AccessPlan(account_id=account.account_id, account_name=account.name, routes=(route,), unresolved_gaps=account.missing_roles)

    board = PowerWebBoardBuilder().build(account=account, access_plan=plan)

    assert board.summary.visible_count == 2
    assert board.summary.missing_count == 1
    assert board.summary.primary_route_type == "partner_intro"
    assert board.summary.primary_route_score == 82
    assert "account:acct-sample" in board.route_path
    assert any(node.node_type == "partner" and node.route_member for node in board.nodes)
    assert any(node.node_type == "missing" and node.role == "economic_buyer" for node in board.nodes)
    assert any(edge.highlighted and edge.edge_type == "partner_to_account" for edge in board.edges)


def test_power_web_board_adds_procurement_route_target_when_role_is_not_surfaced() -> None:
    account = Account(
        account_id="acct-procurement",
        name="Procurement Account",
        icp_fit=0.7,
        signals=(Signal("procurement", "Procurement signal.", 0.8),),
        roles=(),
        missing_roles=(),
    )
    route = AccessRoute(
        route_type="procurement_discovery",
        title="Map procurement path before outreach",
        score=70,
        reason="Procurement signal.",
        risk="Formal route risk.",
        owner="SDR",
    )
    plan = AccessPlan(account_id=account.account_id, account_name=account.name, routes=(route,))

    board = PowerWebBoardBuilder().build(account=account, access_plan=plan)

    assert "missing:procurement_role" in board.route_path
    assert any(node.node_id == "missing:procurement_role" and node.route_member for node in board.nodes)
    assert board.summary.missing_count == 1
    assert board.summary.total_count == 1
    assert board.summary.route_coverage == 1


def test_generated_access_plan_artifact_contains_power_web_board(tmp_path: Path) -> None:
    artifact = generate_access_plan_artifact(
        input_path=Path("demo/sample_account.json"),
        output_path=tmp_path / "demo" / "access_plan.json",
        frontend_output_path=tmp_path / "frontend" / "access_plan.json",
    )

    board = artifact["power_web_board"]

    assert board["summary"]["visible_count"] >= 1
    assert board["nodes"]
    assert board["edges"]
    assert board["route_path"]


def test_generated_account_radar_writes_matching_plan_boards(tmp_path: Path) -> None:
    frontend_access_plans_dir = tmp_path / "frontend" / "public" / "demo" / "access_plans"
    artifact = generate_account_radar_artifact(
        input_path=Path("demo/sample_portfolio.json"),
        output_path=tmp_path / "demo" / "account_radar.json",
        frontend_output_path=tmp_path / "frontend" / "public" / "demo" / "account_radar.json",
        frontend_access_plans_dir=frontend_access_plans_dir,
    )

    for item in artifact["accounts"]:
        plan_artifact = json.loads((frontend_access_plans_dir / f"{item['account_id']}.json").read_text(encoding="utf-8"))
        board = plan_artifact["power_web_board"]
        assert board["account_id"] == item["account_id"]
        assert board["summary"]["primary_route_type"] == item["best_route_type"]
        assert board["summary"]["primary_route_score"] == item["best_route_score"]
