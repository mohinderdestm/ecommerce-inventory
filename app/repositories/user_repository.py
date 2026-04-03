from app.core.database import users_collection


class UserRepository:

    @staticmethod
    async def create_user(user_data: dict):
        return await users_collection.insert_one(user_data)

    @staticmethod
    async def get_user_by_email(email: str):
        return await users_collection.find_one({"email": email})
