"""SQLAlchemy adapter for versioned product and sales-playbook configuration."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from power_web_os.application.sales_playbook.contracts import (
    AccessPlaybookDefinition,
    AccessPlaybookVersion,
    BuyingRolePolicyVersion,
    ProductDefinition,
    ProductDefinitionVersion,
    ProductLifecycle,
    ProductSummary,
    SalesPlaybookDefinitionVersion,
    SalesPlaybookDraft,
    SemanticBuyingRole,
)
from power_web_os.application.sales_playbook.ports import DraftConflictError, ProductNotFoundError
from power_web_os.persistence.models import (
    AccessPlaybookVersionModel,
    BuyingRolePolicyVersionModel,
    ProductDefinitionVersionModel,
    ProductModel,
    SalesPlaybookDefinitionVersionModel,
    SalesPlaybookDraftModel,
    utc_now,
)


class SqlAlchemySalesPlaybookRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_product(self, draft: SalesPlaybookDraft) -> ProductSummary:
        now = utc_now()
        product = ProductModel(
            product_id=draft.product_id,
            product_code=draft.product.product_code,
            lifecycle=ProductLifecycle.DRAFT.value,
            created_at=now,
            updated_at=now,
        )
        self._session.add(product)
        self._session.add(self._draft_model(draft, created_at=now))
        self._session.flush()
        return self._summary(product)

    def list_products(self) -> tuple[ProductSummary, ...]:
        products = self._session.scalars(select(ProductModel).order_by(ProductModel.updated_at.desc())).all()
        return tuple(self._summary(product) for product in products)

    def get_product(self, product_id: str) -> ProductSummary | None:
        product = self._session.get(ProductModel, product_id)
        return self._summary(product) if product is not None else None

    def get_draft(self, product_id: str) -> SalesPlaybookDraft | None:
        model = self._session.get(SalesPlaybookDraftModel, product_id)
        return self._draft_record(model) if model is not None else None

    def save_draft(self, draft: SalesPlaybookDraft, *, expected_revision: int) -> SalesPlaybookDraft:
        model = self._session.get(SalesPlaybookDraftModel, draft.product_id)
        product = self._session.get(ProductModel, draft.product_id)
        if model is None or product is None:
            raise ProductNotFoundError(draft.product_id)
        if model.draft_revision != expected_revision:
            raise DraftConflictError(
                f"Draft revision {expected_revision} is stale; current revision is {model.draft_revision}."
            )
        if product.active_version_id is not None and product.product_code != draft.product.product_code:
            raise ValueError("product_code is immutable after first publication")
        product.product_code = draft.product.product_code
        product.updated_at = draft.updated_at
        self._assign_draft(model, draft)
        self._session.flush()
        return self._draft_record(model)

    def publish(
        self,
        draft: SalesPlaybookDraft,
        *,
        published_by: str,
        activate: bool,
    ) -> SalesPlaybookDefinitionVersion:
        product = self._session.get(ProductModel, draft.product_id)
        draft_model = self._session.get(SalesPlaybookDraftModel, draft.product_id)
        if product is None or draft_model is None:
            raise ProductNotFoundError(draft.product_id)
        number = int(
            self._session.scalar(
                select(func.max(SalesPlaybookDefinitionVersionModel.version_number)).where(
                    SalesPlaybookDefinitionVersionModel.product_id == draft.product_id
                )
            )
            or 0
        ) + 1
        now = datetime.now(UTC)
        suffix = str(uuid4())
        product_version_id = f"product-definition-{suffix}"
        role_version_id = f"buying-role-policy-{suffix}"
        version_id = f"sales-playbook-{suffix}"
        self._session.add(ProductDefinitionVersionModel(
            version_id=product_version_id,
            product_id=draft.product_id,
            version_number=number,
            payload_json=draft.product.model_dump(mode="json"),
            published_by=published_by,
            published_at=now,
        ))
        self._session.add(BuyingRolePolicyVersionModel(
            version_id=role_version_id,
            product_id=draft.product_id,
            version_number=number,
            payload_json=[role.model_dump(mode="json") for role in draft.buying_roles],
            published_by=published_by,
            published_at=now,
        ))
        version_model = SalesPlaybookDefinitionVersionModel(
            version_id=version_id,
            product_id=draft.product_id,
            version_number=number,
            product_definition_version_id=product_version_id,
            buying_role_policy_version_id=role_version_id,
            access_playbook_version_id=None,
            published_by=published_by,
            published_at=now,
        )
        self._session.add(version_model)
        if activate:
            product.active_version_id = version_id
            product.lifecycle = ProductLifecycle.ACTIVE.value
        product.updated_at = now
        clean_draft = draft.model_copy(update={
            "draft_revision": draft_model.draft_revision + 1,
            "base_version_id": version_id,
            "updated_at": now,
            "updated_by": published_by,
        })
        self._assign_draft(draft_model, clean_draft)
        self._session.flush()
        return self._version_record(version_model)

    def list_versions(self, product_id: str) -> tuple[SalesPlaybookDefinitionVersion, ...]:
        models = self._session.scalars(
            select(SalesPlaybookDefinitionVersionModel)
            .where(SalesPlaybookDefinitionVersionModel.product_id == product_id)
            .order_by(SalesPlaybookDefinitionVersionModel.version_number.desc())
        ).all()
        return tuple(self._version_record(model) for model in models)

    def get_version(self, product_id: str, version_id: str) -> SalesPlaybookDefinitionVersion | None:
        model = self._session.get(SalesPlaybookDefinitionVersionModel, version_id)
        if model is None or model.product_id != product_id:
            return None
        return self._version_record(model)

    def activate(self, product_id: str, version_id: str) -> SalesPlaybookDefinitionVersion:
        product = self._session.get(ProductModel, product_id)
        model = self._session.get(SalesPlaybookDefinitionVersionModel, version_id)
        if product is None or model is None or model.product_id != product_id:
            raise ProductNotFoundError(version_id)
        product.active_version_id = version_id
        product.lifecycle = ProductLifecycle.ACTIVE.value
        product.updated_at = utc_now()
        self._session.flush()
        return self._version_record(model)

    def replace_draft(self, draft: SalesPlaybookDraft) -> SalesPlaybookDraft:
        model = self._session.get(SalesPlaybookDraftModel, draft.product_id)
        if model is None:
            raise ProductNotFoundError(draft.product_id)
        self._assign_draft(model, draft)
        self._session.flush()
        return self._draft_record(model)

    def set_lifecycle(self, product_id: str, lifecycle: ProductLifecycle) -> ProductSummary:
        product = self._session.get(ProductModel, product_id)
        if product is None:
            raise ProductNotFoundError(product_id)
        product.lifecycle = lifecycle.value
        product.updated_at = utc_now()
        self._session.flush()
        return self._summary(product)

    def _summary(self, product: ProductModel) -> ProductSummary:
        draft = self._session.get(SalesPlaybookDraftModel, product.product_id)
        draft_record = self._draft_record(draft) if draft is not None else None
        active = (
            self._session.get(SalesPlaybookDefinitionVersionModel, product.active_version_id)
            if product.active_version_id
            else None
        )
        return ProductSummary(
            product_id=product.product_id,
            product_code=product.product_code,
            name=draft_record.product.name if draft_record else product.product_code,
            lifecycle=ProductLifecycle(product.lifecycle),
            active_version_id=product.active_version_id,
            active_version_number=active.version_number if active else None,
            draft_revision=draft.draft_revision if draft else None,
            updated_at=product.updated_at,
        )

    def _version_record(self, model: SalesPlaybookDefinitionVersionModel) -> SalesPlaybookDefinitionVersion:
        product_model = self._session.get(ProductModel, model.product_id)
        product_version = self._session.get(ProductDefinitionVersionModel, model.product_definition_version_id)
        role_version = self._session.get(BuyingRolePolicyVersionModel, model.buying_role_policy_version_id)
        access_version = (
            self._session.get(AccessPlaybookVersionModel, model.access_playbook_version_id)
            if model.access_playbook_version_id
            else None
        )
        if product_version is None or role_version is None:
            raise RuntimeError(f"Incomplete sales playbook version {model.version_id}")
        return SalesPlaybookDefinitionVersion(
            version_id=model.version_id,
            product_id=model.product_id,
            version_number=model.version_number,
            product_definition_version_id=model.product_definition_version_id,
            buying_role_policy_version_id=model.buying_role_policy_version_id,
            access_playbook_version_id=model.access_playbook_version_id,
            product=ProductDefinition.model_validate(product_version.payload_json),
            buying_roles=tuple(SemanticBuyingRole.model_validate(item) for item in role_version.payload_json),
            access_playbook=(
                AccessPlaybookDefinition.model_validate(access_version.payload_json)
                if access_version is not None
                else None
            ),
            published_at=model.published_at,
            published_by=model.published_by,
            is_active=bool(product_model and product_model.active_version_id == model.version_id),
        )

    @staticmethod
    def _draft_record(model: SalesPlaybookDraftModel) -> SalesPlaybookDraft:
        payload = dict(model.payload_json)
        payload.update({
            "draft_revision": model.draft_revision,
            "base_version_id": model.base_version_id,
            "updated_at": model.updated_at,
            "updated_by": model.updated_by,
        })
        return SalesPlaybookDraft.model_validate(payload)

    @staticmethod
    def _draft_model(draft: SalesPlaybookDraft, *, created_at: datetime) -> SalesPlaybookDraftModel:
        return SalesPlaybookDraftModel(
            product_id=draft.product_id,
            draft_revision=draft.draft_revision,
            base_version_id=draft.base_version_id,
            payload_json=draft.model_dump(mode="json", exclude={"draft_revision", "base_version_id", "updated_at", "updated_by"}),
            updated_by=draft.updated_by,
            created_at=created_at,
            updated_at=draft.updated_at,
        )

    @staticmethod
    def _assign_draft(model: SalesPlaybookDraftModel, draft: SalesPlaybookDraft) -> None:
        model.draft_revision = draft.draft_revision
        model.base_version_id = draft.base_version_id
        model.payload_json = draft.model_dump(
            mode="json", exclude={"draft_revision", "base_version_id", "updated_at", "updated_by"}
        )
        model.updated_by = draft.updated_by
        model.updated_at = draft.updated_at
