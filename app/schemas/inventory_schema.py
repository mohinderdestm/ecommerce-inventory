from pydantic import BaseModel
from typing import Optional

class InventoryCreate(BaseModel):
    product_id: str
    quantity: int
    movement_type: str 

    warehouse_id: Optional[str] = None
    from_warehouse_id: Optional[str] = None
    to_warehouse_id: Optional[str] = None