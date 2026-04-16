from app.core.database import db
from bson import ObjectId

collection = db["staff"]


class StaffRepository:

    @staticmethod
    async def create(data: dict):
        return await collection.insert_one(data)

    @staticmethod
    async def get_all():
        return await collection.find().to_list(length=None)

    @staticmethod
    async def get_by_id(staff_id: str):
        return await collection.find_one({"_id": ObjectId(staff_id)})

    @staticmethod
    async def update(staff_id: str, data: dict):
        return await collection.update_one({"_id": ObjectId(staff_id)}, {"$set": data})

    @staticmethod
    async def delete(staff_id: str):
        return await collection.delete_one({"_id": ObjectId(staff_id)})

    @staticmethod
    async def get_by_email(email: str):
        return await collection.find_one({"email": email})
