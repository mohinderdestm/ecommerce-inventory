from app.core.database import db
from bson import ObjectId

collection = db["warehouse_staff"]


class WarehouseStaffRepository:

    @staticmethod
    async def assign(data: dict):
        return await collection.insert_one(data)

    @staticmethod
    async def get_by_warehouse(warehouse_id: str):
        return await collection.find({"warehouse_id": warehouse_id}).to_list(
            length=None
        )

    @staticmethod
    async def get_one(warehouse_id: str, staff_id: str):
        return await collection.find_one(
            {"warehouse_id": warehouse_id, "staff_id": staff_id}
        )

    @staticmethod
    async def get_by_id(assignment_id: str):
        return await collection.find_one({"_id": ObjectId(assignment_id)})

    @staticmethod
    async def exists(warehouse_id: str, staff_id: str):
        return await collection.find_one(
            {"warehouse_id": warehouse_id, "staff_id": staff_id}
        )

    @staticmethod
    async def remove(warehouse_id: str, staff_id: str):
        return await collection.delete_one(
            {"warehouse_id": warehouse_id, "staff_id": staff_id}
        )

    @staticmethod
    async def get_all():
        return await collection.find().to_list(length=None)
