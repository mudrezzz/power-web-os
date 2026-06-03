from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from power_web_os.domain import Account, Playbook
from power_web_os.planner import DeterministicAccessPlanner
from power_web_os.serialization import account_from_payload, access_plan_to_payload, playbook_from_payload
from power_web_os.workflow import AccessPlanningState, AccessPlanningWorkflow


def load_demo_account(path: Path) -> tuple[Account, Playbook]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return account_from_payload(payload["account"]), playbook_from_payload(payload["playbook"])


def build_demo_plan(path: Path) -> dict[str, Any]:
    account, playbook = load_demo_account(path)
    plan = DeterministicAccessPlanner().build_plan(account, playbook)
    return access_plan_to_payload(plan)


def build_access_plan_artifact(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    workflow = AccessPlanningWorkflow()
    state = AccessPlanningState(
        task_context={
            "task_id": "demo-access-plan",
            "correlation_id": "demo-slice-0.2",
            "requester": "demo",
            "source_path": str(path),
        },
        account_payload=payload["account"],
        playbook_payload=payload["playbook"],
    )
    result = workflow.invoke(state)
    if result.access_plan is None:
        raise RuntimeError("AccessPlanningWorkflow did not produce an access plan artifact")
    return result.access_plan


def generate_access_plan_artifact(
    *,
    input_path: Path,
    output_path: Path,
    frontend_output_path: Path | None = None,
) -> dict[str, Any]:
    artifact = build_access_plan_artifact(input_path)
    _write_json(output_path, artifact)
    if frontend_output_path is not None:
        _write_json(frontend_output_path, artifact)
    return artifact


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(prog="power-web-os-demo")
    parser.add_argument(
        "command",
        nargs="?",
        default="print-plan",
        choices=("print-plan", "generate-access-plan"),
    )
    parser.add_argument("--input", type=Path, default=root / "demo" / "sample_account.json")
    parser.add_argument("--output", type=Path, default=root / "demo" / "output" / "access_plan.json")
    parser.add_argument(
        "--frontend-output",
        type=Path,
        default=root / "frontend" / "public" / "demo" / "access_plan.json",
    )
    args = parser.parse_args()

    if args.command == "generate-access-plan":
        artifact = generate_access_plan_artifact(
            input_path=args.input,
            output_path=args.output,
            frontend_output_path=args.frontend_output,
        )
    else:
        artifact = build_demo_plan(args.input)
    print(json.dumps(artifact, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
