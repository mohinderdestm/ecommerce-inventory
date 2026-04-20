from pydantic import BaseModel
from typing import List,Literal


class OrderItem(BaseModel):
    product_name: str  
    quantity: int
    price: float


class OrderCreate(BaseModel):
    customer_name: str
    warehouse_name: str 
    items: List[OrderItem]


class OrderStatusUpdate(BaseModel):
    status: Literal[
        "draft",
        "confirmed",
        "packed",
        "shipped",
        "delivered",
        "cancelled",
        "returned"
    ]