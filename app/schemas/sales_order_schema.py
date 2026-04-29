from pydantic import BaseModel
from typing import List,Literal,Optional


class OrderItem(BaseModel):
    product_name: str 
    product_id: str   
    quantity: int
    price: float


class OrderCreate(BaseModel):
    customer_name: str
    # warehouse_name: str 
    phone: Optional[str] = None   # ✅ NEW
    address: Optional[str] = None # ✅ NEW
    email: Optional[str] = None  
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