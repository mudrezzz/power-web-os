import json
from pathlib import Path

from power_web_os.demo import generate_access_plan_artifact, generate_account_radar_artifact
from power_web_os.domain import AccessPlan, AccessRoute, Account, Playbook, PowerWebRole
from power_web_os.playbook_analysis import PlaybookAnalysisBuilder


def test_playbook_analysis_explains_current_and_no_partner_variant() -> None:
    account = Account(
        account_id="acct-sample",
        name="Sample Account",
        icp_fit=0.8,
        roles=(PowerWebRole("Integrator", "Partner One", "identified", 0.8, relation="partner"),),
    )
    playbook = Playbook(
        name="Sample playbook",
        allowed_routes=("partner_intro", "technical_benchmark"),
        available_assets=("partner_case_platform", "data_benchmark_report"),
        required_review_for=("all",),
    )
    plan = AccessPlan(
        account_id=account.account_id,
        account_name=account.name,
        routes=(
            AccessRoute(
                route_type="partner_intro",
                title="Request partner intro",
                score=82,
                reason="Partner connected.",
                risk="Partner risk.",
                owner="Partner Manager",
            ),
        ),
    )

    analysis = PlaybookAnalysisBuilder().build(account=account, playbook=playbook, access_plan=plan)
    no_partner = analysis.variants[0]

    assert analysis.contract_version == "0.6"
    assert analysis.current.variant_id == "current"
    assert no_partner.variant_id == "no_partner_motion"
    assert "partner_intro" not in no_partner.playbook.allowed_routes
    assert not any(asset.startswith("partner_case") for asset in no_partner.playbook.available_assets)
    assert all(route.route_type != "partner_intro" for route in no_partner.route_preview.routes)
    assert _decision(no_partner.route_decisions, "partner_intro").status == "blocked"


def test_playbook_analysis_review_policy_is_review_first() -> None:
    account = Account(account_id="acct-review", name="Review Account", icp_fit=0.7)
    playbook = Playbook(name="Review playbook", allowed_routes=("procurement_discovery",), required_review_for=("all",))
    plan = AccessPlan(account_id=account.account_id, account_name=account.name)

    analysis = PlaybookAnalysisBuilder().build(account=account, playbook=playbook, access_plan=plan)

    assert analysis.current.playbook.required_review_for == ("all",)
    assert all(decision.requires_human_review for decision in analysis.current.route_decisions)


def test_generated_access_plan_artifact_contains_playbook_analysis(tmp_path: Path) -> None:
    artifact = generate_access_plan_artifact(
        input_path=Path("demo/sample_account.json"),
        output_path=tmp_path / "demo" / "access_plan.json",
        frontend_output_path=tmp_path / "frontend" / "access_plan.json",
    )

    analysis = artifact["playbook_analysis"]

    assert analysis["contract_version"] == "0.6"
    assert analysis["current"]["route_decisions"]
    assert analysis["variants"][0]["variant_id"] == "no_partner_motion"


def test_generated_account_radar_writes_playbook_analysis_for_every_plan(tmp_path: Path) -> None:
    frontend_access_plans_dir = tmp_path / "frontend" / "public" / "demo" / "access_plans"
    artifact = generate_account_radar_artifact(
        input_path=Path("demo/sample_portfolio.json"),
        output_path=tmp_path / "demo" / "account_radar.json",
        frontend_output_path=tmp_path / "frontend" / "public" / "demo" / "account_radar.json",
        frontend_access_plans_dir=frontend_access_plans_dir,
    )

    for item in artifact["accounts"]:
        plan_artifact = json.loads((frontend_access_plans_dir / f"{item['account_id']}.json").read_text(encoding="utf-8"))
        analysis = plan_artifact["playbook_analysis"]
        assert analysis["current"]["route_preview"]["account_id"] == item["account_id"]
        assert analysis["variants"][0]["variant_id"] == "no_partner_motion"


def _decision(decisions, route_type: str):
    return next(item for item in decisions if item.route_type == route_type)
