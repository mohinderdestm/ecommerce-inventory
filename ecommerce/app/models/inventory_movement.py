from enum import Enum
from datetime import datetime, timezone
from typing import Optional


class MovementType(str, Enum):
    INWARD = "inward"
    OUTWARD = "outward"
    RETURN = "return"
    DAMAGED = "damaged"
    EXPIRED = "expired"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"


def build_inventory_movement_document(
    product_id: str,
    warehouse_id: str,
    movement_type: MovementType,
    quantity: int,
    reference_type: str,
    performed_by: str,
    variant_id: Optional[str] = None,
    reference_id: Optional[str] = None,
    remarks: Optional[str] = None,
) -> dict:
    return {
        "product_id": product_id,
        "variant_id": variant_id,
        "warehouse_id": warehouse_id,
        "movement_type": movement_type.value,
        "quantity": abs(quantity),  # Absolute value, movement_type dictates sign
        "reference_type": reference_type,
        "reference_id": reference_id,
        "performed_by": performed_by,
        "timestamp": datetime.now(timezone.utc),
        "remarks": remarks or "",
    }
