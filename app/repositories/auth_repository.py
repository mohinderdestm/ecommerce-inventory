from app.core.database import db

class AuthRepository:
    def __init__(self):
        self.collection = db["users"]

    async def get_by_email(self,email:str):
         return  await self.collection.find_one({"email":email})
    
    async def create_user(self, data: dict):
        result = await self.collection.insert_one(data)
        return str(result.inserted_id) 
    
   