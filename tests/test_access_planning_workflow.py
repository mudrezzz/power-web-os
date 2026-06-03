import json
from pathlib import Path

import pytest

from power_web_os.demo import generate_access_plan_artifact
from power_web_os.workflow import AccessPlanningState, AccessPlanningWorkflow, FRAMEWORK_AVAILABLE


def _sample_payload() -> dict:
    return json.loads(Path("demo/sample_account.json").read_text(encoding="utf-8"))


def test_access_planning_state_and_artifact_contract() -> None:
    payload = _sample_payload()
    state = AccessPlanningState(
        task_context={"task_id": "test-task", "correlation_id": "test-correlation"},
        account_payload=payload["account"],
        playbook_payload=payload["playbook"],
    )

    result = AccessPlanningWorkflow().invoke(state)

    assert result.access_plan is not None
    artifact = result.access_plan
    assert artifact["artifact_type"] == "access_plan"
    assert artifact["artifact_version"] == "0.2"
    assert artifact["account"]["account_id"] == "acct-vitamin-bank"
    assert artifact["playbook"]["name"] == "Enterprise IT Board MVP"
    assert artifact["access_plan"]["unresolved_gaps"] == ["economic_buyer", "security_gatekeeper"]
    assert artifact["access_plan"]["routes"][0]["route_type"] == "technical_benchmark"
    assert artifact["access_plan"]["routes"][0]["evidence_refs"] == ["careers:vitamin-bank:data-platform"]
    assert all(route["requires_human_review"] for route in artifact["access_plan"]["routes"])
    assert artifact["workflow_metadata"]["workflow_name"] == "AccessPlanningWorkflow"
    assert artifact["workflow_metadata"]["planner"] == "DeterministicAccessPlanner"


def test_generate_access_plan_artifact_writes_demo_outputs(tmp_path: Path) -> None:
    output_path = tmp_path / "demo" / "access_plan.json"
    frontend_output_path = tmp_path / "frontend" / "public" / "demo" / "access_plan.json"

    artifact = generate_access_plan_artifact(
        input_path=Path("demo/sample_account.json"),
        output_path=output_path,
        frontend_output_path=frontend_output_path,
    )

    assert output_path.exists()
    assert frontend_output_path.exists()
    assert json.loads(output_path.read_text(encoding="utf-8")) == artifact
    assert json.loads(frontend_output_path.read_text(encoding="utf-8")) == artifact


def test_langgraph_framework_metadata_when_optional_dependency_is_available() -> None:
    if not FRAMEWORK_AVAILABLE:
        pytest.skip("langgraph-dai framework package is not installed")

    payload = _sample_payload()
    result = AccessPlanningWorkflow().invoke(
        {
            "task_context": {"task_id": "framework-test"},
            "account_payload": payload["account"],
            "playbook_payload": payload["playbook"],
        }
    )

    assert result.access_plan is not None
    assert result.access_plan["workflow_metadata"]["framework_available"] is True
    assert result.access_plan["workflow_metadata"]["runtime"] == "langgraph_dai"
