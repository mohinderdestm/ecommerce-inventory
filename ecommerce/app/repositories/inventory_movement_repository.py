from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from typing import List, Tuple, Optional


class InventoryMovementRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["inventory_logs"]

    async def create(self, document: dict) -> dict:
        result = await self.collection.insert_one(document)
        document["_id"] = str(result.inserted_id)
        return document

    async def list_movements(
        self,
        product_id: Optional[str] = None,
        warehouse_id: Optional[str] = None,
        movement_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[dict], int]:
        query = {}
        if product_id:
            query["product_id"] = product_id
        if warehouse_id:
            query["warehouse_id"] = warehouse_id
        if movement_type:
            query["movement_type"] = movement_type

        cursor = self.collection.find(query).sort("timestamp", -1).skip(skip).limit(limit)
        movements = await cursor.to_list(length=limit)
        for mov in movements:
            mov["_id"] = str(mov["_id"])
        
        total = await self.collection.count_documents(query)
        return movements, total

    async def get_all_for_product(self, product_id: str) -> List[dict]:
        cursor = self.collection.find({"product_id": product_id}).sort("timestamp", -1)
        movements = await cursor.to_list(length=None)
        for mov in movements:
            mov["_id"] = str(mov["_id"])
        return movements
