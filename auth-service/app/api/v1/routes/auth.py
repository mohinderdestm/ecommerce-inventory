from fastapi import APIRouter, Depends, status

from app.schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
)
from app.services.user_service import UserService
from app.repositories.user_repository import UserRepository
from app.utils.dependencies import get_user_repo, get_current_user
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_user_service(repo: UserRepository = Depends(get_user_repo)) -> UserService:
    return UserService(repo)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new user account. Role defaults to **customer** if not specified.",
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
    description="Authenticates a user and returns a JWT access token.",
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
    description="Returns the profile of the user associated with the provided JWT token.",
)
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user
