from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.models.user import UserRole, UserStatus


# Shared / Base

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, examples=["john_doe"])
    email: EmailStr = Field(..., examples=["john@test.com"])
    full_name: Optional[str] = Field(default="", max_length=100, examples=["John Doe"])
    phone: Optional[str] = Field(default="", max_length=20, examples=["+91-9876543210"])
    role: UserRole = Field(default=UserRole.CUSTOMER, examples=[UserRole.CUSTOMER])

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        sanitized = v.strip().lower()
        if not sanitized.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username may only contain letters, numbers, underscores, and hyphens.")
        return sanitized


# Registration

class UserRegisterRequest(UserBase):
    password: str = Field(..., min_length=8, max_length=128, examples=["SecurePass@123"])

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        return v


# Login 

class UserLoginRequest(BaseModel):
    email: EmailStr = Field(..., examples=["john@test.com"])
    password: str = Field(..., examples=["Password123"])


# Update

class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)
    # Admins can also change role and status
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        return v


# Responses

class UserResponse(BaseModel):
    
    id: str = Field(..., alias="_id")
    username: str
    email: str
    full_name: str
    phone: str
    role: UserRole
    status: UserStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    model_config = {"populate_by_name": True}


class UserListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    users: list[UserResponse]


# Token

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserResponse


# Standard API Response Wrapper

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None