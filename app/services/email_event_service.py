from app.core.database import db
from datetime import datetime


class EmailEventService:

    @staticmethod
    async def create(data):

        data["created_at"] = datetime.utcnow()
        data["updated_at"] = datetime.utcnow()

        result = await db["email_events"].insert_one(data)

        return str(result.inserted_id)

    @staticmethod
    async def update(event_id, data):

        data["updated_at"] = datetime.utcnow()

        result = await db["email_events"].update_one(
            {
                "event_id": str(event_id)
            },
            {
                "$set": data
            }
        )

        print("Matched:", result.matched_count)
        print("Modified:", result.modified_count)