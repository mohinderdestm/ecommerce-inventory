from app.repositories.user_repository import UserRepository
from app.core.security import hash_password, verify_password, create_access_token
from datetime import datetime


class UserService:

    @staticmethod
    async def register(user_data: dict):
        existing_user = await UserRepository.get_user_by_email(user_data["email"])

        if existing_user:
            return {"error": "User already exists"}

        user_data["password"] = hash_password(user_data["password"])
        user_data["created_at"] = datetime.utcnow()

        result = await UserRepository.create_user(user_data)

        return {
            "message": "User created successfully",
            "user_id": str(result.inserted_id),
        }

    @staticmethod
    async def login(email: str, password: str):
        user = await UserRepository.get_user_by_email(email)

        if not user or not verify_password(password, user["password"]):
            return None

        token = create_access_token({"sub": user["email"], "role": user["role"]})

        return {"access_token": token, "token_type": "bearer"}
