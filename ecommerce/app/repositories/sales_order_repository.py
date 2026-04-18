from typing import Optional
from bson import ObjectId
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


class SalesOrderRepository:

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["sales_orders"]

    def _serialize(self, doc: dict) -> dict:
        if not doc:
            return doc
        doc["_id"] = str(doc["_id"])
        return doc

    # Create 

    async def create(self, doc: dict) -> dict:
        result = await self.collection.insert_one(doc)
        created = await self.collection.find_one({"_id": result.inserted_id})
        return self._serialize(created)

    # Read 

    async def find_by_id(self, order_id: str) -> Optional[dict]:
        try:
            doc = await self.collection.find_one({"_id": ObjectId(order_id)})
            return self._serialize(doc) if doc else None
        except Exception:
            return None

    async def find_by_order_number(self, order_number: str) -> Optional[dict]:
        doc = await self.collection.find_one({"order_number": order_number})
        return self._serialize(doc) if doc else None

    async def list_orders(
        self,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        warehouse_id: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[dict], int]:
        query: dict = {}
        if customer_id:
            query["customer_id"] = customer_id
        if status:
            query["status"] = status
        if warehouse_id:
            query["warehouse_id"] = warehouse_id
        if search:
            query["$or"] = [
                {"order_number": {"$regex": search, "$options": "i"}},
                {"customer_name": {"$regex": search, "$options": "i"}},
            ]

        total = await self.collection.count_documents(query)
        cursor = self.collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
        return [self._serialize(doc) async for doc in cursor], total

    # Update 

    async def update(self, order_id: str, update_data: dict) -> Optional[dict]:
        update_data["updated_at"] = datetime.now(timezone.utc)
        await self.collection.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": update_data}
        )
        return await self.find_by_id(order_id)

    async def push_status_history(self, order_id: str, entry: dict) -> None:
        
        await self.collection.update_one(
            {"_id": ObjectId(order_id)},
            {
                "$push": {"status_history": entry},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            }
        )

    # Analytics helpers 

    async def get_order_summary(self, customer_id: Optional[str] = None) -> dict:
        
        match = {"customer_id": customer_id} if customer_id else {}
        pipeline = [
            {"$match": match},
            {"$group": {"_id": "$status", "count": {"$sum": 1}, "total_value": {"$sum": "$grand_total"}}},
        ]
        cursor = self.collection.aggregate(pipeline)
        result = {}
        async for doc in cursor:
            result[doc["_id"]] = {"count": doc["count"], "total_value": round(doc["total_value"], 2)}
        return result