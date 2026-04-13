from bson import ObjectId
from datetime import datetime
from app.core.database import db

class ProductRepository:
    def __init__(self,db):
        self.collection = db["products"]

    async def create(self,product_data):
        product_data["created_at"] = datetime.utcnow()
        product_data["updated_at"] = datetime.utcnow()
        
      
        product_data["status"] = product_data.get("status", "active")
        product_data["is_deleted"] = False

        
        result = await self.collection.insert_one(product_data)
        return str(result.inserted_id)
    
    async def get_by_id(self,product_id:str):
        return await self.collection.find_one({"_id":ObjectId(product_id), "is_deleted": False})
    
    async def update(self, product_id, update_data):
        update_data["updated_at"] = datetime.utcnow()
        return await self.collection.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": update_data}
        )

    async def soft_delete(self, product_id):
        return await self.collection.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": {"is_deleted": True}}
        )

    async def list(self, filters, skip, limit):
        return await self.collection.find(filters).skip(skip).limit(limit).to_list(length=limit)

                                                
