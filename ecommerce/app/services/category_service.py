from fastapi import HTTPException
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository
from app.models.product import build_category_document
from app.schemas.product import CategoryCreateRequest, CategoryUpdateRequest
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class CategoryService:
    def __init__(self, category_repo: CategoryRepository, product_repo: ProductRepository):
        self.category_repo = category_repo
        self.product_repo = product_repo

    async def create_category(self, payload: CategoryCreateRequest, created_by: str) -> dict:
        if await self.category_repo.name_exists(payload.name):
            raise HTTPException(status_code=409, detail="A category with this name already exists.")

        if payload.parent_id:
            parent = await self.category_repo.find_by_id(payload.parent_id)
            if not parent:
                raise HTTPException(status_code=404, detail="Parent category not found.")
            if not parent["is_active"]:
                raise HTTPException(status_code=400, detail="Cannot create subcategory under an inactive category.")

        doc = build_category_document(
            name=payload.name,
            description=payload.description,
            parent_id=payload.parent_id,
            created_by=created_by,
        )
        created = await self.category_repo.create(doc)
        logger.info(f"Category created: {created['name']} by {created_by}")
        return created

    async def get_category(self, category_id: str) -> dict:
        category = await self.category_repo.find_by_id(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found.")
        return category

    async def list_categories(
        self,
        parent_id: Optional[str] = None,
        only_active: bool = True
    ) -> list[dict]:
        return await self.category_repo.list_categories(
            parent_id=parent_id,
            only_active=only_active
        )

    async def update_category(
        self,
        category_id: str,
        payload: CategoryUpdateRequest,
        updated_by: str,
    ) -> dict:
        category = await self.category_repo.find_by_id(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found.")

        update_data: dict = {"updated_by": updated_by}
        
        if payload.name is not None:
            if await self.category_repo.name_exists(payload.name, exclude_id=category_id):
                raise HTTPException(status_code=409, detail="A category with this name already exists.")
            update_data["name"] = payload.name.strip()
            update_data["slug"] = payload.name.strip().lower().replace(" ", "-")

        if payload.description is not None:
            update_data["description"] = payload.description

        if payload.is_active is not None:
            update_data["is_active"] = payload.is_active

        updated = await self.category_repo.update(category_id, update_data)
        logger.info(f"Category {category_id} updated by {updated_by}")
        return updated

    async def delete_category(self, category_id: str) -> None:
        category = await self.category_repo.find_by_id(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found.")
        # if subcategory - prevent delete
        if await self.category_repo.has_children(category_id):
            raise HTTPException(
                status_code=400,
                detail="Cannot delete category that has subcategories. Delete subcategories first."
            )
        # If product linked - prevent delete
        product_count = await self.product_repo.find_by_category(category_id)
        if product_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete category — {product_count} product(s) are linked to it."
            )
        
        deleted = await self.category_repo.delete(category_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Category not found.")
        logger.info(f"Category {category_id} deleted.")