from app.core.database import db

class UserRepository:

    @staticmethod
    async def create_user(user: dict):
        return await db["users"].insert_one(user)

    @staticmethod
    async def get_by_email(email: str):
        return await db["users"].find_one({"email": email})