from fastapi import APIRouter, Depends, Query, HTTPException

from app.services.notification_service import NotificationService
from app.utils.dependencies import get_current_user


router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/")
async def list_notifications(
    include_read: bool = Query(default=False),
    limit: int = Query(default=100, ge=1, le=1000),
    user=Depends(get_current_user),
):
    return await NotificationService.list_notifications(
        user, include_read=include_read, limit=limit
    )


@router.post("/refresh")
async def refresh_notifications(user=Depends(get_current_user)):
    if user.get("role") not in {"admin", "manager"}:
        raise HTTPException(
            status_code=403, detail="Only admin and manager can refresh alerts"
        )
    await NotificationService.refresh_operational_alerts()
    return await NotificationService.list_notifications(
        user, include_read=False, limit=100
    )


@router.put("/{notification_id}/read")
async def mark_notification_read(notification_id: str, user=Depends(get_current_user)):
    return await NotificationService.mark_read(notification_id, user)


@router.put("/read-all")
async def mark_all_notifications_read(user=Depends(get_current_user)):
    return await NotificationService.mark_all_read(user)


@router.get("/logs")
async def notification_logs(
    limit: int = Query(default=500, ge=1, le=2000),
    user=Depends(get_current_user),
):
    try:
        return await NotificationService.list_logs(user, limit=limit)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
