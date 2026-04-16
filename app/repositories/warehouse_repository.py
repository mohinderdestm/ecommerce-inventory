from datetime import datetime
from bson import ObjectId

class WarehouseRepository:
    def __init__(self, db):
        self.collection = db["warehouses"]

    async def create(self, data):
        data["created_at"] = datetime.utcnow()
        data["updated_at"] = datetime.utcnow()
        data["status"] = "active"
        data["is_deleted"] = False

        result = await self.collection.insert_one(data)
        return str(result.inserted_id)

    async def get_all(self):
        return await self.collection.find({"is_deleted": False}).to_list(100)

    async def get_by_id(self, warehouse_id):
        return await self.collection.find_one({
            "_id": ObjectId(warehouse_id),
            "is_deleted": False
        })

    async def update(self, warehouse_id, data):
        data["updated_at"] = datetime.utcnow()
        return await self.collection.update_one(
            {"_id": ObjectId(warehouse_id)},
            {"$set": data}
        )

    async def delete(self, warehouse_id):
        return await self.collection.update_one(
            {"_id": ObjectId(warehouse_id)},
            {"$set": {"is_deleted": True}}
        )
        
    async def add_staff(self, warehouse_id, user_id):
        await self.collection.update_one(
        {"_id": ObjectId(warehouse_id)},
        {"$addToSet": {"staff_ids": user_id}}
    )