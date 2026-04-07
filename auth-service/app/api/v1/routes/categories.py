from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from app.schemas.product import (
    CategoryCreateRequest,
    CategoryUpdateRequest,
    CategoryResponse,
    APIResponse,
)
from app.services.category_service import CategoryService
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository
from app.utils.dependencies import get_current_user, require_admin, get_db
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/categories", tags=["Categories"])


def get_category_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> CategoryService:
    return CategoryService(
        category_repo=CategoryRepository(db),
        product_repo=ProductRepository(db),
    )


@router.post(
    "/",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a category or subcategory [Admin only]",
)
async def create_category(
    payload: CategoryCreateRequest,
    service: CategoryService = Depends(get_category_service),
    current_user: dict = Depends(require_admin),
):
    return await service.create_category(payload, created_by=current_user["_id"])


@router.get(
    "/",
    response_model=list[CategoryResponse],
    summary="List categories",
    description="Returns all top-level categories by default. Pass `parent_id` to get subcategories.",
)
async def list_categories(
    parent_id: Optional[str] = Query(
        default=None,
        description="Filter subcategories by parent ID. Omit for top-level categories."
    ),
    only_active: bool = Query(default=True),
    service: CategoryService = Depends(get_category_service),
    _: dict = Depends(get_current_user),
):
    return await service.list_categories(parent_id=parent_id, only_active=only_active)


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Get category by ID",
)
async def get_category(
    category_id: str,
    service: CategoryService = Depends(get_category_service),
    _: dict = Depends(get_current_user),
):
    return await service.get_category(category_id)


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Update category [Admin only]",
)
async def update_category(
    category_id: str,
    payload: CategoryUpdateRequest,
    service: CategoryService = Depends(get_category_service),
    current_user: dict = Depends(require_admin),
):
    return await service.update_category(category_id, payload, updated_by=current_user["_id"])


@router.delete(
    "/{category_id}",
    response_model=APIResponse,
    summary="Delete category [Admin only]",
    description="Cannot delete if category has subcategories or linked products.",
)
async def delete_category(
    category_id: str,
    service: CategoryService = Depends(get_category_service),
    _: dict = Depends(require_admin),
):
    await service.delete_category(category_id)
    return {"success": True, "message": "Category deleted successfully."}