from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field


MovementType = Literal["inward", "outward", "return", "damaged", "expired", "transfer"]


class InventoryMovementCreate(BaseModel):
    product_id: str
    warehouse_id: str
    variant_sku: Optional[str] = None
    movement_type: MovementType
    quantity: int = Field(..., gt=0)
    destination_warehouse_id: Optional[str] = None
    reference_type: str = Field(default="manual")
    reference_id: Optional[str] = None
    remarks: Optional[str] = None


class InventoryMovementResponse(BaseModel):
    id: str
    product_id: Optional[str]
    product_name: Optional[str]
    variant_sku: Optional[str]
    variant_name: Optional[str]
    warehouse_id: Optional[str]
    warehouse_name: Optional[str]
    movement_type: str
    quantity: int
    delta: int
    reference_type: Optional[str]
    reference_id: Optional[str]
    performed_by: dict
    remarks: Optional[str]
    created_at: Optional[datetime]
