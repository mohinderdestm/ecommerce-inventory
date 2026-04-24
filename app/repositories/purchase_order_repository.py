from bson import ObjectId


class PurchaseRepository:
    def __init__(self, db):
        self.collection = db["purchase_orders"]

    async def create(self, data):
        result = await self.collection.insert_one(data)
        return str(result.inserted_id)

    async def get_all(self):
        cursor = self.collection.find()
        return await cursor.to_list(length=100)

    async def get_by_id(self, po_id):
        return await self.collection.find_one({"_id": ObjectId(po_id)})

    async def update(self, po_id, data):
        return await self.collection.update_one(
            {"_id": ObjectId(po_id)},
            {"$set": data}
        )