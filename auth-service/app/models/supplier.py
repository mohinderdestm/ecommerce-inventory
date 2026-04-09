from enum import Enum
from datetime import datetime, timezone
from typing import Optional


class SupplierStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLACKLISTED = "blacklisted"


class PaymentTerms(str, Enum):
    IMMEDIATE = "immediate"       # Pay on delivery
    NET_15 = "net_15"             # Pay within 15 days
    NET_30 = "net_30"             # Pay within 30 days
    NET_60 = "net_60"             # Pay within 60 days
    NET_90 = "net_90"             # Pay within 90 days
    ADVANCE = "advance"           # Pay before delivery


def build_supplier_document(
    name: str,
    created_by: str,
    contact_person: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    address: Optional[dict] = None,
    gst_number: Optional[str] = None,
    payment_terms: str = PaymentTerms.NET_30.value,
    rating: float = 0.0,
    notes: Optional[str] = None,
) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "name": name.strip(),
        "contact_person": contact_person or "",
        "phone": phone or "",
        "email": email.lower().strip() if email else "",
        # Address stored as a sub-document for flexibility
        "address": address or {
            "street": "",
            "city": "",
            "state": "",
            "pincode": "",
            "country": "India",
        },
        "gst_number": gst_number.upper().strip() if gst_number else "",
        "payment_terms": payment_terms,
        "rating": round(max(0.0, min(5.0, rating)), 1),  # clamp 0–5
        "status": SupplierStatus.ACTIVE.value,
        "is_active": True,
        "notes": notes or "",
        # product_ids: maintained via supplier-product mapping endpoints
        "product_ids": [],
        "user_id": None,
        "created_by": created_by,
        "updated_by": created_by,
        "created_at": now,
        "updated_at": now,
    }