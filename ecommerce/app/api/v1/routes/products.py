from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from app.schemas.product import (
    ProductCreateRequest,
    ProductUpdateRequest,
    ProductResponse,
    ProductListResponse,
    APIResponse,
)
from app.services.product_service import ProductService
from app.repositories.product_repository import ProductRepository
from app.repositories.category_repository import CategoryRepository
from app.utils.dependencies import get_current_user, require_admin, require_roles, get_db
from app.models.user import UserRole
from app.models.product import ProductStatus
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/products", tags=["Products"])


def get_product_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> ProductService:
    return ProductService(
        product_repo=ProductRepository(db),
        category_repo=CategoryRepository(db),
    )


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product [Admin / Supplier]",
)
async def create_product(
    payload: ProductCreateRequest,
    service: ProductService = Depends(get_product_service),
    current_user: dict = Depends(require_roles(UserRole.ADMIN, UserRole.SUPPLIER)),
):
    return await service.create_product(payload, created_by=current_user["_id"])


@router.get(
    "/",
    response_model=ProductListResponse,
    summary="Search and list products",
    description=(
        "Supports full-text search across name, SKU, brand, and description. "
        "Also filterable by category, supplier, status, and price range."
    ),
)
async def list_products(
    q: Optional[str] = Query(default=None, description="Search by name, SKU, brand, or description"),
    category_id: Optional[str] = Query(default=None),
    supplier_id: Optional[str] = Query(default=None),
    status: Optional[ProductStatus] = Query(default=None),
    min_price: Optional[float] = Query(default=None, ge=0),
    max_price: Optional[float] = Query(default=None, ge=0),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: ProductService = Depends(get_product_service),
    _: dict = Depends(get_current_user),
):
    return await service.search_products(
        query=q,
        category_id=category_id,
        supplier_id=supplier_id,
        status=status.value if status else None,
        min_price=min_price,
        max_price=max_price,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/sku/{sku}",
    response_model=ProductResponse,
    summary="Get product by SKU",
)
async def get_by_sku(
    sku: str,
    service: ProductService = Depends(get_product_service),
    _: dict = Depends(get_current_user),
):
    return await service.get_product_by_sku(sku)


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get product by ID",
)
async def get_product(
    product_id: str,
    service: ProductService = Depends(get_product_service),
    _: dict = Depends(get_current_user),
):
    return await service.get_product(product_id)


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update product [Admin / Supplier]",
)
async def update_product(
    product_id: str,
    payload: ProductUpdateRequest,
    service: ProductService = Depends(get_product_service),
    current_user: dict = Depends(require_roles(UserRole.ADMIN, UserRole.SUPPLIER)),
):
    return await service.update_product(product_id, payload, updated_by=current_user["_id"])


@router.delete(
    "/{product_id}",
    response_model=APIResponse,
    summary="Delete product [Admin only]",
)
async def delete_product(
    product_id: str,
    service: ProductService = Depends(get_product_service),
    _: dict = Depends(require_admin),
):
    await service.delete_product(product_id)
    return {"success": True, "message": "Product deleted successfully."}