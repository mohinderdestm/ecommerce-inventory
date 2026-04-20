from app.core.database import db
from bson import ObjectId
from datetime import datetime

class OrderRepository:
    def __init__(self):
        self.collection = db["sales_orders"]

    async def create(self, data):
        result = await self.collection.insert_one(data)
        return str(result.inserted_id)

    async def get_all(self):
        return await self.collection.find().to_list(100)

    async def get_by_id(self, order_id):
        return await self.collection.find_one({"_id": ObjectId(order_id)})

    async def update(self, order_id, data):
        return await self.collection.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": data}
        )