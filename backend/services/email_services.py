from database import email_logs_collection
from datetime import datetime


async def send_email_simulation(
    to,
    subject,
    message,
    type="general"
):

    await email_logs_collection.insert_one({

        "to": to,

        "subject": subject,

        "message": message,

        "type": type,

        "status": "sent",

        "created_at": datetime.utcnow().isoformat()

    })