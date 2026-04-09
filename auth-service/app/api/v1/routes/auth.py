from fastapi import APIRouter, Depends, status

from app.schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
)
from app.services.user_service import UserService
from app.repositories.user_repository import UserRepository
from app.repositories.supplier_repository import SupplierRepository
from app.utils.dependencies import get_current_user, get_db
from app.core.config import settings
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_user_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> UserService:
    return UserService(
        repo=UserRepository(db),
        supplier_repo=SupplierRepository(db),  # injected for auto supplier profile
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description=(
        "Creates a new user account.\n\n"
        "- Role defaults to **customer** if not specified.\n"
        "- If role is **supplier**, a basic supplier profile is automatically "
        "created and linked to this account. Admin can later fill in GST, "
        "address, and payment terms via `PUT /suppliers/{id}`."
    ),
)
async def register(
    payload: UserRegisterRequest,
    service: UserService = Depends(get_user_service),
):
    user = await service.register(payload)
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and get JWT token",
)
async def login(
    payload: UserLoginRequest,
    service: UserService = Depends(get_user_service),
):
    result = await service.login(payload)
    return {
        "access_token": result["token"],
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": result["user"],
    }


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current logged-in user",
)
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user