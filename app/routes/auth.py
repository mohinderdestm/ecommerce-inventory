from fastapi import APIRouter, status,Depends
from app.schemas.auth_schema import RegisterSchema, loginSchema
from app.services.auth_service import AuthService
from app.core.dependencies import get_current_user,required_roles


router = APIRouter(prefix="/auth", tags=["Auth"])

auth_service = AuthService()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: RegisterSchema):
    return await auth_service.register(user)


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(user: loginSchema):
    return await auth_service.login(user)


@router.get("/me")
async def get_user(user=Depends(get_current_user)):
    return{
        "success":True,
        "user":{
            "id":str(user["_id"]),
            "email":user["email"],
            "role":user["role"],
            "name":user.get("name")
        }
    }

@router.get("/admin-only")
async def admin_only(user=Depends(required_roles(["admin"]))):
    return{
        "success":True,
        "message":"Welcome Admin!"
    }    