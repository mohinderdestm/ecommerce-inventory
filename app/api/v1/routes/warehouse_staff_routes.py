from fastapi import APIRouter, Depends
from app.schemas.warehouse_staff_schema import AssignStaffSchema, BulkAssignStaff
from app.services.warehouse_staff_service import WarehouseStaffService
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/warehouse-staff", tags=["Warehouse Staff"])


@router.post("/bulk-assign")
async def bulk_assign_staff(data: BulkAssignStaff, user=Depends(get_current_user)):
    return await WarehouseStaffService.bulk_assign_staff(data, user)


@router.post("/{warehouse_id}")
async def assign_staff(
    warehouse_id: str, data: AssignStaffSchema, user=Depends(get_current_user)
):
    return await WarehouseStaffService.assign_staff(warehouse_id, data.staff_id, user)


@router.get("/{warehouse_id}")
async def get_staff(warehouse_id: str, user=Depends(get_current_user)):
    return await WarehouseStaffService.get_staff_by_warehouse(warehouse_id, user)


@router.delete("/{warehouse_id}/{staff_id}")
async def remove_staff(
    warehouse_id: str, staff_id: str, user=Depends(get_current_user)
):
    return await WarehouseStaffService.remove_staff(warehouse_id, staff_id, user)


@router.get("/")
async def get_all_assignments(user=Depends(get_current_user)):
    return await WarehouseStaffService.get_all_assignments(user)
