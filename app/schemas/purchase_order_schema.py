from datetime import date
from typing import List, Optional, Literal

from pydantic import BaseModel, Field


PurchaseOrderStatus = Literal[
    "draft",
    "submitted",
    "approved",
    "rejected",
    "partially_received",
    "completed",
    "cancelled",
]


class PurchaseOrderItemCreate(BaseModel):
    product_id: str
    variant_sku: Optional[str] = None
    quantity: int = Field(..., gt=0)
    unit_cost: float = Field(default=0, ge=0)
    remarks: Optional[str] = None


class PurchaseOrderCreate(BaseModel):
    supplier_email: Optional[str] = None
    notes: Optional[str] = None
    items: List[PurchaseOrderItemCreate] = []


class PurchaseOrderAddItems(BaseModel):
    items: List[PurchaseOrderItemCreate]


class PurchaseOrderInvoiceMetadata(BaseModel):
    invoice_number: Optional[str] = None
    bill_number: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    tax_amount: Optional[float] = Field(default=None, ge=0)
    total_amount: Optional[float] = Field(default=None, ge=0)
    currency: Optional[str] = "INR"
    attachment_url: Optional[str] = None


class PurchaseOrderReceiveLine(BaseModel):
    product_id: str
    variant_sku: Optional[str] = None
    warehouse_id: str
    quantity_received: int = Field(..., gt=0)
    remarks: Optional[str] = None
    expiry_date: Optional[date] = None


class PurchaseOrderReceive(BaseModel):
    lines: List[PurchaseOrderReceiveLine]
    invoice_metadata: Optional[PurchaseOrderInvoiceMetadata] = None


class PurchaseOrderActionNote(BaseModel):
    remarks: Optional[str] = None
