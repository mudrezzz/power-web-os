"""Versioned product and sales-playbook configuration."""

from power_web_os.application.sales_playbook.contracts import (
    AccessPlaybookDefinition,
    AccessPlaybookVersion,
    AccountRoleTitleHypothesis,
    ProductDefinition,
    ProductDefinitionVersion,
    ProductLifecycle,
    ProductSummary,
    RolePriority,
    RoleScope,
    SalesPlaybookDefinitionVersion,
    SalesPlaybookDraft,
    SemanticBuyingRole,
    BuyingRolePolicyVersion,
    AccessRouteRule,
)
from power_web_os.application.sales_playbook.service import SalesPlaybookService

__all__ = [
    "AccessPlaybookDefinition",
    "AccessPlaybookVersion",
    "AccessRouteRule",
    "AccountRoleTitleHypothesis",
    "BuyingRolePolicyVersion",
    "ProductDefinition",
    "ProductDefinitionVersion",
    "ProductLifecycle",
    "ProductSummary",
    "RolePriority",
    "RoleScope",
    "SalesPlaybookDefinitionVersion",
    "SalesPlaybookDraft",
    "SalesPlaybookService",
    "SemanticBuyingRole",
]
