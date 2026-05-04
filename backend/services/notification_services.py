# services/notification_service.py

from database import notifications_collection
from datetime import datetime


async def create_notification(
    user_email: str,
    title: str,
    message: str,
    notif_type: str = "general"
):

    notification = {
        "user_email": user_email,
        "title": title,
        "message": message,
        "type": notif_type,
        "read": False,
        "created_at": datetime.utcnow().isoformat()
    }

    await notifications_collection.insert_one(
        notification
    )