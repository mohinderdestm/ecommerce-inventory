from app.core.database import db
from datetime import datetime
from bson import ObjectId


class OrderRepository:
    collection = db["orders"]

    @classmethod
    async def create_order(cls, order_data: dict):
        order_data["created_at"] = datetime.utcnow()
        result = await cls.collection.insert_one(order_data)
        order_data["id"] = str(result.inserted_id)
        return order_data

    @classmethod
    async def get_order_by_id(cls, order_id: str):
        try:
            order = await cls.collection.find_one({"_id": ObjectId(order_id)})
            if order:
                order["id"] = str(order["_id"])
            return order
        except Exception:
            return None

    @classmethod
    async def get_all_orders(cls):
        orders = []
        async for order in cls.collection.find():
            order["id"] = str(order["_id"])
            orders.append(order)
        return orders

    @classmethod
    async def get_orders_by_user(cls, user_id: str):
        orders = []
        async for order in cls.collection.find({"user_id": user_id}):
            order["id"] = str(order["_id"])
            orders.append(order)
        return orders

    @classmethod
    async def get_orders_by_supplier(cls, supplier_email: str):
        orders = []
        async for order in cls.collection.find(
            {"items.supplier_email": supplier_email}
        ):
            order["id"] = str(order["_id"])
            orders.append(order)
        return orders

    @classmethod
    async def update_order_status(cls, order_id: str, status: str):
        await cls.collection.update_one(
            {"_id": ObjectId(order_id)}, {"$set": {"status": status}}
        )
