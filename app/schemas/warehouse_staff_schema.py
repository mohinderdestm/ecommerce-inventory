from pydantic import BaseModel
from typing import List


class AssignStaffSchema(BaseModel):
    staff_id: str


class WarehouseStaffResponse(BaseModel):
    id: str
    warehouse_id: str
    staff_id: str
    staff: dict


class BulkAssignStaff(BaseModel):
    warehouse_id: str
    staff_ids: List[str]
