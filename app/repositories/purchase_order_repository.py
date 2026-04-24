from datetime import datetime
from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId

from app.core.database import db


collection = db["purchase_orders"]


class PurchaseOrderRepository:
    @staticmethod
    def _to_object_id(value: Optional[str]):
        if not value:
            return None
        try:
            return ObjectId(value)
        except (InvalidId, TypeError):
            return None

    @staticmethod
    async def create_purchase_order(data: dict):
        result = await collection.insert_one(data)
        return str(result.inserted_id)

    @staticmethod
    async def get_purchase_order_by_id(purchase_order_id: str):
        object_id = PurchaseOrderRepository._to_object_id(purchase_order_id)
        if not object_id:
            return None
        return await collection.find_one({"_id": object_id})

    @staticmethod
    async def get_purchase_order_by_number(po_number: str):
        return await collection.find_one({"po_number": po_number})

    @staticmethod
    async def list_purchase_orders(
        status: Optional[str] = None,
        supplier_email: Optional[str] = None,
        limit: int = 200,
    ):
        query = {}
        if status:
            query["status"] = status
        if supplier_email:
            query["supplier_email"] = supplier_email

        cursor = (
            collection.find(query)
            .sort("created_at", -1)
            .limit(max(1, min(limit, 1000)))
        )
        return await cursor.to_list(length=None)

    @staticmethod
    async def update_fields(purchase_order_id: str, fields: dict):
        object_id = PurchaseOrderRepository._to_object_id(purchase_order_id)
        if not object_id:
            return None

        fields["updated_at"] = datetime.utcnow()
        return await collection.update_one({"_id": object_id}, {"$set": fields})

    @staticmethod
    async def replace_items(purchase_order_id: str, items: list[dict]):
        object_id = PurchaseOrderRepository._to_object_id(purchase_order_id)
        if not object_id:
            return None

        return await collection.update_one(
            {"_id": object_id},
            {"$set": {"items": items, "updated_at": datetime.utcnow()}},
        )
