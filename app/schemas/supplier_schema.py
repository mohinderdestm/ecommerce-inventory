from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class SupplierBase(BaseModel):
    name: str
    contact_person: Optional[str]
    phone: str
    email: EmailStr
    address: Optional[str]
    gst: Optional[str]
    payment_terms: Optional[str]
    rating: Optional[float] = 0
    is_active: Optional[bool] = True


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    gst: Optional[str] = None
    payment_terms: Optional[str] = None
    rating: Optional[float] = None
    is_active: Optional[bool] = None


class SupplierResponse(SupplierBase):
    id: str

    class Config:
        from_attributes = True
