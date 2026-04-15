from enum import Enum
from datetime import datetime, timezone
from typing import Optional


class WarehouseStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNDER_MAINTENANCE = "under_maintenance"


class TransferStatus(str, Enum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


def build_warehouse_document(
    name: str,
    created_by: str,
    address: Optional[dict] = None,
    contact_person: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    capacity: Optional[int] = None,
    notes: Optional[str] = None,
) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "name": name.strip(),
        "address": address or {
            "street": "", "city": "", "state": "",
            "pincode": "", "country": "India",
        },
        "contact_person": contact_person or "",
        "phone": phone or "",
        "email": email.lower().strip() if email else "",
        "capacity": capacity,           # max units the warehouse can hold (optional)
        "status": WarehouseStatus.ACTIVE.value,
        "is_active": True,
        "notes": notes or "",
        "staff_ids": [],                # user IDs assigned to this warehouse
        "created_by": created_by,
        "updated_by": created_by,
        "created_at": now,
        "updated_at": now,
    }


def build_stock_transfer_document(
    from_warehouse_id: str,
    to_warehouse_id: str,
    product_id: str,
    variant_id: Optional[str],
    quantity: int,
    created_by: str,
    notes: Optional[str] = None,
) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "from_warehouse_id": from_warehouse_id,
        "to_warehouse_id": to_warehouse_id,
        "product_id": product_id,
        "variant_id": variant_id or None,
        "quantity": quantity,
        "status": TransferStatus.PENDING.value,
        "notes": notes or "",
        "created_by": created_by,
        "completed_by": None,
        "created_at": now,
        "updated_at": now,
        "completed_at": None,
    }