from fastapi import HTTPException, status
from app.modules.auth.repository import AuthRepository
from app.core.security import hash_password, verify_password, create_access_token


class AuthService:

    def __init__(self):
        self.repo = AuthRepository()

    async def register(self, user):

        existing = await self.repo.get_by_email(user.email)

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists"
            )

        user_dict = user.dict()
        user_dict["password"] = hash_password(user.password)

        user_id = await self.repo.create_user(user_dict)

        token = create_access_token({
        "user_id": str(user_id),
        "role": user.role
    })

       
        return {
            "success": True,
            "message": "User registered successfully",
            "user_id": user_id,
            "access_token": token 
        }

    async def login(self, user):

        db_user = await self.repo.get_by_email(user.email)

        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if not verify_password(user.password, db_user["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        token = create_access_token({
            "user_id": str(db_user["_id"]),
            "role": db_user["role"]
        })

        return {
            "success": True,
            "access_token": token,
            "token_type": "bearer"
        }