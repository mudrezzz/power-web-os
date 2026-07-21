"""Compatibility projection to the deterministic Access Planner contract."""

from power_web_os.application.sales_playbook.contracts import SalesPlaybookDefinitionVersion
from power_web_os.domain import Playbook


def legacy_playbook(version: SalesPlaybookDefinitionVersion) -> Playbook:
    access = version.access_playbook
    if access is None:
        return Playbook(name=version.product.name, allowed_routes=())
    return Playbook(
        name=version.product.name,
        allowed_routes=tuple(route.route_code for route in access.route_rules if route.enabled),
        blocked_channels=access.blocked_channels,
        available_assets=access.available_assets,
        required_review_for=access.required_review_for,
    )
