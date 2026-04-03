from fastapi import APIRouter, HTTPException
from app.schemas.user import UserCreate, UserLogin
from app.services.user_service import UserService
from app.schemas.token import TokenResponse

router = APIRouter()


@router.post("/register")
async def register(user: UserCreate):
    return await UserService.register(user.dict())


@router.post("/login", response_model=TokenResponse)
async def login(user: UserLogin):
    result = await UserService.login(user.email, user.password)

    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return result
