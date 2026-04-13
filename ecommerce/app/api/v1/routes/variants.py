from fastapi import APIRouter, Depends, status

from app.schemas.variant import (
    VariantBulkCreateRequest,
    VariantUpdateRequest,
    VariantResponse,
    APIResponse,
)
from app.services.variant_service import VariantService
from app.repositories.product_repository import ProductRepository
from app.utils.dependencies import get_current_user, require_roles, get_db
from app.models.user import UserRole
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/products/{product_id}/variants", tags=["Product Variants"])


def get_variant_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> VariantService:
    return VariantService(product_repo=ProductRepository(db))


@router.get(
    "/",
    response_model=list[VariantResponse],
    summary="Get all variants for a product",
)
async def get_variants(
    product_id: str,
    service: VariantService = Depends(get_variant_service),
    _: dict = Depends(get_current_user),
):
    return await service.get_variants(product_id)


@router.post(
    "/",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Add variants to a product [Admin / Supplier]",
    description=(
        "Add one or more variants to a product. Each variant can have its own "
        "color, attributes (RAM, ROM, Size etc.), price, stock, and images. "
    ),
)
async def add_variants(
    product_id: str,
    payload: VariantBulkCreateRequest,
    service: VariantService = Depends(get_variant_service),
    current_user: dict = Depends(require_roles(UserRole.ADMIN, UserRole.SUPPLIER)),
):
    return await service.add_variants(product_id, payload, created_by=current_user["_id"])


@router.put(
    "/{variant_id}",
    response_model=dict,
    summary="Update a specific variant [Admin / Supplier]",
)
async def update_variant(
    product_id: str,
    variant_id: str,
    payload: VariantUpdateRequest,
    service: VariantService = Depends(get_variant_service),
    current_user: dict = Depends(require_roles(UserRole.ADMIN, UserRole.SUPPLIER)),
):
    return await service.update_variant(
        product_id, variant_id, payload, updated_by=current_user["_id"]
    )


@router.delete(
    "/{variant_id}",
    response_model=APIResponse,
    summary="Delete a variant [Admin only]",
)
async def delete_variant(
    product_id: str,
    variant_id: str,
    service: VariantService = Depends(get_variant_service),
    _: dict = Depends(require_roles(UserRole.ADMIN)),
):
    await service.delete_variant(product_id, variant_id)
    return {"success": True, "message": "Variant deleted successfully."}