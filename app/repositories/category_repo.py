from app.core.database import db
from bson import ObjectId
from typing import Optional, List

class CategoryRepository:

    @staticmethod
    def serialize(category) -> dict:
        if category is None:
            return None
        return {
            "id": str(category["_id"]),
            "name": category.get("name", ""),
            "slug": category.get("slug", ""),
            "description": category.get("description", ""),
            "parent_id": str(category["parent_id"]) if category.get("parent_id") else None,
            "image_url": category.get("image_url", ""),
            "status": category.get("status", "active"),
            "created_by": str(category.get("created_by", "")),
            "updated_by": str(category.get("updated_by", "")),
            "created_at": category.get("created_at"),
            "updated_at": category.get("updated_at")
        }

    @staticmethod
    async def create(category: dict):
        result = await db["categories"].insert_one(category)
        return str(result.inserted_id)

    @staticmethod
    async def get_all(include_inactive: bool = False):
        categories = []
        query = {} if include_inactive else {"status": "active"}
        
        async for c in db["categories"].find(query):
            categories.append(CategoryRepository.serialize(c))
        
        return categories

    @staticmethod
    async def get_by_id(category_id: str):
        if not ObjectId.is_valid(category_id):
            return None
        
        category = await db["categories"].find_one({"_id": ObjectId(category_id)})
        return CategoryRepository.serialize(category)

    @staticmethod
    async def get_by_slug(slug: str):
        category = await db["categories"].find_one({"slug": slug})
        return CategoryRepository.serialize(category)

    @staticmethod
    async def get_subcategories(parent_id: str):
        subcategories = []
        query = {"parent_id": ObjectId(parent_id), "status": "active"}
        
        async for c in db["categories"].find(query):
            subcategories.append(CategoryRepository.serialize(c))
        
        return subcategories

    @staticmethod
    async def get_parent_categories():
        """Get only parent categories (no parent_id)"""
        categories = []
        query = {"parent_id": None, "status": "active"}
        
        async for c in db["categories"].find(query):
            cat = CategoryRepository.serialize(c)
            # Get subcategories
            cat["subcategories"] = await CategoryRepository.get_subcategories(cat["id"])
            categories.append(cat)
        
        return categories

    @staticmethod
    async def update(category_id: str, data: dict):
        if not ObjectId.is_valid(category_id):
            return False
        
        result = await db["categories"].update_one(
            {"_id": ObjectId(category_id)},
            {"$set": data}
        )
        return result.modified_count > 0

    @staticmethod
    async def delete(category_id: str):
        if not ObjectId.is_valid(category_id):
            return False
        
        result = await db["categories"].delete_one({"_id": ObjectId(category_id)})
        return result.deleted_count > 0

    @staticmethod
    async def check_slug_exists(slug: str, exclude_id: str = None) -> bool:
        query = {"slug": slug}
        if exclude_id:
            query["_id"] = {"$ne": ObjectId(exclude_id)}
        
        category = await db["categories"].find_one(query)
        return category is not None