from typing import Optional
from fastapi import HTTPException, status
import logging

from app.repositories.user_repository import UserRepository
from app.repositories.supplier_repository import SupplierRepository
from app.models.user import UserRole, UserStatus, build_user_document
from app.models.supplier import build_supplier_document
from app.schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    UserUpdateRequest,
    PasswordChangeRequest,
)
from app.core.security import hash_password, verify_password, create_access_token
from app.core.config import settings

logger = logging.getLogger(__name__)


class UserService:

    def __init__(self, repo: UserRepository, supplier_repo: Optional[SupplierRepository] = None):
        self.repo = repo
        self.supplier_repo = supplier_repo  # For potential supplier-related user operations

    # Registration

    async def register(self, payload: UserRegisterRequest) -> dict:
        if await self.repo.email_exists(payload.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists."
            )
        if await self.repo.username_exists(payload.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This username is already taken."
            )

        hashed = hash_password(payload.password)
        user_doc = build_user_document(
            username=payload.username,
            email=payload.email,
            hashed_password=hashed,
            role=payload.role,
            full_name=payload.full_name,
            phone=payload.phone,
        )
        created_user = await self.repo.create(user_doc)
        logger.info(f"New user registered: {created_user['email']} | role={created_user['role']}")

        if payload.role == UserRole.SUPPLIER and self.supplier_repo:
            await self._create_supplier_profile(created_user, payload)

        return created_user

    async def _create_supplier_profile(self, user: dict, payload: UserRegisterRequest):
        try:
            supplier_name = payload.full_name.strip() if payload.full_name else payload.username

            supplier_doc = build_supplier_document(
                name=supplier_name,
                created_by=user["_id"],
                contact_person=payload.full_name or payload.username,
                phone=payload.phone or "",
                email=str(payload.email),
            )

            supplier_doc["user_id"] = user["_id"]

            created_supplier = await self.supplier_repo.create(supplier_doc)
            logger.info(
                f"Auto-created supplier profile '{created_supplier['name']}' "
                f"for user {user['email']}"
            )
        except Exception as e:
            logger.error(f"Failed to auto-create supplier profile for {user['email']}: {e}")

    # Login

    async def login(self, payload: UserLoginRequest) -> dict:
        
        user = await self.repo.find_by_email(payload.email)

        invalid_creds = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

        if not user:
            raise invalid_creds
        if not verify_password(payload.password, user["hashed_password"]):
            raise invalid_creds
        if not user.get("is_active"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been deactivated. Contact support."
            )

        # Stamp last login (fire-and-forget, non-blocking)
        await self.repo.update_last_login(user["_id"])

        token = create_access_token(data={"sub": user["_id"], "role": user["role"]})
        logger.info(f"User logged in: {user['email']}")
        return {"token": token, "user": user}

    # Get Current User

    async def get_user_by_id(self, user_id: str) -> dict:
        user = await self.repo.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")
        return user

    # Update Profile

    async def update_user(
        self,
        target_user_id: str,
        payload: UserUpdateRequest,
        requesting_user: dict,
    ) -> dict:
        target_user = await self.repo.find_by_id(target_user_id)
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found.")

        is_admin = requesting_user["role"] == UserRole.ADMIN.value
        is_self = requesting_user["_id"] == target_user_id

        if not is_admin and not is_self:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this user."
            )

        update_data = {}

        if payload.full_name is not None:
            update_data["full_name"] = payload.full_name
        if payload.phone is not None:
            update_data["phone"] = payload.phone

        # Role and status changes are admin-only
        if payload.role is not None:
            if not is_admin:
                raise HTTPException(status_code=403, detail="Only admins can change roles.")
            update_data["role"] = payload.role.value
        if payload.status is not None:
            if not is_admin:
                raise HTTPException(status_code=403, detail="Only admins can change status.")
            update_data["status"] = payload.status.value
            update_data["is_active"] = (payload.status == UserStatus.ACTIVE)

        if not update_data:
            raise HTTPException(status_code=400, detail="No valid fields provided for update.")

        updated = await self.repo.update(target_user_id, update_data)
        logger.info(f"User {target_user_id} updated by {requesting_user['_id']}")
        return updated

    # Change Password

    async def change_password(
        self,
        user_id: str,
        payload: PasswordChangeRequest,
        requesting_user: dict,
    ):
        if requesting_user["_id"] != user_id:
            raise HTTPException(status_code=403, detail="You can only change your own password.")

        user = await self.repo.find_by_id(user_id)
        if not verify_password(payload.current_password, user["hashed_password"]):
            raise HTTPException(status_code=400, detail="Current password is incorrect.")

        new_hash = hash_password(payload.new_password)
        await self.repo.update(user_id, {"hashed_password": new_hash})
        logger.info(f"Password changed for user {user_id}")

    # List Users (Admin)

    async def list_users(
        self,
        role: Optional[str],
        status: Optional[str],
        page: int,
        page_size: int,
    ) -> dict:
        skip = (page - 1) * page_size
        users, total = await self.repo.list_users(
            role=role, status=status, skip=skip, limit=page_size
        )
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "users": users,
        }

    # Delete User (Admin)

    async def delete_user(self, target_user_id: str, requesting_user: dict):
        if requesting_user["_id"] == target_user_id:
            raise HTTPException(status_code=400, detail="You cannot delete your own account.")
        deleted = await self.repo.delete(target_user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="User not found.")
        logger.info(f"User {target_user_id} deleted by admin {requesting_user['_id']}")