from fastapi import APIRouter, Depends
from app.schemas.staff_schema import StaffCreate, StaffUpdate
from app.services.staff_service import StaffService
from app.utils.dependencies import get_current_user, get_request_audit_context
from app.schemas.staff_schema import BulkStaffCreate

router = APIRouter(prefix="/staff", tags=["Staff"])


@router.post("/")
async def create_staff(
    data: StaffCreate,
    user=Depends(get_current_user),
    audit_context=Depends(get_request_audit_context),
):
    return await StaffService.create_staff(data, user, audit_context=audit_context)


@router.get("/")
async def get_all_staff(user=Depends(get_current_user)):
    return await StaffService.get_all_staff(user)


@router.put("/{staff_id}")
async def update_staff(
    staff_id: str,
    data: StaffUpdate,
    user=Depends(get_current_user),
    audit_context=Depends(get_request_audit_context),
):
    return await StaffService.update_staff(
        staff_id, data, user, audit_context=audit_context
    )


@router.delete("/{staff_id}")
async def delete_staff(
    staff_id: str,
    user=Depends(get_current_user),
    audit_context=Depends(get_request_audit_context),
):
    return await StaffService.delete_staff(staff_id, user, audit_context=audit_context)


@router.post("/bulk")
async def bulk_create_staff(
    data: BulkStaffCreate,
    user=Depends(get_current_user),
    audit_context=Depends(get_request_audit_context),
):
    return await StaffService.bulk_create_staff(data, user, audit_context=audit_context)
