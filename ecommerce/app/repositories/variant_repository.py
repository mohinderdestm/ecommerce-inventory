from typing import Optional
from bson import ObjectId
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


class VariantRepository:

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["variants"]

    def _serialize(self, doc: dict) -> dict:
        if not doc:
            return doc
        doc["_id"] = str(doc["_id"])
        return doc

    # Create 

    async def create_many(self, docs: list[dict]) -> list[dict]:
        
        result = await self.collection.insert_many(docs)
        inserted = await self.collection.find(
            {"_id": {"$in": result.inserted_ids}}
        ).to_list(length=None)
        return [self._serialize(doc) for doc in inserted]

    # Read 

    async def find_by_id(self, variant_id: str) -> Optional[dict]:
        
        try:
            doc = await self.collection.find_one({"_id": ObjectId(variant_id)})
            return self._serialize(doc) if doc else None
        except Exception:
            return None

    async def find_by_variant_id(self, variant_id: str) -> Optional[dict]:
        
        doc = await self.collection.find_one({"variant_id": variant_id})
        return self._serialize(doc) if doc else None

    async def find_by_product_id(
        self,
        product_id: str,
        only_active: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[dict], int]:
        
        query: dict = {"product_id": product_id}
        if only_active:
            query["is_active"] = True
        total = await self.collection.count_documents(query)
        cursor = self.collection.find(query).skip(skip).limit(limit).sort("created_at", 1)
        variants = [self._serialize(doc) async for doc in cursor]
        return variants, total

    async def sku_exists(self, sku: str, exclude_id: Optional[str] = None) -> bool:
        query: dict = {"sku": sku.upper().strip()}
        if exclude_id:
            try:
                query["_id"] = {"$ne": ObjectId(exclude_id)}
            except Exception:
                pass
        return await self.collection.count_documents(query) > 0

    async def variant_id_exists(self, variant_id: str) -> bool:
        return await self.collection.count_documents({"variant_id": variant_id}) > 0

    # Update 

    async def update(self, variant_id: str, update_data: dict) -> Optional[dict]:
        
        update_data["updated_at"] = datetime.now(timezone.utc)
        await self.collection.update_one(
            {"variant_id": variant_id},
            {"$set": update_data}
        )
        return await self.find_by_variant_id(variant_id)

    # Delete 

    async def delete(self, variant_id: str) -> bool:
        
        result = await self.collection.delete_one({"variant_id": variant_id})
        return result.deleted_count > 0

    async def delete_all_for_product(self, product_id: str) -> int:
        
        result = await self.collection.delete_many({"product_id": product_id})
        return result.deleted_count

    # Aggregation helpers 

    async def get_summary_for_products(self, product_ids: list[str]) -> dict:

        if not product_ids:
            return {}

        pipeline = [
            {"$match": {"product_id": {"$in": product_ids}, "is_active": True}},
            {"$group": {
                "_id": "$product_id",
                "count": {"$sum": 1},
                "min_price": {"$min": "$selling_price"},
                "max_price": {"$max": "$selling_price"},
                "colors": {"$push": "$color"},
                "total_stock": {"$sum": "$stock"},
            }},
        ]
        cursor = self.collection.aggregate(pipeline)
        result = {}
        async for doc in cursor:
            result[doc["_id"]] = {
                "count": doc["count"],
                "min_price": doc["min_price"],
                "max_price": doc["max_price"],
                "colors": [c for c in doc["colors"] if c],
                "total_stock": doc["total_stock"],
            }
        return result