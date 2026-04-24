from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.security import decode_access_token
from app.core.database import get_database
from app.repositories.user_repository import UserRepository
from app.models.user import UserRole

bearer_scheme = HTTPBearer()


# Database Dependency

def get_db() -> AsyncIOMotorDatabase:
    return get_database()


# Repository Dependency

def get_user_repo(db: AsyncIOMotorDatabase = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


# Auth Dependencies

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    repo: UserRepository = Depends(get_user_repo),
) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if not user_id:
        raise credentials_exception

    user = await repo.find_by_id(user_id)
    if not user or not user.get("is_active"):
        raise credentials_exception

    return user


# Role-Based Guards

def require_roles(*roles: UserRole):
    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in [r.value for r in roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {[r.value for r in roles]}",
            )
        return current_user
    return role_checker


# Convenience shortcuts
require_admin = require_roles(UserRole.ADMIN)
require_admin_or_supplier = require_roles(UserRole.ADMIN, UserRole.SUPPLIER)
require_admin_or_warehouse_staff = require_roles(UserRole.ADMIN, UserRole.WAREHOUSE_STAFF, UserRole.INVENTORY_MANAGER)
require_inventory_manager = require_roles(UserRole.INVENTORY_MANAGER)
require_admin_or_inventory_manager = require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER)