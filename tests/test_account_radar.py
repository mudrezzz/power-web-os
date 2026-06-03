import json
from pathlib import Path

from power_web_os.demo import generate_account_radar_artifact
from power_web_os.domain import AccessPlan, AccessRoute, Account, Evidence, PowerWebRole, Signal
from power_web_os.radar import AccountRadar, AccountRadarItem


def test_account_radar_orders_sample_portfolio(tmp_path: Path) -> None:
    artifact = generate_account_radar_artifact(
        input_path=Path("demo/sample_portfolio.json"),
        output_path=tmp_path / "demo" / "account_radar.json",
        frontend_output_path=tmp_path / "frontend" / "public" / "demo" / "account_radar.json",
        frontend_access_plans_dir=tmp_path / "frontend" / "public" / "demo" / "access_plans",
    )

    account_ids = [item["account_id"] for item in artifact["accounts"]]

    assert len(account_ids) == 6
    assert account_ids[0] == "acct-northwind-robotics"
    assert account_ids[-1] == "acct-caldera-energy"
    assert artifact["accounts"][0]["radar_score"] >= artifact["accounts"][1]["radar_score"]


def test_account_radar_missing_role_penalty_and_best_route_extraction() -> None:
    route = AccessRoute(
        route_type="technical_benchmark",
        title="Invite technical stakeholder to a benchmark",
        score=80,
        reason="Strong technical signal.",
        risk="Economic buyer not confirmed.",
        owner="Account Executive",
        evidence_refs=("careers:sample:data-platform",),
    )
    plan = AccessPlan(account_id="acct-sample", account_name="Sample", routes=(route,))
    signal = Signal(
        kind="hiring",
        summary="Hiring signal is active.",
        strength=0.8,
        evidence=(Evidence("careers:sample:data-platform", None, "Hiring evidence.", 0.8),),
    )
    role = PowerWebRole("Head of Data", "Ada Lane", "identified", 0.8)
    complete = Account("acct-complete", "Complete", 0.8, (signal,), (role,), ())
    incomplete = Account("acct-incomplete", "Incomplete", 0.8, (signal,), (role,), ("economic_buyer",))
    radar = AccountRadar()

    complete_item = radar.build_item(
        account=complete,
        access_plan=plan,
        stage="Mapping",
        access_plan_path="/demo/access_plans/acct-complete.json",
    )
    incomplete_item = radar.build_item(
        account=incomplete,
        access_plan=plan,
        stage="Mapping",
        access_plan_path="/demo/access_plans/acct-incomplete.json",
    )

    assert complete_item.radar_score > incomplete_item.radar_score
    assert complete_item.best_route_type == "technical_benchmark"
    assert complete_item.best_route_score == 80
    assert complete_item.owner == "Account Executive"


def test_account_radar_tie_breaks_by_route_score_then_name() -> None:
    items = [
        _radar_item("acct-c", "Gamma", radar_score=70, route_score=80),
        _radar_item("acct-a", "Alpha", radar_score=70, route_score=80),
        _radar_item("acct-b", "Beta", radar_score=70, route_score=90),
    ]

    ranked = AccountRadar().rank(items)

    assert [item.account_name for item in ranked] == ["Beta", "Alpha", "Gamma"]


def test_generate_account_radar_artifact_writes_portfolio_and_matching_plans(tmp_path: Path) -> None:
    output_path = tmp_path / "demo" / "account_radar.json"
    frontend_output_path = tmp_path / "frontend" / "public" / "demo" / "account_radar.json"
    frontend_access_plans_dir = tmp_path / "frontend" / "public" / "demo" / "access_plans"

    artifact = generate_account_radar_artifact(
        input_path=Path("demo/sample_portfolio.json"),
        output_path=output_path,
        frontend_output_path=frontend_output_path,
        frontend_access_plans_dir=frontend_access_plans_dir,
    )

    assert output_path.exists()
    assert frontend_output_path.exists()
    assert json.loads(output_path.read_text(encoding="utf-8")) == artifact
    for item in artifact["accounts"]:
        plan_path = frontend_access_plans_dir / f"{item['account_id']}.json"
        assert plan_path.exists()
        plan_artifact = json.loads(plan_path.read_text(encoding="utf-8"))
        assert plan_artifact["account"]["account_id"] == item["account_id"]
        assert plan_artifact["artifact_type"] == "access_plan"


def _radar_item(account_id: str, account_name: str, *, radar_score: int, route_score: int) -> AccountRadarItem:
    return AccountRadarItem(
        account_id=account_id,
        account_name=account_name,
        stage="Mapping",
        radar_score=radar_score,
        signal_count=1,
        missing_role_count=0,
        top_reason="Reason.",
        best_route_type="technical_benchmark",
        best_route_title="Benchmark",
        best_route_score=route_score,
        owner="Account Executive",
        review_required=True,
        access_plan_path=f"/demo/access_plans/{account_id}.json",
    )
