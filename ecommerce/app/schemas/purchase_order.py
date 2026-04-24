from pydantic import BaseModel, Field, conint, confloat
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.purchase_order import PurchaseOrderStatus

class PurchaseOrderItemCreate(BaseModel):
    product_id: str
    variant_id: Optional[str] = None
    product_name: str
    sku: str
    ordered_quantity: conint(gt=0)
    unit_cost: confloat(ge=0.0)
    tax_percentage: confloat(ge=0.0) = 0.0

class PurchaseOrderCreate(BaseModel):
    supplier_id: str
    supplier_name: str
    destination_warehouse_id: str
    items: List[PurchaseOrderItemCreate]
    notes: Optional[str] = None

class PurchaseOrderStatusUpdate(BaseModel):
    status: PurchaseOrderStatus
    notes: Optional[str] = None

class ItemReceipt(BaseModel):
    product_id: str
    variant_id: Optional[str] = None
    received_quantity: conint(gt=0)

class InvoiceMetadata(BaseModel):
    invoice_number: Optional[str] = None
    invoice_date: Optional[datetime] = None
    total_amount: Optional[float] = None
    notes: Optional[str] = None

class PurchaseOrderReceive(BaseModel):
    items: List[ItemReceipt]
    invoice_metadata: Optional[InvoiceMetadata] = None
    notes: Optional[str] = "Received items"

class PurchaseOrderItemResponse(BaseModel):
    product_id: str
    variant_id: Optional[str] = None
    product_name: str
    sku: str
    ordered_quantity: int
    received_quantity: int
    unit_cost: float
    tax_percentage: float
    subtotal: float
    tax_amount: float
    total: float

class StatusHistoryItem(BaseModel):
    status: str
    changed_by: str
    timestamp: datetime
    notes: Optional[str] = None

class PurchaseOrderResponse(BaseModel):
    id: str = Field(alias="_id")
    po_number: str
    supplier_id: str
    supplier_name: str
    destination_warehouse_id: str
    items: List[PurchaseOrderItemResponse]
    status: str
    notes: Optional[str] = None
    subtotal: float
    tax_total: float
    grand_total: float
    invoice_metadata: Optional[Dict[str, Any]] = None
    created_by: str
    updated_by: str
    status_history: List[StatusHistoryItem]
    created_at: datetime
    updated_at: datetime
