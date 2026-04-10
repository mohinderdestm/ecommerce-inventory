from pydantic import BaseModel, EmailStr, field_validator
from app.utils.validators import validate_password
from typing import Literal

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Literal["admin", "supplier", "user"]

    @field_validator("password")
    def password_validation(cls, v):
        return validate_password(v)