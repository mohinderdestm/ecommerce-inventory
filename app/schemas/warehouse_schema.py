from pydantic import BaseModel
from typing import Optional,List

class WarehouseCreate(BaseModel):
    name: str
    location: str
    manager_id: Optional[str] = None
    staff_ids: List[str] = []

class WarehouseUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    manager_id: Optional[str] = None
    status: Optional[str] = None
    staff_ids: List[str] = []