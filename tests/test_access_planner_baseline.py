from pathlib import Path

from power_web_os.demo import build_demo_plan


def test_demo_plan_ranks_explainable_routes() -> None:
    plan = build_demo_plan(Path("demo/sample_account.json"))

    assert plan["account_id"] == "acct-vitamin-bank"
    assert len(plan["routes"]) == 3
    assert plan["routes"][0]["score"] >= plan["routes"][1]["score"]
    assert plan["routes"][0]["evidence_refs"]
    assert all(route["requires_human_review"] for route in plan["routes"])


def test_demo_plan_keeps_missing_roles_as_unresolved_gaps() -> None:
    plan = build_demo_plan(Path("demo/sample_account.json"))

    assert plan["unresolved_gaps"] == ["economic_buyer", "security_gatekeeper"]
