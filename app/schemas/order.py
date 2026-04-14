from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class OrderItem(BaseModel):
    product_id: str
    variant_sku: Optional[str] = None
    quantity: int = Field(..., gt=0)


class OrderCreate(BaseModel):
    customer_name: str
    items: List[OrderItem]


class OrderItemResponse(BaseModel):
    product_id: str
    variant_sku: Optional[str] = None
    name: str
    quantity: int
    price_at_purchase: float
    supplier_email: Optional[str] = None


class UserSnapshot(BaseModel):
    name: str
    email: str
    role: str


class OrderResponse(BaseModel):
    id: str
    customer_name: str
    items: List[OrderItemResponse]
    total_amount: float
    status: str
    created_at: datetime
    user_details: Optional[UserSnapshot] = None
