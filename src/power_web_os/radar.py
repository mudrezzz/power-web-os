from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from power_web_os.domain import AccessPlan, Account


@dataclass(frozen=True, slots=True)
class AccountRadarItem:
    account_id: str
    account_name: str
    stage: str
    radar_score: int
    signal_count: int
    missing_role_count: int
    top_reason: str
    best_route_type: str | None
    best_route_title: str | None
    best_route_score: int
    owner: str | None
    review_required: bool
    access_plan_path: str


class AccountRadar:
    def build_item(
        self,
        *,
        account: Account,
        access_plan: AccessPlan,
        stage: str,
        access_plan_path: str,
    ) -> AccountRadarItem:
        best_route = access_plan.routes[0] if access_plan.routes else None
        strongest_signal = max((signal.strength for signal in account.signals), default=0.0)
        missing_penalty = min(0.2, len(account.missing_roles) * 0.05)
        route_score = (best_route.score / 100) if best_route is not None else 0.0
        score = round(
            max(
                0.0,
                (
                    account.icp_fit * 0.35
                    + strongest_signal * 0.25
                    + route_score * 0.30
                    + self._coverage(account) * 0.10
                    - missing_penalty
                ),
            )
            * 100
        )

        return AccountRadarItem(
            account_id=account.account_id,
            account_name=account.name,
            stage=stage,
            radar_score=score,
            signal_count=len(account.signals),
            missing_role_count=len(account.missing_roles),
            top_reason=self._top_reason(account),
            best_route_type=best_route.route_type if best_route is not None else None,
            best_route_title=best_route.title if best_route is not None else None,
            best_route_score=best_route.score if best_route is not None else 0,
            owner=best_route.owner if best_route is not None else None,
            review_required=best_route.requires_human_review if best_route is not None else False,
            access_plan_path=access_plan_path,
        )

    def rank(self, items: list[AccountRadarItem]) -> list[AccountRadarItem]:
        return sorted(
            items,
            key=lambda item: (-item.radar_score, -item.best_route_score, item.account_name),
        )

    @staticmethod
    def to_payload(items: list[AccountRadarItem], *, workflow_metadata: dict[str, Any]) -> dict[str, Any]:
        return {
            "artifact_type": "account_radar",
            "artifact_version": "0.4",
            "accounts": [
                {
                    "account_id": item.account_id,
                    "account_name": item.account_name,
                    "stage": item.stage,
                    "radar_score": item.radar_score,
                    "signal_count": item.signal_count,
                    "missing_role_count": item.missing_role_count,
                    "top_reason": item.top_reason,
                    "best_route_type": item.best_route_type,
                    "best_route_title": item.best_route_title,
                    "best_route_score": item.best_route_score,
                    "owner": item.owner,
                    "review_required": item.review_required,
                    "access_plan_path": item.access_plan_path,
                }
                for item in items
            ],
            "workflow_metadata": workflow_metadata,
        }

    @staticmethod
    def _coverage(account: Account) -> float:
        total = len(account.roles) + len(account.missing_roles)
        return len(account.roles) / total if total else 0.0

    @staticmethod
    def _top_reason(account: Account) -> str:
        if not account.signals:
            return "No strong signal is present yet."
        signal = max(account.signals, key=lambda item: item.strength)
        return signal.summary
