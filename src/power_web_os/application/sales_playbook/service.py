"""Application use cases for product and sales-playbook configuration."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from power_web_os.application.sales_playbook.contracts import (
    AccessPlaybookDefinition,
    ProductDefinition,
    ProductLifecycle,
    ProductSummary,
    SalesPlaybookDefinitionVersion,
    SalesPlaybookDraft,
    validate_publishable,
)
from power_web_os.application.sales_playbook.ports import ProductNotFoundError, SalesPlaybookRepository


class SalesPlaybookValidationError(ValueError):
    def __init__(self, errors: tuple[str, ...]) -> None:
        super().__init__("; ".join(errors))
        self.errors = errors


class AccessPlaybookFrozenError(RuntimeError):
    """Raised when a caller tries to mutate deprecated access-strategy data."""


class SalesPlaybookService:
    def __init__(self, repository: SalesPlaybookRepository) -> None:
        self._repository = repository

    def create_product(self, *, product_code: str, name: str, requester: str) -> ProductSummary:
        now = datetime.now(UTC)
        product_id = f"product-{uuid4()}"
        draft = SalesPlaybookDraft(
            product_id=product_id,
            draft_revision=1,
            product=ProductDefinition(product_code=product_code, name=name),
            access_playbook=AccessPlaybookDefinition(),
            updated_at=now,
            updated_by=requester,
        )
        return self._repository.create_product(draft)

    def create_from_draft(self, draft: SalesPlaybookDraft) -> ProductSummary:
        """Create an explicitly identified product for deterministic seed/import workflows."""

        return self._repository.create_product(draft)

    def list_products(self) -> tuple[ProductSummary, ...]:
        return self._repository.list_products()

    def get_product(self, product_id: str) -> ProductSummary:
        product = self._repository.get_product(product_id)
        if product is None:
            raise ProductNotFoundError(product_id)
        return product

    def get_draft(self, product_id: str) -> SalesPlaybookDraft:
        self.get_product(product_id)
        draft = self._repository.get_draft(product_id)
        if draft is None:
            raise ProductNotFoundError(f"draft:{product_id}")
        return draft

    def save_draft(self, draft: SalesPlaybookDraft, *, expected_revision: int) -> SalesPlaybookDraft:
        self.get_product(draft.product_id)
        current = self.get_draft(draft.product_id)
        if draft.access_playbook != current.access_playbook:
            raise AccessPlaybookFrozenError("access_playbook_frozen")
        updated = draft.model_copy(
            update={"draft_revision": expected_revision + 1, "updated_at": datetime.now(UTC)}
        )
        return self._repository.save_draft(updated, expected_revision=expected_revision)

    def publish(self, product_id: str, *, published_by: str, activate: bool = True) -> SalesPlaybookDefinitionVersion:
        draft = self.get_draft(product_id)
        validation = validate_publishable(draft)
        if not validation.valid:
            raise SalesPlaybookValidationError(validation.errors)
        return self._repository.publish(draft, published_by=published_by, activate=activate)

    def list_versions(self, product_id: str) -> tuple[SalesPlaybookDefinitionVersion, ...]:
        self.get_product(product_id)
        return self._repository.list_versions(product_id)

    def get_version(self, product_id: str, version_id: str) -> SalesPlaybookDefinitionVersion:
        self.get_product(product_id)
        version = self._repository.get_version(product_id, version_id)
        if version is None:
            raise ProductNotFoundError(version_id)
        return version

    def activate(self, product_id: str, version_id: str) -> SalesPlaybookDefinitionVersion:
        self.get_version(product_id, version_id)
        return self._repository.activate(product_id, version_id)

    def restore_as_draft(self, product_id: str, version_id: str, *, requester: str) -> SalesPlaybookDraft:
        version = self.get_version(product_id, version_id)
        current = self.get_draft(product_id)
        draft = SalesPlaybookDraft(
            product_id=product_id,
            draft_revision=current.draft_revision + 1,
            base_version_id=version.version_id,
            product=version.product,
            buying_roles=version.buying_roles,
            access_playbook=current.access_playbook,
            updated_at=datetime.now(UTC),
            updated_by=requester,
        )
        return self._repository.replace_draft(draft)

    def archive(self, product_id: str) -> ProductSummary:
        self.get_product(product_id)
        return self._repository.set_lifecycle(product_id, ProductLifecycle.ARCHIVED)
