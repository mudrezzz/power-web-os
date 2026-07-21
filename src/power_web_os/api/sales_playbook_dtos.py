"""Transport DTOs for sales-playbook configuration."""

from pydantic import BaseModel, ConfigDict, Field

from power_web_os.application.sales_playbook.contracts import (
    AccessPlaybookDefinition,
    ProductDefinition,
    SemanticBuyingRole,
)


class SalesPlaybookRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CreateProductRequest(SalesPlaybookRequest):
    product_code: str = Field(min_length=2)
    name: str = Field(min_length=1)
    requester: str = Field(default="ui", min_length=1)


class UpdateDraftRequest(SalesPlaybookRequest):
    expected_revision: int = Field(ge=1)
    updated_by: str = Field(default="ui", min_length=1)
    product: ProductDefinition
    buying_roles: tuple[SemanticBuyingRole, ...]
    access_playbook: AccessPlaybookDefinition | None = None


class PublishProductRequest(SalesPlaybookRequest):
    requester: str = Field(default="ui", min_length=1)
    activate: bool = True


class RestoreVersionRequest(SalesPlaybookRequest):
    requester: str = Field(default="ui", min_length=1)
