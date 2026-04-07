from fastapi import HTTPException
from app.core.config import security


class AuthService:
    def __init__(self, repo):
        self.repo = repo

    async def signup(self, user):
        existing = await self.repo.get_by_email(user.email)
        if existing:
            raise HTTPException(status_code=400, detail="User already exists")

        hashed_password = security.hash_password(user.password)

        user_dict = user.dict()
        user_dict["password"] = hashed_password

        await self.repo.create_user(user_dict)

        return {"message": "User created"}

    async def login(self, user):
        db_user = await self.repo.get_by_email(user.email)

        if not db_user:
            raise HTTPException(status_code=400, detail="Invalid credentials")

        if not security.verify_password(user.password, db_user["password"]):
            raise HTTPException(status_code=400, detail="Invalid credentials")

        payload = {
            "sub": db_user["name"],
            "role": db_user.get("role", "Viewer")
        }

        access_token = security.create_access_token(payload)
        refresh_token = security.create_refresh_token(payload)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    

