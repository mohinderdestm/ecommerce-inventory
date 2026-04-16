from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List


class WarehouseBase(BaseModel):
    name: str = Field(..., min_length=3)
    code: str = Field(..., min_length=2)
    email: EmailStr
    phone: Optional[str]

    street: str
    city: str
    state: str
    country: str
    pincode: str

    capacity: Optional[int] = 0
    is_active: Optional[bool] = True


class WarehouseCreate(WarehouseBase):
    pass


class WarehouseUpdate(BaseModel):
    name: Optional[str]
    code: Optional[str]
    email: Optional[EmailStr]
    phone: Optional[str]

    street: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    pincode: Optional[str]

    capacity: Optional[int]
    is_active: Optional[bool]


class WarehouseResponse(BaseModel):
    id: str
    name: str
    code: str
    email: str
    phone: Optional[str]
    address: dict
    capacity: int
    is_active: bool
    created_by: Optional[dict]


class BulkWarehouseCreate(BaseModel):
    warehouses: List[WarehouseCreate]
