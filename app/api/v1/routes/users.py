from fastapi import APIRouter, Depends
from app.utils.dependencies import get_current_user, require_role

router = APIRouter()


@router.get("/me")
async def get_me(user=Depends(get_current_user)):
    return {"message": "User info", "user": user}


@router.get("/admin-only")
async def admin_data(user=Depends(require_role(["admin"]))):
    return {"message": "Welcome Admin", "user": user}


@router.get("/manager-data")
async def manager_data(user=Depends(require_role(["admin", "manager"]))):
    return {"message": "Manager access granted", "user": user}
