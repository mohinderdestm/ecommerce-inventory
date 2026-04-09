from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from app.schemas.user import (
    UserResponse,
    UserUpdateRequest,
    UserListResponse,
    PasswordChangeRequest,
    APIResponse,
)
from app.services.user_service import UserService
from app.repositories.user_repository import UserRepository
from app.repositories.supplier_repository import SupplierRepository
from app.utils.dependencies import (
    get_user_repo,
    get_current_user,
    require_admin,
    get_db,
)
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.user import UserRole, UserStatus

router = APIRouter(prefix="/users", tags=["Users"])


def get_user_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> UserService:
    return UserService(
        repo = UserRepository(db),
        supplier_repo = SupplierRepository(db),
    )


@router.get(
    "/",
    response_model=UserListResponse,
    summary="List all users [Admin only]",
    dependencies=[Depends(require_admin)],
)
async def list_users(
    role: Optional[UserRole] = Query(default=None, description="Filter by role"),
    status: Optional[UserStatus] = Query(default=None, description="Filter by status"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    service: UserService = Depends(get_user_service),
    _: dict = Depends(require_admin),
):
    return await service.list_users(
        role=role.value if role else None,
        status=status.value if status else None,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="Admins can view any user. Other users can only view their own profile.",
)
async def get_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
    current_user: dict = Depends(get_current_user),
):
    # Non-admins can only fetch their own profile via this endpoint
    if current_user["role"] != UserRole.ADMIN.value and current_user["_id"] != user_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Access denied.")
    return await service.get_user_by_id(user_id)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user",
    description="Users can update their own name/phone. Admins can also change role and status.",
)
async def update_user(
    user_id: str,
    payload: UserUpdateRequest,
    service: UserService = Depends(get_user_service),
    current_user: dict = Depends(get_current_user),
):
    return await service.update_user(user_id, payload, current_user)


@router.put(
    "/{user_id}/password",
    response_model=APIResponse,
    summary="Change password",
    description="Users can only change their own password.",
)
async def change_password(
    user_id: str,
    payload: PasswordChangeRequest,
    service: UserService = Depends(get_user_service),
    current_user: dict = Depends(get_current_user),
):
    await service.change_password(user_id, payload, current_user)
    return {"success": True, "message": "Password changed successfully."}


@router.delete(
    "/{user_id}",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete user [Admin only]",
    dependencies=[Depends(require_admin)],
)
async def delete_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
    current_user: dict = Depends(require_admin),
):
    await service.delete_user(user_id, current_user)
    return {"success": True, "message": "User deleted successfully."}