from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from .models import Role

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)
    role: Role = Role.VIEWER   

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category_id: str
    brand: Optional[str] = None
    supplier_id: str
    cost_price: float
    selling_price: float
    reorder_level: int
    tax_percentage: float
    unit: str