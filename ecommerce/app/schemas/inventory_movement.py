from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.inventory_movement import MovementType


class InventoryMovementCreate(BaseModel):
    product_id: str
    variant_id: Optional[str] = None
    warehouse_id: str
    movement_type: MovementType
    quantity: int = Field(gt=0, description="Quantity must be positive")
    remarks: Optional[str] = None


class InventoryMovementResponse(BaseModel):
    id: str = Field(alias="_id")
    product_id: str
    variant_id: Optional[str] = None
    warehouse_id: str
    movement_type: MovementType
    quantity: int
    reference_type: str
    reference_id: Optional[str] = None
    performed_by: str
    timestamp: datetime
    remarks: str

    class Config:
        populate_by_name = True


class InventoryMovementListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    movements: List[InventoryMovementResponse]


class InventoryLedgerEntry(InventoryMovementResponse):
    pass


class InventoryLedgerResponse(BaseModel):
    product_id: str
    total_inward: int
    total_outward: int
    total_return: int
    total_damaged: int
    total_expired: int
    total_transfer: int
    current_stock_estimate: int
    movements: List[InventoryLedgerEntry]
