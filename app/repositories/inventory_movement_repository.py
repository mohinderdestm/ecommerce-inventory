from datetime import datetime
from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId

from app.core.database import db


collection = db["inventory_movements"]


class InventoryMovementRepository:
    @staticmethod
    def _to_object_id(value: Optional[str]):
        if not value:
            return None
        try:
            return ObjectId(value)
        except (InvalidId, TypeError):
            return None

    @staticmethod
    async def create(data: dict):
        result = await collection.insert_one(data)
        return str(result.inserted_id)

    @staticmethod
    async def get_by_id(movement_id: str):
        object_id = InventoryMovementRepository._to_object_id(movement_id)
        if not object_id:
            return None
        return await collection.find_one({"_id": object_id})

    @staticmethod
    async def list_movements(
        product_id: Optional[str] = None,
        warehouse_id: Optional[str] = None,
        movement_type: Optional[str] = None,
        reference_type: Optional[str] = None,
        limit: int = 200,
    ):
        query = {}

        if product_id:
            object_id = InventoryMovementRepository._to_object_id(product_id)
            if not object_id:
                return []
            query["product_id"] = object_id

        if warehouse_id:
            object_id = InventoryMovementRepository._to_object_id(warehouse_id)
            if not object_id:
                return []
            query["warehouse_id"] = object_id

        if movement_type:
            query["movement_type"] = movement_type

        if reference_type:
            query["reference_type"] = reference_type

        cursor = (
            collection.find(query)
            .sort("created_at", -1)
            .limit(max(1, min(limit, 1000)))
        )
        return await cursor.to_list(length=None)

    @staticmethod
    async def get_product_ledger(product_id: str, warehouse_id: Optional[str] = None):
        product_object_id = InventoryMovementRepository._to_object_id(product_id)
        if not product_object_id:
            return []

        query = {"product_id": product_object_id}
        if warehouse_id:
            warehouse_object_id = InventoryMovementRepository._to_object_id(
                warehouse_id
            )
            if not warehouse_object_id:
                return []
            query["warehouse_id"] = warehouse_object_id

        cursor = collection.find(query).sort("created_at", -1)
        return await cursor.to_list(length=None)

    @staticmethod
    async def summarize_product_balance(product_id: str):
        product_object_id = InventoryMovementRepository._to_object_id(product_id)
        if not product_object_id:
            return {"total_in": 0, "total_out": 0, "net": 0}

        pipeline = [
            {"$match": {"product_id": product_object_id}},
            {
                "$group": {
                    "_id": None,
                    "total_in": {
                        "$sum": {"$cond": [{"$gt": ["$delta", 0]}, "$delta", 0]}
                    },
                    "total_out": {
                        "$sum": {
                            "$cond": [{"$lt": ["$delta", 0]}, {"$abs": "$delta"}, 0]
                        }
                    },
                    "net": {"$sum": "$delta"},
                }
            },
        ]
        result = await collection.aggregate(pipeline).to_list(length=1)
        if not result:
            return {"total_in": 0, "total_out": 0, "net": 0}
        return {
            "total_in": int(result[0].get("total_in") or 0),
            "total_out": int(result[0].get("total_out") or 0),
            "net": int(result[0].get("net") or 0),
        }

    @staticmethod
    async def cleanup_old_entries(older_than: datetime):
        return await collection.delete_many({"created_at": {"$lt": older_than}})
