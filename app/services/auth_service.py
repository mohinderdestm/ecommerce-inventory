from app.repositories.user_repo import UserRepository
from app.core.security import hash_password, verify_password, create_access_token
from fastapi import HTTPException
from app.models.user_model import UserModel


class AuthService:

    @staticmethod
    async def register(user_data: dict):
        existing = await UserRepository.get_by_email(user_data["email"])
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")

        user_data["password"] = hash_password(user_data["password"])

        user = UserModel.create_user_dict(user_data)

        await UserRepository.create_user(user)

        return {"message": "User registered successfully"}

    @staticmethod
    async def login(email: str, password: str):
        user = await UserRepository.get_by_email(email)

        if not user:
            raise HTTPException(status_code=401, detail="Invalid email")

        if not verify_password(password, user["password"]):
            raise HTTPException(status_code=401, detail="Invalid password")

        token = create_access_token({
            "user_id": str(user["_id"]),
            "role": user["role"]
        })

        return {"access_token": token}