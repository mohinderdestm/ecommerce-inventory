from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.models.supplier import SupplierStatus, PaymentTerms


# Address sub-schema

class AddressSchema(BaseModel):
    street: Optional[str] = Field(default="", max_length=200)
    city: Optional[str] = Field(default="", max_length=100)
    state: Optional[str] = Field(default="", max_length=100)
    pincode: Optional[str] = Field(default="", max_length=10)
    country: Optional[str] = Field(default="India", max_length=100)


# Create 

class SupplierCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=200, examples=["ABC Traders Pvt Ltd"])
    contact_person: Optional[str] = Field(default="", max_length=100, examples=["Rajesh Kumar"])
    phone: Optional[str] = Field(default="", max_length=20, examples=["+91-9876543210"])
    email: Optional[EmailStr] = Field(default=None, examples=["supplier@abctraders.com"])
    address: Optional[AddressSchema] = None
    gst_number: Optional[str] = Field(
        default="",
        max_length=15,
        examples=["27AABCU9603R1ZX"],
        description="15-character GST Identification Number"
    )
    payment_terms: PaymentTerms = Field(default=PaymentTerms.NET_30)
    rating: float = Field(default=0.0, ge=0, le=5, examples=[4.2])
    notes: Optional[str] = Field(default="", max_length=1000)

    @field_validator("gst_number")
    @classmethod
    def validate_gst(cls, v: str) -> str:
        if v and len(v) != 15:
            raise ValueError("GST number must be exactly 15 characters.")
        return v.upper() if v else v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if v:
            digits = v.replace("+", "").replace("-", "").replace(" ", "")
            if not digits.isdigit():
                raise ValueError("Phone number must contain only digits, +, -, or spaces.")
        return v


# Update 

class SupplierUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    contact_person: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)
    email: Optional[EmailStr] = None
    address: Optional[AddressSchema] = None
    gst_number: Optional[str] = Field(default=None, max_length=15)
    payment_terms: Optional[PaymentTerms] = None
    rating: Optional[float] = Field(default=None, ge=0, le=5)
    notes: Optional[str] = Field(default=None, max_length=1000)
    status: Optional[SupplierStatus] = None

    @field_validator("gst_number")
    @classmethod
    def validate_gst(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) != 15:
            raise ValueError("GST number must be exactly 15 characters.")
        return v.upper() if v else v


# Supplier-Product Mapping 

class SupplierProductMapRequest(BaseModel):
    product_ids: list[str] = Field(
        ...,
        min_length=1,
        description="List of product MongoDB ObjectIds to link/unlink"
    )


# Response 

class SupplierResponse(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    contact_person: str
    phone: str
    email: str
    address: AddressSchema
    gst_number: str
    payment_terms: PaymentTerms
    rating: float
    status: SupplierStatus
    is_active: bool
    notes: str
    product_ids: list[str]
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}


class SupplierListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    suppliers: list[SupplierResponse]


class SupplierSummaryResponse(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    contact_person: str
    phone: str
    email: str
    payment_terms: PaymentTerms
    rating: float
    status: SupplierStatus
    product_count: int

    model_config = {"populate_by_name": True}


# Standard

class APIResponse(BaseModel):
    success: bool
    message: str