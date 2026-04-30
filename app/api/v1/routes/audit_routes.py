from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.schemas.audit_schema import AuditLogResponse
from app.services.audit_service import AuditService
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get("/", response_model=list[AuditLogResponse])
async def get_audit_logs(
    entity_type: Optional[str] = Query(default=None),
    entity_id: Optional[str] = Query(default=None),
    action: Optional[str] = Query(default=None),
    user_id: Optional[str] = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    user=Depends(get_current_user),
):
    return await AuditService.list_logs(
        user,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        user_id=user_id,
        limit=limit,
    )
