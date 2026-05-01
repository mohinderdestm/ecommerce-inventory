from datetime import datetime, timezone
from typing import Optional, Any

def build_audit_log_document(
    user_id: str,
    action: str,
    entity_type: str,
    entity_id: str,
    old_value: Optional[dict] = None,
    new_value: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> dict:
    return {
        "user_id": user_id,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "old_value": old_value,
        "new_value": new_value,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "timestamp": datetime.now(timezone.utc),
    }
