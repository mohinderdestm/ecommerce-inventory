from enum import Enum
from datetime import datetime, timezone
from typing import Optional


class UserRole(str, Enum):
    ADMIN = "admin"
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    WAREHOUSE_STAFF = "warehouse_staff"


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


def build_user_document(
    username: str,
    email: str,
    hashed_password: str,
    role: UserRole,
    full_name: Optional[str] = None,
    phone: Optional[str] = None,
) -> dict:
    
    now = datetime.now(timezone.utc)
    return {
        "username": username.lower().strip(),
        "email": email.lower().strip(),
        "hashed_password": hashed_password,
        "full_name": full_name or "",
        "phone": phone or "",
        "role": role.value,
        "status": UserStatus.ACTIVE.value,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
        "last_login": None,
    }