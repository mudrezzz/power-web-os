from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from power_web_os.domain import Account, Playbook
from power_web_os.icp_radar import icp_radar_artifact_to_payload
from power_web_os.icp_radar_xlsx import load_icp_radar_workbook
from power_web_os.planner import DeterministicAccessPlanner
from power_web_os.radar import AccountRadar
from power_web_os.serialization import (
    access_plan_from_payload,
    account_from_payload,
    access_plan_to_payload,
    playbook_from_payload,
)
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
    return build_access_plan_artifact_from_payload(
        account_payload=payload["account"],
        playbook_payload=payload["playbook"],
        task_context={
            "task_id": "demo-access-plan",
            "correlation_id": "demo-slice-0.2",
            "requester": "demo",
            "source_path": str(path),
        },
    )


def build_access_plan_artifact_from_payload(
    *,
    account_payload: dict[str, Any],
    playbook_payload: dict[str, Any],
    task_context: dict[str, Any],
) -> dict[str, Any]:
    workflow = AccessPlanningWorkflow()
    state = AccessPlanningState(
        task_context=task_context,
        account_payload=account_payload,
        playbook_payload=playbook_payload,
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


def generate_account_radar_artifact(
    *,
    input_path: Path,
    output_path: Path,
    frontend_output_path: Path,
    frontend_access_plans_dir: Path,
) -> dict[str, Any]:
    portfolio_payload = json.loads(input_path.read_text(encoding="utf-8"))
    radar = AccountRadar()
    radar_items = []
    access_plan_artifacts: dict[str, dict[str, Any]] = {}

    for entry in portfolio_payload["portfolio"]:
        account_payload = entry["account"]
        playbook_payload = entry["playbook"]
        account = account_from_payload(account_payload)
        access_plan_artifact = build_access_plan_artifact_from_payload(
            account_payload=account_payload,
            playbook_payload=playbook_payload,
            task_context={
                "task_id": f"demo-access-plan-{account.account_id}",
                "correlation_id": "demo-slice-0.4",
                "requester": "demo",
                "source_path": str(input_path),
            },
        )
        access_plan = access_plan_from_payload(access_plan_artifact["access_plan"])
        access_plan_path = f"/demo/access_plans/{account.account_id}.json"
        radar_items.append(
            radar.build_item(
                account=account,
                access_plan=access_plan,
                stage=str(entry.get("stage", "Mapping")),
                access_plan_path=access_plan_path,
            )
        )
        access_plan_artifacts[account.account_id] = access_plan_artifact

    ranked_items = radar.rank(radar_items)
    artifact = radar.to_payload(
        ranked_items,
        workflow_metadata={
            "workflow_name": "AccountRadar",
            "artifact_version": "0.4",
            "account_count": len(ranked_items),
            "access_workflow": "AccessPlanningWorkflow",
            "planner": "DeterministicAccessPlanner",
            "task_id": "demo-account-radar",
            "correlation_id": "demo-slice-0.4",
        },
    )

    _write_json(output_path, artifact)
    _write_json(frontend_output_path, artifact)
    for account_id, access_plan_artifact in access_plan_artifacts.items():
        _write_json(frontend_access_plans_dir / f"{account_id}.json", access_plan_artifact)
    return artifact


def generate_icp_radar_artifact(
    *,
    input_path: Path,
    output_path: Path,
    frontend_output_path: Path,
    normalized_output_path: Path,
) -> dict[str, Any]:
    artifact = icp_radar_artifact_to_payload(load_icp_radar_workbook(input_path))
    _write_json(output_path, artifact)
    _write_json(frontend_output_path, artifact)
    _write_json(normalized_output_path, artifact)
    return artifact


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(prog="power-web-os-demo")
    parser.add_argument(
        "command",
        nargs="?",
        default="print-plan",
        choices=("print-plan", "generate-access-plan", "generate-account-radar", "generate-icp-radar"),
    )
    parser.add_argument("--input", type=Path, default=root / "demo" / "sample_account.json")
    parser.add_argument("--output", type=Path, default=root / "demo" / "output" / "access_plan.json")
    parser.add_argument(
        "--frontend-output",
        type=Path,
        default=root / "frontend" / "public" / "demo" / "access_plan.json",
    )
    parser.add_argument("--portfolio-input", type=Path, default=root / "demo" / "sample_portfolio.json")
    parser.add_argument("--radar-output", type=Path, default=root / "demo" / "output" / "account_radar.json")
    parser.add_argument(
        "--frontend-radar-output",
        type=Path,
        default=root / "frontend" / "public" / "demo" / "account_radar.json",
    )
    parser.add_argument(
        "--frontend-access-plans-dir",
        type=Path,
        default=root / "frontend" / "public" / "demo" / "access_plans",
    )
    parser.add_argument(
        "--icp-radar-input",
        type=Path,
        default=root / "demo" / "fixtures" / "icp_radar" / "sibur_icp_pass1.xlsx",
    )
    parser.add_argument(
        "--icp-radar-output",
        type=Path,
        default=root / "demo" / "output" / "icp_radar.json",
    )
    parser.add_argument(
        "--frontend-icp-radar-output",
        type=Path,
        default=root / "frontend" / "public" / "demo" / "icp_radar.json",
    )
    parser.add_argument(
        "--normalized-icp-radar-output",
        type=Path,
        default=root / "demo" / "fixtures" / "icp_radar" / "toir_sibur_icp_radar.json",
    )
    args = parser.parse_args()

    if args.command == "generate-access-plan":
        artifact = generate_access_plan_artifact(
            input_path=args.input,
            output_path=args.output,
            frontend_output_path=args.frontend_output,
        )
    elif args.command == "generate-account-radar":
        artifact = generate_account_radar_artifact(
            input_path=args.portfolio_input,
            output_path=args.radar_output,
            frontend_output_path=args.frontend_radar_output,
            frontend_access_plans_dir=args.frontend_access_plans_dir,
        )
    elif args.command == "generate-icp-radar":
        artifact = generate_icp_radar_artifact(
            input_path=args.icp_radar_input,
            output_path=args.icp_radar_output,
            frontend_output_path=args.frontend_icp_radar_output,
            normalized_output_path=args.normalized_icp_radar_output,
        )
    else:
        artifact = build_demo_plan(args.input)
    print(json.dumps(artifact, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
