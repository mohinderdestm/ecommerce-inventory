from fastapi import APIRouter, HTTPException, status
from app.schemas.user import UserCreate, UserLogin
from app.services.user_service import UserService
from app.schemas.token import TokenResponse


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register")
async def register(user: UserCreate):
    try:

        return await UserService.register(user.dict())
    except Exception as e:

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(user: UserLogin):

    result = await UserService.login(user.email, user.password)

    if not result:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    return result
