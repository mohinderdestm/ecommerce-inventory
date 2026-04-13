from bson import ObjectId

class SupplierRepository:
    def __init__(self, db):
        self.collection = db["suppliers"]

    async def create(self, data):
        result = await self.collection.insert_one(data)
        return str(result.inserted_id)

    async def get_by_user_id(self, user_id):
        return await self.collection.find_one({"user_id": str(user_id)})