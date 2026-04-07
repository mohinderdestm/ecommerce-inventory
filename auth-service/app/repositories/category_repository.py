from typing import Optional
from bson import ObjectId
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


class CategoryRepository:

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["categories"]

    def _serialize(self, doc: dict) -> dict:
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
        if doc and "parent_id" in doc and isinstance(doc["parent_id"], ObjectId):
            doc["parent_id"] = str(doc["parent_id"])
        return doc

    async def create(self, category_doc: dict) -> dict:
        result = await self.collection.insert_one(category_doc)
        created = await self.collection.find_one({"_id": result.inserted_id})
        return self._serialize(created)

    async def find_by_id(self, category_id: str) -> Optional[dict]:
        try:
            doc = await self.collection.find_one({"_id": ObjectId(category_id)})
            return self._serialize(doc) if doc else None
        except Exception:
            return None

    async def find_by_name(self, name: str) -> Optional[dict]:
        doc = await self.collection.find_one({"name": {"$regex": f"^{name}$", "$options": "i"}})
        return self._serialize(doc) if doc else None

    async def name_exists(self, name: str, exclude_id: Optional[str] = None) -> bool:
        query: dict = {"name": {"$regex": f"^{name}$", "$options": "i"}}
        if exclude_id:
            query["_id"] = {"$ne": ObjectId(exclude_id)}
        return await self.collection.count_documents(query) > 0

    async def update(self, category_id: str, update_data: dict) -> Optional[dict]:
        update_data["updated_at"] = datetime.now(timezone.utc)
        try:
            await self.collection.update_one(
                {"_id": ObjectId(category_id)},
                {"$set": update_data}
            )
            return await self.find_by_id(category_id)
        except Exception as e:
            logger.error(f"Category update failed: {e}")
            return None

    async def delete(self, category_id: str) -> bool:
        try:
            result = await self.collection.delete_one({"_id": ObjectId(category_id)})
            return result.deleted_count > 0
        except Exception:
            return False

    async def list_categories(
        self,
        parent_id: Optional[str] = None,
        only_active: bool = True,
    ) -> list[dict]:
        query: dict = {}
        if only_active:
            query["is_active"] = True
        if parent_id is not None:
            query["parent_id"] = ObjectId(parent_id) if parent_id else None
        cursor = self.collection.find(query).sort("name", 1)
        return [self._serialize(doc) async for doc in cursor]

    async def has_children(self, category_id: str) -> bool:
        return await self.collection.count_documents({"parent_id": ObjectId(category_id)}) > 0