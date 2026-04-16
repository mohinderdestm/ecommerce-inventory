from app.core.database import db
from bson import ObjectId


class WarehouseRepository:

    collection = db["warehouses"]

    @staticmethod
    async def create(data: dict):
        result = await WarehouseRepository.collection.insert_one(data)
        return str(result.inserted_id)

    @staticmethod
    async def get_all():
        return await WarehouseRepository.collection.find().to_list(length=None)

    @staticmethod
    async def get_by_id(warehouse_id: str):
        return await WarehouseRepository.collection.find_one(
            {"_id": ObjectId(warehouse_id)}
        )

    @staticmethod
    async def update(warehouse_id: str, data: dict):
        return await WarehouseRepository.collection.update_one(
            {"_id": ObjectId(warehouse_id)}, {"$set": data}
        )

    @staticmethod
    async def delete(warehouse_id: str):
        return await WarehouseRepository.collection.delete_one(
            {"_id": ObjectId(warehouse_id)}
        )

    @staticmethod
    async def exists_by_code(code: str):
        return await WarehouseRepository.collection.find_one({"code": code})

    @staticmethod
    async def add_staff(warehouse_id: str, staff_id: str, staff_name: str):
        return await WarehouseRepository.collection.update_one(
            {"_id": ObjectId(warehouse_id)},
            {"$addToSet": {"staff_ids": staff_id, "staff_names": staff_name}},
        )

    @staticmethod
    async def remove_staff(warehouse_id: str, staff_id: str, staff_name: str):
        return await WarehouseRepository.collection.update_one(
            {"_id": ObjectId(warehouse_id)},
            {"$pull": {"staff_ids": staff_id, "staff_names": staff_name}},
        )
