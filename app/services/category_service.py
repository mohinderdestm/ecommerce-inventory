from app.repositories.category_repo import CategoryRepository
from app.models.category_model import CategoryModel
from fastapi import HTTPException
from datetime import datetime

class CategoryService:

    @staticmethod
    async def create_category(data: dict, user_id: str):
        # Check if slug exists
        slug = data.get("slug") or CategoryModel.generate_slug(data["name"])
        if await CategoryRepository.check_slug_exists(slug):
            raise HTTPException(status_code=400, detail="Category slug already exists")

        # Validate parent_id if provided
        if data.get("parent_id"):
            parent = await CategoryRepository.get_by_id(data["parent_id"])
            if not parent:
                raise HTTPException(status_code=400, detail="Parent category not found")

        category = CategoryModel.create(data, user_id)
        category_id = await CategoryRepository.create(category)
        
        return {
            "message": "Category created successfully",
            "id": category_id
        }

    @staticmethod
    async def get_all_categories(include_inactive: bool = False):
        return await CategoryRepository.get_all(include_inactive)

    @staticmethod
    async def get_categories_with_subcategories():
        """Get parent categories with nested subcategories"""
        return await CategoryRepository.get_parent_categories()

    @staticmethod
    async def get_category(category_id: str):
        category = await CategoryRepository.get_by_id(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        # Get subcategories
        category["subcategories"] = await CategoryRepository.get_subcategories(category_id)
        return category

    @staticmethod
    async def get_subcategories(parent_id: str):
        return await CategoryRepository.get_subcategories(parent_id)

    @staticmethod
    async def update_category(category_id: str, data: dict, user_id: str):
        category = await CategoryRepository.get_by_id(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        # Check slug if being updated
        if data.get("slug"):
            if await CategoryRepository.check_slug_exists(data["slug"], category_id):
                raise HTTPException(status_code=400, detail="Slug already exists")

        update_data = {k: v for k, v in data.items() if v is not None}
        update_data["updated_by"] = user_id
        update_data["updated_at"] = datetime.utcnow()

        await CategoryRepository.update(category_id, update_data)
        return {"message": "Category updated successfully"}

    @staticmethod
    async def delete_category(category_id: str):
        category = await CategoryRepository.get_by_id(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        # Check if has subcategories
        subcategories = await CategoryRepository.get_subcategories(category_id)
        if subcategories:
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete category with subcategories"
            )

        await CategoryRepository.delete(category_id)
        return {"message": "Category deleted successfully"}