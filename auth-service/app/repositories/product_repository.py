from typing import Optional
from bson import ObjectId
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


class ProductRepository:

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["products"]

    def _serialize(self, doc: dict) -> dict:
        if not doc:
            return doc
        doc["_id"] = str(doc["_id"])
        return doc

    async def create(self, product_doc: dict) -> dict:
        result = await self.collection.insert_one(product_doc)
        created = await self.collection.find_one({"_id": result.inserted_id})
        return self._serialize(created)

    async def find_by_id(self, product_id: str) -> Optional[dict]:
        try:
            doc = await self.collection.find_one({"_id": ObjectId(product_id)})
            return self._serialize(doc) if doc else None
        except Exception:
            return None

    async def find_by_sku(self, sku: str) -> Optional[dict]:
        doc = await self.collection.find_one({"sku": sku.upper().strip()})
        return self._serialize(doc) if doc else None

    async def sku_exists(self, sku: str, exclude_id: Optional[str] = None) -> bool:
        query: dict = {"sku": sku.upper().strip()}
        if exclude_id:
            query["_id"] = {"$ne": ObjectId(exclude_id)}
        return await self.collection.count_documents(query) > 0

    async def update(self, product_id: str, update_data: dict) -> Optional[dict]:
        update_data["updated_at"] = datetime.now(timezone.utc)
        try:
            await self.collection.update_one(
                {"_id": ObjectId(product_id)},
                {"$set": update_data}
            )
            return await self.find_by_id(product_id)
        except Exception as e:
            logger.error(f"Product update failed: {e}")
            return None

    async def delete(self, product_id: str) -> bool:
        try:
            result = await self.collection.delete_one({"_id": ObjectId(product_id)})
            return result.deleted_count > 0
        except Exception:
            return False

    async def search(
        self,
        query_str: Optional[str] = None,
        category_id: Optional[str] = None,
        supplier_id: Optional[str] = None,
        status: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[dict], int]:
        mongo_query: dict = {}

        # Text search across name, SKU, brand
        if query_str:
            mongo_query["$or"] = [
                {"name": {"$regex": query_str, "$options": "i"}},
                {"sku": {"$regex": query_str, "$options": "i"}},
                {"brand": {"$regex": query_str, "$options": "i"}},
                {"description": {"$regex": query_str, "$options": "i"}},
            ]

        if category_id:
            mongo_query["category_id"] = category_id

        if supplier_id:
            mongo_query["supplier_ids"] = supplier_id

        if status:
            mongo_query["status"] = status

        if min_price is not None or max_price is not None:
            price_filter: dict = {}
            if min_price is not None:
                price_filter["$gte"] = min_price
            if max_price is not None:
                price_filter["$lte"] = max_price
            mongo_query["selling_price"] = price_filter

        total = await self.collection.count_documents(mongo_query)
        cursor = self.collection.find(mongo_query).skip(skip).limit(limit).sort("created_at", -1)
        products = [self._serialize(doc) async for doc in cursor]
        return products, total

    async def find_by_category(self, category_id: str) -> int:
        return await self.collection.count_documents({"category_id": category_id})

    async def create_indexes(self):
        await self.collection.create_index("sku", unique=True)
        await self.collection.create_index("category_id")
        await self.collection.create_index("status")
        await self.collection.create_index("supplier_ids")
        await self.collection.create_index([("name", "text"), ("brand", "text")])