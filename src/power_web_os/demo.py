from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from power_web_os.domain import Account, Evidence, Playbook, PowerWebRole, Signal
from power_web_os.planner import DeterministicAccessPlanner


def load_demo_account(path: Path) -> tuple[Account, Playbook]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    account_payload = payload["account"]
    playbook_payload = payload["playbook"]

    signals = tuple(
        Signal(
            kind=item["kind"],
            summary=item["summary"],
            strength=float(item["strength"]),
            evidence=tuple(
                Evidence(
                    source=evidence["source"],
                    url=evidence.get("url"),
                    summary=evidence["summary"],
                    confidence=float(evidence.get("confidence", 0.5)),
                )
                for evidence in item.get("evidence", [])
            ),
        )
        for item in account_payload.get("signals", [])
    )
    roles = tuple(
        PowerWebRole(
            role=item["role"],
            person_name=item.get("person_name"),
            state=item["state"],
            influence=float(item["influence"]),
            relation=item.get("relation"),
        )
        for item in account_payload.get("roles", [])
    )
    account = Account(
        account_id=account_payload["account_id"],
        name=account_payload["name"],
        icp_fit=float(account_payload["icp_fit"]),
        signals=signals,
        roles=roles,
        missing_roles=tuple(account_payload.get("missing_roles", [])),
    )
    playbook = Playbook(
        name=playbook_payload["name"],
        allowed_routes=tuple(playbook_payload["allowed_routes"]),
        blocked_channels=tuple(playbook_payload.get("blocked_channels", [])),
        available_assets=tuple(playbook_payload.get("available_assets", [])),
        required_review_for=tuple(playbook_payload.get("required_review_for", [])),
    )
    return account, playbook


def build_demo_plan(path: Path) -> dict[str, Any]:
    account, playbook = load_demo_account(path)
    plan = DeterministicAccessPlanner().build_plan(account, playbook)
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


def main() -> None:
    demo_path = Path(__file__).resolve().parents[2] / "demo" / "sample_account.json"
    print(json.dumps(build_demo_plan(demo_path), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
