from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    role: str = Field(..., pattern="^(admin|manager|viewer|supplier)$")

    phone: Optional[str] = None
    address: Optional[str] = None
    gst: Optional[str] = None
    contact_person: Optional[str] = None
    payment_terms: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
