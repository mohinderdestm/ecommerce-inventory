from enum import Enum
from datetime import datetime, timezone
from typing import Optional
import uuid


class SalesOrderStatus(str, Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PACKED = "packed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"


# Valid status transitions — prevents illegal jumps
VALID_TRANSITIONS = {
    SalesOrderStatus.DRAFT:      [SalesOrderStatus.CONFIRMED, SalesOrderStatus.CANCELLED],
    SalesOrderStatus.CONFIRMED:  [SalesOrderStatus.PACKED,    SalesOrderStatus.CANCELLED],
    SalesOrderStatus.PACKED:     [SalesOrderStatus.SHIPPED,   SalesOrderStatus.CANCELLED],
    SalesOrderStatus.SHIPPED:    [SalesOrderStatus.DELIVERED, SalesOrderStatus.RETURNED],
    SalesOrderStatus.DELIVERED:  [SalesOrderStatus.RETURNED],
    SalesOrderStatus.CANCELLED:  [],   # terminal
    SalesOrderStatus.RETURNED:   [],   # terminal
}


def generate_order_number() -> str:
    from datetime import datetime
    date_part = datetime.now().strftime("%Y%m%d")
    rand_part = str(uuid.uuid4())[:6].upper()
    return f"SO-{date_part}-{rand_part}"


def build_order_item(
    product_id: str,
    product_name: str,
    sku: str,
    quantity: int,
    unit_price: float,
    variant_id: Optional[str] = None,
    variant_sku: Optional[str] = None,
    tax_percentage: float = 0.0,
) -> dict:
    subtotal = round(unit_price * quantity, 2)
    tax_amount = round(subtotal * tax_percentage / 100, 2)
    return {
        "product_id": product_id,
        "variant_id": variant_id,
        "product_name": product_name,
        "sku": variant_sku or sku,
        "quantity": quantity,
        "unit_price": round(unit_price, 2),
        "tax_percentage": tax_percentage,
        "subtotal": subtotal,
        "tax_amount": tax_amount,
        "total": round(subtotal + tax_amount, 2),
    }


def build_sales_order_document(
    customer_id: str,
    customer_name: str,
    items: list[dict],
    warehouse_id: str,
    created_by: str,
    shipping_address: Optional[dict] = None,
    notes: Optional[str] = None,
    discount: float = 0.0,
) -> dict:
    now = datetime.now(timezone.utc)
    subtotal = sum(i["subtotal"] for i in items)
    tax_total = sum(i["tax_amount"] for i in items)
    discount_amount = round(subtotal * discount / 100, 2) if discount > 0 else 0.0
    grand_total = round(subtotal + tax_total - discount_amount, 2)

    return {
        "order_number": generate_order_number(),
        "customer_id": customer_id,
        "customer_name": customer_name,
        "warehouse_id": warehouse_id,
        "items": items,
        "status": SalesOrderStatus.DRAFT.value,
        "shipping_address": shipping_address or {},
        "notes": notes or "",
        "subtotal": round(subtotal, 2),
        "tax_total": round(tax_total, 2),
        "discount_percentage": discount,
        "discount_amount": discount_amount,
        "grand_total": grand_total,
        "stock_reserved": False,
        "created_by": created_by,
        "updated_by": created_by,
        "status_history": [
            {
                "status": SalesOrderStatus.DRAFT.value,
                "changed_by": created_by,
                "timestamp": now,
                "notes": "Order created",
            }
        ],
        "created_at": now,
        "updated_at": now,
    }