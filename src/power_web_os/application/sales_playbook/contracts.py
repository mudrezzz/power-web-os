"""Provider-neutral contracts for product and semantic buying-role policy."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SalesPlaybookContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class ProductLifecycle(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class RolePriority(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"


class RoleScope(StrEnum):
    HOLDING = "holding"
    ACCOUNT = "account"
    SITE = "site"
    EXTERNAL = "external"


class ProductDefinition(SalesPlaybookContract):
    product_code: str = Field(min_length=2, max_length=80, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    name: str = Field(min_length=1, max_length=160)
    short_description: str = Field(default="", max_length=500)
    customer_problem: str = Field(default="", max_length=1600)
    value_proposition: str = Field(default="", max_length=1600)
    use_contexts: tuple[str, ...] = ()


class SemanticBuyingRole(SalesPlaybookContract):
    role_code: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    display_name: str = Field(min_length=1, max_length=200)
    business_responsibility: str = Field(min_length=1, max_length=1200)
    decision_rights: tuple[str, ...] = ()
    required: bool = True
    priority: RolePriority
    scope: RoleScope = RoleScope.ACCOUNT
    reason: str = Field(default="", max_length=1200)
    expected_evidence: tuple[str, ...] = ()
    exclusions: tuple[str, ...] = ()

    @model_validator(mode="before")
    @classmethod
    def default_priority_from_requiredness(cls, value: Any) -> Any:
        if isinstance(value, dict) and not value.get("priority"):
            value = dict(value)
            value["priority"] = "high" if value.get("required", True) else "normal"
        return value


class AccessRouteRule(SalesPlaybookContract):
    route_code: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    name: str = Field(min_length=1, max_length=200)
    source_role_codes: tuple[str, ...] = Field(min_length=1)
    target_role_codes: tuple[str, ...] = Field(min_length=1)
    allowed_channels: tuple[str, ...] = ()
    required_assets: tuple[str, ...] = ()
    requires_human_review: bool = False
    reason: str = Field(min_length=1, max_length=1200)
    enabled: bool = True


class AccessPlaybookDefinition(SalesPlaybookContract):
    route_rules: tuple[AccessRouteRule, ...] = ()
    blocked_channels: tuple[str, ...] = ()
    available_assets: tuple[str, ...] = ()
    required_review_for: tuple[str, ...] = ()


class SalesPlaybookDraft(SalesPlaybookContract):
    product_id: str = Field(min_length=1)
    draft_revision: int = Field(ge=1)
    base_version_id: str | None = None
    product: ProductDefinition
    buying_roles: tuple[SemanticBuyingRole, ...] = ()
    access_playbook: AccessPlaybookDefinition = Field(default_factory=AccessPlaybookDefinition)
    updated_at: datetime
    updated_by: str = Field(min_length=1)


class ProductDefinitionVersion(SalesPlaybookContract):
    version_id: str
    product_id: str
    version_number: int = Field(ge=1)
    definition: ProductDefinition
    published_at: datetime
    published_by: str


class BuyingRolePolicyVersion(SalesPlaybookContract):
    version_id: str
    product_id: str
    version_number: int = Field(ge=1)
    roles: tuple[SemanticBuyingRole, ...]
    published_at: datetime
    published_by: str


class AccessPlaybookVersion(SalesPlaybookContract):
    version_id: str
    product_id: str
    version_number: int = Field(ge=1)
    definition: AccessPlaybookDefinition
    published_at: datetime
    published_by: str


class SalesPlaybookDefinitionVersion(SalesPlaybookContract):
    version_id: str
    product_id: str
    version_number: int = Field(ge=1)
    product_definition_version_id: str
    buying_role_policy_version_id: str
    access_playbook_version_id: str | None = None
    product: ProductDefinition
    buying_roles: tuple[SemanticBuyingRole, ...]
    access_playbook: AccessPlaybookDefinition | None = None
    published_at: datetime
    published_by: str
    is_active: bool = False


class ProductSummary(SalesPlaybookContract):
    product_id: str
    product_code: str
    name: str
    lifecycle: ProductLifecycle
    active_version_id: str | None = None
    active_version_number: int | None = None
    draft_revision: int | None = None
    updated_at: datetime


class AccountRoleTitleHypothesis(SalesPlaybookContract):
    hypothesis_id: str
    account_id: str
    semantic_role_code: str
    title_variants: tuple[str, ...] = Field(min_length=1)
    query_variants: tuple[str, ...] = ()
    expected_evidence: tuple[str, ...] = ()
    exclusion_terms: tuple[str, ...] = ()
    reason: str = Field(min_length=1)


class PublishValidationResult(SalesPlaybookContract):
    valid: bool
    errors: tuple[str, ...] = ()


def validate_publishable(draft: SalesPlaybookDraft) -> PublishValidationResult:
    errors: list[str] = []
    product = draft.product
    for field_name in ("short_description", "customer_problem", "value_proposition"):
        if not getattr(product, field_name).strip():
            errors.append(f"product.{field_name} is required")
    if not product.use_contexts:
        errors.append("product.use_contexts requires at least one value")
    if not draft.buying_roles:
        errors.append("buying_roles requires at least one role")
    if draft.buying_roles and not any(role.required for role in draft.buying_roles):
        errors.append("buying_roles requires at least one required role")

    role_codes = [role.role_code for role in draft.buying_roles]
    if len(role_codes) != len(set(role_codes)):
        errors.append("buying_roles contains duplicate role_code")
    serialized = ProductAndRolePolicy(product=product, buying_roles=draft.buying_roles).model_dump_json().lower()
    if "http://" in serialized or "https://" in serialized:
        errors.append("product configuration must not contain source URLs")
    return PublishValidationResult(valid=not errors, errors=tuple(errors))


class ProductAndRolePolicy(SalesPlaybookContract):
    """Canonical Power Web discovery configuration, excluding access strategy."""

    product: ProductDefinition
    buying_roles: tuple[SemanticBuyingRole, ...]
