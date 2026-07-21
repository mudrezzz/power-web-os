"""FastAPI transport for product and sales-playbook configuration."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from power_web_os.api.sales_playbook_dtos import (
    CreateProductRequest,
    PublishProductRequest,
    RestoreVersionRequest,
    UpdateDraftRequest,
)
from power_web_os.api.dependencies import get_sales_playbook_service
from power_web_os.application.sales_playbook.contracts import (
    ProductSummary,
    SalesPlaybookDefinitionVersion,
    SalesPlaybookDraft,
)
from power_web_os.application.sales_playbook.ports import DraftConflictError, ProductNotFoundError
from power_web_os.application.sales_playbook.service import (
    AccessPlaybookFrozenError,
    SalesPlaybookService,
    SalesPlaybookValidationError,
)

router = APIRouter(prefix="/api/products", tags=["sales-playbook"])


@router.get("", response_model=tuple[ProductSummary, ...])
def list_products(service: SalesPlaybookService = Depends(get_sales_playbook_service)) -> tuple[ProductSummary, ...]:
    return service.list_products()


@router.post("", response_model=ProductSummary, status_code=status.HTTP_201_CREATED)
def create_product(
    request: CreateProductRequest,
    service: SalesPlaybookService = Depends(get_sales_playbook_service),
) -> ProductSummary:
    try:
        return service.create_product(
            product_code=request.product_code,
            name=request.name,
            requester=request.requester,
        )
    except Exception as exc:
        if "unique" in str(exc).lower():
            raise HTTPException(status_code=409, detail="Product code already exists.") from exc
        raise


@router.get("/{product_id}", response_model=ProductSummary)
def get_product(product_id: str, service: SalesPlaybookService = Depends(get_sales_playbook_service)) -> ProductSummary:
    return _not_found(lambda: service.get_product(product_id))


@router.get("/{product_id}/draft", response_model=SalesPlaybookDraft)
def get_draft(product_id: str, service: SalesPlaybookService = Depends(get_sales_playbook_service)) -> SalesPlaybookDraft:
    return _not_found(lambda: service.get_draft(product_id))


@router.put("/{product_id}/draft", response_model=SalesPlaybookDraft)
def update_draft(
    product_id: str,
    request: UpdateDraftRequest,
    service: SalesPlaybookService = Depends(get_sales_playbook_service),
) -> SalesPlaybookDraft:
    current = _not_found(lambda: service.get_draft(product_id))
    draft = current.model_copy(update={
        "product": request.product,
        "buying_roles": request.buying_roles,
        "access_playbook": current.access_playbook if request.access_playbook is None else request.access_playbook,
        "updated_by": request.updated_by,
    })
    try:
        return service.save_draft(draft, expected_revision=request.expected_revision)
    except DraftConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except AccessPlaybookFrozenError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{product_id}/publish", response_model=SalesPlaybookDefinitionVersion)
def publish(
    product_id: str,
    request: PublishProductRequest,
    service: SalesPlaybookService = Depends(get_sales_playbook_service),
) -> SalesPlaybookDefinitionVersion:
    try:
        return service.publish(product_id, published_by=request.requester, activate=request.activate)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Product not found.") from exc
    except SalesPlaybookValidationError as exc:
        raise HTTPException(status_code=422, detail={"errors": exc.errors}) from exc


@router.get("/{product_id}/versions", response_model=tuple[SalesPlaybookDefinitionVersion, ...])
def list_versions(
    product_id: str,
    service: SalesPlaybookService = Depends(get_sales_playbook_service),
) -> tuple[SalesPlaybookDefinitionVersion, ...]:
    return _not_found(lambda: service.list_versions(product_id))


@router.get("/{product_id}/versions/{version_id}", response_model=SalesPlaybookDefinitionVersion)
def get_version(
    product_id: str,
    version_id: str,
    service: SalesPlaybookService = Depends(get_sales_playbook_service),
) -> SalesPlaybookDefinitionVersion:
    return _not_found(lambda: service.get_version(product_id, version_id))


@router.post("/{product_id}/versions/{version_id}/activate", response_model=SalesPlaybookDefinitionVersion)
def activate_version(
    product_id: str,
    version_id: str,
    service: SalesPlaybookService = Depends(get_sales_playbook_service),
) -> SalesPlaybookDefinitionVersion:
    return _not_found(lambda: service.activate(product_id, version_id))


@router.post("/{product_id}/versions/{version_id}/restore-as-draft", response_model=SalesPlaybookDraft)
def restore_version(
    product_id: str,
    version_id: str,
    request: RestoreVersionRequest,
    service: SalesPlaybookService = Depends(get_sales_playbook_service),
) -> SalesPlaybookDraft:
    return _not_found(lambda: service.restore_as_draft(product_id, version_id, requester=request.requester))


@router.post("/{product_id}/archive", response_model=ProductSummary)
def archive_product(product_id: str, service: SalesPlaybookService = Depends(get_sales_playbook_service)) -> ProductSummary:
    return _not_found(lambda: service.archive(product_id))


def _not_found(call):  # type: ignore[no-untyped-def]
    try:
        return call()
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Product or version not found.") from exc
