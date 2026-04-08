from app.core.database import db

collection = db["suppliers"]


class SupplierRepository:

    async def create(self, data: dict):
        result = await collection.insert_one(data)
        return str(result.inserted_id)

    async def get_all(self):
        suppliers = []
        async for supplier in collection.find():
            supplier["id"] = str(supplier["_id"])
            del supplier["_id"]
            suppliers.append(supplier)
        return suppliers

    async def get_by_id(self, supplier_id: str):
        from bson import ObjectId

        supplier = await collection.find_one({"_id": ObjectId(supplier_id)})
        if supplier:
            supplier["id"] = str(supplier["_id"])
            del supplier["_id"]
        return supplier

    async def update(self, supplier_id: str, data: dict):
        from bson import ObjectId

        await collection.update_one({"_id": ObjectId(supplier_id)}, {"$set": data})
        return await self.get_by_id(supplier_id)

    async def delete(self, supplier_id: str):
        from bson import ObjectId

        return await collection.delete_one({"_id": ObjectId(supplier_id)})
