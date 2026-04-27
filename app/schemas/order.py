from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class PaymentMethod(str, Enum):
    upi = "upi"
    card = "card"
    netbanking = "netbanking"
    cod = "cod"


class OrderItem(BaseModel):
    product_id: str
    variant_sku: Optional[str] = None
    warehouse_id: Optional[str] = None
    quantity: int = Field(..., gt=0)


class OrderCreate(BaseModel):
    customer_name: str
    customer_email: Optional[str] = None
    shipping_address: Optional[str] = None
    payment_method: Optional[PaymentMethod] = None
    items: List[OrderItem]


class OrderItemResponse(BaseModel):
    product_id: str
    variant_sku: Optional[str] = None
    warehouse_id: Optional[str] = None
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
    customer_email: Optional[str] = None
    shipping_address: Optional[str] = None
    payment_method: Optional[str] = None
    order_reference: Optional[str] = None
    items: List[OrderItemResponse]
    total_amount: float
    status: str
    created_at: datetime
    confirmation_email_sent: Optional[bool] = None
    confirmation_email_error: Optional[str] = None
    invoice_file_name: Optional[str] = None
    user_details: Optional[UserSnapshot] = None
