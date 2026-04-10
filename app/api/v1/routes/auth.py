from fastapi import APIRouter, Depends
from app.schemas.user_schema import UserCreate
from app.schemas.auth_schema import LoginRequest
from app.services.auth_service import AuthService
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register")
async def register(user: UserCreate):
    return await AuthService.register(user.model_dump())


@router.post("/login")
async def login(data: LoginRequest):
    return await AuthService.login(data.email, data.password)


#  Protected test route
@router.get("/me")
async def get_me(user=Depends(get_current_user)):
    return {"message": "You are authenticated", "user": user}