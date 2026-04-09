from typing import Optional
from fastapi import APIRouter, Depends, Query, status, Body

from app.schemas.supplier import (
    SupplierCreateRequest,
    SupplierUpdateRequest,
    SupplierResponse,
    SupplierListResponse,
    SupplierProductMapRequest,
    APIResponse,
)
from app.services.supplier_service import SupplierService
from app.repositories.supplier_repository import SupplierRepository
from app.repositories.product_repository import ProductRepository
from app.utils.dependencies import get_current_user, require_admin, require_roles, get_db
from app.models.user import UserRole
from app.models.supplier import SupplierStatus
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


def get_supplier_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> SupplierService:
    return SupplierService(
        supplier_repo=SupplierRepository(db),
        product_repo=ProductRepository(db),
    )


# CRUD 

@router.post(
    "/",
    response_model=SupplierResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new supplier [Admin only]",
)
async def create_supplier(
    payload: SupplierCreateRequest,
    service: SupplierService = Depends(get_supplier_service),
    current_user: dict = Depends(require_admin),
):
    return await service.create_supplier(payload, created_by=current_user["_id"])


@router.get(
    "/",
    response_model=SupplierListResponse,
    summary="List and search suppliers",
    description="Supports search by name, email, contact person, or GST. Filter by status.",
)
async def list_suppliers(
    search: Optional[str] = Query(default=None, description="Search by name, email, contact, GST"),
    status: Optional[SupplierStatus] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: SupplierService = Depends(get_supplier_service),
    _: dict = Depends(get_current_user),
):
    return await service.list_suppliers(
        status=status.value if status else None,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{supplier_id}",
    response_model=SupplierResponse,
    summary="Get supplier by ID",
)
async def get_supplier(
    supplier_id: str,
    service: SupplierService = Depends(get_supplier_service),
    _: dict = Depends(get_current_user),
):
    return await service.get_supplier(supplier_id)


@router.put(
    "/{supplier_id}",
    response_model=SupplierResponse,
    summary="Update supplier [Admin only]",
)
async def update_supplier(
    supplier_id: str,
    payload: SupplierUpdateRequest,
    service: SupplierService = Depends(get_supplier_service),
    current_user: dict = Depends(require_admin),
):
    return await service.update_supplier(supplier_id, payload, updated_by=current_user["_id"])


@router.delete(
    "/{supplier_id}",
    response_model=APIResponse,
    summary="Delete supplier [Admin only]",
    description="Blocked if supplier still has products linked to them.",
)
async def delete_supplier(
    supplier_id: str,
    service: SupplierService = Depends(get_supplier_service),
    _: dict = Depends(require_admin),
):
    await service.delete_supplier(supplier_id)
    return {"success": True, "message": "Supplier deleted successfully."}


# Rating 

@router.patch(
    "/{supplier_id}/rating",
    response_model=SupplierResponse,
    summary="Update supplier rating [Admin only]",
    description="Set supplier rating between 0.0 and 5.0.",
)
async def update_rating(
    supplier_id: str,
    rating: float = Body(..., ge=0, le=5, embed=True, examples=[4.5]),
    service: SupplierService = Depends(get_supplier_service),
    current_user: dict = Depends(require_admin),
):
    return await service.update_rating(supplier_id, rating, updated_by=current_user["_id"])


# Supplier-Product Mapping 

@router.post(
    "/{supplier_id}/products",
    response_model=SupplierResponse,
    summary="Link products to supplier [Admin only]",
    description="Links one or more products to this supplier. Also updates supplier_ids on each product.",
)
async def link_products(
    supplier_id: str,
    payload: SupplierProductMapRequest,
    service: SupplierService = Depends(get_supplier_service),
    current_user: dict = Depends(require_admin),
):
    return await service.link_products(supplier_id, payload, updated_by=current_user["_id"])


@router.delete(
    "/{supplier_id}/products",
    response_model=SupplierResponse,
    summary="Unlink products from supplier [Admin only]",
    description="Removes product links from supplier. Also cleans up supplier_ids on each product.",
)
async def unlink_products(
    supplier_id: str,
    payload: SupplierProductMapRequest,
    service: SupplierService = Depends(get_supplier_service),
    current_user: dict = Depends(require_admin),
):
    return await service.unlink_products(supplier_id, payload, updated_by=current_user["_id"])


@router.get(
    "/by-product/{product_id}",
    response_model=list[SupplierResponse],
    summary="Get all suppliers for a product",
    description="Returns every supplier linked to the given product ID.",
)
async def get_suppliers_for_product(
    product_id: str,
    service: SupplierService = Depends(get_supplier_service),
    _: dict = Depends(get_current_user),
):
    return await service.get_suppliers_for_product(product_id)