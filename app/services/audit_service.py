from datetime import datetime
from app.core.database import db

class AuditService:

    @staticmethod
    async def log(
        user_id: str,
        action: str,
        entity_type: str,
        entity_id: str = None,
        value: dict = None,
        old_value: dict = None,
        new_value: dict = None
     ): 
        log = {
            "user_id": user_id,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "timestamp": datetime.utcnow()
        }

    # ✅ PRIORITY: use value if present
        if value:
           log["value"] = value
        else:
           log["old_value"] = old_value
           log["new_value"] = new_value

        await db["audit_logs"].insert_one(log)