from fastapi import APIRouter
from app.services.notification_service import NotificationService
from app.core.database import db 

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/")
async def get_notifications(user_id: str = None, role: str = None):
    return await NotificationService.get(user_id, role)


@router.put("/read-all")
async def mark_all(user_id: str = None, role: str = None):
    query = {}

    if role == "admin":
        query["role"] = "admin"
    elif user_id:
        query["user_id"] = user_id
    else:
        return {"message": "No filter provided"} 

    await db["notifications"].update_many(
        query,
        {"$set": {"is_read": True}}
    )

    return {"message": "All marked as read"}