from app.core.database import db
from bson import ObjectId
from datetime import datetime

collection = db["warehouse_stock"]


class WarehouseStockRepository:

    @staticmethod
    async def create(data):
        return await collection.insert_one(data)

    @staticmethod
    async def find_one(warehouse_id, sku):
        return await collection.find_one(
            {"warehouse_id": ObjectId(warehouse_id), "variant_sku": sku}
        )

    @staticmethod
    async def find_by_warehouse(warehouse_id):
        cursor = collection.find({"warehouse_id": ObjectId(warehouse_id)})
        return await cursor.to_list(length=None)

    @staticmethod
    async def increase_stock(warehouse_id, sku, qty):
        return await collection.update_one(
            {"warehouse_id": ObjectId(warehouse_id), "variant_sku": sku},
            {"$inc": {"quantity": qty}, "$set": {"updated_at": datetime.utcnow()}},
        )

    @staticmethod
    async def decrease_stock(warehouse_id, sku, qty):
        return await collection.update_one(
            {"warehouse_id": ObjectId(warehouse_id), "variant_sku": sku},
            {"$inc": {"quantity": -qty}, "$set": {"updated_at": datetime.utcnow()}},
        )

    @staticmethod
    async def update_stock(warehouse_id, sku, qty):
        return await collection.update_one(
            {"warehouse_id": ObjectId(warehouse_id), "variant_sku": sku},
            {"$set": {"quantity": qty, "updated_at": datetime.utcnow()}},
        )
