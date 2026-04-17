from fastapi import APIRouter, Depends, Response, HTTPException, Request
from app.db.database import db
from app.modules.authentication.services import AuthService
from app.modules.authentication.schemas import UserCreate, UserLogin
from app.core.user_repo import UserRepository
from app.core.config import security


router = APIRouter(prefix="/auth", tags=["Auth"])

def get_auth_service():
    repo = UserRepository(db)
    return AuthService(repo)


# ✅ SIGNUP
@router.post("/signup")
async def signup(user: UserCreate, response: Response, service: AuthService = Depends(get_auth_service)):
    await service.signup(user)

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return {"message": "Signup successful"}


# ✅ LOGIN
@router.post("/login")
async def login(user: UserLogin, response: Response, service: AuthService = Depends(get_auth_service)):
    result = await service.login(user)

    response.set_cookie(
        key="access_token",
        value=result["access_token"],
        httponly=True,
        samesite="lax"
    )

    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True,
        samesite="lax"
    )

    return {"message": "Login successful"}


# ✅ REFRESH
@router.post("/refresh")
async def refresh_token(request: Request):
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    payload = security.verify_token(refresh_token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_access_token = security.create_access_token({
        "sub": payload["sub"],
        "role": payload.get("role", "Viewer")
    })

    return {"access_token": new_access_token}
