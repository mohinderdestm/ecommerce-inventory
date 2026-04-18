from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from app.models.sales_order import SalesOrderStatus


# Order Item 

class OrderItemRequest(BaseModel):
    product_id: str = Field(..., description="MongoDB ObjectId of the product")
    variant_id: Optional[str] = Field(default=None, description="UUID variant_id if variant-specific")
    quantity: int = Field(..., gt=0, examples=[2])

    @field_validator("quantity")
    @classmethod
    def qty_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Quantity must be greater than 0.")
        return v


# Shipping Address 

class ShippingAddressSchema(BaseModel):
    full_name: str = Field(..., max_length=100)
    phone: str = Field(..., max_length=20)
    street: str = Field(..., max_length=200)
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=100)
    pincode: str = Field(..., max_length=10)
    country: str = Field(default="India", max_length=100)


# Create 

class SalesOrderCreateRequest(BaseModel):
    warehouse_id: str = Field(..., description="Warehouse to fulfil from")
    items: list[OrderItemRequest] = Field(..., min_length=1, max_length=50)
    shipping_address: Optional[ShippingAddressSchema] = None
    notes: Optional[str] = Field(default="", max_length=1000)
    discount_percentage: float = Field(default=0.0, ge=0, le=100)


# Status Update 

class StatusUpdateRequest(BaseModel):
    notes: Optional[str] = Field(default="", max_length=500)


# Return 

class ReturnRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500, examples=["Product damaged on arrival"])
    items_to_return: Optional[list[OrderItemRequest]] = Field(
        default=None,
        description="Partial return — specific items to return. Leave empty to return full order."
    )


# Item Response 

class OrderItemResponse(BaseModel):
    product_id: str
    variant_id: Optional[str]
    product_name: str
    sku: str
    quantity: int
    unit_price: float
    tax_percentage: float
    subtotal: float
    tax_amount: float
    total: float


# Status History 

class StatusHistoryEntry(BaseModel):
    status: str
    changed_by: str
    timestamp: datetime
    notes: str


# Sales Order Response 

class SalesOrderResponse(BaseModel):
    id: str = Field(..., alias="_id")
    order_number: str
    customer_id: str
    customer_name: str
    warehouse_id: str
    items: list[OrderItemResponse]
    status: SalesOrderStatus
    shipping_address: dict
    notes: str
    subtotal: float
    tax_total: float
    discount_percentage: float
    discount_amount: float
    grand_total: float
    stock_reserved: bool
    status_history: list[StatusHistoryEntry]
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}


class SalesOrderListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    orders: list[SalesOrderResponse]


class OrderSummaryResponse(BaseModel):
    id: str = Field(..., alias="_id")
    order_number: str
    customer_name: str
    status: SalesOrderStatus
    grand_total: float
    item_count: int
    created_at: datetime

    model_config = {"populate_by_name": True}


class APIResponse(BaseModel):
    success: bool
    message: str