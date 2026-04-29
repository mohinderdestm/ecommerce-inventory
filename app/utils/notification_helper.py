from app.services.notification_service import NotificationService


# ✅ USER NOTIFICATION
async def notify_user(user_id, title, message, notif_type):
    await NotificationService.create({
        "user_id": user_id,
        "title": title,
        "type": notif_type,
        "message": message
    })


# ✅ ADMIN NOTIFICATION

async def notify_admin(title, message, notif_type):
    await NotificationService.create({
        "role": "admin",
         "type": notif_type,
        "title": title,
        "message": message
    })

   