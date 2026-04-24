from enum import Enum
from datetime import datetime, timezone
from typing import Optional
import uuid

class PurchaseOrderStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    PARTIALLY_RECEIVED = "partially_received"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

VALID_TRANSITIONS = {
    PurchaseOrderStatus.DRAFT: [PurchaseOrderStatus.SUBMITTED, PurchaseOrderStatus.CANCELLED],
    PurchaseOrderStatus.SUBMITTED: [PurchaseOrderStatus.APPROVED, PurchaseOrderStatus.REJECTED, PurchaseOrderStatus.CANCELLED],
    PurchaseOrderStatus.APPROVED: [PurchaseOrderStatus.PARTIALLY_RECEIVED, PurchaseOrderStatus.COMPLETED, PurchaseOrderStatus.CANCELLED],
    PurchaseOrderStatus.REJECTED: [],
    PurchaseOrderStatus.PARTIALLY_RECEIVED: [PurchaseOrderStatus.PARTIALLY_RECEIVED, PurchaseOrderStatus.COMPLETED, PurchaseOrderStatus.CANCELLED],
    PurchaseOrderStatus.COMPLETED: [],
    PurchaseOrderStatus.CANCELLED: [],
}

def generate_po_number() -> str:
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    rand_part = str(uuid.uuid4())[:6].upper()
    return f"PO-{date_part}-{rand_part}"

def build_purchase_order_item(
    product_id: str,
    product_name: str,
    sku: str,
    ordered_quantity: int,
    unit_cost: float,
    variant_id: Optional[str] = None,
    variant_sku: Optional[str] = None,
    tax_percentage: float = 0.0,
) -> dict:
    subtotal = round(unit_cost * ordered_quantity, 2)
    tax_amount = round(subtotal * tax_percentage / 100, 2)
    return {
        "product_id": product_id,
        "variant_id": variant_id,
        "product_name": product_name,
        "sku": variant_sku or sku,
        "ordered_quantity": ordered_quantity,
        "received_quantity": 0,
        "unit_cost": round(unit_cost, 2),
        "tax_percentage": tax_percentage,
        "subtotal": subtotal,
        "tax_amount": tax_amount,
        "total": round(subtotal + tax_amount, 2),
    }

def build_purchase_order_document(
    supplier_id: str,
    supplier_name: str,
    items: list[dict],
    destination_warehouse_id: str,
    created_by: str,
    notes: Optional[str] = None,
) -> dict:
    now = datetime.now(timezone.utc)
    subtotal = sum(i["subtotal"] for i in items)
    tax_total = sum(i["tax_amount"] for i in items)
    grand_total = round(subtotal + tax_total, 2)

    return {
        "po_number": generate_po_number(),
        "supplier_id": supplier_id,
        "supplier_name": supplier_name,
        "destination_warehouse_id": destination_warehouse_id,
        "items": items,
        "status": PurchaseOrderStatus.DRAFT.value,
        "notes": notes or "",
        "subtotal": round(subtotal, 2),
        "tax_total": round(tax_total, 2),
        "grand_total": grand_total,
        "invoice_metadata": {}, # To store invoice_number, invoice_date etc. upon receiving
        "created_by": created_by,
        "updated_by": created_by,
        "status_history": [
            {
                "status": PurchaseOrderStatus.DRAFT.value,
                "changed_by": created_by,
                "timestamp": now,
                "notes": "Purchase order created",
            }
        ],
        "created_at": now,
        "updated_at": now,
    }
