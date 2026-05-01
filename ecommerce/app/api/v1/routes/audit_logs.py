from typing import Optional
from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.audit_log import AuditLogListResponse
from app.services.audit_log_service import AuditLogService
from app.repositories.audit_log_repository import AuditLogRepository
from app.utils.dependencies import get_db, require_admin

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])

def get_audit_log_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> AuditLogService:
    return AuditLogService(audit_log_repo=AuditLogRepository(db))

@router.get(
    "/",
    response_model=AuditLogListResponse,
    summary="List and filter audit logs [Admin only]",
)
async def list_audit_logs(
    entity_type: Optional[str] = Query(default=None, description="Filter by entity type (e.g. product, purchase_order)"),
    user_id: Optional[str] = Query(default=None, description="Filter by user ID"),
    action: Optional[str] = Query(default=None, description="Filter by action (e.g. created, updated)"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: AuditLogService = Depends(get_audit_log_service),
    _: dict = Depends(require_admin),
):
    return await service.list_logs(
        entity_type=entity_type,
        user_id=user_id,
        action=action,
        page=page,
        page_size=page_size,
    )
