from pydantic import BaseModel
from typing import List, Literal


class PurchaseItem(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    cost_price: float


class PurchaseCreate(BaseModel):
    supplier_id: str
    supplier_name: str
    warehouse_id: str
    warehouse_name: str
    items: List[PurchaseItem]


class PurchaseStatusUpdate(BaseModel):
    status: Literal[
        "draft",
        "submitted",
        "approved",
        "rejected",
        "partially_received",
        "completed",
        "cancelled"
    ]


class ReceiveItems(BaseModel):
    items: List[PurchaseItem]

class InvoiceData(BaseModel):
    invoice_number: str | None = None
    invoice_date: str