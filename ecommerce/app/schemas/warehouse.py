from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.models.warehouse import WarehouseStatus, TransferStatus


# Address 

class AddressSchema(BaseModel):
    street: Optional[str] = Field(default="", max_length=200)
    city: Optional[str] = Field(default="", max_length=100)
    state: Optional[str] = Field(default="", max_length=100)
    pincode: Optional[str] = Field(default="", max_length=10)
    country: Optional[str] = Field(default="India", max_length=100)


# Warehouse Create / Update 

class WarehouseCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=200, examples=["Mumbai Central Warehouse"])
    address: Optional[AddressSchema] = None
    contact_person: Optional[str] = Field(default="", max_length=100)
    phone: Optional[str] = Field(default="", max_length=20)
    email: Optional[EmailStr] = None
    capacity: Optional[int] = Field(default=None, ge=1, description="Max units this warehouse can hold")
    notes: Optional[str] = Field(default="", max_length=1000)


class WarehouseUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    address: Optional[AddressSchema] = None
    contact_person: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)
    email: Optional[EmailStr] = None
    capacity: Optional[int] = Field(default=None, ge=1)
    notes: Optional[str] = Field(default=None, max_length=1000)
    status: Optional[WarehouseStatus] = None


# Staff Assignment 

class StaffAssignRequest(BaseModel):
    user_ids: list[str] = Field(..., min_length=1, description="List of user IDs to assign/unassign")


# Stock Entry (per warehouse) 

class StockUpdateRequest(BaseModel):
    product_id: str = Field(..., description="MongoDB ObjectId of product")
    variant_id: Optional[str] = Field(default=None, description="variant_id UUID if variant-specific")
    quantity: int = Field(..., description="Positive to add, negative to reduce")
    notes: Optional[str] = Field(default="")

    @field_validator("quantity")
    @classmethod
    def quantity_not_zero(cls, v: int) -> int:
        if v == 0:
            raise ValueError("Quantity cannot be zero.")
        return v


# Stock Transfer 

class StockTransferRequest(BaseModel):
    to_warehouse_id: str = Field(..., description="Destination warehouse ID")
    product_id: str
    variant_id: Optional[str] = None
    quantity: int = Field(..., gt=0, description="Units to transfer")
    notes: Optional[str] = Field(default="")


# Responses 

class WarehouseResponse(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    address: AddressSchema
    contact_person: str
    phone: str
    email: str
    capacity: Optional[int]
    status: WarehouseStatus
    is_active: bool
    notes: str
    staff_ids: list[str]
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}


class WarehouseListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    warehouses: list[WarehouseResponse]


class StockEntryResponse(BaseModel):
    id: str = Field(..., alias="_id")
    warehouse_id: str
    product_id: str
    variant_id: Optional[str]
    quantity: int
    updated_at: datetime

    model_config = {"populate_by_name": True}


class StockSummaryItem(BaseModel):
    product_id: str
    variant_id: Optional[str]
    quantity: int
    product_name: Optional[str] = None
    sku: Optional[str] = None


class WarehouseStockSummary(BaseModel):
    warehouse_id: str
    warehouse_name: str
    total_items: int
    stock: list[StockSummaryItem]


class TransferResponse(BaseModel):
    id: str = Field(..., alias="_id")
    from_warehouse_id: str
    to_warehouse_id: str
    product_id: str
    variant_id: Optional[str]
    quantity: int
    status: TransferStatus
    notes: str
    created_by: str
    completed_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    model_config = {"populate_by_name": True}


class APIResponse(BaseModel):
    success: bool
    message: str